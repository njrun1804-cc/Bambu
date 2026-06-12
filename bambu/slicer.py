"""Dry-run-safe slicer command construction for Bambu printers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SliceRequest:
    model_path: Path
    output_path: Path
    slicer: str = "bambu-studio"
    bed_type: str = "Textured PEI Plate"
    plate: int = 0
    machine_profile: Path | None = None
    process_profile: Path | None = None
    filament_profile: Path | None = None


@dataclass(frozen=True)
class SlicePlan:
    tool: str
    command: list[str]
    checklist: list[str]


def build_slice_plan(request: SliceRequest) -> SlicePlan:
    tool = _normalize_slicer(request.slicer)
    command = [
        tool,
        "--orient",
        "--arrange",
        "1",
        "--curr-bed-type",
        request.bed_type,
    ]

    settings = _settings_arg(request)
    if settings:
        command.extend(["--load-settings", settings])
    if request.filament_profile:
        command.extend(["--load-filaments", str(request.filament_profile)])

    command.extend(
        [
            "--slice",
            str(request.plate),
            "--export-3mf",
            str(request.output_path),
            str(request.model_path),
        ]
    )

    checklist = [
        "Review supports, overhangs, and first-layer adhesion in the slicer before printing.",
        "Confirm the printer profile is Bambu Lab A1 mini and the bed is Textured PEI Plate.",
        "Scale the model down before slicing if the estimated print time is too long.",
        "Use manual approval before sending any job to the printer.",
    ]
    return SlicePlan(tool=tool, command=command, checklist=checklist)


def _normalize_slicer(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"orca", "orca-slicer", "orcaslicer"}:
        return "orcaslicer"
    if normalized in {"bambu", "bambu-studio", "bambustudio"}:
        return "bambu-studio"
    raise ValueError(f"Unsupported slicer: {value}")


def _settings_arg(request: SliceRequest) -> str | None:
    if not (request.machine_profile or request.process_profile):
        return None
    return f"{request.machine_profile or ''};{request.process_profile or ''}"

