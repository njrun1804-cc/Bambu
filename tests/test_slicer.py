import unittest
from pathlib import Path


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
        self.assertIn("--arrange", plan.command)
        self.assertIn("Textured PEI Plate", " ".join(plan.command))
        self.assertEqual(plan.command[-1], "outputs/world-cup-neighbors.stl")
        self.assertIn("Review supports", plan.checklist[0])

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


if __name__ == "__main__":
    unittest.main()

