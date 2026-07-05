import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bambu.meshy import MeshyError


class SlicerRunTests(unittest.TestCase):
    def test_sliced_output_for_stl_appends_gcode_suffix(self):
        from bambu.slicer import sliced_output_for_stl

        self.assertEqual(
            sliced_output_for_stl(Path("outputs/demo-v1-fused.stl")),
            Path("outputs/demo-v1-fused.gcode.3mf"),
        )

    def test_run_slice_returns_result_without_raising(self):
        from bambu.slicer import SliceRequest, run_slice

        with tempfile.TemporaryDirectory() as tmp:
            model = Path(tmp) / "model.stl"
            output = Path(tmp) / "model.gcode.3mf"
            model.write_text("solid test")
            with patch("bambu.slicer.subprocess.run") as run:

                def _fake_run(command, **_kwargs):
                    output.write_text("3mf")
                    return type(
                        "Completed",
                        (),
                        {"returncode": 0, "stdout": "ok", "stderr": ""},
                    )()

                run.side_effect = _fake_run
                result = run_slice(
                    SliceRequest(model_path=model, output_path=output, executable="fake-slicer"),
                )
                self.assertTrue(result.ok)
                self.assertEqual(result.returncode, 0)


class PipelineRunTests(unittest.TestCase):
    def test_run_project_pipeline_skips_slice_when_gcode_exists(self):
        from bambu.pipeline import PipelineOptions, run_project_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "projects" / "demo"
            (project / "designs" / "v1").mkdir(parents=True)
            (project / "designs" / "v1" / "design.yaml").write_text(
                "agentic_pipeline:\n  source_of_truth: structured_specs\n"
                "design:\n  title: Demo\n  intent: test\n"
            )
            (project / "designs" / "v1" / "build_plan.yaml").write_text(
                "build_plan:\n  review_tools:\n    manual:\n      - Bambu Studio\n"
            )
            (project / "designs" / "v1" / "print_constraints.yaml").write_text(
                "print_constraints:\n  geometry_contract:\n    single_fused_solid: true\n"
            )
            (project / "designs" / "v1" / "people.yaml").write_text("people: []\n")
            (project / "designs" / "v1" / "visual_acceptance.yaml").write_text(
                "visual_acceptance: {}\n"
            )
            (project / "project.yaml").write_text(
                "schema_version: 2\nslug: demo\nintent: Demo\nlane: build123d\n"
                "current_revision: v1\nprinter:\n  model: Bambu Lab A1 mini\n"
                "material:\n  name: Bambu PLA Basic\nplate:\n  name: Bambu Textured PEI Plate\n"
            )
            outputs = root / "outputs"
            outputs.mkdir()
            fused = outputs / "demo-v1.stl"
            fused.write_text("solid fused")
            sliced = outputs / "demo-v1.gcode.3mf"
            sliced.write_bytes(b"PK\x03\x04")

            with (
                patch(
                    "bambu.pipeline.validate_design_spec", return_value={"ok": True, "errors": []}
                ),
                patch("bambu.pipeline.load_design_spec", return_value={}),
                patch("bambu.pipeline.load_review_views", return_value=[]),
                patch(
                    "bambu.pipeline.review_project_3d",
                    return_value={
                        "stl": str(fused),
                        "fits_a1_mini": True,
                        "mesh": {"watertight_manifold": True},
                        "overhangs": {"ok": True},
                        "islands": {"ok": True},
                    },
                ),
                patch("bambu.pipeline.run_slice") as run_slice,
                patch("bambu.pipeline.qc_sliced_3mf", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_stl_overhangs", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_islands", return_value={"ok": True}),
                patch("bambu.pipeline.inspect_print_handoff") as handoff,
                patch("bambu.pipeline.sync_project_artifacts", return_value={}),
            ):
                handoff.return_value = type(
                    "Report",
                    (),
                    {
                        "ready_for_manual_review": True,
                        "open_command": "open demo.gcode.3mf",
                        "missing_markers": [],
                    },
                )()
                run_slice.return_value = type(
                    "SliceResult",
                    (),
                    {"ok": True, "returncode": 0, "command": ["fake-slicer"], "stderr": ""},
                )()
                result = run_project_pipeline(
                    project,
                    PipelineOptions(
                        outputs_root=outputs,
                        skip_meshy=True,
                        no_render=True,
                    ),
                )

        self.assertTrue(result.ok)
        run_slice.assert_not_called()
        statuses = {step.name: step.status for step in result.steps}
        self.assertEqual(statuses["slice"], "skip")


