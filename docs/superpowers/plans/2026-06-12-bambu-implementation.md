# Bambu Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public-ready Bambu repo with a tested Python CLI for agent-assisted 3D-print preparation.

**Architecture:** A small Python package generates OpenSCAD source from structured briefs, detects optional external CAD/slicer tools, and builds safe dry-run slicer commands. The repo ships docs, examples, and GitHub Actions, while keeping private photos and generated print files out of git.

**Tech Stack:** Python 3.11+, standard-library `unittest`, OpenSCAD as optional CAD backend, Bambu Studio/OrcaSlicer as optional slicers.

---

### Task 1: Core Tests

**Files:**
- Create: `tests/test_preflight.py`
- Create: `tests/test_figurine.py`
- Create: `tests/test_slicer.py`

- [x] **Step 1: Write failing tests for tool detection, figurine generation, and slicer command planning.**
- [x] **Step 2: Run `python3 -m unittest discover -s tests -v` and verify tests fail because modules are missing.**

### Task 2: Core Package

**Files:**
- Create: `bambu/__init__.py`
- Create: `bambu/preflight.py`
- Create: `bambu/figurine.py`
- Create: `bambu/slicer.py`

- [x] **Step 1: Implement the minimal modules required by Task 1 tests.**
- [x] **Step 2: Run `python3 -m unittest discover -s tests -v` and verify tests pass.**

### Task 3: CLI And Examples

**Files:**
- Create: `bambu/cli.py`
- Create: `examples/world-cup-neighbors/brief.yaml`
- Create: `examples/world-cup-neighbors/README.md`
- Create: `outputs/.gitkeep`

- [x] **Step 1: Write CLI tests for `doctor`, `make-figurines`, and `slice-plan`.**
- [x] **Step 2: Implement the CLI and example files.**
- [x] **Step 3: Run CLI smoke tests and unit tests.**

### Task 4: Public Repo Polish

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `pyproject.toml`
- Create: `.github/workflows/ci.yml`
- Create: `profiles/bambu-a1-mini/README.md`
- Create: `scripts/bambu`
- Create: `LICENSE`

- [x] **Step 1: Document the public workflow and safety boundary.**
- [x] **Step 2: Add package metadata, CI, license, and helper script.**
- [x] **Step 3: Run all tests and commit.**

