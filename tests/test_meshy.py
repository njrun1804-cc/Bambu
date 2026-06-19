import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from bambu.meshy import (
    TEST_MODE_API_KEY,
    MeshyClient,
    MeshyError,
    _reject_unsafe_url,
    concept_prompt_from_intake,
    meshy_analyze,
    meshy_concept,
    meshy_figure_build,
    meshy_head,
    meshy_scene,
    resolve_head_crop,
)


class MeshyTests(unittest.TestCase):
    def test_client_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("MESHY_API_KEY", None)
            with self.assertRaises(MeshyError):
                MeshyClient.from_env()

    def test_test_mode_key_is_recognized(self):
        client = MeshyClient(api_key=TEST_MODE_API_KEY)
        self.assertTrue(client.test_mode)

    def test_request_refuses_test_mode_key_without_network(self):
        # The documented placeholder key must never reach the network: _request
        # short-circuits before any httpx call.
        client = MeshyClient(api_key=TEST_MODE_API_KEY)
        with patch("httpx.Client") as http_client:
            with self.assertRaises(MeshyError):
                client.balance()
            http_client.assert_not_called()

    def test_reject_unsafe_url_blocks_non_https_and_internal_hosts(self):
        _reject_unsafe_url("https://assets.meshy.ai/model.stl")  # public https: allowed
        for bad in (
            "http://assets.meshy.ai/model.stl",  # not https
            "https://localhost/model.stl",
            "https://127.0.0.1/model.stl",
            "https://169.254.169.254/latest/meta-data",  # link-local metadata
            "https://10.0.0.5/model.stl",  # private
            "ftp://assets.meshy.ai/model.stl",
        ):
            with self.assertRaises(MeshyError, msg=bad):
                _reject_unsafe_url(bad)

    @patch.object(MeshyClient, "_request")
    def test_balance_calls_v1_endpoint(self, request: MagicMock):
        request.return_value = {"balance": 100}
        client = MeshyClient(api_key="msy_test")
        self.assertEqual(client.balance()["balance"], 100)
        request.assert_called_with("GET", "v1/balance")

    @patch.object(MeshyClient, "poll_task")
    @patch.object(MeshyClient, "create_task")
    def test_analyze_printability_uses_print_analyze_endpoint(self, create_task: MagicMock, poll_task: MagicMock):
        create_task.return_value = "analyze-task"
        poll_task.return_value = {"status": "SUCCEEDED"}
        client = MeshyClient(api_key="msy_test")
        client.analyze_printability(input_task_id="head-task")
        create_task.assert_called_once_with("v1/print/analyze", {"input_task_id": "head-task"})
        poll_task.assert_called_once_with("v1/print/analyze", "analyze-task")

    @patch.object(MeshyClient, "poll_task")
    @patch.object(MeshyClient, "create_task")
    def test_repair_printability_uses_print_repair_endpoint(self, create_task: MagicMock, poll_task: MagicMock):
        create_task.return_value = "repair-task"
        poll_task.return_value = {"status": "SUCCEEDED"}
        client = MeshyClient(api_key="msy_test")
        client.repair_printability(input_task_id="head-task")
        create_task.assert_called_once_with("v1/print/repair", {"input_task_id": "head-task"})
        poll_task.assert_called_once_with("v1/print/repair", "repair-task")

    def test_meshy_analyze_requires_task_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            (project / "mesh").mkdir(parents=True)
            with self.assertRaises(MeshyError):
                meshy_analyze(project, client=MeshyClient(api_key=TEST_MODE_API_KEY))

    def test_concept_prompt_from_intake_uses_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            refs = project / "references"
            refs.mkdir(parents=True)
            (refs / "intake.yaml").write_text(
                "intent: Woman with glasses and tri-color dog on patio chair diorama\n"
                "agent_fill:\n"
                "  pose: seated on patio chair\n"
                "  recognition_cues:\n"
                "    - glasses ridge\n"
                "    - dog floppy ears\n"
            )
            prompt = concept_prompt_from_intake(project)
            self.assertIn("patio chair", prompt)
            self.assertIn("glasses ridge", prompt)

    @patch.object(MeshyClient, "run_figure_prototype")
    @patch.object(MeshyClient, "download_url")
    @patch.object(MeshyClient, "extract_model_urls")
    def test_meshy_concept_writes_png(self, urls, download, prototype):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            ref = project / "photos" / "reference"
            ref.mkdir(parents=True)
            photo = ref / "patio.jpg"
            photo.write_bytes(b"jpeg")
            (project / "references").mkdir()
            (project / "references" / "intake.yaml").write_text(
                "reference_photo: photos/reference/patio.jpg\n"
            )
            prototype.return_value = {"id": "task-1", "consumed_credits": 6}
            urls.return_value = {"image_url": "https://example.com/concept.png"}
            download.side_effect = lambda url, dest: dest.write_bytes(b"png") or dest

            result = meshy_concept(project, client=MeshyClient(api_key=TEST_MODE_API_KEY))

            self.assertTrue(Path(result["concept_path"]).exists())
            self.assertIn("concept-meshy.png", result["concept_path"])

    def test_resolve_head_crop_requires_crop_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            with self.assertRaises(FileNotFoundError):
                resolve_head_crop(project, "woman")

    @patch.object(MeshyClient, "run_image_to_3d")
    @patch.object(MeshyClient, "download_url")
    @patch.object(MeshyClient, "extract_model_urls")
    def test_meshy_head_writes_stl(self, urls, download, i23d):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            ref = project / "photos" / "reference"
            ref.mkdir(parents=True)
            (ref / "crop-woman.jpg").write_bytes(b"jpeg")
            (project / "project.yaml").write_text("slug: demo\ncurrent_revision: v1\n")
            i23d.return_value = {"id": "head-task", "consumed_credits": 20}
            urls.return_value = {"stl": "https://example.com/woman.stl"}
            download.side_effect = lambda url, dest: dest.write_bytes(b"stl") or dest

            result = meshy_head(project, subject="woman", client=MeshyClient(api_key=TEST_MODE_API_KEY))

            self.assertTrue(Path(result["stl_path"]).exists())
            self.assertIn("woman-head.stl", result["stl_path"])

    @patch("bambu.meshy._export_meshy_model")
    @patch.object(MeshyClient, "run_figure_build")
    def test_meshy_figure_build_uses_provenance_prototype(self, build, export):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            mesh = project / "mesh"
            mesh.mkdir(parents=True)
            (project / "project.yaml").write_text("slug: demo\ncurrent_revision: v1\n")
            (mesh / "provenance.yaml").write_text(
                "concept:\n  task_id: proto-123\n"
            )
            build.return_value = {"id": "build-task", "consumed_credits": 30}
            dest = mesh / "figure-full.stl"
            dest.write_bytes(b"stl")
            export.return_value = dest

            result = meshy_figure_build(project, client=MeshyClient(api_key=TEST_MODE_API_KEY))

            build.assert_called_once_with("proto-123")
            self.assertIn("figure-full.stl", result["stl_path"])

    @patch("bambu.meshy._export_meshy_model")
    @patch.object(MeshyClient, "run_image_to_3d")
    def test_meshy_scene_defaults_to_concept_sheet(self, i23d, export):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            ref = project / "photos" / "reference"
            ref.mkdir(parents=True)
            concept = ref / "concept-meshy.png"
            concept.write_bytes(b"png")
            (project / "project.yaml").write_text("slug: demo\ncurrent_revision: v1\n")
            i23d.return_value = {"id": "scene-task", "consumed_credits": 20}
            dest = project / "mesh" / "scene-full.stl"
            dest.parent.mkdir(parents=True)
            dest.write_bytes(b"stl")
            export.return_value = dest

            result = meshy_scene(project, client=MeshyClient(api_key=TEST_MODE_API_KEY))

            i23d.assert_called_once()
            self.assertEqual(i23d.call_args.args[0], concept)
            self.assertIn("scene-full.stl", result["stl_path"])

    @patch("bambu.meshy._export_meshy_model")
    @patch.object(MeshyClient, "run_image_to_3d")
    def test_meshy_scene_blocks_known_wrong_image(self, i23d, export):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            ref = project / "photos" / "reference"
            ref.mkdir(parents=True)
            (project / "project.yaml").write_text("slug: demo\ncurrent_revision: v1\n")
            wrong = ref / "patio-reference.jpg"
            wrong_bytes = b"the-exact-marina-couple-bytes"
            wrong.write_bytes(wrong_bytes)
            wrong_hash = hashlib.sha256(wrong_bytes).hexdigest()

            with patch(
                "bambu.reference_validation.KNOWN_WRONG_REFERENCE_SHA256",
                frozenset({wrong_hash}),
            ):
                with self.assertRaises(MeshyError):
                    meshy_scene(
                        project,
                        image=wrong,
                        client=MeshyClient(api_key=TEST_MODE_API_KEY),
                    )
            i23d.assert_not_called()


if __name__ == "__main__":
    unittest.main()
