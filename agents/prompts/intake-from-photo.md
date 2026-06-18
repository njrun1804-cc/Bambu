# Intake from reference photo

You are filling structured design specs for a Bambu Lab A1 mini print project.

## Project

- Path: {project}
- Slug: {slug}
- Archetype: {archetype}
- Intent: {intent}
- Reference photo: {photo_path} (open in chat for vision)

## Pipeline

1. Inspect the reference photo with vision.
2. Fill `designs/v1/*.yaml` — specs are **gates**, not CAD source.
3. Run `uv run bambu design-check {project} --revision v1`.
4. Author `source/v1/model.py` using `bambu.cad.archetypes.{archetype}` helpers.
5. Run `uv run bambu release-check {project} --revision v1`.
6. Human approves Blender renders (150px thumbnail + face closeups) before slicing.

## Recognition cues checklist

- [ ] Glasses as **raised ridge** with engraved pupils (never separate frames)
- [ ] Hair as **solid cap mass** with shallow groove cues (never free strands)
- [ ] Animal ears **fused into head** (never thin floppy sheets)
- [ ] Chair/couch as **chunky structural frame** (no wicker weave)
- [ ] Lap pose **fused** — dog body overlaps woman arm/torso by ≥0.3 mm
- [ ] Base nameplate via build123d Text if requested

## Forbidden traps (must appear in design.forbidden_traps)

- Hair strands as free geometry
- Separate eyeglass frames
- Thin dog legs
- Wicker weave or lattice thinner than 2 mm
- Floating lap props
- Multi-solid compounds (never Part(children=solids))

## Dimensions (seated_diorama defaults)

- Width: 110–125 mm
- Depth: 60–70 mm
- Height: under 70 mm
- Min feature width: 1.2 mm for 0.4 mm nozzle

## people.yaml

- Add one entry per recognizable subject (humans and prominent animals).
- Set `review.face_center` [x, y, z] for dynamic face closeup cameras.
- Add `face_closeup_<id>` to visual_acceptance.required_views.

## Contract

CAD is **hand-authored** against these specs (v4 pattern). Do not compile YAML directly into geometry on day one. Multifuse entire scene; assert `len(scene.solids()) == 1`.
