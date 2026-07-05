import tempfile
import unittest
from pathlib import Path


class CadTests(unittest.TestCase):
    def test_export_build123d_model_writes_step_stl_and_bounding_box(self):
        from bambu.cad import export_build123d_project
        from bambu.projects import create_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_project("Calibration block", root=root)
            project_dir = root / "calibration-block"
            source = project_dir / "source" / "v1" / "model.py"
            source.write_text(
                "\n".join(
                    [
                        "from build123d import Box",
                        "model = Box(10, 20, 5)",
                    ]
                )
            )

            result = export_build123d_project(project_dir, output_dir=root / "outputs")

            self.assertTrue(Path(result["step"]).exists())
            self.assertTrue(Path(result["stl"]).exists())
            self.assertEqual(result["bounding_box_mm"], [10.0, 20.0, 5.0])
            self.assertTrue(result["fits_a1_mini"])
            self.assertIn(
                "cad_step", {entry["kind"] for entry in result["artifacts"]["artifacts"]}
            )

    def test_export_build123d_project_rejects_missing_model_symbol(self):
        from bambu.cad import export_build123d_project
        from bambu.projects import create_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            create_project("Empty", root=root)
            project_dir = root / "empty"
            (project_dir / "source" / "v1" / "model.py").write_text("value = 1\n")

            with self.assertRaises(ValueError) as error:
                export_build123d_project(project_dir, output_dir=root / "outputs")

        self.assertIn("model", str(error.exception))

    def test_export_build123d_project_honors_revision_over_manifest(self):
        from bambu.cad import export_build123d_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo"
            (project_dir / "source" / "v4").mkdir(parents=True)
            (project_dir / "source" / "v4" / "model.py").write_text(
                "from build123d import Box\nmodel = Box(4, 5, 6)\n"
            )
            (project_dir / "source" / "model.py").write_text(
                "from build123d import Box\nmodel = Box(99, 99, 99)\n"
            )
            (project_dir / "project.yaml").write_text(
                "\n".join(
                    [
                        "slug: demo",
                        "intent: test",
                        "privacy: private",
                        "lane: build123d",
                        "current_revision: v4.1",
                        "printer:",
                        "  model: Bambu Lab A1 mini",
                        "  build_volume_mm: [180, 180, 180]",
                        "material:",
                        "  name: Bambu PLA Basic",
                        "plate:",
                        "  name: Bambu Dual-Texture PEI Plate",
                    ]
                )
            )

            result = export_build123d_project(
                project_dir,
                output_dir=root / "outputs",
                revision="v4",
            )

        self.assertEqual(result["bounding_box_mm"], [4.0, 5.0, 6.0])
        self.assertIn("source/v4/model.py", result["source"])

    def test_world_cup_v2_source_defines_exportable_model(self):
        from bambu.cad import load_build123d_model

        model = load_build123d_model(Path("projects/_archive/world-cup-neighbors/source/model.py"))

        box = model.bounding_box()
        self.assertLessEqual(float(box.size.X), 130.0)
        self.assertLessEqual(float(box.size.Y), 75.0)
        self.assertLessEqual(float(box.size.Z), 85.0)


if __name__ == "__main__":
    unittest.main()
