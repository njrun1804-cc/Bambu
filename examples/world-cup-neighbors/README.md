# World Cup Neighbors Example

This example generates two generic, stylized Brazil-watch-party figurines. It is meant as a safe public version of a private reference-photo workflow.

Run:

```bash
python3 -m bambu.cli make-figurines --output outputs/world-cup-neighbors.scad
```

Then open the `.scad` file in OpenSCAD, export STL, and run:

```bash
python3 -m bambu.cli slice-plan outputs/world-cup-neighbors.stl --output outputs/world-cup-neighbors.gcode.3mf
```

Or run the full local prototype pipeline:

```bash
uv run bambu prototype-world-cup --output-dir outputs --slicer bambu-studio
uv run bambu handoff
```

`handoff` checks the generated `.gcode.3mf` for the A1 mini, PLA Basic, Textured PEI, and A1M standard process markers, then prints the Bambu Studio open command. It still stops before the physical print.

The generated OpenSCAD uses raised jersey panels and numbers as paint guides. It does not include official Brazil federation marks or private photos.
