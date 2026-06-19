# World Cup Neighbors V4 Source

V4 resets the character generator around Blender Python instead of build123d primitives.

The purpose of this lane is visual fidelity first:

1. Generate a smooth single-material chibi scene in Blender.
2. Render fixed review views.
3. Compare those views against cropped ChatGPT visual targets.
4. Iterate until the candidate is recognizably in the same visual family.
5. Only then move toward mesh repair, CAD validation, slicer checks, and printer handoff.

Run:

```bash
uv run python tools/render_v4_blender.py projects/world-cup-neighbors \
  --json outputs/review/world-cup-neighbors-v4/review-report.json
```
