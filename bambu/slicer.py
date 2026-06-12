"""Dry-run-safe slicer command construction for Bambu printers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SliceRequest:
    model_path: Path
    output_path: Path
    slicer: str = "bambu-studio"
    executable: str | None = None
    bed_type: str = "Textured PEI Plate"
    plate: int = 0
    machine_profile: Path | None = None
    process_profile: Path | None = None
    filament_profile: Path | None = None
    resolve_paths: bool = False


@dataclass(frozen=True)
class ProfileSet:
    machine: Path
    process: Path
    filament: Path


@dataclass(frozen=True)
class SlicePlan:
    tool: str
    command: list[str]
    checklist: list[str]


def build_slice_plan(request: SliceRequest) -> SlicePlan:
    tool = _normalize_slicer(request.slicer)
    executable = request.executable or tool
    machine_profile = request.machine_profile
    process_profile = request.process_profile
    filament_profile = request.filament_profile
    if not (machine_profile or process_profile or filament_profile):
        if profiles := default_a1_mini_profiles(tool):
            machine_profile = profiles.machine
            process_profile = profiles.process
            filament_profile = profiles.filament
    model_path = request.model_path.resolve() if request.resolve_paths else request.model_path
    output_path = request.output_path.resolve() if request.resolve_paths else request.output_path
    command = [
        executable,
        "--orient",
        "1",
        "--arrange",
        "1",
        "--curr-bed-type",
        request.bed_type,
    ]

    settings = _settings_arg(machine_profile, process_profile)
    if settings:
        command.extend(["--load-settings", settings])
    if filament_profile:
        command.extend(["--load-filaments", str(filament_profile)])

    command.extend(
        [
            "--slice",
            str(request.plate),
            "--export-3mf",
            str(output_path),
            str(model_path),
        ]
    )

    checklist = [
        "Review supports, overhangs, and first-layer adhesion in the slicer before printing.",
        "Confirm the printer profile is Bambu Lab A1 mini and the bed is Textured PEI Plate.",
        "Use A1 mini auto bed leveling and flow calibration before the first real print of this model.",
        "Use AMS lite color assignment only if the printer is actually connected with AMS lite; otherwise print PLA Basic single-color and paint the raised guides.",
        "Confirm the slicer filament profile matches the actual loaded spool; if using the visible blue PETG HF spool, re-slice with a PETG HF profile instead of PLA Basic.",
        "Keep the 118mm shared base centered on the Textured PEI Plate for adhesion and clearance.",
        "Use manual approval before sending any job to the printer.",
    ]
    return SlicePlan(tool=tool, command=command, checklist=checklist)


def default_a1_mini_profiles(
    slicer: str,
    *,
    profile_root: Path | None = None,
) -> ProfileSet | None:
    """Return bundled A1 mini profiles when the slicer installation provides them."""

    root = profile_root or _default_profile_root(_normalize_slicer(slicer))
    machine = root / "machine" / "Bambu Lab A1 mini 0.4 nozzle.json"
    process = root / "process" / "0.20mm Standard @BBL A1M.json"
    filament = root / "filament" / "Bambu PLA Basic @BBL A1M.json"
    if machine.exists() and process.exists() and filament.exists():
        return ProfileSet(machine=machine, process=process, filament=filament)
    return None


def _normalize_slicer(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"orca", "orca-slicer", "orcaslicer"}:
        return "orcaslicer"
    if normalized in {"bambu", "bambu-studio", "bambustudio"}:
        return "bambu-studio"
    raise ValueError(f"Unsupported slicer: {value}")


def _default_profile_root(slicer: str) -> Path:
    app_name = "OrcaSlicer.app" if slicer == "orcaslicer" else "BambuStudio.app"
    return Path("/Applications") / app_name / "Contents" / "Resources" / "profiles" / "BBL"


def _settings_arg(machine_profile: Path | None, process_profile: Path | None) -> str | None:
    if not (machine_profile or process_profile):
        return None
    return f"{machine_profile or ''};{process_profile or ''}"
