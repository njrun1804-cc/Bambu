# Bambu Lab A1 Mini Profile Notes

This repo targets a Bambu Lab A1 mini.

Default assumptions in `bambu.slicer`:

- bed type: `Textured PEI Plate`
- slicer output: `.gcode.3mf`
- auto-orient enabled
- auto-arrange enabled
- plate: `0`, meaning all plates in common Bambu/Orca CLI usage

The repo does not ship machine, process, or filament JSON profiles yet. The safest first workflow is:

1. Generate or export STL.
2. Open the STL in Bambu Studio.
3. Select the A1 mini printer profile manually.
4. Select the filament actually loaded in the printer.
5. Inspect supports and first layer.
6. Save/export the sliced `.gcode.3mf`.

When stable local profile JSON files exist, put local copies in `private/` first. Only publish sanitized profile files after confirming they do not contain account, device, or network-specific values.

