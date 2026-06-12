# Bambu Agent Layer

This directory is the public agent-facing control surface for Bambu.

The local MCP server command is:

```bash
uv run bambu-mcp
```

The server exposes safe workflow tools:

- `bambu_doctor`: inspect local CAD/slicer setup and next steps.
- `bambu_generate_world_cup_figurines`: generate the default figurine OpenSCAD source.
- `bambu_openscad_export_plan`: return the OpenSCAD export command for `.scad -> .stl`.
- `bambu_slice_plan`: return a Bambu Studio or OrcaSlicer command and review checklist.
- `bambu_build_world_cup_prototype`: generate SCAD, export STL, and slice 3MF without printer contact.
- `bambu_print_handoff`: inspect a generated `.gcode.3mf`, verify A1 mini markers, and return the Bambu Studio handoff.

The MCP server **does not start print jobs**. Agents must stop at source/export/slice plans and require manual approval before anything reaches the printer.

Keep private reference photos, printer credentials, and local slicer profiles under `private/`. Do not commit them.

## Suggested MCP Client Config

For clients that accept JSON MCP config, adapt this template:

```json
{
  "mcpServers": {
    "bambu": {
      "command": "uv",
      "args": ["--directory", "/Users/mikeedwards/CC/Bambu", "run", "bambu-mcp"]
    }
  }
}
```

For a portable public checkout, replace `/Users/mikeedwards/CC/Bambu` with the repo path.

## Agent Roles

- `agents/prompts/maker.md`: build or revise printable artifacts.
- `agents/prompts/reviewer.md`: inspect generated geometry plans before printing.
- `.agents/skills/bambu-operate/SKILL.md`: shared skill entrypoint for agent runtimes that support skills.
- `.codex/agents/bambu-maker.toml`: Codex custom agent sketch using `bambu-mcp`.
- `.claude/agents/bambu-maker.md`: Claude Code custom agent sketch with the same safety boundary.
