import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class BlenderV4Tests(unittest.TestCase):
    def test_load_v4_spec_returns_project_paths_and_people(self):
        from bambu.blender_v4 import load_v4_spec

        spec = load_v4_spec(Path("projects/world-cup-neighbors"))

        self.assertEqual(spec["scene"]["generation"]["visual_source_of_truth"], "blender")
        self.assertEqual([person["id"] for person in spec["people"]["people"]], ["dan", "carrie"])
        self.assertTrue(spec["target_image"].exists())
        self.assertTrue(spec["generator_script"].exists())

    def test_build_blender_v4_command_is_background_and_read_only(self):
        from bambu.blender_v4 import build_blender_v4_command

        command = build_blender_v4_command(
            blender="/opt/homebrew/bin/blender",
            project=Path("projects/world-cup-neighbors"),
            output_dir=Path("outputs/review/world-cup-neighbors-v4"),
        )

        self.assertEqual(command[:2], ["/opt/homebrew/bin/blender", "--background"])
        self.assertIn("projects/world-cup-neighbors/source/v4/blender_scene.py", command)
        self.assertIn("--", command)
        self.assertIn("--project", command)
        self.assertIn("--output-dir", command)
        self.assertNotIn("BambuStudio", " ".join(command))

    def test_render_v4_candidate_builds_contact_sheet_and_never_contacts_printer(self):
        from bambu.blender_v4 import render_v4_candidate

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            design = project / "designs" / "v4"
            source = project / "source" / "v4"
            target_dir = project / "references" / "ai-concepts"
            design.mkdir(parents=True)
            source.mkdir(parents=True)
            target_dir.mkdir(parents=True)
            (source / "blender_scene.py").write_text("# fake")
            target = target_dir / "target.png"
            from PIL import Image

            Image.new("RGB", (1000, 800), (20, 120, 40)).save(target)
            (design / "scene.yaml").write_text(
                "generation:\n  visual_source_of_truth: blender\n  cad_role: mechanical_validation_only\n"
                "output_slug: demo-v4\nsafety:\n  printer_contact_allowed: false\n"
            )
            (design / "people.yaml").write_text("people:\n  - id: dan\n  - id: carrie\n")
            (design / "visual_targets.yaml").write_text(
                "primary_target:\n  path: references/ai-concepts/target.png\n  role: visual_contract\ncrop_views:\n"
                "  front: [0.1, 0.1, 0.3, 0.3]\n"
            )
            (design / "print_constraints.yaml").write_text("printer:\n  model: Bambu Lab A1 mini\n")
            (design / "acceptance.yaml").write_text("required_views: [front]\n")
            output_dir = root / "outputs" / "review" / "demo-v4"
            front = output_dir / "front.png"
            output_dir.mkdir(parents=True)
            Image.new("RGB", (200, 160), (40, 180, 80)).save(front)

            with patch("bambu.blender_v4.detect_blender", return_value="/opt/homebrew/bin/blender"), patch(
                "subprocess.run"
            ) as run:
                run.return_value.returncode = 0
                run.return_value.stdout = ""
                run.return_value.stderr = ""
                report = render_v4_candidate(project, outputs_root=root / "outputs")

        self.assertFalse(report["printer_contact"])
        self.assertEqual(report["blender"]["returncode"], 0)
        self.assertTrue(Path(report["visual_contact_sheet"]["path"]).exists())

    def test_generator_source_declares_fixed_review_views(self):
        source = Path("projects/world-cup-neighbors/source/v4/blender_scene.py").read_text()

        for name in ("front", "front-angle", "top", "dan-head", "carrie-head", "low-front"):
            self.assertIn(f"render_view({name!r}", source)
        self.assertIn("--project", source)
        self.assertIn("--output-dir", source)


if __name__ == "__main__":
    unittest.main()
