# Agent Operating Substrate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build the substrate layer from `docs/superpowers/specs/2026-06-12-agent-operating-substrate-design.md` so agents can read printer context, create structured model projects, validate manifests, track artifacts, and record physical print feedback.

**Architecture:** Add small focused Python modules for repo context, project manifests, artifact manifests, and print feedback. Expose those modules through MCP read views and narrow mutation tools. Use real YAML manifests with PyYAML safe_load and safe_dump. Add build123d as the optional CAD extra for supported Python runtimes, while keeping basic substrate commands light.

**Tech Stack:** Python 3.12, PyYAML, first-class build123d CAD dependency, `unittest`, existing MCP server, existing Bambu Studio/Orca slicer planning.

---

## File Structure

- Create `bambu/context.py`: durable printer/material/plate rules and read views.
- Create `bambu/projects.py`: project manifest creation, loading, validation, artifact manifest writing, and print-result recording.
- Create `profiles/bambu-a1-mini/context.yaml`: repo-readable printer, material, and plate state.
- Create `projects/world-cup-neighbors/project.yaml`: public example project manifest in real YAML.
- Create `projects/world-cup-neighbors/source/.gitkeep`, `reviews/.gitkeep`, `measurements/.gitkeep`, `photos/.gitkeep`: public project folder skeleton.
- Create `projects/world-cup-neighbors/artifacts.json`: generated-style artifact index with no heavy artifacts.
- Modify `bambu/mcp_server.py`: add context/rules/project views and narrow project mutation tools.
- Modify `bambu/cli.py`: add project creation and print-result commands.
- Modify `README.md`, `agents/README.md`, `.agents/skills/bambu-operate/SKILL.md`: document the general substrate.
- Create `tests/test_context.py`: context/rules view tests.
- Create `tests/test_projects.py`: manifest creation, validation, artifacts, and print-result tests.
- Modify `tests/test_mcp_tools.py`: MCP view/tool coverage.
- Modify `tests/test_cli.py`: CLI coverage for project and print-result commands.

## Task 1: Context And Rules Views

**Files:**
- Create: `tests/test_context.py`
- Create: `bambu/context.py`
- Create: `profiles/bambu-a1-mini/context.yaml`

- [x] **Step 1: Write failing tests for printer context and rules**

```python
import unittest


class ContextTests(unittest.TestCase):
    def test_context_view_exposes_a1_mini_constraints_and_material_state(self):
        from bambu.context import context_view

        view = context_view()

        self.assertEqual(view["printer"]["model"], "Bambu Lab A1 mini")
        self.assertEqual(view["printer"]["build_volume_mm"], [180, 180, 180])
        self.assertEqual(view["printer"]["nozzle_mm"], 0.4)
        self.assertEqual(view["printer"]["printer_contact_policy"], "manual_only")
        self.assertIn("Bambu PLA Basic", [item["name"] for item in view["materials"]])
        petg = next(item for item in view["materials"] if item["name"] == "Bambu PETG HF")
        self.assertTrue(petg["requires_dryness_tracking"])
        self.assertEqual(view["plate"]["name"], "Bambu Dual-Texture PEI Plate")

    def test_rules_view_names_backend_and_artifact_policy(self):
        from bambu.context import rules_view

        rules = rules_view()

        self.assertEqual(rules["cad_backends"]["serious"], "build123d")
        self.assertEqual(rules["cad_backends"]["simple_public"], "openscad")
        self.assertEqual(rules["slicing"]["primary"], "bambu-studio")
        self.assertEqual(rules["slicing"]["backup"], "orcaslicer")
        self.assertIn("stl", rules["artifacts"]["generated_extensions"])
        self.assertEqual(rules["printer_contact"], "manual_only")
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest tests.test_context -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bambu.context'`.

- [x] **Step 3: Implement minimal context module and data file**

Create `profiles/bambu-a1-mini/context.yaml`:

```json
{
  "printer": {
    "model": "Bambu Lab A1 mini",
    "build_volume_mm": [180, 180, 180],
    "nozzle_mm": 0.4,
    "max_hotend_c": 300,
    "printer_contact_policy": "manual_only"
  },
  "materials": [
    {
      "name": "Bambu PLA Basic",
      "lane_default": "easy",
      "requires_dryness_tracking": false
    },
    {
      "name": "Bambu PETG HF",
      "lane_default": "functional",
      "requires_dryness_tracking": true,
      "drying_note": "Dry before use and keep moisture-free during longer prints."
    }
  ],
  "plate": {
    "name": "Bambu Dual-Texture PEI Plate",
    "side_required": "explicit"
  }
}
```

