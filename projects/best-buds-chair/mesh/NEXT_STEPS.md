# Meshy head meshes — next steps

## Automated fusion (heads complete)

Head STLs and body scaffold are ready. Run:

```bash
uv run bambu fuse-mesh projects/best-buds-chair --revision v1
uv run bambu release-check projects/best-buds-chair --revision v1 \
  --stl outputs/best-buds-chair-v1-fused.stl --skip-export --skip-freecad
```

Fusion manifest stub alignment:

- `mesh/woman-head.stl` → stub `[20, 2, 50.5]`, scale=1.0, sink=5mm
- `mesh/dog-head.stl` → stub `[0, -4, 26]`, scale=1.05, sink=10mm
- Output: `outputs/best-buds-chair-v1-fused.stl`

See `docs/learning/hybrid-lane.md` and `designs/v1/fusion_manifest.yaml`.

Optional Shapr3D override: `docs/learning/shapr3d-fusion-workflow.md`.

## Meshy pipeline reference

```bash
uv run bambu meshy concept projects/best-buds-chair
uv run bambu meshy head projects/best-buds-chair --subject woman
uv run bambu meshy head projects/best-buds-chair --subject dog
uv run bambu meshy analyze projects/best-buds-chair --subject woman
uv run bambu meshy analyze projects/best-buds-chair --subject dog
```

Expected credits (from plan): concept ~6, each head ~20, analyze free.
