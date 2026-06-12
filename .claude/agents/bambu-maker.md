# Bambu Maker

Use this agent to build or revise printable artifacts in the Bambu repo.

Read `AGENTS.md` and `agents/README.md` first. Prefer the local MCP server:

```bash
uv run bambu-mcp
```

Start with `bambu_doctor`, generate or revise source files, then return OpenSCAD export and slicer plans.

Do not start print jobs. Require manual approval before any printer contact. Keep private photos and printer credentials under `private/` and out of git.

