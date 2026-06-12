---
name: bambu-operate
description: Use when operating the Bambu repo for 3D-print generation, setup checks, slicer planning, MCP use, or printer-safe hand holding.
---

# Bambu Operate

Bambu turns plain-English print ideas into reviewable source and slicing plans for a Bambu Lab A1 mini.

## Protocol

1. Start with `bambu_context_view` and `bambu_doctor` through MCP, or `uv run bambu doctor` in the terminal.
2. Keep private reference photos under `private/`; never commit them.
3. For new general work, call `bambu_create_project` first so the request has a manifest, CAD lane, material, plate, revision, and next-safe-action state.
4. Use build123d for serious/private/dimensional CAD. Use OpenSCAD for simple public/remixable models and the current figurine first pass.
5. Generate or revise source files before thinking about slicing.
6. For build123d source, use `bambu_build123d_export`; it exports STEP/STL and bounding-box metadata only.
7. After any export, call `bambu_sync_artifacts` so generated files are classified and hashed in `artifacts.json`.
8. For the current watch-party prototype, use `bambu_generate_world_cup_figurines`.
9. For OpenSCAD export, use `bambu_openscad_export_plan`; do not guess the OpenSCAD command.
10. For slicing, use `bambu_slice_plan`; it should use detected Bambu Studio or OrcaSlicer executables.
11. For the full safe prototype path, use `bambu_build_world_cup_prototype`; it generates SCAD, STL, and sliced 3MF but does not start the printer.
12. After a physical print, call `bambu_record_print_result` with outcome, measurements, material state, failure mode, and next revision notes.
13. Do not start print jobs. Stop at a plan and require manual approval before printer contact.

## Safe Surfaces

- MCP: `uv run bambu-mcp`
- CLI: `uv run bambu doctor`
- CLI: `uv run bambu create-project "Shelf bracket" --lane build123d --material "Bambu PETG HF" --plate-side textured`
- CLI: `uv run bambu export-build123d projects/shelf-bracket --output-dir outputs`
- CLI: `uv run bambu sync-artifacts projects/shelf-bracket --outputs-root outputs`
- CLI: `uv run bambu make-figurines --output outputs/world-cup-neighbors.scad`
- CLI: `uv run bambu slice-plan outputs/world-cup-neighbors.stl --output outputs/world-cup-neighbors.gcode.3mf`
- CLI: `uv run bambu record-print-result projects/shelf-bracket --outcome failed --failure-mode warped_corner --notes "Corner lifted." --next-revision "Add brim."`

## Hard Rules

- Do not commit `private/`, printer credentials, generated STL/3MF/G-code, or private photos.
- Do not use official Brazil federation crests or trademarked marks unless licensed assets are supplied.
- Do not present a slicer command as print-ready until supports, scale, filament, bed type, and first layer have been reviewed.
