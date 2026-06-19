# Best Buds — pivot off head-on-CSG-body (2026-06-19)

## Honest gap: reference vs concept vs fused output

| Target | What it shows | Match to intent? |
|--------|---------------|------------------|
| **intake.yaml intent** | Seated woman + glasses + tri-color dog on patio chair, "Best Buds" | ✅ canonical goal |
| **patio-reference.jpg** | Standing marina couple (man + woman), no dog, no chair | ❌ wrong photo |
| **concept-meshy.png** | Standing chibi couple on dock diorama (from marina photo via Figure prototype) | ❌ wrong scene grammar |
| **crop-dog.jpg** | Man's torso from marina photo | ❌ not a dog |
| **fused STL renders** | Green CSG blocks + tiny detached Meshy busts; legs/feet as random cylinders | ❌ ~1% of concept fidelity |

**Bottom line:** We are not failing alignment tuning — we are failing **scene selection**. The hybrid lane used 1% of Meshy (detached head crops) and 99% build123d CSG primitives, while the acceptance target is an integrated chibi diorama like `concept-meshy.png`.

## Why head-on-CSG-body failed

1. **Wrong inputs** — reference photo and crops do not depict woman+dog+chair; Figure prototype faithfully reproduced the marina couple instead.
2. **Wrong Meshy stage** — repo only ran `figure/v1/prototype` (2D PNG) and `image-to-3d` on face crops. It never ran `figure/v1/build` (full chibi figure) or `image-to-3d` on the concept sheet.
3. **Wrong likeness split** — CSG torsos/chair cannot carry glasses, hair, dog ears, or seated pose; only ~5 engraved cues. Meshy heads are 3D portraits in wrong scale/orientation, not diorama figures.
4. **Codex/history lesson** — v3b YAML→geometry and v4 hand-authored CSG both pass print gates but fail human recognition. Hybrid lane was supposed to fix likeness via Meshy, but implemented the narrowest possible Meshy slice (heads only).
5. **Gates ≠ fidelity** — watertight/overhang/island checks pass on geometric abominations.

## Meshy APIs that can produce FULL figures/scenes

| API | Output | Cost | Fit for Best Buds |
|-----|--------|------|-------------------|
| **Creative Lab Figure `prototype` → `build`** | Full chibi figure (body+clothes+head) from photo | 6 + 30 credits | Per-subject likeness; needs correct photo per subject |
| **`v1/image-to-3d`** on concept sheet | Unified scene mesh (woman+dog+chair together) | ~20 credits | Best match to concept-sheet acceptance workflow |
| **`v1/text-to-image`** from intake intent | Correct concept before 3D | ~6 credits | Fixes wrong-photo problem without manual ChatGPT |
| **`v1/text-to-3d`** (preview→refine) | Full mesh from text only | 5+10 credits | Fallback if concept PNG is weak |
| **`v1/multi-image-to-3d`** | Mesh from multiple views | ~20 credits | Needs consistent ortho crops, not implemented yet |
| **`v1/print/repair` + `remesh`** | Print-safe cleanup | 5–10 credits | Post-process for any AI mesh |

**Deprecated for this project:** `fuse-mesh` head alignment on CSG neck stubs.

## Three alternative architectures

### A. Concept-first scene mesh (recommended)

```
intake.yaml intent → text-to-image concept → image-to-3d → remesh/repair → release-check → slice
```

- **Pros:** Single integrated diorama; matches visual acceptance against concept PNG; no CSG likeness ceiling.
- **Cons:** Entire scene must fit A1 mini envelope; may need repair pass; chair geometry less parametric.

### B. Figure-build per subject + CSG chair/base assembly

```
crop-woman → figure prototype→build; crop-dog → figure prototype→build; build123d chair+base → scene merge
```

- **Pros:** Best per-subject likeness; chair stays parametric/print-safe.
- **Cons:** Two 36-credit figure builds; manual/auto placement; needs real dog photo.

### C. Text-to-3d from intake prompt (no photo dependency)

```
intake.yaml → text-to-3d preview → refine → scale/repair → release-check
```

- **Pros:** No photo/crop quality issues.
- **Cons:** Weakest likeness to specific people; harder to hit exact chair+dog composition.

## Recommended path: **A — concept-first scene mesh**

Regenerate the concept from **intent** (not the marina photo), then run image-to-3d on that PNG.

### One command for Mike

```bash
export MESHY_API_KEY=msy_... && \
uv run bambu meshy concept projects/best-buds-chair --mode prompt && \
uv run bambu meshy scene projects/best-buds-chair && \
uv run bambu release-check projects/best-buds-chair --revision v1 \
  --stl projects/best-buds-chair/mesh/scene-full.stl --skip-export --skip-freecad
```

Then compare `outputs/review/.../three-quarter.png` to `photos/reference/concept-meshy.png`.

### Before spending credits (manual)

1. Replace `photos/reference/patio-reference.jpg` with the actual woman+dog+chair photo.
2. Replace `photos/reference/crop-dog.jpg` with a real dog face crop (only needed for architecture B).
3. Approve the new `concept-meshy.png` before running `meshy scene`.

### Credit budget (architecture A)

| Step | Credits |
|------|---------|
| text-to-image concept (`--mode prompt`) | ~6 |
| image-to-3d scene | ~20 |
| analyze + optional repair | 0–10 |

**Do not run** `fuse-mesh` or head-crop `meshy head` on this project until architecture A/B is evaluated.
