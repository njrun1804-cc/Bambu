---
name: bambu-operate
description: Use when operating the Bambu repo for 3D-print generation, setup checks, slicer planning, MCP use, or printer-safe hand holding.
---

# Bambu Operate

Bambu turns plain-English print ideas into reviewable source and slicing plans for a Bambu Lab A1 mini.

## Protocol

1. Start with `bambu_doctor` through MCP, or `uv run bambu doctor` in the terminal.
2. Keep private reference photos under `private/`; never commit them.
3. Generate or revise source files before thinking about slicing.
4. For the current watch-party prototype, use `bambu_generate_world_cup_figurines`.
5. For export, use `bambu_openscad_export_plan`; do not guess the OpenSCAD command.
6. For slicing, use `bambu_slice_plan`; it should use detected Bambu Studio or OrcaSlicer executables.
7. For the full safe prototype path, use `bambu_build_world_cup_prototype`; it generates SCAD, STL, and sliced 3MF but does not start the printer.
8. Do not start print jobs. Stop at a plan and require manual approval before printer contact.

## Safe Surfaces

- MCP: `uv run bambu-mcp`
- CLI: `uv run bambu doctor`
- CLI: `uv run bambu make-figurines --output outputs/world-cup-neighbors.scad`
- CLI: `uv run bambu slice-plan outputs/world-cup-neighbors.stl --output outputs/world-cup-neighbors.gcode.3mf`

## Hard Rules

- Do not commit `private/`, printer credentials, generated STL/3MF/G-code, or private photos.
- Do not use official Brazil federation crests or trademarked marks unless licensed assets are supplied.
- Do not present a slicer command as print-ready until supports, scale, filament, bed type, and first layer have been reviewed.
