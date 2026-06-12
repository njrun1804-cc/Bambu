# World Cup Neighbors V2 Build123d Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the World Cup neighbors v2 model as a build123d project while documenting reusable 3D-printing lessons.

**Architecture:** Add a project-local build123d model at `projects/world-cup-neighbors/source/model.py` and keep generated STEP/STL outputs under ignored `outputs/`. Use tests to verify the model contract, public-safe docs, source tracking, export path, artifact indexing, and learning deliverables. Preserve the v001 OpenSCAD path as historical output while making v002 the active build123d revision.

**Tech Stack:** Python 3.12, build123d 0.10, PyYAML, unittest, Bambu CLI export/sync surfaces, Bambu Lab A1 mini constraints.

---

### Task 1: Add Tests For The V2 Contract

**Files:**
- Modify: `tests/test_cad.py`
- Create: `tests/test_world_cup_v2.py`

- [ ] **Step 1: Add a build123d source contract test**

Append this test to `tests/test_cad.py` before the `if __name__ == "__main__"` block:

```python
    def test_world_cup_v2_source_defines_exportable_model(self):
        from bambu.cad import load_build123d_model

        model = load_build123d_model(Path("projects/world-cup-neighbors/source/model.py"))

        box = model.bounding_box()
        self.assertLessEqual(float(box.size.X), 130.0)
        self.assertLessEqual(float(box.size.Y), 75.0)
        self.assertLessEqual(float(box.size.Z), 85.0)
```

- [ ] **Step 2: Add documentation and manifest tests**

Create `tests/test_world_cup_v2.py` with:

```python
import json
import unittest
from pathlib import Path

import yaml


class WorldCupV2Tests(unittest.TestCase):
    def test_project_manifest_points_to_v2_build123d_source(self):
        project = yaml.safe_load(Path("projects/world-cup-neighbors/project.yaml").read_text())

        self.assertEqual(project["lane"], "build123d")
        self.assertEqual(project["current_revision"], "v002")
        self.assertIn("source/model.py", project["source_files"])
        self.assertIn("outputs/world-cup-neighbors.scad", project["source_files"])
        self.assertEqual(project["next_safe_action"], "export build123d v2 and review geometry")

    def test_v2_learning_docs_exist_and_capture_print_lessons(self):
        source_readme = Path("projects/world-cup-neighbors/source/README.md").read_text()
        review = Path("projects/world-cup-neighbors/reviews/005-v2-build123d-design-notes.md").read_text()
        learning = Path("docs/learning/build123d-figurine-workflow.md").read_text()
        root_readme = Path("README.md").read_text()

        for text in (source_readme, review, learning, root_readme):
            self.assertIn("build123d", text)

        self.assertIn("goal backdrop", source_readme)
        self.assertIn("low-relief soccer ball", review)
        self.assertIn("support", learning)
        self.assertIn("World Cup neighbors v2", root_readme)

    def test_artifact_manifest_records_v2_build123d_outputs(self):
        artifacts = json.loads(Path("projects/world-cup-neighbors/artifacts.json").read_text())

        self.assertEqual(artifacts["revision"], "v002")
        kinds = {entry["kind"] for entry in artifacts["artifacts"]}
        paths = {entry["path"] for entry in artifacts["artifacts"]}

        self.assertIn("cad_step", kinds)
        self.assertIn("mesh_stl", kinds)
        self.assertIn("outputs/world-cup-neighbors.step", paths)
        self.assertIn("outputs/world-cup-neighbors.stl", paths)
```

- [ ] **Step 3: Run tests and verify expected failures**

Run:

```bash
uv run python -m unittest tests.test_cad tests.test_world_cup_v2 -v
```

Expected: failures or errors because `source/model.py`, v2 docs, and updated artifact metadata do not exist yet.

### Task 2: Implement The build123d V2 Model

**Files:**
- Create: `projects/world-cup-neighbors/source/model.py`
- Modify: `projects/world-cup-neighbors/project.yaml`

- [ ] **Step 1: Create the project-local model**

Create `projects/world-cup-neighbors/source/model.py` with a build123d model that exposes `model = assemble_scene()`. The file must define:

```python
PARAMS = {
    "base": {"width": 125.0, "depth": 70.0, "height": 4.0},
    "goal": {"width": 106.0, "height": 52.0, "post": 4.0, "rail_y": 25.0},
    "ball": {"radius": 7.0},
    "feature_min": 0.8,
}
```

The scene must include:

- a rounded or chamfered base;
- raised `DAN`, `CARRIE`, and `BRAZIL WATCH PARTY` labels;
- a rear goal backdrop with thick posts, crossbar, and non-fragile net bars;
- a low-relief soccer ball attached to the base;
- Dan and Carrie as separate chunky person assemblies with broad face planes, glasses/hair/jersey cues, attached arms, and stable legs.

- [ ] **Step 2: Update project manifest**

