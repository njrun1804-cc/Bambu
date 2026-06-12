# Bambu Design

## Goal

Build a public-ready repository named `Bambu` that helps a non-expert use an agent such as Codex or Claude to turn a plain-English idea into printable artifacts for a Bambu Lab A1 mini.

## Product Shape

The repo is a guided workbench, not a blind print bot. It keeps the hot-printer step behind a human approval boundary and focuses on reproducible intermediate files: briefs, generated CAD, previews, STL/3MF exports, slicer command plans, and print checklists.

Two creation lanes share one command-line surface:

- `figurine`: stylized, privacy-safe miniatures and party objects from written descriptions or private reference photos that stay out of git.
- `functional`: parametric OpenSCAD/CadQuery-style parts such as brackets, hooks, holders, spacers, organizers, and adapters.

## Initial Use Case

The first concrete example is a pair of stylized Brazil-watch-party neighbor figurines. The public repo should not contain the private photos. Instead it stores a generic example brief and generator. The local `private/` folder can hold personal reference notes or images.

## Architecture

The core package exposes small modules:

- `bambu.preflight`: detects optional external tools such as OpenSCAD, Bambu Studio, OrcaSlicer, and Blender.
- `bambu.figurine`: turns a structured figurine brief into OpenSCAD source.
- `bambu.slicer`: builds dry-run-safe slicer command plans for Bambu Studio or OrcaSlicer.
- `bambu.cli`: provides hand-holding commands: `doctor`, `make-figurines`, `slice-plan`, and `next`.

External CAD and slicer tools are optional. If they are missing, the CLI still creates source files and exact next-step commands.

## Safety And Privacy

The repo ignores `private/`, generated mesh outputs, local environment files, and printer credentials. It does not automate print starts in v1. Any future printer-send integration must be opt-in, documented, and require explicit confirmation.

## Verification

The project uses Python standard-library tests so it works before installing third-party packages. Tests cover preflight detection, OpenSCAD generation, slicer command planning, and CLI hand-holding.