def _scaffold_scene_project(root: Path) -> Path:
    """Create a hybrid project wired for mesh_strategy: scene."""

    project = root / "projects" / "best-buds"
    (project / "designs" / "v1").mkdir(parents=True)
    (project / "references").mkdir(parents=True)
    (project / "photos" / "reference").mkdir(parents=True)
    (project / "mesh").mkdir(parents=True)
    (project / "references" / "intake.yaml").write_text(
        "intent: Woman with glasses and tri-color dog on patio chair diorama\n"
        "reference_photo: photos/reference/patio-reference.jpg\n"
        "reference_photo_confirmed: true\n"
    )
    (project / "photos" / "reference" / "patio-reference.jpg").write_bytes(b"jpeg")
    (project / "project.yaml").write_text(
        "schema_version: 2\nslug: best-buds\nintent: Best Buds\nlane: hybrid\n"
        "mesh_strategy: scene\ncurrent_revision: v1\n"
        "printer:\n  model: Bambu Lab A1 mini\n"
        "material:\n  name: Bambu PLA Basic\nplate:\n  name: Bambu Textured PEI Plate\n"
        "constraints:\n  dimensions_mm: [118, 65, 68]\n"
    )
    return project


class SceneStrategyPipelineTests(unittest.TestCase):
    def _green_review(self, fused: Path):
        return {
            "stl": str(fused),
            "fits_a1_mini": True,
            "mesh": {"watertight_manifold": True},
            "overhangs": {"ok": True},
            "islands": {"ok": True},
        }

    def test_scene_mode_skips_fuse_and_head(self):
        from bambu.pipeline import PipelineOptions, run_project_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = _scaffold_scene_project(root)
            outputs = root / "outputs"
            outputs.mkdir()
            scene_stl = project / "mesh" / "scene-full.stl"
            concept_png = project / "photos" / "reference" / "concept-meshy.png"
            concept_png.write_bytes(b"stale-marina-png")

            def fake_concept(project_dir, **kwargs):
                dest = Path(project_dir) / "photos" / "reference" / "concept-meshy.png"
                dest.write_bytes(b"fresh-png")
                return {"concept_path": str(dest)}

            def fake_scene(project_dir, **kwargs):
                scene_stl.write_text("solid scene")
                return {"stl_path": str(scene_stl)}

            with (
                patch(
                    "bambu.pipeline.validate_design_spec", return_value={"ok": True, "errors": []}
                ),
                patch("bambu.pipeline.load_design_spec", return_value={}),
                patch(
                    "bambu.pipeline.validate_reference_photo",
                    return_value=SimpleNamespace(ok=True, errors=[], warnings=[]),
                ),
                patch("bambu.pipeline.meshy_concept", side_effect=fake_concept) as meshy_concept,
                patch("bambu.pipeline.meshy_scene", side_effect=fake_scene) as meshy_scene,
                patch("bambu.pipeline.meshy_head") as meshy_head,
                patch("bambu.pipeline.fuse_hybrid_project") as fuse_hybrid_project,
                patch(
                    "bambu.pipeline.scale_mesh_to_envelope",
                    return_value={
                        "scaled": False,
                        "factor": 1.0,
                        "original_extents": [10, 10, 10],
                    },
                ) as scale_mesh,
                patch("bambu.pipeline.load_review_views", return_value=[]),
                patch(
                    "bambu.pipeline.review_project_3d", return_value=self._green_review(scene_stl)
                ),
                patch("bambu.pipeline.run_slice") as run_slice,
                patch("bambu.pipeline.qc_sliced_3mf", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_stl_overhangs", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_islands", return_value={"ok": True}),
                patch("bambu.pipeline.inspect_print_handoff") as handoff,
                patch("bambu.pipeline.sync_project_artifacts", return_value={}),
            ):
                handoff.return_value = type(
                    "Report",
                    (),
                    {
                        "ready_for_manual_review": True,
                        "open_command": "open scene.gcode.3mf",
                        "missing_markers": [],
                    },
                )()
                run_slice.return_value = type(
                    "SliceResult",
                    (),
                    {"ok": True, "returncode": 0, "command": ["fake-slicer"], "stderr": ""},
                )()
                result = run_project_pipeline(
                    project,
                    PipelineOptions(outputs_root=outputs, force_meshy=True, no_render=True),
                )

            self.assertTrue(result.ok, msg=[s.__dict__ for s in result.steps])
            # Scene lane must NOT touch the fuse/head path.
            meshy_head.assert_not_called()
            fuse_hybrid_project.assert_not_called()
            scale_mesh.assert_called_once()
            meshy_concept.assert_called_once()
            meshy_scene.assert_called_once()

            step_names = {step.name for step in result.steps}
            self.assertNotIn("fuse-mesh", step_names)
            self.assertNotIn("export-body", step_names)
            self.assertIn("meshy scene", step_names)

            statuses = {step.name: step.status for step in result.steps}
            self.assertEqual(statuses["meshy concept"], "pass")
            self.assertEqual(statuses["meshy scene"], "pass")
            self.assertEqual(statuses["invalidate-marina"], "pass")
            self.assertEqual(result.artifacts.get("stl"), str(scene_stl))

            # --force-meshy archived the stale marina concept locally.
            self.assertTrue(
                (project / "photos" / "reference" / "concept-meshy.WRONG-marina.png").exists()
            )

    def test_scene_concept_falls_back_to_prompt_mode(self):
        from bambu.pipeline import PipelineOptions, run_project_pipeline

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = _scaffold_scene_project(root)
            outputs = root / "outputs"
            outputs.mkdir()
            scene_stl = project / "mesh" / "scene-full.stl"

            calls: list[str | None] = []

            def fake_concept(project_dir, **kwargs):
                mode = kwargs.get("mode")
                calls.append(mode)
                if mode == "photo":
                    raise MeshyError("figure prototype failed")
                dest = Path(project_dir) / "photos" / "reference" / "concept-meshy.png"
                dest.write_bytes(b"prompt-png")
                return {"concept_path": str(dest)}

            def fake_scene(project_dir, **kwargs):
                scene_stl.write_text("solid scene")
                return {"stl_path": str(scene_stl)}

            with (
                patch(
                    "bambu.pipeline.validate_design_spec", return_value={"ok": True, "errors": []}
                ),
                patch("bambu.pipeline.load_design_spec", return_value={}),
                patch("bambu.pipeline.meshy_concept", side_effect=fake_concept) as meshy_concept,
                patch("bambu.pipeline.meshy_scene", side_effect=fake_scene),
                patch("bambu.pipeline.meshy_head") as meshy_head,
                patch("bambu.pipeline.fuse_hybrid_project") as fuse_hybrid_project,
                patch(
                    "bambu.pipeline.scale_mesh_to_envelope",
                    return_value={
                        "scaled": False,
                        "factor": 1.0,
                        "original_extents": [10, 10, 10],
                    },
                ),
                patch("bambu.pipeline.load_review_views", return_value=[]),
                patch(
                    "bambu.pipeline.review_project_3d", return_value=self._green_review(scene_stl)
                ),
                patch("bambu.pipeline.run_slice") as run_slice,
                patch("bambu.pipeline.qc_sliced_3mf", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_stl_overhangs", return_value={"ok": True}),
                patch("bambu.pipeline.analyze_islands", return_value={"ok": True}),
                patch("bambu.pipeline.inspect_print_handoff") as handoff,
                patch("bambu.pipeline.sync_project_artifacts", return_value={}),
            ):
                handoff.return_value = type(
                    "Report",
                    (),
                    {
                        "ready_for_manual_review": True,
                        "open_command": "open scene.gcode.3mf",
                        "missing_markers": [],
                    },
                )()
                run_slice.return_value = type(
                    "SliceResult",
                    (),
                    {"ok": True, "returncode": 0, "command": ["fake-slicer"], "stderr": ""},
                )()
                result = run_project_pipeline(
                    project,
                    PipelineOptions(outputs_root=outputs, force_meshy=True, no_render=True),
                )

            self.assertTrue(result.ok, msg=[s.__dict__ for s in result.steps])
            self.assertEqual(calls, ["photo", "prompt"])
            self.assertEqual(meshy_concept.call_count, 2)
            meshy_head.assert_not_called()
            fuse_hybrid_project.assert_not_called()

            concept_steps = [s for s in result.steps if s.name == "meshy concept"]
            self.assertTrue(any(s.status == "warn" for s in concept_steps))
            self.assertTrue(any("prompt fallback" in s.detail for s in concept_steps))


class ScaleMeshTests(unittest.TestCase):
    def test_scales_oversized_mesh_down_to_envelope(self):
        import trimesh

        from bambu.pipeline import scale_mesh_to_envelope

        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / "scene-full.stl"
            trimesh.creation.box(extents=[200.0, 100.0, 90.0]).export(stl)

            report = scale_mesh_to_envelope(stl, [118.0, 65.0, 68.0])

            self.assertTrue(report["scaled"])
            self.assertLess(report["factor"], 1.0)
            reloaded = sorted(trimesh.load(stl, force="mesh").extents, reverse=True)
            envelope = sorted([118.0, 65.0, 68.0], reverse=True)
            for ext, env in zip(reloaded, envelope, strict=True):
                self.assertLessEqual(ext, env + 1e-6)

    def test_does_not_scale_mesh_already_within_envelope(self):
        import trimesh

        from bambu.pipeline import scale_mesh_to_envelope

        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / "scene-full.stl"
            trimesh.creation.box(extents=[50.0, 40.0, 30.0]).export(stl)

            report = scale_mesh_to_envelope(stl, [118.0, 65.0, 68.0])

            self.assertFalse(report["scaled"])
            self.assertGreaterEqual(report["factor"], 1.0)


if __name__ == "__main__":
    unittest.main()
