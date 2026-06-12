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

The generated OpenSCAD uses raised jersey panels and numbers as paint guides. It does not include official Brazil federation marks or private photos.

