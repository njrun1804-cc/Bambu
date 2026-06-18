# Hybrid lane

Likeness gifts default to `lane: hybrid` in `project.yaml`: build123d structure, Meshy Pro heads, automated Bambu mesh fusion, existing Bambu mesh gates and Blender renders.

## Tool responsibilities

| Component | Tool | Role |
|-----------|------|------|
| Base, chair, torsos, nameplate | build123d → STEP | Parametric, FreeCAD-valid structure |
| Woman + dog heads | Meshy Pro → STL | Organic recognition at figurine scale |
| Boolean union, cleanup | `bambu fuse-mesh` (default) | Align Meshy heads to neck stubs and merge |
| Manual cleanup override | Shapr3D (optional) | Use only when automated merge fails a gate you care about |
| Ortho renders, thumbnail | Blender | Automated from `views.yaml` |
| Print contract | `bambu release-check --stl` | Watertight, overhang, island gates |

Pure CSG (`lane: build123d`) remains for functional parts without likeness requirements.

## Key files per revision

- `designs/v1/design.yaml` — must include `reference_inputs.concept_sheet` when `lane: hybrid`
- `designs/v1/fusion_manifest.yaml` — body/head/fused artifact paths, stub centers, rotations, sink depth
- `designs/v1/visual_acceptance.yaml` — concept sheet, human review questions
- `mesh/provenance.yaml` — Meshy task ids and credits (gitignored under `projects/*/mesh/`)
- `source/v1/model.py` — exports `model` (full CSG regression) and `body_model` (head stubs)

## CLI quick reference

```bash
# Concept sheet (Figure prototype, 6 credits)
uv run bambu meshy concept projects/<slug>

# Head meshes (image-to-3d on crops, ~20 credits each)
uv run bambu meshy head projects/<slug> --subject woman
uv run bambu meshy head projects/<slug> --subject dog

# Free printability pre-check
uv run bambu meshy analyze projects/<slug> --subject woman

# Body scaffold for fusion
uv run bambu export-body projects/<slug> --revision v1

# Automated head fusion (no Shapr3D required)
uv run bambu fuse-mesh projects/<slug> --revision v1

# Release gates + Blender renders on fused STL
uv run bambu release-check projects/<slug> --revision v1 \
  --stl outputs/<slug>-v1-fused.stl --skip-export --skip-freecad

# Preview renders only
uv run bambu review-mesh outputs/<slug>-v1-fused.stl \
  --project projects/<slug> --revision v1
```

Set `MESHY_API_KEY` in the environment (`export MESHY_API_KEY=msy_...`). Never commit keys. Test mode: `msy_dummy_api_key_for_test_mode_12345678`.

## Credit budget (first prototype)

| Step | Credits |
|------|---------|
| Figure prototype (concept) | 6 |
| Image-to-3d × 2 heads | 40 |
| Analyze × 2 | 0 |
| Remesh/repair (if needed) | 5–20 |

See [shapr3d-fusion-workflow.md](shapr3d-fusion-workflow.md) for the optional Shapr3D override runbook.
