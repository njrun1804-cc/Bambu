import unittest
from pathlib import Path
import tempfile


class SlicerTests(unittest.TestCase):
    def test_bambu_studio_slice_plan_uses_a1_mini_defaults(self):
        from bambu.slicer import SliceRequest, build_slice_plan

        plan = build_slice_plan(
            SliceRequest(
                model_path=Path("outputs/world-cup-neighbors.stl"),
                output_path=Path("outputs/world-cup-neighbors.gcode.3mf"),
            )
        )

        self.assertEqual(plan.tool, "bambu-studio")
        self.assertIn("--orient", plan.command)
        self.assertEqual(plan.command[plan.command.index("--orient") + 1], "1")
        self.assertIn("--arrange", plan.command)
        self.assertIn("Textured PEI Plate", " ".join(plan.command))
        self.assertEqual(plan.command[-1], "outputs/world-cup-neighbors.stl")
        self.assertIn("Review supports", plan.checklist[0])
        checklist = " ".join(plan.checklist)
        self.assertIn("A1 mini", checklist)
        self.assertIn("auto bed leveling", checklist.lower())
        self.assertIn("AMS lite", checklist)
        self.assertIn("Textured PEI", checklist)
        self.assertIn("actual loaded spool", checklist)
        self.assertIn("PETG HF", checklist)
        self.assertIn("green PLA Basic", checklist)
        self.assertIn("white PLA+", checklist)

    def test_orca_slice_plan_can_be_selected(self):
        from bambu.slicer import SliceRequest, build_slice_plan

        plan = build_slice_plan(
            SliceRequest(
                model_path=Path("part.stl"),
                output_path=Path("part.gcode.3mf"),
                slicer="orcaslicer",
            )
        )

        self.assertEqual(plan.tool, "orcaslicer")
        self.assertEqual(plan.command[0], "orcaslicer")

    def test_default_a1_mini_profiles_are_loaded_when_present(self):
        from bambu.slicer import SliceRequest, build_slice_plan, default_a1_mini_profiles

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = root / "machine" / "Bambu Lab A1 mini 0.4 nozzle.json"
            process = root / "process" / "0.20mm Standard @BBL A1M.json"
            filament = root / "filament" / "Bambu PLA Basic @BBL A1M.json"
            for path in (machine, process, filament):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")

            profiles = default_a1_mini_profiles("bambu-studio", profile_root=root)
            plan = build_slice_plan(
                SliceRequest(
                    model_path=Path("part.stl"),
                    output_path=Path("part.gcode.3mf"),
                    machine_profile=profiles.machine,
                    process_profile=profiles.process,
                    filament_profile=profiles.filament,
                    resolve_paths=True,
                )
            )

        self.assertIn("--load-settings", plan.command)
        self.assertIn("--load-filaments", plan.command)
        self.assertTrue(Path(plan.command[-1]).is_absolute())

    def test_a1_mini_profiles_resolve_requested_material(self):
        from bambu.slicer import resolve_a1_mini_profiles

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = root / "machine" / "Bambu Lab A1 mini 0.4 nozzle.json"
            process = root / "process" / "0.20mm Standard @BBL A1M.json"
            filament = root / "filament" / "Bambu PETG HF @BBL A1M.json"
            for path in (machine, process, filament):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f'{{"name": "{path.stem}"}}')

            profiles = resolve_a1_mini_profiles(
                "bambu-studio",
                material="Bambu PETG HF",
                nozzle_mm=0.4,
                profile_root=root,
            )

        self.assertIsNotNone(profiles)
        self.assertEqual(profiles.filament, filament)
        self.assertEqual(profiles.material, "Bambu PETG HF")

    def test_slice_plan_uses_requested_material_profile_metadata(self):
        from bambu.slicer import SliceRequest, build_slice_plan, resolve_a1_mini_profiles

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            machine = root / "machine" / "Bambu Lab A1 mini 0.4 nozzle.json"
            process = root / "process" / "0.20mm Standard @BBL A1M.json"
            filament = root / "filament" / "Bambu PETG HF @BBL A1M.json"
            for path in (machine, process, filament):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}")
            profiles = resolve_a1_mini_profiles("bambu-studio", material="Bambu PETG HF", profile_root=root)

            plan = build_slice_plan(
                SliceRequest(
                    model_path=Path("part.stl"),
                    output_path=Path("part.gcode.3mf"),
                    material="Bambu PETG HF",
                    machine_profile=profiles.machine,
                    process_profile=profiles.process,
                    filament_profile=profiles.filament,
                )
            )

        self.assertEqual(plan.profiles["material"], "Bambu PETG HF")
        self.assertEqual(plan.profiles["filament"], str(filament))
        self.assertIn("Bambu PETG HF", " ".join(plan.checklist))


if __name__ == "__main__":
    unittest.main()
