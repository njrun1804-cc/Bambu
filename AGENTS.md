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
- `bambu/cad.py`: build123d export gate (STEP/STL + bounding box).
- `bambu/mesh.py`: STL analysis core - watertight, overhang patches, floating islands.
- `bambu/printability.py`: sliced-3mf QC against printer + owned filament inventory.
- `bambu/review3d.py`: FreeCAD STEP review + Blender render harness.
- `bambu/design_pipeline.py`: structured design-spec gates (designs/<rev>/*.yaml).
- `bambu/slicer.py`: builds Bambu Studio or OrcaSlicer command plans.
- `bambu/cli.py`: command-line workflow (doctor, design-check, release-check, qc, handoff, ...).
- `bambu/mcp_server.py`: local stdio MCP server; safe workflow tools only.
- `agents/`: public MCP/agent configuration, prompts, and workflows.
- `.agents/skills/`: shared skill entrypoints for runtimes that support skills.
- `docs/learning/`: paid-for lessons (OCCT/STEP geometry rules, print-path QC).
- `examples/`: public-safe briefs and workflows.
- `profiles/`: printer profile + owned filament inventory (QC reads this).
- `projects/<slug>/`: manifests, designs/<rev> specs, source, reviews, artifacts.
- `private/`: ignored local-only work area.
- `outputs/`: ignored generated output area.

## Verification

Run:

```bash
python3 -m unittest discover -s tests -v
```

When chaining the suite into a pipeline, do not let a filter mask the exit
code (`unittest ... | rg OK` exits 0 even on failures); gate on the
unfiltered run or check the FAILED line explicitly.

Run `uv run ruff check bambu tools tests` after Python changes.

For manual smoke testing:

```bash
uv run bambu doctor
uv run bambu release-check projects/world-cup-neighbors --revision v4 \
  --source-file projects/world-cup-neighbors/source/v4/model.py \
  --output-slug world-cup-neighbors-v4 --no-render
uv run bambu qc outputs/world-cup-neighbors-v4.gcode.3mf --stl outputs/world-cup-neighbors-v4.stl
uv run bambu-mcp
```

The operating contract is the learning feedback loop in `docs/learning/README.md`:
specs gate, gates verify, humans print, results get recorded, lessons become
gates or defaults. Before writing build123d geometry, read
`docs/learning/occt-step-geometry-rules.md`; before slicing or printing, read
`docs/learning/print-path-qc.md`. The project manifest's `next_safe_action`
names the loop's current position - keep it current.