Create `bambu/context.py`:

```python
"""Durable printer, material, and workflow context for Bambu agents."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from bambu.preflight import detect_tools, serialize_report


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = REPO_ROOT / "profiles" / "bambu-a1-mini" / "context.yaml"


def context_view() -> dict[str, Any]:
    data = json.loads(CONTEXT_PATH.read_text())
    data["tools"] = serialize_report(detect_tools())
    data["safety"] = [
        "Do not start print jobs automatically.",
        "Treat slicer output as a plan requiring manual review.",
        "Review supports, scale, filament, plate side, and first layer before printing.",
        "Keep private photos and printer credentials under private/ and out of git.",
    ]
    return data


def rules_view() -> dict[str, Any]:
    return {
        "cad_backends": {
            "serious": "build123d",
            "simple_public": "openscad",
            "figurine_first_pass": "openscad",
            "mesh_later": "blender",
        },
        "slicing": {
            "primary": "bambu-studio",
            "backup": "orcaslicer",
            "policy": "Bambu Studio is blessed but not trusted as the only durable state.",
        },
        "artifacts": {
            "source_of_truth": ["project.yaml", "source/model.py", "source/model.scad"],
            "generated_extensions": ["stl", "step", "3mf", "gcode", "gcode.3mf", "png"],
            "generated_policy": "Generated artifacts are indexed, not hand-edited source.",
        },
        "privacy": {
            "private_paths": ["private/", "projects/*/photos/"],
            "public_examples": "Use only non-private placeholder assets unless explicitly approved.",
        },
        "printer_contact": "manual_only",
        "gates": {
            "design": ["valid_manifest", "lane_chosen", "material_selected", "privacy_declared"],
            "export": ["source_exists", "artifact_hash_recorded", "fits_build_volume"],
            "slicer": ["profile_named", "material_profile_named", "plate_side_named", "manual_review"],
            "print_feedback": ["outcome_recorded", "failure_mode_classified", "next_revision_proposed"],
        },
    }


def default_project_context() -> dict[str, Any]:
    view = context_view()
    return {
        "printer": deepcopy(view["printer"]),
        "material": deepcopy(view["materials"][0]),
        "plate": deepcopy(view["plate"]),
    }
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run python -m unittest tests.test_context -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add tests/test_context.py bambu/context.py profiles/bambu-a1-mini/context.yaml
git commit -m "feat: add Bambu context views"
```

## Task 2: Project Manifests And Artifact Index

**Files:**
- Create: `tests/test_projects.py`
- Create: `bambu/projects.py`

- [x] **Step 1: Write failing tests for project creation, validation, and artifacts**

```python
import json
import tempfile
import unittest
from pathlib import Path


class ProjectTests(unittest.TestCase):
    def test_create_project_writes_manifest_and_safe_folders(self):
        from bambu.projects import create_project, load_project, validate_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = create_project(
                "Shelf bracket",
                root=root,
                lane="build123d",
                privacy="private",
                material="Bambu PETG HF",
                plate_side="textured",
            )

            manifest = root / "shelf-bracket" / "project.yaml"
            self.assertTrue(manifest.exists())
            self.assertTrue((root / "shelf-bracket" / "source").is_dir())
            loaded = load_project(manifest)
            self.assertEqual(loaded["slug"], "shelf-bracket")
            self.assertEqual(loaded["lane"], "build123d")
            self.assertEqual(loaded["material"]["name"], "Bambu PETG HF")
            self.assertEqual(validate_project(loaded), [])

    def test_validate_project_reports_missing_design_gate_fields(self):
        from bambu.projects import validate_project

        errors = validate_project({"slug": "bad"})

        self.assertIn("intent is required", errors)
        self.assertIn("lane must be one of build123d, openscad, figurine", errors)
        self.assertIn("material.name is required", errors)

    def test_write_artifact_manifest_records_hashes(self):
        from bambu.projects import write_artifact_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "part.stl"
            artifact.write_text("solid test")
            result = write_artifact_manifest(root / "artifacts.json", project_slug="part", revision="v001", paths=[artifact])
            data = json.loads((root / "artifacts.json").read_text())

        self.assertEqual(result["project_slug"], "part")
        self.assertEqual(data["artifacts"][0]["path"], "part.stl")
        self.assertEqual(len(data["artifacts"][0]["sha256"]), 64)
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest tests.test_projects -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'bambu.projects'`.

