import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile


class HandoffTests(unittest.TestCase):
    def test_inspect_gcode_3mf_confirms_a1_mini_print_handoff_metadata(self):
        from bambu.handoff import inspect_print_handoff

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prototype.gcode.3mf"
            with ZipFile(path, "w", ZIP_DEFLATED) as archive:
                archive.writestr(
                    "Metadata/project_settings.config",
                    "\n".join(
                        [
                            "Bambu Lab A1 mini",
                            "0.20mm Standard @BBL A1M",
                            "Bambu PLA Basic",
                            "Textured PEI Plate",
                        ]
                    ),
                )

            report = inspect_print_handoff(path)

        self.assertTrue(report.exists)
        self.assertTrue(report.ready_for_manual_review)
        self.assertEqual(report.missing_markers, [])
        self.assertIn("open -a /Applications/BambuStudio.app", report.open_command)
        self.assertIn("prototype.gcode.3mf", report.open_command)

    def test_cli_handoff_prints_file_location_profile_and_network_plugin_boundary(self):
        from bambu.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "world-cup-neighbors.gcode.3mf"
            with ZipFile(path, "w", ZIP_DEFLATED) as archive:
                archive.writestr(
                    "Metadata/project_settings.config",
                    "\n".join(
                        [
                            "Bambu Lab A1 mini",
                            "0.20mm Standard @BBL A1M",
                            "Bambu PLA Basic",
                            "Textured PEI Plate",
                        ]
                    ),
                )

            output = io.StringIO()
            with patch("sys.stdout", output):
                exit_code = main(["handoff", "--file", str(path)])

        self.assertEqual(exit_code, 0)
        text = output.getvalue()
        self.assertIn("Morning print handoff", text)
        self.assertIn("Bambu Lab A1 mini", text)
        self.assertIn("Bambu Network plug-in", text)
        self.assertIn("Do not start the physical print unattended", text)


if __name__ == "__main__":
    unittest.main()
