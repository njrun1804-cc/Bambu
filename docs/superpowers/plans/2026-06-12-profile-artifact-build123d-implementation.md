# Profile Artifact Build123d Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten the Bambu substrate around real installed slicer profiles, generated artifact indexing, and build123d STEP/STL export.

**Architecture:** Extend existing focused modules instead of adding a workflow engine. `bambu.slicer` resolves A1 mini machine/process/filament profiles from actual Bambu/Orca profile files. `bambu.projects` syncs generated output files into project artifact manifests. A new `bambu.cad` module loads build123d source files and exports STEP/STL plus bounding-box metadata.

**Tech Stack:** Python 3.12, build123d 0.10.0, PyYAML, Bambu Studio/Orca profile JSON, `unittest`.

---

## File Structure

- Modify `bambu/slicer.py`: material-aware A1 mini profile resolver and profile metadata in slice plans.
- Modify `tests/test_slicer.py`: tests for PETG HF profile resolution and command/profile metadata.
- Modify `bambu/projects.py`: artifact sync helper that classifies generated files.
- Modify `tests/test_projects.py`: tests for syncing output artifacts into `artifacts.json`.
- Create `bambu/cad.py`: build123d source loading, STEP/STL export, bounding-box summary, and fit validation.
- Create `tests/test_cad.py`: tests for build123d export from `source/model.py`.
- Modify `bambu/mcp_server.py`: expose `bambu_sync_artifacts` and `bambu_build123d_export`.
- Modify `bambu/cli.py`: expose `sync-artifacts` and `export-build123d`.
- Modify `tests/test_mcp_tools.py` and `tests/test_cli.py`: coverage for the new surfaces.

## Tasks

- [x] Add failing slicer tests for PETG HF profile resolution.
- [x] Implement material-aware profile resolution and profile metadata.
- [x] Add failing project tests for artifact sync/classification.
- [x] Implement project artifact sync.
- [x] Add failing CAD tests for build123d export and bounding box.
- [x] Implement `bambu.cad`.
- [x] Add failing MCP/CLI tests for sync/export surfaces.
- [x] Implement MCP/CLI wrappers.
- [x] Run full verification: `uv run python -m unittest discover -s tests -v`, `uv run bambu doctor`, and `uv run python -c 'import build123d'`.

## Self-Review

- Scope stays off printer contact and cloud behavior.
- Bambu Studio remains primary; Orca remains fallback/comparison.
- Generated STL/STEP/3MF/PNG/G-code stay ignored and are represented by hashes in `artifacts.json`.
- The build123d lane exports local files only; it does not slice or start a print.
