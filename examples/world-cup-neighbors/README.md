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

The current quality pass uses a shared 118 x 62 mm display base, raised `DAN` and `CARRIE` name labels, two stylized figures with distinct height/build/hair/glasses/bag cues, and A1-mini-safe raised details for a 0.4 mm nozzle. The soccer ball and goal/net are shallow raised base details so the print keeps the watch-party feel without fragile free-standing mesh or support-heavy posts. To render a preview:

```bash
openscad -o outputs/world-cup-neighbors-preview.png --imgsize=1600,1200 --viewall --autocenter --camera=0,-90,60,65,0,0,220 outputs/world-cup-neighbors.scad
```

Current local filament note: the generated `.gcode.3mf` uses the PLA Basic profile and matches the green PLA Basic spool. The white spool is PLA+ and should use a PLA/PLA+ profile if used. The blue spool is PETG HF; re-slice with a PETG HF profile before printing with that spool.
