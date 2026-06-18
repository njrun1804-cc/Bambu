# v4 / v4.1 build notes

Date: 2026-06-12

## Outcome

v4.1 was sliced in the Bambu Studio GUI (1h45m, 52.6 g green PLA Basic,
283 layers, supportless) and sent to the A1 mini at 18:29 with Mike
supervising. Result to be recorded via `bambu record-print-result`.

## Lineage

- v3b (codex branch): spec-compiled compound of overlapping solids; failed
  FreeCAD validity; never sliced.
- v4: hand-authored single fused solid against `designs/v4/*.yaml` spec
  gates. Sunglass-pad faces, raised cheer arms, ball front-center.
- v4.1 (shipped): retargeted to the colored ChatGPT sheet after review —
  ~49% chibi heads with engraved pupils behind open glasses, arms-down
  couple pose with joined hands grounded in the base, Dan's hair low in
  back, Carrie's cone-tapered bob with shoulder lobes, 19 mm ball fused at
  Dan's foot, WORLD CUP 2026 deck banner, Carrie jersey number 9.

## What the gates caught (in order)

1. FreeCAD BOP: scaled-sphere pcurves, unorientable oblate revolves,
   graze tangencies (shoulder/fillet, jaw/neck near-coaxial, smile-lune
   tips), crossing torus engraves, exact-fit lens walls, converging hair
   grooves. All encoded in `docs/learning/occt-step-geometry-rules.md`.
2. OCCT fuse hang: near-tangent cheek spheres pegged a core for 20+
   minutes; prism cheek pads fixed it.
3. Bambu Studio "floating regions": outer mittens started mid-air — the
   one class the overhang QC could not see. Fixed by grounding all four
   hands; nose tips flat-trimmed; lower ball seams dropped. The island
   gate (`bambu/mesh.py::analyze_islands`) now reproduces this finding:
   pre-fix geometry fails on Carrie's floating mitten, shipped geometry
   passes with two tolerated cheek nubs.
4. CLI vs GUI slicer: CLI predicted 7h05m; GUI sliced the same model at
   1h45m. GUI numbers are authoritative
   (`docs/learning/print-path-qc.md`).

## Reproduce the shipped artifacts

```bash
uv run bambu release-check projects/world-cup-neighbors --revision v4 \
  --source-file projects/world-cup-neighbors/source/v4/model.py \
  --output-slug world-cup-neighbors-v4 \
  --views projects/world-cup-neighbors/designs/v4/views.yaml
# slice in Bambu Studio GUI (CLI .gcode.3mf does not reopen in the GUI),
# or for the repo artifact + QC:
uv run bambu qc outputs/world-cup-neighbors-v4.gcode.3mf \
  --stl outputs/world-cup-neighbors-v4.stl
uv run bambu handoff --file outputs/world-cup-neighbors-v4.gcode.3mf
```

## Post-print follow-ups

- Record the physical result (`bambu record-print-result`) with photos
  under `projects/world-cup-neighbors/photos/`.
- Inspect the known tolerated nubs after support-free printing: cheek-pad
  rims, glasses-ring bottoms, bridged crossbar underside.
- Paint guides are in place if Mike wants the yellow/blue accents:
  jersey panels, numbers, base lettering.
