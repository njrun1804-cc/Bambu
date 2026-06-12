# V2 Build123d Design Notes

## Chosen Path

V2 uses the hybrid build123d caricature path. The goal is a sturdier, more readable single-material gift object rather than photorealistic likeness.

The scene is a goal backdrop plus a low-relief soccer ball. This keeps the soccer context stronger than v001 and makes the scene props do structural work.

## Rejected Pathways

- Full portrait sculpting was rejected for v2 because build123d is better at parametric solid modeling than organic likeness.
- Generic icon figures were rejected because they would print reliably but lose too much of the personal Dan and Carrie gift quality.
- Fragile freestanding net mesh was rejected because it would be hard to print cleanly and easy to break.
- A tiny freestanding soccer ball was rejected in favor of an attached low-relief soccer ball.

## Printability Choices

- The model keeps a `125 x 70 mm` footprint and stays under `85 mm` high.
- Face details are attached to flat head fronts and use thick raised bars.
- Arms stay close to the body instead of reaching into unsupported spans.
- Hair is modeled as broad caps and side masses rather than strands.
- The goal backdrop uses thick posts, crossbar, and raised net bars.
- Jersey details are raised paint guides, not multicolor printing requirements.

## What To Inspect Before Slicing

- Confirm the head and face area reads as two people from the front.
- Confirm the goal backdrop and ball read as soccer scene cues.
- Confirm the slicer preview does not place heavy supports on glasses, smiles, hair, or arms.
- Confirm `DAN`, `CARRIE`, and `BRAZIL WATCH PARTY` remain legible.
- Confirm the Bambu Studio profile is A1 mini, PLA Basic, textured PEI, and 0.20 mm standard unless intentionally changed.

## Learning Captured

`Text` uses `font_size` in build123d 0.10. The project model also avoids dataclasses because the current dynamic loader does not register the module in `sys.modules`, which breaks dataclass type handling.
