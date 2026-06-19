"""Automated hybrid-lane mesh fusion: build123d body + Meshy head STLs."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import trimesh
import yaml

from bambu.cad.archetypes.seated_diorama import head_stub_centers
from bambu.cad.specs import character_metrics, load_specs
from bambu.mesh import analyze_islands, analyze_overhangs, inspect_mesh
from bambu.mesh_lane import (
    DEFAULT_SINK_MM,
    FUSION_MANIFEST_NAME,
    fusion_manifest_path,
    load_fusion_manifest,
)
from bambu.projects import load_project, sync_project_artifacts


DEFAULT_HEAD_ROTATIONS: dict[str, tuple[float, float, float]] = {
    # Meshy image-to-3d exports are Y-up; seated_diorama faces -Y.
    "woman": (0.0, 0.0, 180.0),
    "dog": (0.0, 180.0, 0.0),
}

DEFAULT_HEAD_CAP_FRACTION: dict[str, float] = {
    # Meshy bust crops include shoulders/feet; keep the upper cap only.
    "woman": 0.50,
    "dog": 0.40,
}

DEFAULT_MIN_COMPONENT_FACES = 20
DEFAULT_MIN_COMPONENT_EXTENT_MM = 0.8
DEFAULT_SEAT_TRIM_MARGIN_MM = 4.0
DEFAULT_BRIDGE_SINK_OVERLAP_MM = 1.0
DEFAULT_HEAD_REPAIR_MERGE_PCT = 0.5
DEFAULT_FUSED_REPAIR_MERGE_PCT = 0.25
DEFAULT_STUB_EXTRA_SINK_MM: dict[str, float] = {
    # Woman head bottom rim creates neck-ring island seeds unless seated deeper.
    "woman": 4.0,
}
DEFAULT_ISLAND_BUMP_PRUNE_RADIUS_MM = 1.5
DEFAULT_ISLAND_BUMP_PRUNE_MAX_ITER = 12
# Refuse to prune more than this fraction of faces in one pass: trimming a blocking bump
# should remove a few faces, not gouge the head. A larger removal means the island seed
# landed on real geometry, so we stop and let the island gate report it for human review.
DEFAULT_ISLAND_BUMP_PRUNE_MAX_FRACTION = 0.05


def seated_diorama_stub_centers() -> dict[str, tuple[float, float, float]]:
    """Alias for manifest scaffolding."""

    return head_stub_centers()


@dataclass(frozen=True)
class HeadFusionSpec:
    head_id: str
    source: Path
    stub_center: tuple[float, float, float]
    target_width_mm: float
    target_height_mm: float | None = None
    cap_fraction: float | None = None
    scale: float = 1.0
    sink_mm: float = DEFAULT_SINK_MM
    extra_sink_mm: float = 0.0
    rotation_deg: tuple[float, float, float] = (-90.0, 0.0, 0.0)


def fuse_hybrid_project(
    project_path: Path | str,
    *,
    revision: str | None = None,
    outputs_root: Path = Path("outputs"),
    body_stl: Path | None = None,
    output_path: Path | None = None,
    repair: bool = True,
) -> dict[str, Any]:
    """Fuse body scaffold STL with Meshy head meshes per fusion_manifest.yaml."""

    project = Path(project_path)
    manifest = load_project(project / "project.yaml")
    rev = revision or manifest.get("current_revision", "v1")
    fusion = load_fusion_manifest(project, revision=rev)
    if not fusion:
        raise ValueError(f"Missing {FUSION_MANIFEST_NAME} under designs/{rev}/")

    repo_root = _repo_root(project)
    body_path = _resolve_body_stl(project, repo_root, fusion, body_stl, outputs_root=outputs_root)
    body_mesh = trimesh.load(body_path, force="mesh")
    if not isinstance(body_mesh, trimesh.Trimesh):
        raise ValueError(f"Body artifact must be a single mesh: {body_path}")

    specs = _load_head_specs(project, fusion, repo_root, revision=rev)
    fused_mesh = fuse_head_specs(body_mesh, specs)
    if repair:
        fused_mesh, mesh_report = repair_fused_mesh(fused_mesh)
    else:
        mesh_report = _mesh_report(fused_mesh)

    fused_rel = fusion.get("fused_artifact", f"outputs/{manifest['slug']}-{rev.split('.')[0]}-fused.stl")
    fused_path = output_path or _resolve_project_path(project, repo_root, fused_rel, outputs_root=outputs_root)
    fused_path.parent.mkdir(parents=True, exist_ok=True)
    fused_mesh.export(fused_path)

    on_disk = inspect_mesh(fused_path)
    overhang_report = analyze_overhangs(fused_path)
    island_report = analyze_islands(fused_path)
    gates_ok = (
        on_disk.get("watertight_manifold")
        and overhang_report.get("ok")
        and island_report.get("ok")
    )

    fusion["fusion_tool"] = "bambu"
    # Status reflects the gates computed from the exported file (watertight + overhang +
    # island), not the weaker in-memory repair metric, so the durable manifest can't read
    # "complete" while a disk gate failed.
    fusion["fusion_status"] = "complete" if gates_ok else "complete_with_warnings"
    fusion["fusion_completed_at"] = _now()
    fusion["fusion_strategy"] = "merge"
    fusion_manifest_path(project, revision=rev).write_text(yaml.safe_dump(fusion, sort_keys=False))
    _update_provenance_fusion(project, fused_rel=str(fused_rel), gates_ok=gates_ok)

    head_reports = [
        {
            "id": spec.head_id,
            "source": str(spec.source),
            "stub_center": list(spec.stub_center),
            "anchor": list(spec.stub_center),
            "target_width_mm": spec.target_width_mm,
            "scale": spec.scale,
            "sink_mm": spec.sink_mm,
            "rotation_deg": list(spec.rotation_deg),
        }
        for spec in specs
    ]
    artifacts = sync_project_artifacts(project, outputs_root=outputs_root)
    return {
        "project": manifest["slug"],
        "revision": rev,
        "body_stl": str(body_path),
        "fused_stl": str(fused_path),
        "heads": head_reports,
        "mesh": on_disk,
        "overhangs": overhang_report,
        "islands": island_report,
        "gates_ok": gates_ok,
        "repair": mesh_report,
        "artifacts": artifacts,
        "manual_boundary": (
            "Automated mesh merge fuses Meshy heads onto the build123d body scaffold. "
            "Non-manifold Meshy topology may fail watertight or island gates; "
            "Shapr3D remains an optional manual override."
        ),
    }


def fuse_project_meshes(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Backward-compatible alias."""

    return fuse_hybrid_project(*args, **kwargs)


