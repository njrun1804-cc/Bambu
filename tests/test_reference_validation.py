import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from bambu.meshy import MeshyClient, MeshyError, TEST_MODE_API_KEY, meshy_concept
from bambu.reference_validation import (
    intake_subject_requirements,
    validate_reference_photo,
)


class ReferenceValidationTests(unittest.TestCase):
    def test_intake_subject_requirements_from_best_buds_intent(self):
        intake = {
            "intent": "Woman with glasses and tri-color dog on patio chair diorama",
            "agent_fill": {
                "subjects": [{"id": "woman"}, {"id": "dog", "type": "animal"}],
                "pose": "seated on patio chair",
                "props": ["chunky patio chair"],
            },
        }
        required = intake_subject_requirements(intake)
        self.assertTrue(required["woman"])
        self.assertTrue(required["dog"])
        self.assertTrue(required["chair"])

    def test_blocks_clear_right_pair_without_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            refs = project / "references"
            refs.mkdir(parents=True)
            photo = project / "photos" / "reference" / "patio-reference.jpg"
            photo.parent.mkdir(parents=True)
            photo.write_bytes(b"marina")
            (refs / "intake.yaml").write_text(
                yaml.safe_dump(
                    {
                        "intent": "Woman with dog on patio chair",
                        "reference_photo": "photos/reference/patio-reference.jpg",
                        "reference_photo_confirmed": False,
                    }
                )
            )
            (project / "mesh").mkdir(parents=True)
            (project / "mesh" / "provenance.yaml").write_text(
                "reference_source: private/references/clear-right-pair.jpg\n"
            )
            result = validate_reference_photo(project, photo=photo)
            self.assertFalse(result.ok)
            self.assertTrue(any("clear-right-pair" in err for err in result.errors))

    def test_allows_confirmed_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            refs = project / "references"
            refs.mkdir(parents=True)
            photo = project / "photos" / "reference" / "patio.jpg"
            photo.parent.mkdir(parents=True)
            photo.write_bytes(b"ok")
            (refs / "intake.yaml").write_text(
                yaml.safe_dump(
                    {
                        "intent": "Woman with dog on patio chair",
                        "reference_photo": "photos/reference/patio.jpg",
                        "reference_photo_confirmed": True,
                    }
                )
            )
            result = validate_reference_photo(project, photo=photo)
            self.assertTrue(result.ok)

    @patch.object(MeshyClient, "run_figure_prototype")
    @patch.object(MeshyClient, "download_url")
    @patch.object(MeshyClient, "extract_model_urls")
    def test_meshy_concept_blocks_unconfirmed_marina_source(self, urls, download, prototype):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            ref = project / "photos" / "reference"
            ref.mkdir(parents=True)
            photo = ref / "patio-reference.jpg"
            photo.write_bytes(b"jpeg")
            (project / "references").mkdir()
            (project / "references" / "intake.yaml").write_text(
                yaml.safe_dump(
                    {
                        "intent": "Woman with dog on patio chair",
                        "reference_photo": "photos/reference/patio-reference.jpg",
                        "reference_photo_confirmed": False,
                    }
                )
            )
            (project / "mesh").mkdir()
            (project / "mesh" / "provenance.yaml").write_text(
                "reference_source: private/references/clear-right-pair.jpg\n"
            )
            with self.assertRaises(MeshyError):
                meshy_concept(project, client=MeshyClient(api_key=TEST_MODE_API_KEY), mode="photo")
            prototype.assert_not_called()


if __name__ == "__main__":
    unittest.main()
