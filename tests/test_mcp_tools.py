import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class McpToolTests(unittest.TestCase):
    def test_mcp_doctor_returns_structured_setup_report(self):
        from bambu.mcp_server import bambu_doctor

        report = bambu_doctor()

        self.assertIn("tools", report)
        self.assertIn("next_steps", report)
        self.assertIn("openscad", report["tools"])

    def test_mcp_generate_world_cup_figurines_writes_under_requested_path(self):
        from bambu.mcp_server import bambu_generate_world_cup_figurines

        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "figures.scad"
            result = bambu_generate_world_cup_figurines(str(output))

            self.assertTrue(output.exists())
            self.assertEqual(result["output"], str(output))
            self.assertIn("World Cup neighbors", output.read_text())

    def test_mcp_slice_plan_uses_detected_slicer_executable(self):
        from bambu.mcp_server import bambu_slice_plan

        fake_report = {
            "bambu_studio": type(
                "Tool",
                (),
                {"available": True, "path": "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"},
            )(),
            "orcaslicer": type("Tool", (), {"available": False, "path": None})(),
        }
        with patch("bambu.mcp_server.detect_tools", return_value=fake_report):
            result = bambu_slice_plan("outputs/a.stl", "outputs/a.gcode.3mf")

        self.assertEqual(result["tool"], "bambu-studio")
        self.assertEqual(result["command"][0], "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio")
        self.assertIn("manual approval", " ".join(result["checklist"]).lower())

    def test_mcp_build_world_cup_prototype_delegates_pipeline(self):
        from bambu.mcp_server import bambu_build_world_cup_prototype

        with patch("bambu.mcp_server.build_world_cup_prototype") as build:
            build.return_value = {"sliced": "outputs/world-cup-neighbors.gcode.3mf"}
            result = bambu_build_world_cup_prototype("outputs", "bambu-studio")

        self.assertEqual(result["sliced"], "outputs/world-cup-neighbors.gcode.3mf")
        build.assert_called_once()


if __name__ == "__main__":
    unittest.main()
