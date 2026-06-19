"""Validate reference photos against intake intent before Meshy API spend."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


KNOWN_WRONG_REFERENCE_MARKERS = (
    "clear-right-pair",
    "group-right-pair",
    "world-cup-neighbors",
    "world_cup_neighbors",
)


@dataclass(frozen=True)
class ReferenceValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _load_intake(project_dir: Path) -> dict[str, Any]:
    intake_path = project_dir / "references" / "intake.yaml"
    if not intake_path.exists():
        return {}
    return yaml.safe_load(intake_path.read_text()) or {}


def _load_provenance(project_dir: Path) -> dict[str, Any]:
    provenance_path = project_dir / "mesh" / "provenance.yaml"
    if not provenance_path.exists():
        return {}
    return yaml.safe_load(provenance_path.read_text()) or {}


def intake_subject_requirements(intake: dict[str, Any]) -> dict[str, bool]:
    """Derive required scene elements from intake intent and agent_fill."""

    intent = str(intake.get("intent", "")).lower()
    agent = intake.get("agent_fill") or {}
    subjects = agent.get("subjects") or []
    props = " ".join(str(p) for p in agent.get("props") or []).lower()
    pose = str(agent.get("pose", "")).lower()
    blob = f"{intent} {props} {pose}"

    has_dog = "dog" in blob or any(
        s.get("type") == "animal" or str(s.get("id", "")).lower() == "dog" for s in subjects
    )
    has_chair = "chair" in blob or "patio" in blob or "seated" in blob or "sitting" in blob
    has_woman = "woman" in blob or any(str(s.get("id", "")).lower() == "woman" for s in subjects)
    return {"woman": has_woman, "dog": has_dog, "chair": has_chair}


def _path_markers(path: Path | str) -> str:
    return str(path).lower().replace("\\", "/")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matches_known_wrong_source(*paths: Path | str | None) -> list[str]:
    hits: list[str] = []
    for raw in paths:
        if not raw:
            continue
        lowered = _path_markers(raw)
        for marker in KNOWN_WRONG_REFERENCE_MARKERS:
            if marker in lowered:
                hits.append(marker)
    return sorted(set(hits))


def validate_reference_photo(
    project_dir: Path | str,
    *,
    photo: Path | str | None = None,
    force: bool = False,
) -> ReferenceValidationResult:
    """Check reference photo path/provenance against intake before Meshy spend."""

    project = Path(project_dir)
    intake = _load_intake(project)
    provenance = _load_provenance(project)

    if intake.get("reference_photo_confirmed") is True or force:
        return ReferenceValidationResult(ok=True)

    if photo is None:
        rel = intake.get("reference_photo", "")
        if rel:
            candidate = project / rel
            if candidate.exists():
                photo = candidate
    if photo is None:
        ref_dir = project / "photos" / "reference"
        if ref_dir.is_dir():
            for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp"):
                matches = sorted(ref_dir.glob(pattern))
                if matches:
                    photo = matches[0]
                    break

    errors: list[str] = []
    warnings: list[str] = []

    if photo is None or not Path(photo).exists():
        errors.append("Reference photo not found for validation")
        return ReferenceValidationResult(ok=False, errors=errors, warnings=warnings)

    photo_path = Path(photo)
    wrong_markers = _matches_known_wrong_source(
        photo_path,
        photo_path.name,
        provenance.get("reference_source"),
        provenance.get("reference_photo"),
    )
    if wrong_markers:
        errors.append(
            "Reference photo matches World Cup / marina neighbor sources "
            f"({', '.join(wrong_markers)}), not the seated woman+dog+chair scene in intake.yaml"
        )

    repo_root = project
    while repo_root.parent != repo_root and not (repo_root / "private").is_dir():
        repo_root = repo_root.parent
    wrong_ref = repo_root / "private" / "references" / "clear-right-pair.jpg"
    if wrong_ref.exists() and photo_path.exists():
        try:
            if _sha256(wrong_ref) == _sha256(photo_path):
                errors.append(
                    "Reference photo is byte-identical to private/references/clear-right-pair.jpg "
                    "(marina couple, not patio woman+dog+chair)"
                )
        except OSError:
            pass

    required = intake_subject_requirements(intake)
    if any(required.values()):
        missing = [name for name, needed in required.items() if needed]
        warnings.append(
            "Intake requires "
            + ", ".join(missing)
            + "; image content is not auto-verified. Visually confirm the photo, then set "
            "references/intake.yaml reference_photo_confirmed: true (or pass --force-reference)."
        )
        if missing and not intake.get("reference_photo_confirmed"):
            errors.append(
                "Reference photo not human-confirmed for required subjects: "
                + ", ".join(missing)
            )

    ok = len(errors) == 0
    return ReferenceValidationResult(ok=ok, errors=errors, warnings=warnings)


def ensure_reference_photo_valid(
    project_dir: Path | str,
    *,
    photo: Path | str | None = None,
    force: bool = False,
    context: str = "meshy",
) -> ReferenceValidationResult:
    """Raise ValueError when validation fails; return result otherwise."""

    result = validate_reference_photo(project_dir, photo=photo, force=force)
    if result.ok:
        return result
    detail = "; ".join(result.errors)
    raise ValueError(
        f"Reference photo validation failed for {context}: {detail}. "
        "Fix the photo, set reference_photo_confirmed: true in references/intake.yaml, "
        "or pass --force-reference after visual review."
    )
