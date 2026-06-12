"""Local MCP server for agent-assisted Bambu workflows.

Run with:
    python3 -m bambu.mcp_server
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bambu.cli import default_world_cup_scene
from bambu.figurine import generate_scad
from bambu.preflight import detect_tools, next_steps, serialize_report
from bambu.pipeline import build_world_cup_prototype
from bambu.slicer import SliceRequest, build_slice_plan


def bambu_doctor() -> dict[str, Any]:
    """Return setup status and beginner-friendly next steps."""

    report = detect_tools()
    return {
        "tools": serialize_report(report),
        "next_steps": next_steps(report),
        "safety": [
            "This MCP server does not start print jobs.",
            "Review meshes, supports, scale, filament, bed type, and first layer before printing.",
            "Keep private reference photos under private/ and out of git.",
        ],
    }


def bambu_generate_world_cup_figurines(
    output: str = "outputs/world-cup-neighbors.scad",
) -> dict[str, Any]:
    """Generate the default Brazil-watch-party figurine OpenSCAD source."""

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    scad = generate_scad(default_world_cup_scene())
    out.write_text(scad)
    return {
        "output": str(out),
        "bytes": len(scad.encode("utf-8")),
        "next": [
            "Open the .scad file in OpenSCAD and export STL.",
            "Call bambu_slice_plan with the STL path before opening the slicer.",
        ],
    }


def bambu_openscad_export_plan(
    scad_path: str,
    output_path: str = "outputs/model.stl",
) -> dict[str, Any]:
    """Return the OpenSCAD command to export a .scad file to STL."""

    report = detect_tools()
    openscad = report["openscad"].path or "openscad"
    command = [openscad, "-o", output_path, scad_path]
    return {
        "tool": "openscad",
        "command": command,
        "checklist": [
            "Render preview before export if the model changed materially.",
            "If OpenSCAD hangs on first launch, open the app once from /Applications.",
            "Use STL for first slice; keep the .scad file as the editable source.",
        ],
    }


def bambu_slice_plan(
    model_path: str,
    output_path: str = "outputs/model.gcode.3mf",
    slicer: str = "bambu-studio",
) -> dict[str, Any]:
    """Return a slicer command and print-review checklist without starting the printer."""

    executable = _detected_slicer_path(slicer)
    plan = build_slice_plan(
        SliceRequest(
            model_path=Path(model_path),
            output_path=Path(output_path),
            slicer=slicer,
            executable=executable,
            resolve_paths=True,
        )
    )
    return {
        "tool": plan.tool,
        "command": plan.command,
        "checklist": plan.checklist,
    }


def bambu_build_world_cup_prototype(
    output_dir: str = "outputs",
    slicer: str = "bambu-studio",
) -> dict[str, Any]:
    """Generate SCAD, export STL, and slice 3MF for the watch-party prototype."""

    return build_world_cup_prototype(Path(output_dir), slicer=slicer)


def _detected_slicer_path(slicer: str) -> str | None:
    normalized = slicer.strip().lower().replace("_", "-")
    key = "orcaslicer" if normalized in {"orca", "orca-slicer", "orcaslicer"} else "bambu_studio"
    status = detect_tools().get(key)
    if status and status.available:
        return status.path
    return None


def _build_mcp():
    from mcp.server.fastmcp import FastMCP

    server = FastMCP("bambu_mcp")

    server.tool()(bambu_doctor)
    server.tool()(bambu_generate_world_cup_figurines)
    server.tool()(bambu_openscad_export_plan)
    server.tool()(bambu_slice_plan)
    server.tool()(bambu_build_world_cup_prototype)
    return server


def main() -> None:
    """Run the local stdio MCP server."""

    _build_mcp().run()


if __name__ == "__main__":
    main()