- [x] **Step 3: Implement project helpers**

Create `bambu/projects.py` with dataless helpers:

```python
"""Project manifests, artifact indexes, and revision feedback for Bambu."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from bambu.context import context_view, rules_view


PROJECTS_ROOT = Path("projects")
LANES = {"build123d", "openscad", "figurine"}
OUTCOMES = {"not_printed", "success", "partial_success", "failed"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "model"


def create_project(
    intent: str,
    *,
    root: Path = PROJECTS_ROOT,
    slug: str | None = None,
    lane: str = "build123d",
    privacy: str = "private",
    material: str = "Bambu PLA Basic",
    plate_side: str = "deferred",
) -> dict[str, Any]:
    project_slug = slug or slugify(intent)
    project_dir = root / project_slug
    for child in ("source", "reviews", "measurements", "photos"):
        directory = project_dir / child
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch()
    context = context_view()
    selected_material = _select_material(context["materials"], material)
    manifest = {
        "schema_version": 1,
        "slug": project_slug,
        "intent": intent,
        "privacy": privacy,
        "lane": lane,
        "status": "design",
        "current_revision": "v001",
        "next_safe_action": "complete design gate",
        "printer": context["printer"],
        "material": selected_material,
        "plate": {**context["plate"], "side": plate_side},
        "constraints": {
            "dimensions_mm": [],
            "tolerance_notes": "",
        },
        "manual_gates": ["export_review", "slicer_review", "print_start"],
        "source_files": _default_source_files(lane),
    }
    errors = validate_project(manifest)
    if errors:
        raise ValueError("; ".join(errors))
    _write_json_yaml(project_dir / "project.yaml", manifest)
    if not (project_dir / "artifacts.json").exists():
        write_artifact_manifest(project_dir / "artifacts.json", project_slug=project_slug, revision="v001", paths=[])
    return manifest


def load_project(path: Path | str) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def validate_project(project: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not project.get("intent"):
        errors.append("intent is required")
    if project.get("lane") not in LANES:
        errors.append("lane must be one of build123d, openscad, figurine")
    if not project.get("privacy"):
        errors.append("privacy is required")
    if not project.get("printer", {}).get("model"):
        errors.append("printer.model is required")
    if not project.get("material", {}).get("name"):
        errors.append("material.name is required")
    if not project.get("plate", {}).get("name"):
        errors.append("plate.name is required")
    if not project.get("current_revision"):
        errors.append("current_revision is required")
    return errors


def project_view(project_path: Path | str) -> dict[str, Any]:
    path = Path(project_path)
    manifest_path = path / "project.yaml" if path.is_dir() else path
    project = load_project(manifest_path)
    project_dir = manifest_path.parent
    artifacts_path = project_dir / "artifacts.json"
    artifacts = json.loads(artifacts_path.read_text()) if artifacts_path.exists() else {}
    errors = validate_project(project)
    return {
        "project": project,
        "validation_errors": errors,
        "artifacts": artifacts,
        "rules": rules_view(),
        "next_safe_action": project.get("next_safe_action", "fix manifest validation errors" if errors else "review project"),
    }


def write_artifact_manifest(
    manifest_path: Path | str,
    *,
    project_slug: str,
    revision: str,
    paths: list[Path],
) -> dict[str, Any]:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    artifacts = [_artifact_entry(path.parent, item) for item in paths]
    data = {
        "schema_version": 1,
        "project_slug": project_slug,
        "revision": revision,
        "updated_at": _now(),
        "artifacts": artifacts,
    }
    path.write_text(json.dumps(data, indent=2) + "\n")
    return data


def _artifact_entry(base: Path, path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    relative = _relative_to_or_name(path, base)
    return {
        "path": relative,
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "bytes": resolved.stat().st_size,
        "generated": True,
    }


def _select_material(materials: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for material in materials:
        if material["name"] == name:
            return material
    raise ValueError(f"Unknown material: {name}")


def _default_source_files(lane: str) -> list[str]:
    if lane == "build123d":
        return ["source/model.py"]
    if lane == "openscad":
        return ["source/model.scad"]
    return ["source/model.scad"]


def _relative_to_or_name(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return path.name


def _write_json_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run python -m unittest tests.test_projects -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add tests/test_projects.py bambu/projects.py
git commit -m "feat: add project manifest helpers"
```

