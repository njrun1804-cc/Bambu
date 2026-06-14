# Bambu

Agent-assisted 3D-print preparation for a Bambu Lab A1 mini: plain-English intent → reviewable printable source (build123d / OpenSCAD), with the print step gated behind manual human review.

## Stack

- Python 3.11–3.12 (pinned 3.12 via `.python-version`), `uv`-managed
- Deps: build123d (CAD), PyYAML, mcp (local agent tool server)
- Optional external tools: OpenSCAD, FreeCAD, Bambu Studio, OrcaSlicer, Blender
- CLI entry points: `bambu` (`uv run bambu ...`), `bambu-mcp`

## Test

```bash
uv run python -m unittest discover -s tests -v
uv run ruff check bambu tools tests
```

No `scripts/check.sh` in this repo.

## Knowledge Surfaces

Cross-repo conventions, rules of engagement, and the sibling-repo map live in **Zion** (`~/CC/Zion/CLAUDE.md`) — the canonical workspace index. This repo is a leaf; consult Zion first for workspace-wide protocol.
