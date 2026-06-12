"""Safe local build pipeline for the current Bambu prototype."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

from bambu.cli import default_world_cup_scene
from bambu.figurine import generate_scad
from bambu.preflight import detect_tools
from bambu.slicer import SliceRequest, build_slice_plan


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

