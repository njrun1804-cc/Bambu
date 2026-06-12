# Neighbor Figurine Quality Pass

## Goal

Improve the World Cup neighbor figurine from a blocky proof of concept into a display-safe, A1-mini-targeted printable prototype.

The model should read as two stylized adults inspired by the private reference photos without attempting photorealistic face reconstruction. The public repo remains safe: private photos stay under `private/`, and generated STL/3MF/G-code files stay out of git.

## Design

- One shared rounded base, 118 x 62 mm, to improve adhesion on the Textured PEI Plate and keep the scene well inside the A1 mini 180 x 180 x 180 mm build volume.
- Two stylized figures with distinct silhouette cues:
  - taller slim figure with short salt-and-pepper hair, glasses, jersey number `10`, and a watch cue
  - shorter curvier figure with swept light hair, sunglasses, hair-clip cue, jersey number `9`, and a crossbody bag cue
- Brazil-watch-party treatment through raised paint guides: jersey panels, collar/side trims, numbers, and base title.
- Single-material PLA Basic remains the default because the printer/AMS-lite connection is not verified. The raised guides are suitable for post-print painting and can later become color regions if AMS lite is available.

## A1 Mini Constraints

- Target profile: Bambu Lab A1 mini 0.4 nozzle, `0.20mm Standard @BBL A1M`, Bambu PLA Basic, Textured PEI Plate.
- Minimum raised detail target: 0.8 mm.
- Arms stay close to the torso to reduce support risk.
- The shared base is centered and low to help first-layer adhesion.
- Manual review remains required before any physical print. Use auto bed leveling and flow calibration before the first real print of this model.

## Verification

- Generate source: `uv run bambu make-figurines --output outputs/world-cup-neighbors.scad`
- Full local build: `uv run bambu prototype-world-cup --output-dir outputs --slicer bambu-studio`
- Handoff check: `uv run bambu handoff`
- Preview render: `openscad -o outputs/world-cup-neighbors-preview.png --imgsize=1600,1200 --viewall --autocenter --camera=0,-90,60,65,0,0,220 outputs/world-cup-neighbors.scad`

