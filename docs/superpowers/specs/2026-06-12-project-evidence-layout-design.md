# Project Evidence Layout Design

## Goal

Make each `projects/<slug>/` directory the source of truth for a print project's full lifecycle: design inputs, private reference evidence, generated artifact metadata, print-result evidence, review notes, and next-revision learnings.

The repo remains public-safe. Raw photos of people, home setup, printer labels, and physical prints stay local and git-ignored. The committed repo stores only metadata, hashes, notes, and manifests that let agents understand what evidence exists and how it was used.

## Current Problem

The first `world-cup-neighbors` print produced useful design and output evidence, but the files are split across old and new surfaces:

- `private/references/` has source-person and filament photos.
- `private/world-cup-neighbors-local-brief.md` has early project context.
- `private/world-cup-neighbors/v001-post-print/` has output photos.
- `projects/world-cup-neighbors/photos/v001-post-print/` has ignored duplicate output photos.
- `projects/world-cup-neighbors/measurements/` and `reviews/` have the first tracked feedback.
- `outputs/` has generated SCAD/STL/3MF files, indexed but intentionally not tracked.

This is workable for one rushed print, but future agents need one project-owned location to inspect before revising design.

## Design Principles

1. Project ownership: if evidence affects a project design or validates an output, it belongs under `projects/<slug>/`.
2. Public-safe commits: raw image pixels and generated print files remain ignored; tracked manifests describe them without exposing private data.
3. Evidence is typed: distinguish source references, material/printer references, generated artifacts, print photos, and human review notes.
4. Iterations are explicit: v001, v002, and later revisions each get their own notes and result files.
5. Top-level docs stay repo-wide: `docs/` explains how Bambu works; project folders explain what happened for one print.

## Target Structure

```text
projects/<slug>/
  project.yaml
  source/
    README.md
  references/
    manifest.yaml
    originals/
    filament/
    printer/
  iterations/
    v001/
      brief.md
      print-result.yaml
      review.md
      photos/
    v002/
      brief.md
      design-notes.md
      photos/
  reviews/
  measurements/
  artifacts.json
```

### Tracked Files

- `project.yaml`: lifecycle state, current revision, printer/material/plate constraints, and next safe action.
- `source/README.md`: public-safe summary of the source references and design intent, without embedding raw photos or sensitive local notes.
- `references/manifest.yaml`: public-safe index of private photos and their design role.
- `iterations/vNNN/brief.md`: human-readable revision intent and constraints.
- `iterations/vNNN/print-result.yaml`: physical print telemetry and outcome.
- `iterations/vNNN/review.md`: qualitative review and next-revision learnings.
- `artifacts.json`: generated output hashes and classifications.

### Ignored Files

- `references/originals/*`: people/source likeness photos.
- `references/filament/*`: spool and label photos.
- `references/printer/*`: printer screen/device photos.
- `iterations/*/photos/*`: physical print photos.
- `outputs/*`: generated SCAD/STL/3MF/G-code/PNG artifacts.

Each ignored directory keeps a tracked `.gitkeep` so agents can discover the intended layout.

## Reference Manifest Schema

`references/manifest.yaml` should be small and readable:

```yaml
schema_version: 1
project_slug: world-cup-neighbors
references:
  - id: ref-dan-carrie-clear
    type: source_people
    privacy: private_local
    local_path: references/originals/clear-right-pair.jpg
    purpose: silhouette, hair, eyewear, body-shape cues
    public_summary: Two adult neighbors used only for stylized, non-photoreal caricature cues.
  - id: ref-green-pla-a3
    type: material
    privacy: private_local
    local_path: references/filament/green-pla-basic-label.jpg
    purpose: confirms green Bambu PLA Basic material and AMS slot mapping
    public_summary: Green Bambu PLA Basic used for v001.
```

Agents may reference `id` values in briefs, reviews, and print-result notes. They must not commit the underlying image files.

## Iteration Files

Each revision should be understandable without scanning old chat:

- `brief.md`: what we are trying to make, for whom, and what constraints matter.
- `print-result.yaml`: objective telemetry such as slicer time, material grams, layer count, plate, calibration settings, and outcome.
- `review.md`: human judgement, photo-observed issues, and next-revision instructions.
- `photos/`: ignored evidence photos named by stable purpose, such as `01-front-supports.jpg` or `02-supports-removed.jpg`.

For `world-cup-neighbors`, v001 should migrate existing feedback from `measurements/v001.yaml` and `reviews/004-print-feedback.md` into `iterations/v001/` while retaining backwards-compatible copies or links until code/docs are updated.

## Migration Strategy

1. Create the target directories under `projects/world-cup-neighbors/` with `.gitkeep` in ignored photo folders.
2. Move or copy private reference photos from `private/references/` into project-owned ignored folders.
3. Split the early private brief into a public-safe `iterations/v001/brief.md` plus an ignored local note only if sensitive detail is still needed.
4. Move print feedback into `iterations/v001/print-result.yaml` and `iterations/v001/review.md`.
5. Create `references/manifest.yaml` describing people, filament, printer, and output-photo evidence.
6. Update `.gitignore` so new project-owned raw-photo directories are ignored.
7. Update README/agent docs to teach future agents to inspect project-local `references/` and `iterations/`.
8. Add tests for project creation to ensure new projects get the target evidence directories and manifest placeholders.

## Open Compatibility Decision

Existing `measurements/` and `reviews/` directories are already used by current code. The first implementation should not remove them immediately. Instead:

- keep writing current files for compatibility;
- add the new `iterations/` structure;
- teach project views to surface both until the old paths are no longer needed.

## Success Criteria

- A new agent can inspect `projects/world-cup-neighbors/` and understand the design inputs, v001 output evidence, and v002 direction without opening top-level `private/`.
- No raw private photos become tracked by git.
- Public metadata explains why each private photo exists.
- Generated output files remain reproducible and indexed by hash, not committed.
- Tests cover project scaffold creation and artifact/photo privacy rules.

## Non-Goals

- Do not build a cloud media store.
- Do not commit photos of real people or private printer/home context.
- Do not rewrite the CAD generator as part of this migration.
- Do not remove existing compatibility paths until callers have moved to the iteration model.
