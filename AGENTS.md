# AGENTS.md - Bambu

Bambu is a public, safety-conscious 3D-print workbench for a Bambu Lab A1 mini.

## Working Rules

- Keep private reference photos and personal notes in `private/`; never commit them.
- Keep generated STL, 3MF, G-code, and PNG outputs out of git unless the user explicitly asks for a release artifact.
- Do not add automatic printer-start behavior without an explicit confirmation gate and documentation.
- Prefer OpenSCAD for first-pass functional and stylized models because agents can inspect and revise it as text.
- Treat slicer output as a plan, not proof. Always remind the user to inspect supports, scale, filament, bed type, and first layer before printing.

## Repo Shape

- `bambu/preflight.py`: detects optional external tools.
- `bambu/figurine.py`: generates OpenSCAD for stylized figurines.
- `bambu/slicer.py`: builds Bambu Studio or OrcaSlicer command plans.
- `bambu/cli.py`: beginner-facing command-line workflow.
- `bambu/mcp_server.py`: local stdio MCP server; safe workflow tools only.
- `agents/`: public MCP/agent configuration, prompts, and workflows.
- `.agents/skills/`: shared skill entrypoints for runtimes that support skills.
- `examples/`: public-safe briefs and workflows.
- `profiles/`: printer/profile notes.
- `private/`: ignored local-only work area.
- `outputs/`: ignored generated output area.

## Verification

Run:

```bash
python3 -m unittest discover -s tests -v
```

For manual smoke testing:

```bash
python3 -m bambu.cli doctor
python3 -m bambu.cli make-figurines --output outputs/world-cup-neighbors.scad
python3 -m bambu.cli slice-plan outputs/world-cup-neighbors.stl --output outputs/world-cup-neighbors.gcode.3mf
uv run bambu-mcp
```
