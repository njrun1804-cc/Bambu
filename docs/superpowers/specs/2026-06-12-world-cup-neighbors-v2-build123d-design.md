# World Cup Neighbors V2 Build123d Design

## Goal

Create a v2 design plan for `projects/world-cup-neighbors` that uses build123d as the learning CAD lane while improving the physical model quality from v001.

The target is not photorealistic likeness. The target is a sturdy, readable, single-material gift object: two stylized neighbors, Dan and Carrie, in Brazil-inspired soccer jerseys, standing in a small soccer watch-party scene that prints cleanly on the Bambu Lab A1 mini.

## Source Context

V001 printed successfully enough to prove the concept, but the head and face area read poorly after printing:

- the figures looked more like cylinders with accessories than people;
- facial details were too small and too buried under tree supports;
- tree supports were visually large and likely to scar face, hair, glasses, and arms during removal;
- the raised names, base text, soccer ball, shallow net cues, base adhesion, and overall scale worked.

The v2 design keeps the successful base/story elements and moves the model from OpenSCAD-first geometry to build123d-first geometry.

## Chosen Approach

Use a **hybrid build123d caricature** approach:

- build the scene from parametric, inspectable Python CAD primitives;
- make likeness cues broad and readable rather than tiny and realistic;
- use the soccer scene as structure, not just decoration;
- export STEP/STL through the existing build123d gate;
- document what was learned as durable repo knowledge while building;
- keep raw private photos and generated meshes out of git.

This is the best tradeoff between learning build123d, improving the print, and staying within what agents can revise safely.

## Learning Objective

V2 is also a learning project. The implementation should leave the repo knowing more than it did before about practical agent-assisted 3D printing.

Document decisions and findings as they happen, not only at the end:

- which build123d APIs worked well for printable figurine geometry;
- which APIs or modeling pathways were tried and rejected;
- what minimum feature sizes were chosen and why;
- how support-avoidance changed the design;
- how the A1 mini, PLA Basic, textured PEI plate, Bambu Studio, and export pipeline shaped the model;
- what an agent should inspect before claiming a model is ready to slice or print.

This knowledge should be public-safe and reusable for future projects. It must not depend on private photos being committed.

## Rejected Alternatives

### Full Likeness Sculpt

This would chase stronger face resemblance through organic mesh sculpting. It is not the v2 path because build123d is a precise BREP CAD tool, not a portrait-sculpting tool. The risk is spending a lot of time on faces that still print poorly at this scale.

### Icon-Only Reliability Pass

This would simplify the figures into generic soccer icons. It would print well, but it loses too much of the personal gift quality.

### Blender-First Organic Model

This may become useful later for real caricature heads, but it is not the right first learning step. Blender meshes are harder for agents to inspect, diff, test, and parameterize than build123d source.

## V2 Visual Direction

### Main Scene: Goal Backdrop + Low-Relief Ball

The v2 scene should use a small soccer goal behind the figures:

- two thick posts and a thick crossbar;
- a shallow raised or engraved net pattern on a sturdy rear panel or rail;
- no fragile free-standing net mesh;
- the goal sits behind the figures and can visually frame the heads;
- the goal may also provide hidden or visible support connection points for shoulders, hair, or arms.

The soccer ball should be a stable low-relief object:

- preferred: a half-ball or flattened ball leaning into the base or goal post;
- panel lines are engraved/recessed or raised enough to paint after printing;
- avoid a tiny free-standing sphere unless it is attached to the base and another object.

### Alternative Scene Concepts

Keep these as fallback design options if the goal backdrop becomes too visually heavy:

1. `sideline_watch_party`: a low rail, cups, and watch-party base details, with soccer ball cues on the base.
2. `large_ball_emblem`: a larger partial soccer-ball medallion behind or between the figures.
3. `goal_backdrop`: the default v2 concept, because it gives soccer context and structural help.

Only `goal_backdrop` should be implemented first.

## Figure Design

Each figure should be a chunky caricature built from named build123d components:

- `base_pose`: standing, stable, slightly different stance for Dan and Carrie;
- `torso`: rounded block or tapered solid with front jersey panel;
- `head`: larger than v001, with a flatter front face plane;
- `hair`: broad cap/shell shapes attached to the head, not thin strands;
- `glasses`: thick raised geometry attached to the face plane;
- `face_cues`: nose, smile, cheeks, and eyes as exaggerated raised or recessed features;
- `arms`: attached to torso or props, with no long unsupported spans;
- `legs`: sturdy and slightly stylized, with enough separation to read but enough mass to print;
- `jersey`: Brazil-inspired raised panels, number guides, collar, and sleeve bands.

Dan and Carrie should differ through silhouette, not fragile detail:

- Dan: taller, narrower stance, glasses, short hair, simple jersey torso.
- Carrie: shorter, rounder silhouette, different hair mass, necklace or collar cue, jersey panel sized for paint.