## Task 3: Print Feedback Recording

**Files:**
- Modify: `tests/test_projects.py`
- Modify: `bambu/projects.py`

- [x] **Step 1: Write failing test for print result recording**

Append to `ProjectTests`:

```python
    def test_record_print_result_writes_revision_feedback(self):
        from bambu.projects import create_project, record_print_result

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_project("Pegboard hook", root=root, lane="build123d", material="Bambu PETG HF")
            result = record_print_result(
                root / "pegboard-hook",
                outcome="failed",
                failure_mode="warped_corner",
                measurements={"slot_width_mm": {"expected": 6.0, "actual": 5.6}},
                material_state={"opened_date": "2026-06-12", "dryness": "unknown"},
                notes="Corner lifted on textured plate.",
                next_revision="Add brim and increase slot width by 0.4 mm.",
            )
            measurement = root / "pegboard-hook" / "measurements" / "v001.yaml"
            review = root / "pegboard-hook" / "reviews" / "004-print-feedback.md"

            self.assertTrue(measurement.exists())
            self.assertTrue(review.exists())
            self.assertEqual(result["outcome"], "failed")
            self.assertIn("warped_corner", review.read_text())
            self.assertIn("slot_width_mm", measurement.read_text())
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run python -m unittest tests.test_projects.ProjectTests.test_record_print_result_writes_revision_feedback -v`

Expected: FAIL with `ImportError` for `record_print_result`.

- [x] **Step 3: Implement print result recording**

Add to `bambu/projects.py`:

```python
def record_print_result(
    project_path: Path | str,
    *,
    outcome: str,
    failure_mode: str = "",
    measurements: dict[str, Any] | None = None,
    material_state: dict[str, Any] | None = None,
    notes: str = "",
    next_revision: str = "",
) -> dict[str, Any]:
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {', '.join(sorted(OUTCOMES))}")
    project_dir = Path(project_path)
    manifest_path = project_dir / "project.yaml"
    project = load_project(manifest_path)
    revision = project.get("current_revision", "v001")
    result = {
        "schema_version": 1,
        "project_slug": project["slug"],
        "revision": revision,
        "recorded_at": _now(),
        "outcome": outcome,
        "failure_mode": failure_mode,
        "measurements": measurements or {},
        "material_state": material_state or {},
        "notes": notes,
        "next_revision": next_revision,
    }
    measurements_dir = project_dir / "measurements"
    reviews_dir = project_dir / "reviews"
    measurements_dir.mkdir(parents=True, exist_ok=True)
    reviews_dir.mkdir(parents=True, exist_ok=True)
    _write_json_yaml(measurements_dir / f"{revision}.yaml", result)
    (reviews_dir / "004-print-feedback.md").write_text(_feedback_markdown(result))
    project["status"] = "print_feedback"
    project["next_safe_action"] = "revise source from print feedback" if next_revision else "review print feedback"
    _write_json_yaml(manifest_path, project)
    return result


def _feedback_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Print Feedback",
        "",
        f"- project: {result['project_slug']}",
        f"- revision: {result['revision']}",
        f"- outcome: {result['outcome']}",
        f"- failure_mode: {result['failure_mode'] or 'none'}",
        f"- notes: {result['notes'] or 'none'}",
        f"- next_revision: {result['next_revision'] or 'none'}",
        "",
        "## Measurements",
        "",
        "```json",
        json.dumps(result["measurements"], indent=2),
        "```",
        "",
        "## Material State",
        "",
        "```json",
        json.dumps(result["material_state"], indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)
