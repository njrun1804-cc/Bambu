"""Load design revision YAML specs and derive character metrics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from bambu.design_pipeline import SPEC_FILES, load_design_spec


def load_specs(project_path: Path | str, *, revision: str = "v1") -> dict[str, Any]:
    """Load all design spec files for a revision (salvaged v3b layout)."""

    return load_design_spec(project_path, revision=revision)["files"]


def character_metrics(specs: dict[str, Any]) -> list[dict[str, Any]]:
    """Return per-subject metrics from people.yaml for CAD/review harness."""

    people = specs.get("people", {}).get("people", [])
    metrics: list[dict[str, Any]] = []
    for person in people:
        head = person.get("head_mm", {})
        torso = person.get("torso_mm", {})
        metrics.append(
            {
                "id": person.get("id", ""),
                "name": person.get("name", ""),
                "target_height_mm": person.get("target_height_mm"),
                "head_width_mm": head.get("width"),
                "head_height_mm": head.get("height"),
                "torso_width_mm": torso.get("width"),
                "torso_height_mm": torso.get("height"),
                "likeness_cues": person.get("likeness_cues", []),
                "face_center": person.get("review", {}).get("face_center"),
            }
        )
    return metrics


def load_archetype_profile(archetype: str, *, profiles_root: Path = Path("profiles/archetypes")) -> dict[str, Any]:
    path = profiles_root / f"{archetype}.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text()) or {}


def spec_file_paths(project_path: Path | str, revision: str) -> dict[str, Path]:
    project = Path(project_path)
    design_dir = project / "designs" / revision
    return {key: design_dir / filename for key, filename in SPEC_FILES.items()}
