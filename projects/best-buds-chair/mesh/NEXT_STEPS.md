# Best Buds — pivot away from head-on-CSG fusion

**Do not tune `mesh_fusion.py` alignment.** The hybrid lane (build123d body + Meshy head crops) cannot reach concept-sheet fidelity.

## Gap (honest)

| Target | Current fused output |
|--------|----------------------|
| Seated woman + tri-color dog on patio chair | Primitive blocks/spheres with tiny heads glued on |
| Glasses, hair, dog ears readable at thumbnail | Geometric abominations; legs/feet sticking from blocks |
| Concept sheet chibi diorama | CSG scaffold dominates; Meshy heads are ~5% of visual mass |

Also: `patio-reference.jpg` and `concept-meshy.png` currently depict a **marina couple** (standing man + woman), not the seated patio-chair + dog scene in `project.yaml`. Regenerate concept from the correct photo first.

## Recommended path: full-scene Meshy (no manual CAD)

```bash
export MESHY_API_KEY=msy_...   # never commit

# 1. Put the real patio+dog+chair photo at photos/reference/patio-reference.jpg
# 2. Regenerate concept from that photo (6 credits)
uv run bambu meshy concept projects/best-buds-chair

# 3. Image-to-3d on the concept sheet → unified scene STL (~20 credits)
uv run bambu meshy scene projects/best-buds-chair

# 4. Release-check + slice the scene mesh (not fuse-mesh)
uv run bambu release-check projects/best-buds-chair --revision v1 \
  --stl mesh/scene-full.stl --skip-export --skip-freecad --no-render
uv run bambu slice mesh/scene-full.stl
uv run bambu qc outputs/scene-full.gcode.3mf
```

Alternative: full single-subject figure from Creative Lab build (30 credits, one character only):

```bash
uv run bambu meshy figure-build projects/best-buds-chair
```

## Legacy hybrid lane (deprecated for likeness gifts)

```bash
uv run bambu pipeline run projects/best-buds-chair --skip-meshy --no-render
```

Produces `outputs/best-buds-chair-v1-fused.gcode.3mf` — structurally printable but not likeness-acceptable.