def fuse_head_specs(body: trimesh.Trimesh, specs: list[HeadFusionSpec]) -> trimesh.Trimesh:
    """Align each head spec and merge onto the body mesh without neck-bridge cylinders."""

    heads: list[trimesh.Trimesh] = []
    for spec in specs:
        raw = trimesh.load(spec.source, force="mesh")
        if not isinstance(raw, trimesh.Trimesh):
            raise ValueError(f"Head mesh must be a single Trimesh: {spec.source}")
        cleaned = clean_head_mesh(raw)
        cleaned = repair_head_mesh(cleaned)
        rotation_deg = spec.rotation_deg
        capped = cap_oriented_head(cleaned, rotation_deg, keep_top_fraction=spec.cap_fraction)
        aligned = align_head_to_stub(
            capped,
            spec.stub_center,
            target_width_mm=spec.target_width_mm,
            target_height_mm=spec.target_height_mm,
            scale=spec.scale,
            sink_mm=spec.sink_mm + spec.extra_sink_mm,
            rotation_deg=(0.0, 0.0, 0.0),
        )
        seat_z = _seat_trim_z(spec)
        trimmed = trim_mesh_below_z(aligned, seat_z)
        heads.append(trimmed)
    fused = merge_meshes(body, heads)
    return cull_small_components(fused)


