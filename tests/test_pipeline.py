import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class PipelineTests(unittest.TestCase):
    def test_build_world_cup_prototype_generates_source_and_runs_export_steps(self):
        from bambu.pipeline import build_world_cup_prototype

        commands = []

        def fake_run(command, **_kwargs):
            commands.append(command)
            output = Path(command[command.index("-o") + 1]) if "-o" in command else None
            if output:
                output.write_text("solid test")
            if "--export-3mf" in command:
                Path(command[command.index("--export-3mf") + 1]).write_text("3mf")
            return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        with tempfile.TemporaryDirectory() as tmp, patch("subprocess.run", side_effect=fake_run):
            result = build_world_cup_prototype(Path(tmp), slicer="orcaslicer")

        self.assertTrue(result["scad"].endswith("world-cup-neighbors.scad"))
        self.assertTrue(result["stl"].endswith("world-cup-neighbors.stl"))
        self.assertTrue(result["sliced"].endswith("world-cup-neighbors.gcode.3mf"))
        self.assertEqual(len(commands), 2)
        self.assertTrue(commands[0][0].endswith("openscad"))
        self.assertIn("--export-3mf", commands[1])


if __name__ == "__main__":
    unittest.main()
