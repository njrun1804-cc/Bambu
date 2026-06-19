"""Dry-run-safe slicer command construction for Bambu printers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any


@dataclass(frozen=True)
class SliceRequest:
    model_path: Path
    output_path: Path
    slicer: str = "bambu-studio"
    executable: str | None = None
    material: str = "Bambu PLA Basic"
    nozzle_mm: float = 0.4
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
    material: str = "Bambu PLA Basic"


@dataclass(frozen=True)
class SlicePlan:
    tool: str
    command: list[str]
    checklist: list[str]
    profiles: dict[str, str]


@dataclass(frozen=True)
class SliceResult:
    model_path: Path
    output_path: Path
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and self.output_path.exists()


def build_slice_plan(request: SliceRequest) -> SlicePlan:
    tool = _normalize_slicer(request.slicer)
    executable = request.executable or tool
    machine_profile = request.machine_profile
    process_profile = request.process_profile
    filament_profile = request.filament_profile
    if not (machine_profile or process_profile or filament_profile):
        if profiles := resolve_a1_mini_profiles(tool, material=request.material, nozzle_mm=request.nozzle_mm):
            machine_profile = profiles.machine
            process_profile = profiles.process
            filament_profile = profiles.filament
            material = profiles.material
        else:
            material = request.material
    else:
        material = request.material
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
        f"Confirm the slicer filament profile matches the selected material: {material}.",
        "Use A1 mini auto bed leveling and flow calibration before the first real print of this model.",
        "Use AMS lite color assignment only if the printer is actually connected with AMS lite; otherwise print PLA Basic single-color and paint the raised guides.",
        "Confirm the slicer filament profile matches the actual loaded spool: green PLA Basic matches this file, white PLA+ needs a PLA/PLA+ profile, and blue PETG HF requires re-slicing with a PETG HF profile.",
        "Keep the 118mm shared base centered on the Textured PEI Plate for adhesion and clearance.",
        "Use manual approval before sending any job to the printer.",
    ]
    profile_summary = {
        "material": material,
        "machine": str(machine_profile) if machine_profile else "",
        "process": str(process_profile) if process_profile else "",
        "filament": str(filament_profile) if filament_profile else "",
    }
    return SlicePlan(tool=tool, command=command, checklist=checklist, profiles=profile_summary)


def sliced_output_for_stl(stl_path: Path) -> Path:
    """Return the default .gcode.3mf path for a printable STL."""

    if stl_path.suffix.lower() == ".stl":
        return stl_path.with_suffix(".gcode.3mf")
    return stl_path.with_name(f"{stl_path.name}.gcode.3mf")


def run_slice(
    request: SliceRequest,
    *,
    timeout_seconds: int = 600,
) -> SliceResult:
    """Slice a model headlessly via Bambu Studio or OrcaSlicer CLI."""

    plan = build_slice_plan(request)
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        plan.command,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
    )
    return SliceResult(
        model_path=request.model_path,
        output_path=request.output_path,
        command=plan.command,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def slice_stl(
    stl_path: Path,
    output_path: Path | None = None,
    *,
    slicer: str = "bambu-studio",
    executable: str | None = None,
    material: str = "Bambu PLA Basic",
    timeout_seconds: int = 600,
) -> dict[str, Any]:
    """Convenience wrapper: slice an STL and raise on failure."""

    output = output_path or sliced_output_for_stl(stl_path)
    slice_result = run_slice(
        SliceRequest(
            model_path=stl_path,
            output_path=output,
            slicer=slicer,
            executable=executable,
            material=material,
            resolve_paths=True,
        ),
        timeout_seconds=timeout_seconds,
    )
    if not slice_result.ok:
        raise RuntimeError(
            f"Slicing failed ({slice_result.returncode}): {' '.join(slice_result.command)}\n"
            f"stdout:\n{slice_result.stdout[-2000:]}\n"
            f"stderr:\n{slice_result.stderr[-2000:]}"
        )
    plan = build_slice_plan(
        SliceRequest(
            model_path=stl_path,
            output_path=output,
            slicer=slicer,
            executable=executable,
            material=material,
            resolve_paths=True,
        )
    )
    return {
        "model": str(stl_path.resolve()),
        "sliced": str(output.resolve()),
        "command": slice_result.command,
        "returncode": slice_result.returncode,
        "profiles": plan.profiles,
        "checklist": plan.checklist,
    }


def default_a1_mini_profiles(
    slicer: str,
    *,
    profile_root: Path | None = None,
) -> ProfileSet | None:
    """Return bundled A1 mini profiles when the slicer installation provides them."""

    return resolve_a1_mini_profiles(slicer, material="Bambu PLA Basic", profile_root=profile_root)


def resolve_a1_mini_profiles(
    slicer: str,
    *,
    material: str = "Bambu PLA Basic",
    nozzle_mm: float = 0.4,
    profile_root: Path | None = None,
) -> ProfileSet | None:
    """Return bundled A1 mini profiles for the requested material when present."""

    root = profile_root or _default_profile_root(_normalize_slicer(slicer))
    machine = root / "machine" / f"Bambu Lab A1 mini {_format_nozzle(nozzle_mm)} nozzle.json"
    process = root / "process" / "0.20mm Standard @BBL A1M.json"
    filament = _resolve_filament_profile(root / "filament", material, nozzle_mm)
    if machine.exists() and process.exists() and filament.exists():
        return ProfileSet(machine=machine, process=process, filament=filament, material=material)
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


def _resolve_filament_profile(filament_root: Path, material: str, nozzle_mm: float) -> Path:
    nozzle = _format_nozzle(nozzle_mm)
    candidates = (
        filament_root / f"{material} @BBL A1M.json",
        filament_root / f"{material} @BBL A1M {nozzle} nozzle.json",
        filament_root / f"Generic {material} @BBL A1M.json",
        filament_root / f"Generic {material} @BBL A1M {nozzle} nozzle.json",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _format_nozzle(nozzle_mm: float) -> str:
    return f"{nozzle_mm:g}"
