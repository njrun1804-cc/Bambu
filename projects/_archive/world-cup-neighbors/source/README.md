# World Cup Neighbors V2 Source

This directory contains the active v2 build123d source for the World Cup neighbors project.

## Model Entry Point

`model.py` exposes `model = assemble_scene()`, which is the object loaded by:

```bash
uv run bambu export-build123d projects/world-cup-neighbors --output-dir outputs
```

The file is intentionally organized around small, named component functions:

- `make_base()` builds the rounded shared base and raised labels.
- `make_goal_backdrop()` builds the structural goal backdrop and robust net bars.
- `make_soccer_ball_relief()` builds the attached low-relief soccer ball.
- `make_person(spec)` builds one chunky caricature figure.
- `make_dan()` and `make_carrie()` are represented by the `DAN` and `CARRIE` specs passed into `make_person`.
- `assemble_scene()` combines the base, goal backdrop, low-relief soccer ball, Dan, and Carrie.

## Safe Edit Points

Start with the `PARAMS` block for broad scale changes. Keep the base near `125 x 70 mm` and the height under `85 mm` unless you are deliberately revising the A1 mini fit.

For visual tradeoffs, edit the `PersonSpec` values before changing helper logic. Dan and Carrie differ by silhouette: height, torso width, head width, hair style, and jersey number cues.

## Printability Choices

The goal backdrop is structural, not just decorative. It adds soccer context while providing a visually coherent rear frame that can reduce fragile support dependency around the heads and arms.

The low-relief soccer ball is attached to the base instead of printed as a tiny freestanding sphere. Its panel guides are raised enough to paint, but thick enough to survive handling.

Face details are chunky and attached to a flat face plane. Glasses, nose, smile, cheeks, hair, arms, and jersey panels use simple raised geometry because v001 showed that tiny isolated features get buried by supports and do not read well after printing.

## build123d Pathway Notes

`Text` in build123d 0.10 uses `font_size`, not `size`. Use `Text("DAN", font_size=7.0, align=Align.CENTER)` for base labels.

Avoid `@dataclass` in project-local model files while `bambu.cad` loads them through `importlib.util.module_from_spec()` without registering the module in `sys.modules`. A plain value object is less elegant but more reliable for dynamically loaded model source.

Generated STEP and STL files belong in `outputs/` and remain ignored by git. The tracked source and artifact manifest are the durable repo state.