```

- [x] **Step 4: Run test to verify it passes**

Run: `uv run python -m unittest tests.test_projects -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add tests/test_projects.py bambu/projects.py
git commit -m "feat: record print feedback"
```

## Task 4: MCP Substrate Views And Tools

**Files:**
- Modify: `tests/test_mcp_tools.py`
- Modify: `bambu/mcp_server.py`

- [x] **Step 1: Write failing MCP tests**

Append to `McpToolTests`:

```python
    def test_mcp_context_and_rules_views_expose_substrate(self):
        from bambu.mcp_server import bambu_context_view, bambu_rules_view

        context = bambu_context_view()
        rules = bambu_rules_view()

        self.assertEqual(context["printer"]["model"], "Bambu Lab A1 mini")
        self.assertEqual(rules["cad_backends"]["serious"], "build123d")
        self.assertEqual(rules["printer_contact"], "manual_only")

    def test_mcp_create_project_and_project_view(self):
        from bambu.mcp_server import bambu_create_project, bambu_project_view

        with tempfile.TemporaryDirectory() as tmp:
            created = bambu_create_project(
                "Cable clip",
                root=tmp,
                lane="build123d",
                privacy="private",
                material="Bambu PLA Basic",
                plate_side="textured",
            )
            view = bambu_project_view(created["project_dir"])

        self.assertEqual(created["project"]["slug"], "cable-clip")
        self.assertEqual(view["project"]["lane"], "build123d")
        self.assertEqual(view["validation_errors"], [])

    def test_mcp_record_print_result(self):
        from bambu.mcp_server import bambu_create_project, bambu_record_print_result

        with tempfile.TemporaryDirectory() as tmp:
            created = bambu_create_project("Cable clip", root=tmp)
            result = bambu_record_print_result(
                created["project_dir"],
                outcome="partial_success",
                failure_mode="too_tight",
                measurements={"clip_gap_mm": {"expected": 8, "actual": 7.4}},
                material_state={"dryness": "not_required"},
                notes="Fits but too tight.",
                next_revision="Increase clip gap.",
            )

        self.assertEqual(result["outcome"], "partial_success")
        self.assertIn("clip_gap_mm", result["measurements"])
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run python -m unittest tests.test_mcp_tools -v`

Expected: FAIL with missing imports.

- [x] **Step 3: Implement MCP functions and register them**

Add imports to `bambu/mcp_server.py`:

```python
from bambu.context import context_view, rules_view
from bambu.projects import create_project, project_view, record_print_result
```

Add functions:

```python
def bambu_context_view() -> dict[str, Any]:
    """Return deterministic printer, material, plate, tool, and safety context."""
    return context_view()


def bambu_rules_view() -> dict[str, Any]:
    """Return agent rules for CAD backends, artifacts, privacy, and print gates."""
    return rules_view()


def bambu_create_project(
    intent: str,
    root: str = "projects",
    slug: str | None = None,
    lane: str = "build123d",
    privacy: str = "private",
    material: str = "Bambu PLA Basic",
    plate_side: str = "deferred",
) -> dict[str, Any]:
    """Create a structured project workspace from a plain-English print idea."""
    project = create_project(
        intent,
        root=Path(root),
        slug=slug,
        lane=lane,
        privacy=privacy,
        material=material,
        plate_side=plate_side,
    )
    return {"project": project, "project_dir": str(Path(root) / project["slug"])}


def bambu_project_view(project: str) -> dict[str, Any]:
    """Return manifest, artifact, validation, and next-action state for a project."""
    return project_view(Path(project))


def bambu_record_print_result(
    project: str,
    outcome: str,
    failure_mode: str = "",
    measurements: dict[str, Any] | None = None,
    material_state: dict[str, Any] | None = None,
    notes: str = "",
    next_revision: str = "",
) -> dict[str, Any]:
    """Record physical print feedback for the current project revision."""
    return record_print_result(
        Path(project),
        outcome=outcome,
        failure_mode=failure_mode,
        measurements=measurements,
        material_state=material_state,
        notes=notes,
        next_revision=next_revision,
    )
```

Register the new tools in `_build_mcp()`:

```python
    server.tool()(bambu_context_view)
    server.tool()(bambu_rules_view)
    server.tool()(bambu_create_project)
    server.tool()(bambu_project_view)
    server.tool()(bambu_record_print_result)
