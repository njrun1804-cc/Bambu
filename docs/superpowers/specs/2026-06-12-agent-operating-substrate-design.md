# Bambu Agent Operating Substrate Design

## Goal

Build a small, deterministic operating substrate that lets agents turn a plain-English 3D-print request into source files, export plans, slicer handoff, and revision feedback for Mike's Bambu Lab A1 mini without improvising around CAD or slicer state.

The substrate is not a full workflow engine yet. It provides manifests, rules, views, validation gates, and revision capture so agents know what is true, what is generated, what has been checked, and what must remain manual.

## Durable Machine Context

The repo targets Mike's Bambu Lab A1 mini. The durable public constraints are:

- printer model: Bambu Lab A1 mini
- build volume: 180 x 180 x 180 mm
- included nozzle: 0.4 mm stainless steel
- max hotend temperature: 300 C
- printer contact policy: manual only

The known local material and plate context is:

- Bambu PLA Basic: easy/default material for simple first prints
- Bambu PETG HF: functional material that requires dryness tracking before print decisions
- Bambu Dual-Texture PEI Plate: plate side must be explicit during handoff

These facts should live in a repo-readable context file and be exposed through MCP views. Agents should not rediscover them from prose every time.

## Source Of Truth Rules

The repo uses one first-class serious CAD backend:

- serious, private, or dimensional parts: `build123d`
- simple, public, remixable CSG-style models: OpenSCAD
- decorative figurine first pass: OpenSCAD now; Blender or mesh workflows later
- slicing: Bambu Studio profile path is blessed
- backup slicer: OrcaSlicer only as fallback or comparison
- generated outputs: STL, STEP, 3MF, PNG, and G-code are generated artifacts, not hand-edited source
- printer contact: never automatic

Bambu Studio is the preferred slicer path because it is the official Bambu workflow, but the repo must not trust it as the only durable state. Source, STEP where available, STL, 3MF, profile names, artifact hashes, and manual checklists remain portable.

## Project Workspace

Each model project gets a structured folder:

```text
projects/<slug>/
  project.yaml
  source/
    model.py
    model.scad
  reviews/
    001-design.md
    002-export.md
    003-slicer.md
    004-print-feedback.md
  measurements/
    v001.yaml
  photos/
    .gitkeep
  artifacts.json
```

`project.yaml` is the project source of truth. It records:

- plain-English intent
- privacy level
- lane: `build123d`, `openscad`, or `figurine`
- printer, material, plate, and nozzle assumptions
- dimensional constraints and tolerance notes
- current revision
- current stage
- next safe action
- manual-only gates

`artifacts.json` is generated. It records exported artifacts, tool versions, paths, hashes, timestamps, and which revision produced each artifact. It is an index for agents, not source.

Photos stay ignored by default. Public examples can include non-private placeholder assets only when explicitly added.

## Revision Model

The substrate is revision-oriented, not just project-oriented. Physical print feedback is a first-class input.

Each revision should capture:

- intended change
- source file path
- exported artifact paths and hashes
- slicer profile names
- print result: not printed, success, partial success, failed
- measured dimensions where relevant
- visible defects or fit issues
- material state at print time
- next proposed revision

Functional prints should use `measurements/vNNN.yaml` for expected vs measured dimensions. Decorative prints can use simpler review notes, but still record the physical outcome.

## MCP Views And Tools

Read-first tools expose deterministic state:

- `bambu_context_view`: printer, build volume, nozzle, material state, plate state, installed tools, and safety rules
- `bambu_rules_view`: backend choice, privacy policy, artifact policy, profile policy, and print gates
- `bambu_project_view`: project manifest, current stage, revision state, artifacts, validation status, and next safe action

Mutation tools stay narrow:

- `bambu_create_project`: create a structured project workspace from a plain-English idea
- `bambu_export_plan`: explain source to STEP/STL/PNG export; no printer side effects
- `bambu_slice_plan`: explain slicer handoff using Bambu Studio by default; no printer contact
- `bambu_review_handoff`: produce the manual pre-print checklist
- `bambu_record_print_result`: record measurements, failure mode, material state, photos path references, and next revision notes

Existing example-specific tools can remain, but new general work should route through the project and context views.

## Validation Gates

Design gate:

- `project.yaml` is valid
- lane is chosen
- dimensions and constraints are declared when relevant
- material is selected
- plate side is selected or explicitly deferred
- privacy level is declared

Export gate:

- source file exists
- export command is deterministic
- artifact hash is recorded
- bounding box fits the A1 mini build volume
- STEP is preferred for CAD review when the backend supports it
- STL is allowed for slicer handoff

Slicer gate:

- Bambu Studio profile is named
- material profile is named
- plate side is named
- support and adhesion assumptions are stated
- generated `.gcode.3mf` is treated as a plan requiring human review
- agent does not start the print

Print-feedback gate:

- outcome is recorded
- measured dimensions are recorded for functional parts
- material state is recorded, including PETG HF dryness when relevant
- failure mode is classified
- next revision is proposed

## Implementation Scope

Implement only the substrate layer first:

- context/rules data structures
- project manifest loader and validator
- project creation helper
- artifact manifest writer
- context, rules, and project MCP views
- print-result recording
- one public example project converted into the new shape
- tests covering manifest validation, view output, and print-result recording

Do not implement a full workflow engine, automatic printer sending, cloud printer control, or first-class Orca workflow in this pass.

## References

- Bambu Lab A1 mini technical specifications: https://bambulab.com/en/a1-mini/tech-specs
- Bambu Lab PETG HF filament guidance: https://bambulab.com/en-us/filament/petg-hf
- Bambu Studio software page: https://bambulab.com/en-us/download/studio
- build123d documentation: https://build123d.readthedocs.io/
