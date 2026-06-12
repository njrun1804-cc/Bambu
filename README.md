# Bambu

Agent-assisted 3D-print preparation for a **Bambu Lab A1 mini**.

Bambu is a public-ready workbench for describing what you want in plain English, letting Codex or Claude help turn it into printable source files, and keeping the actual print step reviewable. It starts with OpenSCAD because the output is text, inspectable, parametric, and easy for agents to revise.

## What It Does Today

- Checks whether local 3D-printing tools are installed.
- Generates a stylized pair of Brazil-watch-party figurines as OpenSCAD.
- Builds dry-run slicer commands for Bambu Studio or OrcaSlicer.
- Keeps private photos, printer credentials, and generated meshes out of git.
- Refuses to pretend the printer is safe to automate blindly: v1 stops at reviewable files and command plans.

## Quick Start

```bash
git clone https://github.com/njrun1804/Bambu.git
cd Bambu
python3 -m bambu.cli doctor
python3 -m bambu.cli make-figurines --output outputs/world-cup-neighbors.scad
python3 -m bambu.cli slice-plan outputs/world-cup-neighbors.stl --output outputs/world-cup-neighbors.gcode.3mf
```

If OpenSCAD is installed, open `outputs/world-cup-neighbors.scad` and export an STL. If Bambu Studio or OrcaSlicer is installed, use the generated slicer command as the starting point, then inspect supports, scale, filament, and first-layer settings before printing.

## Recommended Human-Agent Loop

1. Write a short brief in `private/` for personal work or `examples/` for public-safe examples.
2. Ask Codex or Claude to generate or revise OpenSCAD.
3. Render or export in OpenSCAD.
4. Inspect the mesh before slicing.
5. Build a slicer command with `bambu slice-plan`.
6. Open the sliced project in Bambu Studio or OrcaSlicer.
7. Print only after manual review.

## Installing Optional Tools

The Python package itself has no runtime dependencies. External tools are optional but useful:

- **OpenSCAD**: exports `.scad` to `.stl`, `.3mf`, or `.png`.
- **Bambu Studio**: slices and exports `.gcode.3mf` for Bambu printers.
- **OrcaSlicer**: alternate slicer CLI.
- **Blender**: future sculpting/mesh repair lane for more organic figurines.

Run:

```bash
python3 -m bambu.cli doctor
```

That command tells you what is missing and what to do next.

## World Cup Figurine Example

```bash
python3 -m bambu.cli make-figurines --output outputs/world-cup-neighbors.scad
```

The example creates two simplified soccer-supporter figures with Brazil-inspired jersey panels and raised number guides. It is designed for single-material printing and post-print painting. It does not include private photos or official team marks.

## Public Repo Safety

Do not commit:

- private reference photos
- printer access codes, LAN credentials, or cloud tokens
- generated STL/3MF/G-code files unless they are intentionally published releases

The `.gitignore` is set up for this by default.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Run the local helper:

```bash
scripts/bambu doctor
```

