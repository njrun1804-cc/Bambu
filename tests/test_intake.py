import tempfile
import unittest
from pathlib import Path

from bambu.intake import load_intake_prompt, run_intake


class IntakeTests(unittest.TestCase):
    def test_run_intake_scaffolds_project_and_copies_photo(self):
        from bambu.intake import run_intake

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            photo = Path(tmp) / "patio.jpg"
            photo.write_bytes(b"fake jpeg")
            result = run_intake(
                photo,
                intent="Woman with dog on patio chair",
                slug="test-intake",
                root=root,
                archetype="seated_diorama",
            )

            project = root / "test-intake"
            self.assertTrue(project.exists())
            self.assertTrue((project / "references" / "intake.yaml").exists())
            self.assertTrue((project / "designs" / "v1" / "design.yaml").exists())
            self.assertTrue((project / "photos" / "reference" / "patio.jpg").exists())
            self.assertEqual(result["archetype"], "seated_diorama")
            self.assertIn("design-check", result["agent_prompt"])

    def test_classify_archetype_from_intent(self):
        from bambu.intake import classify_archetype_from_intent

        self.assertEqual(
            classify_archetype_from_intent("Woman with dog on patio chair diorama"),
            "seated_diorama",
        )
        self.assertEqual(
            classify_archetype_from_intent("Standing soccer figurines with goal"),
            "seated_diorama",
        )

    def test_run_intake_rejects_existing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            photo = Path(tmp) / "patio.jpg"
            photo.write_bytes(b"fake jpeg")
            run_intake(
                photo,
                intent="Woman with dog on patio chair",
                slug="test-intake",
                root=root,
            )

            with self.assertRaises(FileExistsError):
                run_intake(
                    photo,
                    intent="Another intent",
                    slug="test-intake",
                    root=root,
                )

    def test_run_intake_rejects_unsupported_archetype(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            photo = Path(tmp) / "patio.jpg"
            photo.write_bytes(b"fake jpeg")

            with self.assertRaises(ValueError) as error:
                run_intake(
                    photo,
                    intent="Standing soccer figurines with goal",
                    slug="standing-test",
                    root=root,
                    archetype="standing_figurines",
                )

            self.assertIn("no spec templates", str(error.exception))

    def test_run_intake_accepts_intent_with_literal_braces(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            photo = Path(tmp) / "patio.jpg"
            photo.write_bytes(b"fake jpeg")

            result = run_intake(
                photo,
                intent="Gift {name} on patio chair",
                slug="brace-test",
                root=root,
            )

            self.assertIn("Gift {name} on patio chair", result["agent_prompt"])

    def test_load_intake_prompt_preserves_literal_braces_in_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "projects"
            photo = Path(tmp) / "patio.jpg"
            photo.write_bytes(b"fake jpeg")
            run_intake(
                photo,
                intent="Gift for name on patio chair",
                slug="prompt-test",
                root=root,
            )
            intake_yaml = root / "prompt-test" / "references" / "intake.yaml"
            intake_yaml.write_text(
                intake_yaml.read_text().replace(
                    "Gift for name on patio chair",
                    "Gift {name} on patio chair",
                )
            )

            prompt = load_intake_prompt(root / "prompt-test")

        self.assertIn("Gift {name} on patio chair", prompt)


if __name__ == "__main__":
    unittest.main()