```

- [x] **Step 4: Run MCP tests to verify they pass**

Run: `uv run python -m unittest tests.test_mcp_tools -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add tests/test_mcp_tools.py bambu/mcp_server.py
git commit -m "feat: expose substrate MCP tools"
```

## Task 5: CLI Commands

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `bambu/cli.py`

- [x] **Step 1: Write failing CLI tests**

Append to `CliTests`:

```python
    def test_create_project_command_writes_manifest(self):
        from bambu.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with patch("sys.stdout", output):
                exit_code = main([
                    "create-project",
                    "Cable clip",
                    "--root",
                    tmp,
                    "--lane",
                    "build123d",
                    "--material",
                    "Bambu PLA Basic",
                    "--plate-side",
                    "textured",
                ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmp) / "cable-clip" / "project.yaml").exists())
            self.assertIn("Next safe action", output.getvalue())

    def test_record_print_result_command_writes_feedback(self):
        from bambu.cli import main
        from bambu.projects import create_project

        with tempfile.TemporaryDirectory() as tmp:
            create_project("Cable clip", root=Path(tmp))
            output = io.StringIO()
            with patch("sys.stdout", output):
                exit_code = main([
                    "record-print-result",
                    str(Path(tmp) / "cable-clip"),
                    "--outcome",
                    "failed",
                    "--failure-mode",
                    "too_tight",
                    "--notes",
                    "Clip gap too small.",
                    "--next-revision",
                    "Increase gap.",
                ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmp) / "cable-clip" / "reviews" / "004-print-feedback.md").exists())
            self.assertIn("Recorded print result", output.getvalue())
```

- [x] **Step 2: Run CLI tests to verify they fail**

Run: `uv run python -m unittest tests.test_cli -v`

Expected: FAIL because commands are not registered.

- [x] **Step 3: Implement CLI commands**

In `build_parser()`, add:

```python
    create = subparsers.add_parser(
        "create-project",
        help="Create a structured agent project workspace from a plain-English print idea.",
    )
    create.add_argument("intent")
    create.add_argument("--root", type=Path, default=Path("projects"))
    create.add_argument("--slug")
    create.add_argument("--lane", default="build123d", choices=["build123d", "openscad", "figurine"])
    create.add_argument("--privacy", default="private")
    create.add_argument("--material", default="Bambu PLA Basic")
    create.add_argument("--plate-side", default="deferred")

    result = subparsers.add_parser(
        "record-print-result",
        help="Record physical print feedback for a project revision.",
    )
    result.add_argument("project", type=Path)
    result.add_argument("--outcome", required=True, choices=["not_printed", "success", "partial_success", "failed"])
    result.add_argument("--failure-mode", default="")
    result.add_argument("--notes", default="")
    result.add_argument("--next-revision", default="")
```

In `main()`, add:

```python
    if args.command == "create-project":
        return _create_project(args)
    if args.command == "record-print-result":
        return _record_print_result(args)
```

Add helpers:

```python
def _create_project(args: argparse.Namespace) -> int:
    from bambu.projects import create_project

    project = create_project(
        args.intent,
        root=args.root,
        slug=args.slug,
        lane=args.lane,
        privacy=args.privacy,
        material=args.material,
        plate_side=args.plate_side,
    )
    print(f"Created project: {args.root / project['slug']}")
    print(f"Lane: {project['lane']}")
    print(f"Next safe action: {project['next_safe_action']}")
    return 0


def _record_print_result(args: argparse.Namespace) -> int:
    from bambu.projects import record_print_result

    result = record_print_result(
        args.project,
        outcome=args.outcome,
        failure_mode=args.failure_mode,
        notes=args.notes,
        next_revision=args.next_revision,
    )
    print(f"Recorded print result: {result['project_slug']} {result['revision']} {result['outcome']}")
    print("Next: revise source from the recorded physical feedback before exporting again.")
    return 0
```

- [x] **Step 4: Run CLI tests to verify they pass**

Run: `uv run python -m unittest tests.test_cli -v`

Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add tests/test_cli.py bambu/cli.py
git commit -m "feat: add substrate CLI commands"
```

## Task 6: Example Project And Documentation

**Files:**
- Create: `projects/world-cup-neighbors/project.yaml`
- Create: `projects/world-cup-neighbors/artifacts.json`
- Create: `projects/world-cup-neighbors/source/.gitkeep`
- Create: `projects/world-cup-neighbors/reviews/.gitkeep`
- Create: `projects/world-cup-neighbors/measurements/.gitkeep`
- Create: `projects/world-cup-neighbors/photos/.gitkeep`
- Modify: `README.md`
- Modify: `agents/README.md`
- Modify: `.agents/skills/bambu-operate/SKILL.md`