Edit `projects/world-cup-neighbors/project.yaml` to:

```yaml
lane: build123d
status: design
current_revision: v002
next_safe_action: export build123d v2 and review geometry
constraints:
  dimensions_mm:
  - shared base target 125 x 70 mm, soft max 130 x 75 mm
  - height under 85 mm
  tolerance_notes: Decorative print; prioritize chunky support-aware facial cues, goal backdrop structure, and paint-friendly Brazil jersey panels.
source_files:
- source/model.py
- outputs/world-cup-neighbors.scad
```

- [ ] **Step 3: Run the source contract test**

Run:

```bash
uv run python -m unittest tests.test_cad.CadTests.test_world_cup_v2_source_defines_exportable_model -v
```

Expected: PASS.

### Task 3: Add Durable Learning Documentation

**Files:**
- Create/modify: `projects/world-cup-neighbors/source/README.md`
- Create: `projects/world-cup-neighbors/reviews/005-v2-build123d-design-notes.md`
- Create: `docs/learning/build123d-figurine-workflow.md`
- Modify: `README.md`

- [ ] **Step 1: Document the project-local source model**

Create `projects/world-cup-neighbors/source/README.md` explaining the component functions, safe edit points, support-avoidance choices, and why the v2 model uses build123d instead of OpenSCAD for the active revision.

- [ ] **Step 2: Record v2 design notes**

Create `projects/world-cup-neighbors/reviews/005-v2-build123d-design-notes.md` with sections for chosen path, rejected pathways, printability choices, and what to inspect before slicing.

- [ ] **Step 3: Create the reusable learning doc**

Create `docs/learning/build123d-figurine-workflow.md` with durable guidance for future agent-assisted figurine projects:

- use build123d for parametric gift objects where dimensions and revision safety matter;
- keep face cues chunky and attached;
- make scene props structural;
- prefer low-relief decorative geometry over fragile freestanding detail;
- use `uv run bambu export-build123d` before any slicer work;
- keep private photos and generated outputs ignored.

- [ ] **Step 4: Link the learning path from README**

Add a short `World Cup Neighbors V2 Learning Path` section to `README.md` pointing to the source README and learning doc.

- [ ] **Step 5: Run the docs tests**

Run:

```bash
uv run python -m unittest tests.test_world_cup_v2.WorldCupV2Tests.test_v2_learning_docs_exist_and_capture_print_lessons -v
```

Expected: PASS.

### Task 4: Export, Sync Artifacts, And Verify

**Files:**
- Modify: `projects/world-cup-neighbors/artifacts.json`
- Generated ignored files: `outputs/world-cup-neighbors.step`, `outputs/world-cup-neighbors.stl`

- [ ] **Step 1: Export the build123d model**

Run:

```bash
uv run bambu export-build123d projects/world-cup-neighbors --output-dir outputs
```

Expected:

- STEP and STL paths printed;
- bounding box fits A1 mini: yes;
- no printer contact.

- [ ] **Step 2: Sync artifacts explicitly**

Run:

```bash
uv run bambu sync-artifacts projects/world-cup-neighbors --outputs-root outputs
```

Expected: artifact count includes `world-cup-neighbors.step` and `world-cup-neighbors.stl`.

- [ ] **Step 3: Run focused tests**

Run:

```bash
uv run python -m unittest tests.test_cad tests.test_world_cup_v2 -v
```

Expected: PASS.

- [ ] **Step 4: Run full test suite**

Run:

```bash
uv run python -m unittest discover -s tests -v
```

Expected: PASS.

- [ ] **Step 5: Inspect generated artifact tracking**

Run:

```bash
git status --short --ignored
```

Expected:

- tracked changes include Python source, docs, tests, project manifest, and `artifacts.json`;
- ignored generated outputs remain ignored under `outputs/`;
- no `private/` files are staged.

### Task 5: Commit And Push

**Files:**
- All tracked implementation files from Tasks 1-4.

- [ ] **Step 1: Stage tracked implementation files**

Run:

```bash
git add README.md docs/learning/build123d-figurine-workflow.md docs/superpowers/plans/2026-06-12-world-cup-neighbors-v2-build123d-implementation.md projects/world-cup-neighbors/project.yaml projects/world-cup-neighbors/source/model.py projects/world-cup-neighbors/source/README.md projects/world-cup-neighbors/reviews/005-v2-build123d-design-notes.md projects/world-cup-neighbors/artifacts.json tests/test_cad.py tests/test_world_cup_v2.py
```

- [ ] **Step 2: Commit**

Run:

```bash
git commit -m "feat: add world cup v2 build123d model"
```

- [ ] **Step 3: Push main**

Run:

```bash
git push origin main
```

- [ ] **Step 4: Final report**

Report:

- model source path;
- learning doc path;
- export results;
- tests run;
- that generated outputs were not committed;
- that no print was started.
