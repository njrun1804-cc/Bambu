# Bambu Lab A1 Mini Profile Notes

This repo targets a Bambu Lab A1 mini.

Default assumptions in `bambu.slicer`:

- bed type: `Textured PEI Plate`
- slicer output: `.gcode.3mf`
- auto-orient enabled
- auto-arrange enabled
- plate: `0`, meaning all plates in common Bambu/Orca CLI usage

When Bambu Studio or OrcaSlicer is installed under `/Applications`, the repo auto-loads bundled defaults when they exist:

- machine: `BBL/machine/Bambu Lab A1 mini 0.4 nozzle.json`
- process: `BBL/process/0.20mm Standard @BBL A1M.json`
- filament: `BBL/filament/Bambu PLA Basic @BBL A1M.json`

The safest first workflow is:

1. Generate or export STL.
2. Open the STL in Bambu Studio.
3. Select the A1 mini printer profile manually.
4. Select the filament actually loaded in the printer.
5. Inspect supports and first layer.
6. Save/export the sliced `.gcode.3mf`.

For a generated `.gcode.3mf`, run:

```bash
uv run bambu handoff
```

That command verifies the expected A1 mini profile markers inside the sliced package and prints the exact Bambu Studio open command. The Device tab still needs a human check that the physical printer is online and is the A1 mini. If Bambu Studio asks for the Bambu Network plug-in, that setup is required before cloud/WLAN print sending and live printer status will work.

When stable local profile JSON files exist, put local copies in `private/` first. Only publish sanitized profile files after confirming they do not contain account, device, or network-specific values.
