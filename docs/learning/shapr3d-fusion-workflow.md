# Shapr3D fusion workflow (optional override)

**Default path:** `bambu fuse-mesh` aligns Meshy head STLs onto the build123d body scaffold and writes `outputs/<slug>-v1-fused.stl`. No Shapr3D required.

Use Shapr3D only when automated fusion fails a gate you cannot accept (watertight topology, island starts, or aesthetic lap contact).

## Automated inputs

| Artifact | Path (best-buds-chair v1) |
|----------|---------------------------|
| Body STEP (neck stubs) | `outputs/best-buds-chair-v1-body.step` |
| Body STL (fusion input) | `outputs/best-buds-chair-v1-body.stl` |
| Woman head STL | `mesh/woman-head.stl` |
| Dog head STL | `mesh/dog-head.stl` |
| Alignment hints | `designs/v1/fusion_manifest.yaml` |
| Face centers (review) | `designs/v1/people.yaml` → `review.face_center` |

Generate body STEP/STL:

```bash
uv run bambu export-body projects/best-buds-chair --revision v1
```

Automated fusion:

```bash
uv run bambu fuse-mesh projects/best-buds-chair --revision v1
```

## Shapr3D override (manual)

1. Open `outputs/best-buds-chair-v1-body.step` in Shapr3D.
2. Import `mesh/woman-head.stl` and `mesh/dog-head.stl`.
3. Scale and position using `fusion_manifest.yaml` stub/align hints and `people.yaml` `head_mm` / `face_center`.
4. Boolean **Union** each head to its neck stub; verify lap contact between arm and dog.
5. Fillet lap contacts ≥ 1 mm where heads meet body stubs.
6. Check wall thickness ≥ 1.2 mm on thin AI mesh spots (Replace Face / offset if needed).
7. Export over `outputs/best-buds-chair-v1-fused.stl`.
8. Run release gates on the fused mesh:

```bash
uv run bambu release-check projects/best-buds-chair --revision v1 \
  --stl outputs/best-buds-chair-v1-fused.stl \
  --skip-export --skip-freecad
```

Optional body STEP validation after fusion:

```bash
uv run bambu release-check projects/best-buds-chair --revision v1 \
  --stl outputs/best-buds-chair-v1-fused.stl \
  --skip-export --body-step outputs/best-buds-chair-v1-body.step
```

9. Compare Blender face closeups to `photos/reference/concept-meshy.png` before slice.

## Success criteria

- Fused STL passes watertight, overhang, and island gates (or documented override).
- Woman: glasses + hair readable at 150px thumbnail vs concept PNG.
- Dog: ears + muzzle visible in face closeup — reads as dog, not cushion.
- Single green PLA legibility without paint.

## Automated fusion tradeoffs

Meshy heads are often non-manifold; `fuse-mesh` uses pragmatic merge (align + concatenate + optional pymeshlab repair). Watertight and island gates may warn even when likeness looks good in Blender. Shapr3D boolean union remains the manual escape hatch.
