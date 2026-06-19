"""Safe local build pipelines: prototypes and full project handoff."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
from typing import Any

from bambu.cli import default_world_cup_scene, export_build123d_project
from bambu.design_pipeline import load_design_spec, validate_design_spec
from bambu.figurine import generate_scad
from bambu.handoff import inspect_print_handoff
from bambu.mesh import analyze_islands
from bambu.mesh_fusion import fuse_hybrid_project
from bambu.mesh_lane import load_fusion_manifest
from bambu.meshy import MeshyError, meshy_concept, meshy_head
from bambu.preflight import detect_tools
from bambu.printability import analyze_stl_overhangs, load_printer_context, qc_sliced_3mf
from bambu.projects import load_project, sync_project_artifacts
from bambu.review3d import load_review_views, review_project_3d
from bambu.slicer import SliceRequest, build_slice_plan, run_slice, sliced_output_for_stl


@dataclass
class PipelineOptions:
    revision: str | None = None
    outputs_root: Path = Path("outputs")
    slicer: str = "bambu-studio"
    slice_timeout_seconds: int = 600
    skip_meshy: bool = False
    force_meshy: bool = False
    force_fuse: bool = False
    force_slice: bool = False
    no_render: bool = False
    repair: bool = True
    context_path: Path = Path("profiles/bambu-a1-mini/context.yaml")
    overhang_budget_mm2: float = 150.0


@dataclass
class PipelineStepResult:
    name: str
    status: str
    detail: str = ""
    artifact: str | None = None


@dataclass
class ProjectPipelineResult:
    project: str
    revision: str
    lane: str
    steps: list[PipelineStepResult] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    qc_ok: bool = False
    handoff_ready: bool = False
    manual_boundaries: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        acceptable = {"pass", "skip", "warn"}
        return (
            all(step.status in acceptable for step in self.steps)
            and self.qc_ok
            and self.handoff_ready
        )

    @property
    def fused_stl(self) -> str | None:
        return self.artifacts.get("fused_stl") or self.artifacts.get("stl")

    @property
    def sliced(self) -> str | None:
        return self.artifacts.get("sliced")

    @property
    def manual_boundary(self) -> str:
        return "\n".join(self.manual_boundaries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "revision": self.revision,
            "lane": self.lane,
            "ok": self.ok,
            "qc_ok": self.qc_ok,
            "handoff_ready": self.handoff_ready,
            "artifacts": self.artifacts,
            "steps": [step.__dict__ for step in self.steps],
            "manual_boundaries": self.manual_boundaries,
        }


def build_world_cup_prototype(
    output_dir: Path = Path("outputs"),
    *,
    slicer: str = "bambu-studio",
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    """Generate SCAD, export STL, and slice 3MF without starting a print job."""

    output_dir.mkdir(parents=True, exist_ok=True)
    scad_path = output_dir / "world-cup-neighbors.scad"
    stl_path = output_dir / "world-cup-neighbors.stl"
    gcode_3mf_path = output_dir / "world-cup-neighbors.gcode.3mf"

    scad_path.write_text(generate_scad(default_world_cup_scene()))

    openscad = detect_tools()["openscad"].path or "openscad"
    export_cmd = [openscad, "-o", str(stl_path.resolve()), str(scad_path.resolve())]
    export_result = _run(export_cmd, timeout_seconds)

    slice_plan = build_slice_plan(
        SliceRequest(
            model_path=stl_path,
            output_path=gcode_3mf_path,
            slicer=slicer,
            executable=_detected_slicer_path(slicer),
            resolve_paths=True,
        )
    )
    slice_result = _run(slice_plan.command, timeout_seconds)

    return {
        "scad": str(scad_path),
        "stl": str(stl_path),
        "sliced": str(gcode_3mf_path),
        "export_command": export_cmd,
        "slice_command": slice_plan.command,
        "export_returncode": export_result.returncode,
        "slice_returncode": slice_result.returncode,
        "checklist": slice_plan.checklist,
        "manual_boundary": "Open the sliced project in Bambu Studio/OrcaSlicer and review it before printing.",
    }


def run_project_pipeline(
    project_path: Path | str,
    options: PipelineOptions | None = None,
) -> ProjectPipelineResult:
    """Run hybrid/build123d pipeline through headless slice, QC, and handoff."""

    opts = options or PipelineOptions()
    project = Path(project_path)
    manifest = load_project(project / "project.yaml")
    rev = opts.revision or manifest.get("current_revision", "v1")
    lane = manifest.get("lane", "build123d")
    slug = manifest["slug"]
    material = manifest.get("material", {}).get("name", "Bambu PLA Basic")
    result = ProjectPipelineResult(project=slug, revision=rev, lane=lane)

    def record(name: str, status: str, detail: str = "", artifact: str | None = None) -> None:
        result.steps.append(PipelineStepResult(name=name, status=status, detail=detail, artifact=artifact))

    spec = load_design_spec(project, revision=rev)
    design_report = validate_design_spec(spec)
    if design_report["ok"]:
        record("design-check", "pass", "specs valid")
    else:
        record("design-check", "fail", "; ".join(design_report["errors"]))
        return result

    if lane == "hybrid" and not opts.skip_meshy:
        concept_path = project / "photos" / "reference" / "concept-meshy.png"
        if concept_path.exists() and not opts.force_meshy:
            record("meshy concept", "skip", "concept sheet exists", str(concept_path))
        else:
            try:
                concept = meshy_concept(project)
                record("meshy concept", "pass", "concept sheet generated", concept["concept_path"])
            except MeshyError as exc:
                record("meshy concept", "fail", str(exc))
                return result

        for subject in _head_subjects(project, rev):
            head_path = project / "mesh" / f"{subject}-head.stl"
            if head_path.exists() and not opts.force_meshy:
                record(f"meshy head {subject}", "skip", "head STL exists", str(head_path))
                continue
            try:
                head = meshy_head(project, subject=subject)
                record(f"meshy head {subject}", "pass", "head STL generated", head["stl_path"])
            except MeshyError as exc:
                record(f"meshy head {subject}", "fail", str(exc))
                return result
    elif lane == "hybrid":
        record("meshy", "skip", "--skip-meshy")

    rev_base = rev.split(".", 1)[0]
    if lane == "hybrid":
        body_stl = _resolve_repo_path(
            project,
            _body_stl_rel(project, rev, slug, rev_base),
            outputs_root=opts.outputs_root,
        )
        if body_stl.exists() and not opts.force_fuse:
            record("export-body", "skip", "body STL exists", str(body_stl))
        else:
            export = export_build123d_project(
                project,
                output_dir=opts.outputs_root,
                output_slug=f"{slug}-{rev_base}-body",
                revision=rev,
                body_only=True,
            )
            body_stl = Path(export["stl"])
            record("export-body", "pass", "body scaffold exported", str(body_stl))
    else:
        model_stl = opts.outputs_root / f"{slug}-{rev_base}.stl"
        if model_stl.exists():
            record("export-build123d", "skip", "STL exists", str(model_stl))
        else:
            export = export_build123d_project(
                project,
                output_dir=opts.outputs_root,
                output_slug=f"{slug}-{rev_base}",
                revision=rev,
            )
            model_stl = Path(export["stl"])
            record("export-build123d", "pass", "model exported", str(model_stl))

    if lane == "hybrid":
        fused_rel = _fused_stl_rel(project, rev, slug, rev_base)
        fused_stl = _resolve_repo_path(project, fused_rel, outputs_root=opts.outputs_root)
        if fused_stl.exists() and not opts.force_fuse:
            record("fuse-mesh", "skip", "fused STL exists", str(fused_stl))
        else:
            fusion = fuse_hybrid_project(
                project,
                revision=rev,
                outputs_root=opts.outputs_root,
                repair=opts.repair,
            )
            fused_stl = Path(fusion["fused_stl"])
            status = "pass" if fusion.get("gates_ok") else "warn"
            record(
                "fuse-mesh",
                status,
                f"watertight={fusion.get('mesh', {}).get('watertight_manifold')}",
                str(fused_stl),
            )
        printable_stl = fused_stl
        result.artifacts["fused_stl"] = str(fused_stl)
    else:
        printable_stl = model_stl
        result.artifacts["stl"] = str(printable_stl)

    views = load_review_views(project, revision=rev)
    review = review_project_3d(
        project,
        outputs_root=opts.outputs_root,
        render=not opts.no_render,
        views=views,
        revision=rev,
        stl_path=printable_stl,
        skip_export=True,
        skip_freecad=True,
    )
    release_ok = (
        review.get("fits_a1_mini")
        and review.get("mesh", {}).get("watertight_manifold")
        and review.get("overhangs", {}).get("ok")
        and review.get("islands", {}).get("ok")
    )
    if release_ok:
        record("release-check", "pass", f"STL {printable_stl.name}")
    else:
        record("release-check", "fail", "mesh/overhang/island gates failed")
        return result

    sliced_path = sliced_output_for_stl(printable_stl)
    if sliced_path.exists() and not opts.force_slice:
        record("slice", "skip", "sliced 3MF exists", str(sliced_path))
    else:
        slice_result = run_slice(
            SliceRequest(
                model_path=printable_stl,
                output_path=sliced_path,
                slicer=opts.slicer,
                executable=_detected_slicer_path(opts.slicer),
                material=material,
                resolve_paths=True,
            ),
            timeout_seconds=opts.slice_timeout_seconds,
        )
        if not slice_result.ok:
            record(
                "slice",
                "fail",
                f"slicer exit {slice_result.returncode}",
                str(sliced_path),
            )
            return result
        record("slice", "pass", "headless slicer CLI", str(sliced_path))
    result.artifacts["sliced"] = str(sliced_path)

    context = load_printer_context(opts.context_path)
    stl_report = analyze_stl_overhangs(printable_stl, patch_budget_mm2=opts.overhang_budget_mm2)
    island_report = analyze_islands(printable_stl)
    slice_qc = qc_sliced_3mf(sliced_path, context=context)
    result.qc_ok = bool(slice_qc.get("ok") and stl_report.get("ok", True) and island_report.get("ok", True))
    if result.qc_ok:
        record("qc", "pass", "printability checks passed")
    else:
        record("qc", "fail", "QC failed on STL or sliced 3MF")
        return result

    handoff = inspect_print_handoff(sliced_path)
    result.handoff_ready = handoff.ready_for_manual_review
    if handoff.ready_for_manual_review:
        record("handoff", "pass", handoff.open_command, str(sliced_path))
    else:
        missing = ", ".join(handoff.missing_markers) or "package incomplete"
        record("handoff", "fail", missing, str(sliced_path))
        return result

    sync_project_artifacts(project, outputs_root=opts.outputs_root)
    result.manual_boundaries.append(
        "Pipeline automated design → mesh → slice → QC. "
        "Open the sliced .gcode.3mf in Bambu Studio for final plate/support review, "
        "then manually send to the printer when satisfied."
    )
    return result


def _head_subjects(project: Path, revision: str) -> list[str]:
    fusion = load_fusion_manifest(project, revision=revision)
    if fusion and fusion.get("head_meshes"):
        return [str(head["id"]) for head in fusion["head_meshes"]]
    return ["woman", "dog"]


def _body_stl_rel(project: Path, revision: str, slug: str, rev_base: str) -> str:
    fusion = load_fusion_manifest(project, revision=revision)
    body = (fusion or {}).get("body_artifact", f"outputs/{slug}-{rev_base}-body.step")
    if str(body).endswith(".stl"):
        return str(body)
    return f"outputs/{slug}-{rev_base}-body.stl"


def _fused_stl_rel(project: Path, revision: str, slug: str, rev_base: str) -> str:
    fusion = load_fusion_manifest(project, revision=revision)
    if fusion and fusion.get("fused_artifact"):
        return str(fusion["fused_artifact"])
    return f"outputs/{slug}-{rev_base}-fused.stl"


def _resolve_repo_path(project: Path, rel: str, *, outputs_root: Path) -> Path:
    rel_path = Path(rel)
    if rel_path.is_absolute():
        return rel_path
    if rel_path.parts and rel_path.parts[0] == "outputs":
        return outputs_root / Path(*rel_path.parts[1:])
    return project / rel_path


def _run(command: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout[-2000:]}\n"
            f"stderr:\n{result.stderr[-2000:]}"
        )
    return result


def _detected_slicer_path(slicer: str) -> str | None:
    normalized = slicer.strip().lower().replace("_", "-")
    key = "orcaslicer" if normalized in {"orca", "orca-slicer", "orcaslicer"} else "bambu_studio"
    status = detect_tools().get(key)
    if status and status.available:
        return status.path
    return None
