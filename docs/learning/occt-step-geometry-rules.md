# OCCT/STEP geometry rules for build123d figurine work

Field manual from the v4 World Cup neighbors build. Every rule below was
paid for with a concrete failure: the symptom is what the gates showed, the
fix is what shipped. The release gate is FreeCAD STEP round-trip validity
(`valid`, `closed`, one solid, zero blocking BOP errors) plus a watertight
STL; see `bambu release-check`.

## Export one fused solid

**Symptom:** `Part(children=solids)` compounds of overlapping primitives
report "valid" locally but fail FreeCAD review outright (the v3b attempt).

**Rule:** boolean-union the whole scene. Multifuse a list in one call
(`base + [goal, ball, dan, carrie]`), subtract engraves afterwards, and
assert `len(scene.solids()) == 1` in the model source so a broken fuse
fails at build time, not review time.

## Ellipsoids: revolve an arc profile, prolate only

**Symptom 1:** non-uniform `scale(Sphere(...))` produces BSpline surfaces
whose pcurves fail FreeCAD's BOP check after a STEP round trip
(`BOPAlgo_InvalidCurveOnSurface`, ~100+ per figure).

**Symptom 2:** trimming a full `Ellipse` sketch with a boolean
(`Ellipse & Rectangle`) yields a profile that revolves into an
unorientable STEP body — reimported volume off by 1.5x.

**Symptom 3:** even with a clean arc profile, an OBLATE revolve
(`r_z < r_xy`) exports unorientable STEP: reimported volume 0, FreeCAD
"Unorientable shape". Prolate revolves are fine.

**Rule:** build the half profile from `EllipticalCenterArc` closed by an
axis `Line`, `make_face`, `revolve` 360 about Z — and only when
`r_z >= r_xy`. Need a squashed mass (jaw, chubby lower face)? Use a
`Sphere` and bury it.

## Graze-depth contacts are the enemy

Every overlap must be >= 0.3 mm penetration or clearly separated; anything
in between produces zero-volume slivers, orphaned solids, or
self-intersecting faces.

- **Exact pole-on-plane tangency:** head ellipsoid bottom exactly at
  `torso_top` → 2 SelfIntersect faces. Seat heads >= 1.5 mm into the torso.
- **Shoulder cap on the fillet-start plane:** a sphere centered exactly
  where the torso top fillet begins leaves a zero-volume tangency sliver
  (reported as a second "solid" with volume ~0). Keep joint lines off
  fillet-start planes.
- **Near-coaxial sphere/cylinder:** a jaw sphere 0.3 mm off the neck
  cylinder axis crosses it where their radii match → degenerate
  intersection, SelfIntersect. Exactly coaxial is a clean circle; 0.3 mm
  off is sliver hell.
- **Near-tangent spheres on curved hosts:** a cheek sphere whose center
  sits ~96-100% of the way to the host ellipsoid surface either stalls the
  OCCT fuse for minutes (CPU pegged in `_bool_op`) or orphans the
  protruding cap as a separate solid in the STEP. Use prism extrusions
  (`_front`) for face pads, or bury spheres deeply (ears at
  `head_r - 1.2`, not `head_r - 0.4`).
- **Conformal tube-on-fillet:** a 2.8 mm arm capsule running along a
  2.5 mm torso top fillet (the wrap-arm experiment) produces near-parallel
  surface contact and invalid geometry. Route limbs to cross surfaces
  transversally or weld them solidly.

## Engraves are real booleans with real failure modes

- **Crossing engraves self-intersect:** three torus rings cutting a ball
  intersect each other inside the cut → SelfIntersect. Design engraves
  that never cross (front pentagon + non-crossing radial seams).
- **Cut depth vs bulges:** an engrave that reaches past a bulge's foremost
  point slices a free-floating wafer off it; an engrave that stops short of
  the local surface leaves grazes at the cut's taper tips. Put the smile
  lune ON the jaw sphere's equator and compute depth from the jaw front
  (`(jaw_front + 1.7) - cut_plane`), not from the head.
- **Converging groove cuts pinch islands:** fanned hair grooves that
  converge isolate sliver solids between them. Keep parallel grooves with
  >= 2 mm ribs.
- **Exact-fit inserts:** a lens pad that exactly fills a frame's hole
  shares coincident walls with it → SelfIntersect. Overlap inserts by
  >= 0.2 mm per side.

## Text, fonts, and lettering

`Text` + extrude is the right way to letter (the pixel-grid LETTER_PATTERNS
hack reads worse and buys nothing). Glyph outlines do carry
`InvalidCurveOnSurface` notes through STEP — that class is informational
(see `tools/freecad_review.py`): BRepCheck stays valid and the STL path is
unaffected. 7 mm Arial Bold is the floor for raised strokes >= 1.2 mm.

## Tessellation-level truths

- The print path is the STL tessellated from the in-memory shape, not the
  STEP. Gate the STL separately: watertight/manifold, overhang patches,
  floating islands (`bambu/mesh.py`).
- A valid, closed, single-solid STEP can still describe an unprintable
  object. CAD validity and printability are different gates; run both.
