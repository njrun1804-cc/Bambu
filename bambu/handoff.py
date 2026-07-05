"""Morning handoff checks for generated Bambu Studio projects."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from zipfile import BadZipFile, ZipFile

REQUIRED_A1_MINI_MARKERS: tuple[str, ...] = (
    "Bambu Lab A1 mini",
    "0.20mm Standard @BBL A1M",
    "Bambu PLA Basic",
    "Textured PEI Plate",
)


@dataclass(frozen=True)
class PrintHandoffReport:
    file: Path
    exists: bool
    is_3mf: bool
    found_markers: tuple[str, ...]
    missing_markers: list[str]
    open_command: str

    @property
    def ready_for_manual_review(self) -> bool:
        return self.exists and self.is_3mf and not self.missing_markers


def inspect_print_handoff(file: Path) -> PrintHandoffReport:
    """Inspect a generated .gcode.3mf for the expected A1 mini profile markers."""

    resolved = file.resolve()
    found: set[str] = set()
    is_3mf = False
    if resolved.exists():
        try:
            with ZipFile(resolved) as archive:
                is_3mf = True
                for name in archive.namelist():
                    if not name.startswith("Metadata/"):
                        continue
                    text = archive.read(name).decode("utf-8", errors="ignore")
                    for marker in REQUIRED_A1_MINI_MARKERS:
                        if marker in text:
                            found.add(marker)
        except BadZipFile:
            is_3mf = False

    missing = [marker for marker in REQUIRED_A1_MINI_MARKERS if marker not in found]
    open_command = " ".join(
        shlex.quote(part)
        for part in (
            "open",
            "-a",
            "/Applications/BambuStudio.app",
            str(resolved),
        )
    )
    return PrintHandoffReport(
        file=resolved,
        exists=resolved.exists(),
        is_3mf=is_3mf,
        found_markers=tuple(marker for marker in REQUIRED_A1_MINI_MARKERS if marker in found),
        missing_markers=missing,
        open_command=open_command,
    )
