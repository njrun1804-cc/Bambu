"""Detect local 3D-printing tools and describe the next safe step."""

from __future__ import annotations

from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class ToolStatus:
    name: str
    available: bool
    path: str | None
    hint: str


TOOL_CANDIDATES: dict[str, tuple[str, ...]] = {
    "openscad": ("openscad",),
    "bambu_studio": ("bambu-studio", "BambuStudio", "BambuStudio.app"),
    "orcaslicer": ("orcaslicer", "OrcaSlicer", "orca-slicer"),
    "blender": ("blender",),
}

TOOL_HINTS: dict[str, str] = {
    "openscad": "Install OpenSCAD to export .scad files to STL/3MF/PNG.",
    "bambu_studio": "Install OpenSCAD first, then install Bambu Studio to slice for the A1 mini.",
    "orcaslicer": "Install OrcaSlicer if you prefer its slicer CLI over Bambu Studio.",
    "blender": "Install Blender for future sculpt/mesh repair workflows; it is optional for OpenSCAD.",
}


def _first_on_path(names: tuple[str, ...]) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def detect_tools() -> dict[str, ToolStatus]:
    """Return availability for the external tools this repo can use."""

    report: dict[str, ToolStatus] = {}
    for key, candidates in TOOL_CANDIDATES.items():
        path = _first_on_path(candidates)
        report[key] = ToolStatus(
            name=key,
            available=path is not None,
            path=path,
            hint=TOOL_HINTS[key],
        )
    return report


def next_steps(
    report: dict[str, object] | None = None,
    *,
    has_scad: bool = False,
    has_stl: bool = False,
) -> list[str]:
    """Explain the next actions in beginner-friendly order."""

    tools = report or detect_tools()
    steps: list[str] = []

    if not has_scad:
        steps.append("Create or generate an OpenSCAD .scad file from a brief.")
    if has_scad and not _available(tools, "openscad"):
        steps.append("Install OpenSCAD, then export the .scad file to STL.")
    elif has_scad and not has_stl:
        steps.append("Run OpenSCAD export to create an STL.")
    if has_stl and not (_available(tools, "bambu_studio") or _available(tools, "orcaslicer")):
        steps.append("Install Bambu Studio or OrcaSlicer, then slice the STL for the A1 mini.")
    elif has_stl:
        steps.append("Build a slicer command, review supports, and export .gcode.3mf.")

    if len(steps) == 1 and not _available(tools, "openscad"):
        steps.append("Install OpenSCAD when you are ready to turn .scad into STL.")

    return steps


def _available(report: dict[str, object], key: str) -> bool:
    item = report.get(key)
    return bool(getattr(item, "available", False))

