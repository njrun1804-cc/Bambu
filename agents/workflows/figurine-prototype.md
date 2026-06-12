# Figurine Prototype Workflow

1. Run `uv run bambu doctor` or call `bambu_doctor`.
2. Keep source photos in `private/references/`.
3. For the full safe prototype path, run:

   ```bash
   uv run bambu prototype-world-cup --output-dir outputs --slicer bambu-studio
   ```

   This creates SCAD, STL, and sliced 3MF but does not start the printer.

4. For source-only iteration, generate source:

   ```bash
   uv run bambu make-figurines --output outputs/world-cup-neighbors.scad
   ```

5. Export plan:

   ```bash
   uv run bambu-mcp
   ```

   Then call `bambu_openscad_export_plan` with `outputs/world-cup-neighbors.scad`.

6. Export STL in OpenSCAD.
7. Build a slicer plan with `bambu_slice_plan`.
8. Open the slicer manually, inspect supports/scale/filament/bed/first layer, and only then print.
