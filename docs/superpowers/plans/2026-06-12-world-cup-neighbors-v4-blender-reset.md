# World Cup Neighbors V4 Blender Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the failed build123d-character path with a Blender-first v4 visual generation loop for the Dan and Carrie Brazil watch party scene.

**Architecture:** Keep v1-v3 as historical evidence, but create a new v4 lane with structured specs, a Blender Python generator, fixed-view renders, and target-crop contact sheets. build123d/FreeCAD remain downstream validation tools; Blender owns the organic character geometry and visual review.

**Tech Stack:** Python 3.12, PyYAML, Pillow, Blender Python/CLI, unittest, existing `bambu.review3d` visual-contact-sheet helpers.

---

### Task 1: V4 Spec Contract

**Files:**
- Create: `projects/world-cup-neighbors/designs/v4/scene.yaml`
- Create: `projects/world-cup-neighbors/designs/v4/people.yaml`
- Create: `projects/world-cup-neighbors/designs/v4/visual_targets.yaml`
- Create: `projects/world-cup-neighbors/designs/v4/print_constraints.yaml`
- Create: `projects/world-cup-neighbors/designs/v4/acceptance.yaml`
- Test: `tests/test_world_cup_v4.py`

- [ ] Write tests proving v4 is Blender-first, uses the colored ChatGPT target image, requires fixed target crops, and keeps printer contact disallowed.
- [ ] Add the v4 YAML files with explicit visual-contract parameters for heads, glasses, hair, bodies, goal, ball, base, and print-safe minimum features.
- [ ] Run `uv run python -m unittest tests.test_world_cup_v4 -v`.

### Task 2: Blender V4 Pipeline Module

**Files:**
- Create: `bambu/blender_v4.py`
- Create: `tools/render_v4_blender.py`
- Test: `tests/test_blender_v4.py`

- [ ] Write tests for loading the v4 specs, building a safe Blender command, and producing a report that never contacts the printer.
- [ ] Implement `load_v4_spec`, `build_blender_v4_command`, and `render_v4_candidate`.
- [ ] Add `tools/render_v4_blender.py` as the agent entrypoint.
- [ ] Run `uv run python -m unittest tests.test_blender_v4 -v`.

### Task 3: Blender Generator Source

**Files:**
- Create: `projects/world-cup-neighbors/source/v4/blender_scene.py`
- Create: `projects/world-cup-neighbors/source/v4/README.md`
- Test: extend `tests/test_blender_v4.py`

- [ ] Write tests that assert the generator source contains the expected CLI args and named render views.
- [ ] Implement a procedural Blender scene with smooth chibi primitives, raised face features, hair masses, jersey relief, integrated ball, goal, and base labels.
- [ ] Export STL and render `front`, `front-angle`, `top`, `dan-head`, `carrie-head`, and `low-front`.

### Task 4: Visual Review Run

**Files:**
- Generated ignored outputs: `outputs/review/world-cup-neighbors-v4/*`
- Review note: `projects/world-cup-neighbors/reviews/008-v4-blender-reset.md`

- [ ] Run `uv run python tools/render_v4_blender.py projects/world-cup-neighbors --json outputs/review/world-cup-neighbors-v4/review-report.json`.
- [ ] Inspect `outputs/review/world-cup-neighbors-v4/visual-contact-sheet.png`.
- [ ] Record what passes/fails against the visual contract.

### Task 5: Optional Vision-Critic Scaffold

**Files:**
- Create: `bambu/visual_qa.py`
- Create: `tools/visual_qa_openai.py`
- Test: `tests/test_visual_qa.py`

- [ ] Add an env-gated OpenAI vision QA request builder that accepts target/current images and emits strict JSON instructions.
- [ ] Do not require API access for normal tests.
- [ ] Keep the visual critic read-only: it proposes CAD/Blender changes but never edits geometry.

### Verification

- [ ] Run `uv run python -m unittest discover -s tests -v`.
- [ ] Confirm `projects/world-cup-neighbors/artifacts.json` is unchanged by v4 preview/review commands.
- [ ] Confirm no command contacts the printer or Bambu Studio.
