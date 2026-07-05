"""Validate reference photos against intake intent before Meshy API spend."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Content hashes of the known-wrong reference photos from the original incident (marina
# neighbors / World Cup figurines). Embedding the digests means the byte-block works in CI
# and fresh clones where the private/ originals are absent (private/ is gitignored). Covers
# the canonical files and the re-encoded copy that actually slipped through once.
KNOWN_WRONG_REFERENCE_SHA256 = frozenset(
    {
        "3b38ec95c09ff3ec426b1b633b667034a69bf3646b1f526fce87efd3f341b3ef",  # clear-right-pair.jpg
        "7eaec9d196cf25162799c7bf174358b7e2e26be0159020056f9831d828d50e5f",  # group-right-pair.jpg
        "ece326557eaf044874036438faba80014315755816b158e1bfd72d83e1e0cea7",  # re-encoded marina couple
    }
)

KNOWN_WRONG_REFERENCE_MARKERS = (
    "clear-right-pair",
    "group-right-pair",
    "world-cup-neighbors",
    "world_cup_neighbors",
    "marina",
    "wrong",
)

_NON_REFERENCE_PREFIXES = ("crop-", "concept-")


def _is_candidate_reference(path: Path) -> bool:
    """True if a photos/reference file is plausibly THE reference photo.

    Excludes head crops, generated concept sheets, and any known-wrong backup so the
    fallback never silently hands a crop or marina backup to the Meshy spend path.
    """

    name = path.name.lower()
    if any(name.startswith(prefix) for prefix in _NON_REFERENCE_PREFIXES):
        return False
    if any(marker in name for marker in KNOWN_WRONG_REFERENCE_MARKERS):
        return False
    return True


def select_reference_photo(ref_dir: Path) -> Path | None:
    """Pick the primary reference photo, skipping crops/concepts/known-wrong backups.

    Prefer a file whose name contains 'reference'; otherwise the first remaining candidate.
    """

    if not ref_dir.is_dir():
        return None
    candidates = [
        path
        for pattern in ("*.jpg", "*.jpeg", "*.png", "*.webp")
        for path in sorted(ref_dir.glob(pattern))
        if _is_candidate_reference(path)
    ]
    if not candidates:
        return None
    preferred = [p for p in candidates if "reference" in p.name.lower()]
    return (preferred or candidates)[0]


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

    # An explicit human override (--force-reference) bypasses every check.
    if force:
        return ReferenceValidationResult(ok=True)

    if photo is None:
        rel = intake.get("reference_photo", "")
        if rel:
            candidate = project / rel
            if candidate.exists():
                photo = candidate
    if photo is None:
        photo = select_reference_photo(project / "photos" / "reference")

    errors: list[str] = []
    warnings: list[str] = []

    if photo is None or not Path(photo).exists():
        errors.append("Reference photo not found for validation")
        return ReferenceValidationResult(ok=False, errors=errors, warnings=warnings)

    confirmed = intake.get("reference_photo_confirmed") is True
    photo_path = Path(photo)

    # Known-wrong by content hash is ground truth: it always blocks, even when
    # reference_photo_confirmed is set, because the bytes are provably wrong. This does
    # not depend on the private/ originals being present (they are gitignored), so the
    # guard holds in CI and fresh clones. An unreadable photo fails closed.
    try:
        digest = _sha256(photo_path)
    except OSError as exc:
        errors.append(f"Reference photo could not be read for validation: {exc}")
        return ReferenceValidationResult(ok=False, errors=errors, warnings=warnings)
    if digest in KNOWN_WRONG_REFERENCE_SHA256:
        errors.append(
            "Reference photo content matches a known-wrong source "
            "(marina couple / World Cup neighbors), not the patio woman+dog+chair scene"
        )

    # A path/provenance name match is a heuristic backstop. When the human has
    # confirmed these exact (byte-different) bytes, treat a marker hit as a warning —
    # it is usually stale audit prose ("previously clear-right-pair.jpg") rather than
    # the wrong photo. Without confirmation it remains a hard error.
    wrong_markers = _matches_known_wrong_source(
        photo_path,
        photo_path.name,
        provenance.get("reference_source"),
        provenance.get("reference_photo"),
    )
    if wrong_markers:
        marker_message = (
            "Reference photo matches World Cup / marina neighbor sources "
            f"({', '.join(wrong_markers)}), not the seated woman+dog+chair scene in intake.yaml"
        )
        if confirmed:
            warnings.append(marker_message)
        else:
            errors.append(marker_message)

    if errors:
        return ReferenceValidationResult(ok=False, errors=errors, warnings=warnings)

    # Past the known-wrong gate, a human confirmation flag clears the subject check.
    if confirmed:
        return ReferenceValidationResult(ok=True, warnings=warnings)

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
                "Reference photo not human-confirmed for required subjects: " + ", ".join(missing)
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
