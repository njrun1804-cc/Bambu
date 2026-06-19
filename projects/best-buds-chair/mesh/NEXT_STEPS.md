# Best Buds — one-command print-ready handoff

When Meshy heads and fused STL already exist:

```bash
uv run bambu pipeline run projects/best-buds-chair --skip-meshy --no-render
```

First run (generates Meshy concept + heads when `MESHY_API_KEY` is set):

```bash
uv run bambu pipeline run projects/best-buds-chair --no-render
```

Output: `outputs/best-buds-chair-v1-fused.gcode.3mf`

Still manual: open in Bambu Studio for plate/support review and physical print start.