def clean_head_mesh(
    mesh: trimesh.Trimesh,
    *,
    min_faces: int = 50,
    min_extent_mm: float = DEFAULT_MIN_COMPONENT_EXTENT_MM,
) -> trimesh.Trimesh:
    """Drop tiny floating components from Meshy exports.

    Meshy image-to-3d often ships a pedestal/base island beside the head; keep the
    largest component so alignment does not park scrap geometry on the neck stub.
    """

    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        cleaned = mesh.copy()
    else:
        ranked = sorted(parts, key=lambda part: len(part.faces), reverse=True)
        cleaned = ranked[0]
    cleaned.merge_vertices()
    cleaned.update_faces(cleaned.unique_faces())
    cleaned.remove_unreferenced_vertices()
    return cleaned


def cap_oriented_head(
    mesh: trimesh.Trimesh,
    rotation_deg: tuple[float, float, float],
    *,
    keep_top_fraction: float | None = None,
) -> trimesh.Trimesh:
    """Rotate a Meshy export and discard bust/pedestal geometry below the head cap."""

    fraction = 0.55 if keep_top_fraction is None else float(keep_top_fraction)
    fraction = min(max(fraction, 0.2), 0.9)
    oriented = mesh.copy()
    oriented.merge_vertices()
    for angle, axis in zip(rotation_deg, ([1, 0, 0], [0, 1, 0], [0, 0, 1])):
        if angle:
            oriented.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle), axis))
    cutoff = float(np.percentile(oriented.vertices[:, 2], (1.0 - fraction) * 100.0))
    return trim_mesh_below_z(oriented, cutoff)


def cull_small_components(
    mesh: trimesh.Trimesh,
    *,
    min_faces: int = DEFAULT_MIN_COMPONENT_FACES,
    min_extent_mm: float = DEFAULT_MIN_COMPONENT_EXTENT_MM,
) -> trimesh.Trimesh:
    """Remove disconnected crumbs that fail island or manifold gates."""

    parts = mesh.split(only_watertight=False)
    if len(parts) <= 1:
        cleaned = mesh.copy()
    else:
        keep = [
            part
            for part in parts
            if len(part.faces) >= min_faces and max(float(axis) for axis in part.extents) >= min_extent_mm
        ]
        if not keep:
            keep = [max(parts, key=lambda part: len(part.faces))]
        cleaned = trimesh.util.concatenate(keep) if len(keep) > 1 else keep[0]
    cleaned.merge_vertices()
    cleaned.update_faces(cleaned.unique_faces())
    cleaned.remove_unreferenced_vertices()
    return cleaned


def trim_mesh_below_z(mesh: trimesh.Trimesh, z_min: float) -> trimesh.Trimesh:
    """Drop faces whose lowest vertex sits below the seating plane."""

    keep = [
        face_idx
        for face_idx, tri in enumerate(mesh.faces)
        if float(mesh.vertices[tri, 2].min()) >= z_min
    ]
    if len(keep) == len(mesh.faces):
        return mesh
    trimmed = mesh.copy()
    trimmed.update_faces(keep)
    trimmed.remove_unreferenced_vertices()
    return trimmed


def _seat_trim_z(spec: HeadFusionSpec) -> float:
    return max(1.0, spec.stub_center[2] - spec.sink_mm - DEFAULT_SEAT_TRIM_MARGIN_MM)


