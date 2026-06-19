import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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
            (project / "designs" / "v1" / "visual_acceptance.yaml").write_text("visual_acceptance: {}\n")
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

            with patch("bambu.pipeline.validate_design_spec", return_value={"ok": True, "errors": []}), patch(
                "bambu.pipeline.load_design_spec", return_value={}
            ), patch("bambu.pipeline.load_review_views", return_value=[]), patch(
                "bambu.pipeline.review_project_3d",
                return_value={
                    "stl": str(fused),
                    "fits_a1_mini": True,
                    "mesh": {"watertight_manifold": True},
                    "overhangs": {"ok": True},
                    "islands": {"ok": True},
                },
            ), patch("bambu.pipeline.run_slice") as run_slice, patch(
                "bambu.pipeline.qc_sliced_3mf", return_value={"ok": True}
            ), patch(
                "bambu.pipeline.analyze_stl_overhangs", return_value={"ok": True}
            ), patch(
                "bambu.pipeline.analyze_islands", return_value={"ok": True}
            ), patch(
                "bambu.pipeline.inspect_print_handoff"
            ) as handoff, patch("bambu.pipeline.sync_project_artifacts", return_value={}):
                handoff.return_value = type(
                    "Report",
                    (),
                    {"ready_for_manual_review": True, "open_command": "open demo.gcode.3mf", "missing_markers": []},
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


if __name__ == "__main__":
    unittest.main()