Do not use official Brazil federation crests or trademarked marks. Use generic Brazil-inspired soccer styling: green/yellow/blue paint guides, jersey panels, stars/dots only if they are generic decorative marks.

## Printability Rules

The model should be designed for green Bambu PLA Basic on the A1 mini with a 0.4 mm nozzle and textured PEI plate.

Default constraints:

- keep footprint around `125 x 70 mm`, with `130 x 75 mm` as the soft upper bound;
- keep height under `85 mm`;
- keep minimum raised feature width at or above `0.8 mm`;
- prefer `1.2 mm+` for facial and jersey features expected to survive support removal;
- keep text at least as large and bold as v001 labels;
- avoid free-standing thin rods, strings, or net mesh;
- make arms, hair, glasses, and props body-adjacent;
- design all overhang-sensitive details to be self-supporting where practical.

Slicer supports are allowed, but they should no longer be the primary structure keeping the scene printable. If supports are needed, they should touch broad, less-visible regions rather than face details.

## build123d Architecture

Add a build123d source model under the project:

```text
projects/world-cup-neighbors/
  source/
    model.py
    README.md
```

`model.py` should expose:

- `model`: the final build123d object consumed by `bambu export-build123d`;
- named helper functions for base, goal, ball, and each person;
- a small parameter block for dimensions and feature widths.

Recommended module shape:

```text
PARAMS
make_base()
make_goal_backdrop()
make_soccer_ball_relief()
make_person(spec)
make_dan()
make_carrie()
assemble_scene()
model = assemble_scene()
```

This keeps the model understandable for agents and makes later tradeoff experiments cheap.

## Data Flow

1. `projects/world-cup-neighbors/source/model.py` defines the build123d model.
2. `uv run bambu export-build123d projects/world-cup-neighbors --output-dir outputs` exports STEP/STL and records the bounding box.
3. `uv run bambu sync-artifacts projects/world-cup-neighbors --outputs-root outputs` records generated artifact hashes.
4. Slicing remains a separate manual-review step through Bambu Studio or OrcaSlicer.
5. Printing remains manual only after support, scale, filament, plate, and first-layer review.

The old OpenSCAD v001 path should remain available until v2 exports and slices successfully.

## Project Evidence Integration

The v2 implementation should align with the project evidence layout design:

- raw reference photos stay ignored;
- v2 intent goes into an iteration brief;
- generated STEP/STL/3MF files stay under `outputs/` and out of git;
- print-result and post-print photos go into ignored iteration/photo locations;
- tracked review files summarize what the private photos show without exposing them.

If the evidence-layout migration is not implemented first, the v2 work may use current `reviews/`, `measurements/`, and `artifacts.json` paths for compatibility.

## Documentation Deliverables

Implementation should update or create these durable documentation surfaces:

- `projects/world-cup-neighbors/source/README.md`: explain the v2 build123d model structure, component names, and safe edit points.
- `projects/world-cup-neighbors/reviews/005-v2-build123d-design-notes.md` or the equivalent v2 iteration review file: record design tradeoffs and visual choices.
- `docs/learning/build123d-figurine-workflow.md`: capture reusable lessons for future figurine or gift-object projects, including tested pathways and rejected approaches.
- `README.md`: add a short pointer to the build123d figurine learning path once the v2 export works.

The learning doc should be practical and agent-facing. It should answer: "If Codex or Claude starts a new personal 3D-print gift project tomorrow, what do we now know that prevents repeating v001 mistakes?"

## Testing And Verification

Automated checks should cover:

- the build123d source defines `model`;
- export writes STEP and STL files when build123d is installed;
- the bounding box fits the A1 mini build volume;
- generated artifact hashes are recorded;
- source files are tracked but generated outputs are ignored;
- required learning docs exist or are updated with v2-specific notes.

Manual checks should cover:

- face/head area reads as people before slicing;
- goal and ball details are visible at the intended print scale;
- slicer support preview avoids heavy supports on faces;
- base text and names remain legible;
- Bambu Studio profile uses A1 mini, PLA Basic, textured PEI, and 0.20 mm standard settings unless deliberately changed.

## Success Criteria

V2 is successful if:

- it teaches and exercises the build123d lane with a real project model;
- it leaves durable, public-safe notes about the build123d and 3D-printing lessons learned;
- the model exports through the repo's existing build123d gate;
- the scene clearly reads as two people at a Brazil soccer watch party;
- the goal and ball are more recognizable than v001;
- faces are chunkier and more person-like than v001;
- the slicer preview shows substantially less fragile support contact near faces and arms;
- the repo remains public-safe.

## Non-Goals

- Do not automate printer start.
- Do not commit private photos.
- Do not commit generated STL, STEP, 3MF, G-code, or slicer project outputs.
- Do not attempt photorealistic portrait likeness in v2.
- Do not add licensed Brazil team marks.
- Do not replace Bambu Studio as the manual slicer/review surface.
