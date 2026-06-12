# build123d Figurine Workflow

This note captures durable learning from the World Cup neighbors v2 build123d pass. It is meant for agents starting future personal 3D-print gift projects in this repo.

## When build123d Helps

Use build123d when the model benefits from parametric dimensions, named components, reproducible exports, and testable fit against the Bambu Lab A1 mini build volume.

For small personal figurines, build123d is not a portrait sculpting tool. It works best for chunky caricature geometry, scene bases, labels, paint guides, sturdy props, and repeated components that an agent can revise safely.

## Model For The Printer, Not The Screenshot

V001 proved that tiny face details can exist in source but disappear visually after supports and printing. V2 shifts to larger face planes and raised features that are attached to the head.

Practical defaults:

- keep raised features at least `0.8 mm` wide;
- prefer `1.2 mm+` for face, jersey, and handled details;
- make arms, hair, glasses, and props body-adjacent;
- make scene props structural where possible;
- prefer low-relief decoration over fragile freestanding detail.

## Soccer Scene Lessons

A goal backdrop is better than a decorative net mesh for this scale. Thick posts, a crossbar, and raised net bars give immediate soccer context while staying printable.

A low-relief soccer ball is safer than a tiny freestanding sphere. Attach it to the base or a post, then use raised or engraved panel guides for painting.

## build123d API Notes

Use `BuildPart`, `BuildSketch`, `Locations`, `Box`, `Cylinder`, and `Text` for this style of model.

In build123d 0.10, text uses `font_size`:

```python
Text("DAN", font_size=7.0, align=Align.CENTER)
```

Do not use `@dataclass` in project-local model files until `bambu.cad` changes its dynamic loader. The loader currently executes source through `importlib.util.module_from_spec()` without registering the module in `sys.modules`, and dataclasses expect that module registration.

## Safe Agent Workflow

1. Read `project.yaml`, `source/README.md`, and the latest review notes.
2. Edit tracked source under `projects/<slug>/source/`.
3. Run the model contract tests.
4. Export with:

   ```bash
   uv run bambu export-build123d projects/<slug> --output-dir outputs
   ```

5. Sync generated artifact hashes:

   ```bash
   uv run bambu sync-artifacts projects/<slug> --outputs-root outputs
   ```

6. Open the generated STL or 3MF in Bambu Studio and inspect supports, scale, filament, plate side, and first layer before any print.

Generated STL, STEP, 3MF, G-code, preview images, printer credentials, and private photos stay out of git.

## FreeCAD Review Lessons

FreeCAD is the CAD inspection layer, not the source of truth. Keep build123d Python as source, export STEP/STL, then use FreeCAD to inspect the STEP.

On Mike's Mac, use the app bundle's console mode:

```bash
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c /absolute/path/to/tools/freecad_review.py --pass /absolute/path/to/model.step /absolute/path/to/review.json
```

Do not rely on `FreeCADCmd`; the installed app bundle may not include it. Do not import FreeCAD modules from ordinary system Python. Use FreeCAD's own executable so its OpenCASCADE and Python linkage stay coherent.

Practical harness notes:

- pass absolute script and artifact paths;
- isolate FreeCAD runtime state under `.freecad-runtime/`;
- scrub the subprocess environment because the FreeCAD wrapper can print environment setup;
- support both `--pass` arguments and `FREECAD_INPUT_STEP` / `FREECAD_OUTPUT_JSON` env vars;
- call the review script unconditionally, because FreeCAD console mode may not set `__name__ == "__main__"`;
- use `CenterOfMass` when available and fall back to `CenterOfGravity`;
- keep FreeCAD inspection separate from GUI viewing.

Interpretation matters: FreeCAD may report a STEP as valid and closed while `shape.check(True)` still reports OpenCASCADE self-intersection warnings. That is useful design feedback, not a reason to hide the report. Preserve the JSON and treat geometry-check warnings as cleanup input before printing.