- [x] **Step 1: Add a public example project manifest**

Create `projects/world-cup-neighbors/project.yaml` as real YAML:

```json
{
  "schema_version": 1,
  "slug": "world-cup-neighbors",
  "intent": "Stylized Brazil watch-party neighbor figurines for the Bambu Lab A1 mini.",
  "privacy": "public_safe",
  "lane": "figurine",
  "status": "source_generated",
  "current_revision": "v001",
  "next_safe_action": "review OpenSCAD source and export STL",
  "printer": {
    "model": "Bambu Lab A1 mini",
    "build_volume_mm": [180, 180, 180],
    "nozzle_mm": 0.4,
    "max_hotend_c": 300,
    "printer_contact_policy": "manual_only"
  },
  "material": {
    "name": "Bambu PLA Basic",
    "lane_default": "easy",
    "requires_dryness_tracking": false
  },
  "plate": {
    "name": "Bambu Dual-Texture PEI Plate",
    "side_required": "explicit",
    "side": "textured"
  },
  "constraints": {
    "dimensions_mm": ["shared base remains within 118 x 62 mm"],
    "tolerance_notes": "Decorative print; prioritize supportless raised details over dimensional fit."
  },
  "manual_gates": ["export_review", "slicer_review", "print_start"],
  "source_files": ["outputs/world-cup-neighbors.scad"]
}
```

Create `projects/world-cup-neighbors/artifacts.json`:

```json
{
  "schema_version": 1,
  "project_slug": "world-cup-neighbors",
  "revision": "v001",
  "updated_at": "2026-06-12T00:00:00+00:00",
  "artifacts": []
}
```

Add `.gitkeep` files under `source`, `reviews`, `measurements`, and `photos`.

- [x] **Step 2: Document the substrate**

Add README text:

```markdown
## Agent Operating Substrate

General model work should live under `projects/<slug>/`. Each project has a `project.yaml`
manifest, source folder, review notes, measurement history, photo placeholder, and generated
artifact index. Agents should start with `bambu context-view`, inspect or create a project,
then move through design, export, slicer, and print-feedback gates.

The serious CAD default is `build123d`. OpenSCAD remains the simple public/remixable lane and
the current figurine first-pass lane. Bambu Studio is the blessed slicer path, OrcaSlicer is a
fallback/comparison path, and printer contact remains manual only.
```

Update agent docs and skill to mention `bambu_context_view`, `bambu_project_view`, and `bambu_record_print_result`.

- [x] **Step 3: Run full tests**

Run: `uv run python -m unittest discover -s tests -v`

Expected: PASS.

- [x] **Step 4: Commit**

```bash
git add README.md agents/README.md .agents/skills/bambu-operate/SKILL.md projects/world-cup-neighbors docs/superpowers/plans/2026-06-12-agent-operating-substrate-implementation.md
git commit -m "docs: add substrate project workflow"
```

## Task 7: Final Verification

**Files:**
- No source changes unless verification reveals a bug.

- [x] **Step 1: Run doctor**

Run: `uv run bambu doctor`

Expected: reports OpenSCAD, Bambu Studio, OrcaSlicer, and Blender status, with no printer contact.

- [x] **Step 2: Run all tests**

Run: `uv run python -m unittest discover -s tests -v`

Expected: PASS.

- [x] **Step 3: Check git status**

Run: `git status --short`

Expected: only pre-existing unrelated dirty figurine edits remain, or no dirty files except intentionally ignored/generated artifacts.

## Self-Review

- Spec coverage: context/rules views are in Task 1, manifests/artifacts in Task 2, print feedback in Task 3, MCP tools in Task 4, CLI hand-holding in Task 5, example project/docs in Task 6, verification in Task 7.
- Scope check: no automatic printer sending, no full workflow engine, no first-class Orca workflow, build123d is first-class and the repo is pinned to Python 3.12.
- Type consistency: public functions are `context_view`, `rules_view`, `create_project`, `load_project`, `validate_project`, `project_view`, `write_artifact_manifest`, and `record_print_result`.
