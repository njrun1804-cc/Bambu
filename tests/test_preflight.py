import unittest
from unittest.mock import patch


class PreflightTests(unittest.TestCase):
    def test_detect_tools_reports_available_and_missing_tools(self):
        from bambu.preflight import detect_tools

        def fake_which(name):
            return f"/usr/local/bin/{name}" if name == "openscad" else None

        with patch("shutil.which", side_effect=fake_which):
            report = detect_tools()

        self.assertTrue(report["openscad"].available)
        self.assertEqual(report["openscad"].path, "/usr/local/bin/openscad")
        self.assertFalse(report["bambu_studio"].available)
        self.assertIn("Install OpenSCAD", report["bambu_studio"].hint)

    def test_next_steps_prefers_generate_then_install_then_slice(self):
        from bambu.preflight import next_steps

        report = {
            "openscad": type("Tool", (), {"available": False})(),
            "bambu_studio": type("Tool", (), {"available": False})(),
            "orcaslicer": type("Tool", (), {"available": False})(),
        }

        steps = next_steps(report, has_scad=False, has_stl=False)

        self.assertEqual(steps[0], "Create or generate an OpenSCAD .scad file from a brief.")
        self.assertIn("Install OpenSCAD", steps[1])


if __name__ == "__main__":
    unittest.main()

