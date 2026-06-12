# Print-path QC for the A1 mini: what actually fails and what doesn't

Lessons from taking World Cup neighbors v4.1 from CAD to a running print.
The implementing gates live in `bambu/mesh.py` + `bambu/printability.py`
and run via `bambu release-check` and `bambu qc`.

## Slope is not reachability

The 45-degree overhang rule and "can this region start printing at all"
are different questions:

- **Overhangs** (slope): large connected SLOPED downward patches droop.
  Total flagged area is the wrong metric — raised-letter undersides, brow
  ledges, and mitten bottoms are a few mm^2 each and print fine. Gate the
  largest connected steep patch (budget ~120 mm^2 for figurines).
- **Bridges** (flat-down, within ~10 degrees of straight down) spanning
  between supports — goal crossbars, net bars, letter undersides — are
  printed with bridging moves. Report them; don't gate them.
- **Floating islands** (reachability): a region whose first layer has
  nothing under it and nothing within nozzle-drag distance beside it
  prints as spaghetti. v4.1's outer mittens hung 2.4 mm above the base,
  passed every overhang number, and were caught only by Bambu Studio's
  "floating regions" warning. `analyze_islands` now reproduces that
  check: local-minimum clusters -> slab connectivity to standing material
  -> drag-distance rescue.

Tolerated island class: sub-1.5 mm convex nubs within ~1.2 mm of a wall
(glasses-ring bottoms, cheek-pad rims, nose tips). They print with a
micro-goober the next layers absorb. Design them out when cheap (flat-trim
the nose underside so its first layer reaches the face; ground hands into
the base; drop engraves on a ball's lower half whose slot roofs hover).

## Trust hierarchy for slicer outputs

- **Bambu Studio GUI slice is authoritative.** The CLI (`--slice 0
  --export-3mf`) produced a 7h05m time prediction for a print the GUI
  slices at 1h45m with identical profiles. Treat CLI `prediction` as
  order-of-magnitude only; read real time/cost from the GUI before
  promising anything.
- **CLI-exported `.gcode.3mf` does not open in the GUI** ("Loading of a
  model file failed" / "no geometry data") on Bambu Studio 02.07. To print,
  import the STL into the GUI, slice there, and use Send. The CLI export
  remains useful for `bambu qc` and `bambu handoff` marker checks.
- The GUI "floating regions" warning is worth a stop-and-diagnose every
  time, but it does not say where or how bad. `analyze_islands` gives the
  seed locations and a blocking verdict; the two together separated one
  real failure (floating mitten) from seven cosmetic nubs.

## Proven print setup (v001 + v4.1)

- Bambu Lab A1 mini, 0.4 nozzle, `0.20mm Standard @BBL A1M`, Textured PEI.
- Green Bambu PLA Basic in AMS slot A3; inventory and slicer profile names
  live in `profiles/bambu-a1-mini/context.yaml` (QC checks sliced filament
  types against owned spools).
- Auto bed leveling ON, flow dynamics calibration ON, timelapse off.
- Supportless is the design contract: `support_used == false` is a hard QC
  gate. v001's tree supports printed but scarred small face details, which
  is why v2+ design rules fuse everything.

## Review rendering for agent eyes

Blender Workbench with cavity + shadow shading
(`bambu/review3d.py::build_blender_preview_command`) makes engraved pupils,
smile lines, and hair grooves legible in renders; flat shading hides them.
Views are data (`designs/<rev>/views.yaml` -> `--views`), so face closeups
and deck shots are reproducible per revision. Blender remains the fast
inner loop (~8 s, deterministic cameras); Shapr3D import of the STEP is the
human spin-around check, not the iteration loop.