def align_head_to_stub(
    mesh: trimesh.Trimesh,
    stub_center: tuple[float, float, float],
    *,
    target_width_mm: float,
    target_height_mm: float | None = None,
    scale: float = 1.0,
    sink_mm: float = DEFAULT_SINK_MM,
    rotation_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> trimesh.Trimesh:
    """Rotate, scale, and seat a Meshy head on a build123d neck stub."""

    aligned = mesh.copy()
    aligned.merge_vertices()
    for angle, axis in zip(rotation_deg, ([1, 0, 0], [0, 1, 0], [0, 0, 1])):
        if angle:
            aligned.apply_transform(trimesh.transformations.rotation_matrix(np.radians(angle), axis))
    horizontal = max(float(aligned.extents[0]), float(aligned.extents[1]), 1e-6)
    scale_factor = (target_width_mm * scale) / horizontal
    if target_height_mm:
        vertical = max(float(aligned.extents[2]), 1e-6)
        scale_factor = min(scale_factor, (target_height_mm * scale) / vertical)
    aligned.apply_scale(scale_factor)
    stub = np.asarray(stub_center, dtype=float)
    centroid = aligned.centroid
    bottom_z = float(aligned.bounds[0, 2])
    aligned.apply_translation(
        [
            stub[0] - centroid[0],
            stub[1] - centroid[1],
            stub[2] - float(sink_mm) - bottom_z,
        ]
    )
    aligned.merge_vertices()
    return aligned


def merge_meshes(body: trimesh.Trimesh, heads: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    """Concatenate body + aligned heads without cross-welding vertices."""

    combined = trimesh.util.concatenate([body, *heads])
    combined.update_faces(combined.unique_faces())
    combined.remove_unreferenced_vertices()
    return combined


def repair_head_mesh(mesh: trimesh.Trimesh, *, merge_pct: float = DEFAULT_HEAD_REPAIR_MERGE_PCT) -> trimesh.Trimesh:
    """Pre-repair Meshy head exports before alignment."""

    try:
        return _pymeshlab_repair(mesh, merge_pct=merge_pct)
    except Exception:
        return mesh.copy()


def repair_fused_mesh(
    mesh: trimesh.Trimesh,
) -> tuple[trimesh.Trimesh, dict[str, Any]]:
    """Best-effort repair pass; returns the repaired mesh and gate metrics."""

    repaired = cull_small_components(mesh.copy())
    repair_path = "pymeshlab"
    repair_error: str | None = None
    try:
        repaired = _pymeshlab_stub_repair(repaired)
        repaired = prune_blocking_island_bumps(repaired)
        repaired = cull_small_components(repaired)
    except Exception as exc:
        # Record that the strong repair path failed and we fell back to trimesh's much
        # weaker fill_holes, so a reader of the report knows which repair actually ran.
        repair_path = "fill_holes_fallback"
        repair_error = str(exc)
        repaired.fill_holes()
    report = _mesh_report(repaired)
    report["repair_path"] = repair_path
    if repair_error:
        report["repair_error"] = repair_error
    return repaired, report


def prune_blocking_island_bumps(
    mesh: trimesh.Trimesh,
    *,
    radius_mm: float = DEFAULT_ISLAND_BUMP_PRUNE_RADIUS_MM,
    max_iterations: int = DEFAULT_ISLAND_BUMP_PRUNE_MAX_ITER,
    max_prune_fraction: float = DEFAULT_ISLAND_BUMP_PRUNE_MAX_FRACTION,
) -> trimesh.Trimesh:
    """Drop tiny downward-facing bumps flagged as blocking print islands."""

    repaired = mesh.copy()
    for _ in range(max_iterations):
        with _temporary_stl(repaired, label="islands") as stl_path:
            island_report = analyze_islands(stl_path)
        if island_report.get("ok"):
            return repaired
        seeds = [entry["seed"] for entry in island_report.get("islands", []) if entry.get("blocking")]
        if not seeds:
            return repaired

        vertices = np.asarray(repaired.vertices, dtype=float)
        faces = np.asarray(repaired.faces)
        keep = np.ones(len(faces), dtype=bool)
        for seed in seeds:
            seed_vec = np.asarray(seed, dtype=float)
            for face_idx, triangle in enumerate(faces):
                centroid = vertices[triangle].mean(axis=0)
                if float(np.linalg.norm(centroid - seed_vec)) <= radius_mm:
                    keep[face_idx] = False
        to_remove = int(np.count_nonzero(~keep))
        if to_remove and to_remove > max_prune_fraction * len(faces):
            # Over-broad removal would deform the head rather than trim a bump; stop and
            # leave the island for the gate to report instead of carving a hole.
            return repaired
        repaired.update_faces(keep)
        repaired.remove_unreferenced_vertices()
        repaired = _pymeshlab_stub_repair(repaired)
        repaired = cull_small_components(repaired)
    return repaired


def _pymeshlab_stub_repair(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Repair fused meshes without global merge_close_vertices (preserves Meshy heads)."""

    import pymeshlab

    with _temporary_stl(mesh, label="input") as stl_path, _temporary_stl(mesh, label="repaired") as out_path:
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(str(stl_path))
        ms.apply_filter("meshing_remove_duplicate_vertices")
        ms.apply_filter("meshing_remove_duplicate_faces")
        ms.apply_filter("meshing_remove_unreferenced_vertices")
        ms.apply_filter("meshing_repair_non_manifold_vertices")
        ms.apply_filter("meshing_repair_non_manifold_edges", method=0)
        ms.apply_filter("meshing_close_holes", maxholesize=500)
        ms.save_current_mesh(str(out_path))
        repaired = trimesh.load(out_path, force="mesh")
    if not isinstance(repaired, trimesh.Trimesh):
        raise ValueError("pymeshlab stub repair did not return a Trimesh")
    return repaired


def _pymeshlab_repair(mesh: trimesh.Trimesh, *, merge_pct: float) -> trimesh.Trimesh:
    import pymeshlab

    with _temporary_stl(mesh, label="input") as stl_path, _temporary_stl(mesh, label="repaired") as out_path:
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(str(stl_path))
        ms.apply_filter("meshing_remove_duplicate_vertices")
        ms.apply_filter("meshing_remove_duplicate_faces")
        ms.apply_filter("meshing_remove_unreferenced_vertices")
        ms.apply_filter("meshing_merge_close_vertices", threshold=pymeshlab.PercentageValue(merge_pct))
        ms.apply_filter("meshing_repair_non_manifold_edges", method=0)
        ms.apply_filter("meshing_repair_non_manifold_vertices")
        ms.apply_filter("meshing_close_holes", maxholesize=500)
        for filter_name, kwargs in (
            ("meshing_remove_connected_component_by_face_number", {"mincomponentsize": 20}),
            ("meshing_remove_connected_component_by_diameter", {"mincomponentdiag": pymeshlab.PercentageValue(1.0)}),
        ):
            try:
                ms.apply_filter(filter_name, **kwargs)
            except Exception:
                pass
        ms.save_current_mesh(str(out_path))
        repaired = trimesh.load(out_path, force="mesh")
    if not isinstance(repaired, trimesh.Trimesh):
        raise ValueError("pymeshlab repair did not return a Trimesh")
    return repaired


def _load_head_specs(
    project: Path,
    fusion: dict[str, Any],
    repo_root: Path,
    *,
    revision: str,
) -> list[HeadFusionSpec]:
    project_manifest = load_project(project / "project.yaml")
    stub_defaults: dict[str, tuple[float, float, float]] = {}
    if project_manifest.get("archetype") == "seated_diorama":
        stub_defaults = seated_diorama_stub_centers()

    metrics = {m["id"]: m for m in character_metrics(load_specs(project, revision=revision)) if m.get("id")}
    specs: list[HeadFusionSpec] = []
    for entry in fusion.get("head_meshes", []):
        head_id = str(entry.get("id", "subject"))
        align = entry.get("align") or {}
        stub_values = align.get("stub") or stub_defaults.get(head_id)
        if stub_values:
            placement = (float(stub_values[0]), float(stub_values[1]), float(stub_values[2]))
        else:
            placement = (
                float(align.get("x", 0.0)),
                float(align.get("y", 0.0)),
                float(align.get("z", 0.0)),
            )
        source = _resolve_project_path(project, repo_root, entry.get("source", ""))
        if not source.exists():
            raise FileNotFoundError(f"Head mesh missing for {head_id}: {source}")

        scale = float(align.get("scale", 1.0))
        base_width = float(metrics.get(head_id, {}).get("head_width_mm") or 20.0)
        base_height = metrics.get(head_id, {}).get("head_height_mm")
        if "target_width_mm" in align:
            target_width = float(align["target_width_mm"])
        else:
            target_width = base_width * scale
        target_height = float(align["target_height_mm"]) if "target_height_mm" in align else (
            float(base_height) * scale if base_height else None
        )
        cap_fraction = float(align["cap_fraction"]) if "cap_fraction" in align else DEFAULT_HEAD_CAP_FRACTION.get(head_id)
        extra_sink = float(align.get("extra_sink_mm", DEFAULT_STUB_EXTRA_SINK_MM.get(head_id, 0.0)))
        specs.append(
            HeadFusionSpec(
                head_id=head_id,
                source=source,
                stub_center=placement,
                target_width_mm=target_width,
                target_height_mm=target_height,
                cap_fraction=cap_fraction,
                scale=1.0,
                sink_mm=float(align.get("sink_mm", DEFAULT_SINK_MM)),
                extra_sink_mm=extra_sink,
                rotation_deg=_rotation_for_head(head_id, align),
            )
        )
    return specs


def _rotation_for_head(head_id: str, align: dict[str, Any]) -> tuple[float, float, float]:
    if "rotation" in align:
        values = align["rotation"]
        if isinstance(values, (list, tuple)) and len(values) == 3:
            return float(values[0]), float(values[1]), float(values[2])
    return DEFAULT_HEAD_ROTATIONS.get(head_id, (-90.0, 0.0, 0.0))


def _resolve_body_stl(
    project: Path,
    repo_root: Path,
    fusion: dict[str, Any],
    body_stl: Path | None,
    *,
    outputs_root: Path,
) -> Path:
    if body_stl is not None:
        path = Path(body_stl)
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    body_rel = fusion.get("body_artifact", "")
    stl_rel = body_rel.replace(".step", ".stl") if body_rel.endswith(".step") else body_rel
    path = _resolve_project_path(project, repo_root, stl_rel, outputs_root=outputs_root)
    if path.exists():
        return path
    step_path = _resolve_project_path(project, repo_root, body_rel, outputs_root=outputs_root)
    if step_path.exists():
        raise FileNotFoundError(
            f"Body STL missing ({path}). Run: uv run bambu export-body {project} --revision v1"
        )
    raise FileNotFoundError(path)


def _resolve_project_path(
    project: Path,
    repo_root: Path,
    rel: str | Path,
    *,
    outputs_root: Path | None = None,
) -> Path:
    rel_path = Path(rel)
    if rel_path.is_absolute():
        return rel_path
    if rel_path.parts and rel_path.parts[0] == "outputs":
        root = outputs_root or repo_root / "outputs"
        return root / Path(*rel_path.parts[1:])
    candidate = project / rel_path
    if candidate.exists():
        return candidate
    return repo_root / rel_path


def _repo_root(project: Path) -> Path:
    resolved = project.resolve()
    if (resolved / "pyproject.toml").exists():
        return resolved
    if (resolved.parent / "pyproject.toml").exists():
        return resolved.parent
    return resolved


def _mesh_report(mesh: trimesh.Trimesh) -> dict[str, Any]:
    with _temporary_stl(mesh) as path:
        return inspect_mesh(path)


@contextmanager
def _temporary_stl(mesh: trimesh.Trimesh, *, label: str = "mesh") -> Iterator[Path]:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=f"-{label}.stl", delete=False) as handle:
        path = Path(handle.name)
    try:
        mesh.export(path)
        yield path
    finally:
        path.unlink(missing_ok=True)


def _update_provenance_fusion(project: Path, *, fused_rel: str, gates_ok: bool) -> None:
    provenance_path = project / "mesh" / "provenance.yaml"
    if not provenance_path.exists():
        return
    provenance = yaml.safe_load(provenance_path.read_text()) or {}
    provenance.setdefault("fusion_readiness", {})
    provenance["fusion_readiness"].update(
        {
            "fused_stl": fused_rel,
            "fused_exists": True,
            "automated_fusion": True,
            "gates_ok": gates_ok,
            "ready_for_shapr3d": False,
        }
    )
    provenance_path.write_text(yaml.safe_dump(provenance, sort_keys=False))


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
