"""Blender-first v4 review pipeline for the World Cup neighbors scene."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any

import yaml

from bambu.review3d import build_target_review_crops, build_visual_contact_sheet, detect_blender


V4_FILES = ("scene", "people", "visual_targets", "print_constraints", "acceptance")


def load_v4_spec(project: Path | str, *, revision: str = "v4") -> dict[str, Any]:
    """Load the v4 Blender-first design packet."""

    project_path = Path(project)
    design_dir = project_path / "designs" / revision
    spec = {name: yaml.safe_load((design_dir / f"{name}.yaml").read_text()) or {} for name in V4_FILES}
    target = project_path / spec["visual_targets"]["primary_target"]["path"]
    generator = project_path / "source" / revision / "blender_scene.py"
    spec.update(
        {
            "project": str(project_path),
            "revision": revision,
            "design_dir": str(design_dir),
            "target_image": target,
            "generator_script": generator,
        }
    )
    return spec


def build_blender_v4_command(
    *,
    blender: str,
    project: Path | str,
    output_dir: Path | str,
    spec_json: Path | None = None,
    revision: str = "v4",
) -> list[str]:
    """Build a background Blender command for the v4 visual generator."""

    project_path = Path(project)
    script = project_path / "source" / revision / "blender_scene.py"
    command = [
        blender,
        "--background",
        "--python",
        str(script),
        "--",
        "--project",
        str(project_path),
        "--output-dir",
        str(output_dir),
    ]
    if spec_json is not None:
        command.extend(["--spec-json", str(spec_json)])
    return command


def render_v4_candidate(
    project: Path | str,
    *,
    outputs_root: Path = Path("outputs"),
    revision: str = "v4",
    blender: str | None = None,
) -> dict[str, Any]:
    """Run Blender v4 generation, then build a target-vs-current contact sheet."""

    project_path = Path(project)
    spec = load_v4_spec(project_path, revision=revision)
    output_slug = spec["scene"]["generation"].get("output_slug", f"{project_path.name}-{revision}")
    review_dir = outputs_root / "review" / output_slug
    review_dir.mkdir(parents=True, exist_ok=True)
    spec_json = review_dir / "spec.json"
    serializable_spec = {
        key: value for key, value in spec.items() if key not in {"target_image", "generator_script"}
    }
    serializable_spec["target_image"] = str(spec["target_image"])
    serializable_spec["generator_script"] = str(spec["generator_script"])
    spec_json.write_text(json.dumps(serializable_spec, indent=2))

    executable = blender or detect_blender()
    if not executable:
        blender_report = {"available": False, "reason": "Blender not found", "paths": []}
    else:
        command = build_blender_v4_command(
            blender=executable,
            project=project_path,
            output_dir=review_dir,
            spec_json=spec_json,
            revision=revision,
        )
        completed = subprocess.run(command, check=False, text=True, capture_output=True)
        paths = sorted(
            str(path)
            for path in review_dir.glob("*.png")
            if path.name != "visual-contact-sheet.png"
        )
        blender_report = {
            "available": True,
            "returncode": completed.returncode,
            "ok": completed.returncode == 0,
            "paths": paths,
            "stderr_tail": completed.stderr[-1000:],
        }

    current_images = {
        Path(path).stem: Path(path)
        for path in blender_report.get("paths", [])
        if Path(path).exists() and Path(path).suffix.lower() == ".png"
    }
    target_images = build_target_review_crops(
        spec["target_image"],
        review_dir / "target-crops",
        crop_regions={
            name: tuple(region)
            for name, region in spec["visual_targets"].get("crop_views", {}).items()
        },
    )
    contact_sheet = None
    if current_images:
        contact_sheet = build_visual_contact_sheet(
            target_images=target_images,
            current_images=current_images,
            output_path=review_dir / "visual-contact-sheet.png",
            title=f"{output_slug} target vs Blender v4",
        )

    return {
        "project": output_slug,
        "review_dir": str(review_dir),
        "target_image": str(spec["target_image"]),
        "stl": str(review_dir / "scene.stl"),
        "blender": blender_report,
        "visual_contact_sheet": contact_sheet,
        "printer_contact": False,
        "manual_boundary": "No printer, slicer, or Bambu Studio contact. This is visual CAD review only.",
    }
