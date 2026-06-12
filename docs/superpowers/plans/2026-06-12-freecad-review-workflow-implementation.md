# FreeCAD Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an agent-friendly 3D review command that uses build123d as source, FreeCAD for STEP/CAD inspection, Blender for visual previews, and Bambu Studio only for downstream manual slicing review.

**Architecture:** Add a small `bambu.review3d` module that coordinates existing export logic, discovers FreeCAD and Blender, runs a FreeCAD Python inspection script against the generated STEP file, renders preview images with Blender, and returns a JSON-serializable report. Add `tools/review_3d.py` as the human/agent entrypoint and tests that mock subprocess boundaries without requiring FreeCAD in CI.

**Tech Stack:** Python 3.12, build123d, FreeCAD app bundle Python, Blender CLI, unittest, existing Bambu export/artifact helpers.

---

### Task 1: Review Workflow Tests

**Files:**
- Create: `tests/test_review3d.py`

- [x] Write tests for FreeCAD environment discovery, FreeCAD JSON parsing, Blender command planning, warning-exit report preservation, and no-printer-contact report fields.
- [x] Run `uv run python -m unittest tests.test_review3d -v`.
- [x] Confirm failures were due to missing `bambu.review3d`, then made the tests pass.

### Task 2: Review Module

**Files:**
- Create: `bambu/review3d.py`

- [x] Implement `detect_freecad()`.
- [x] Implement `inspect_step_with_freecad()`.
- [x] Implement `render_blender_previews()`.
- [x] Implement `review_project_3d()`.
- [x] Run `uv run python -m unittest tests.test_review3d -v`.

### Task 3: CLI Entrypoint

**Files:**
- Create: `tools/review_3d.py`
- Modify: `README.md`
- Modify: `docs/learning/build123d-figurine-workflow.md`

- [x] Add a script runnable as `uv run python tools/review_3d.py projects/world-cup-neighbors`.
- [x] Document the FreeCAD-first CAD review workflow.
- [x] Run `uv run python tools/review_3d.py projects/world-cup-neighbors`.

### Task 4: Verify And Commit

**Files:**
- All tracked files above.

- [x] Run `uv run python -m unittest discover -s tests -v`.
- [x] Confirm generated outputs/previews remain ignored.
- [x] Commit and push to `main`.
