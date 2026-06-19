import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import trimesh


def _write_watertight_tetrahedron(stl: Path) -> None:
    vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    facets = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (0, 3, 2)]
    with open(stl, "wb") as handle:
        handle.write(b"\0" * 80)
        handle.write(struct.pack("<I", len(facets)))
        for a, b, c in facets:
            handle.write(struct.pack("<3f", 0, 0, 0))
            for idx in (a, b, c):
                handle.write(struct.pack("<3f", *vertices[idx]))
            handle.write(struct.pack("<H", 0))


def _write_watertight_sphere(stl: Path, *, center=(0.5, 0.5, 0.5), radius=0.2) -> None:
    mesh = trimesh.creation.icosphere(subdivisions=2, radius=radius)
    mesh.apply_translation(center)
    mesh.export(stl)


class MeshFusionTests(unittest.TestCase):
    def test_seated_diorama_stub_centers(self):
        from bambu.cad.archetypes.seated_diorama import head_stub_centers

        stubs = head_stub_centers()
        self.assertEqual(stubs["woman"], (20.0, 2.0, 50.5))
        self.assertEqual(stubs["dog"], (0.0, -4.0, 26.0))

    def test_clean_head_mesh_keeps_largest_component(self):
        from bambu.mesh_fusion import clean_head_mesh

        large = trimesh.creation.box(extents=[10, 10, 10])
        tiny = trimesh.creation.box(extents=[0.01, 0.01, 0.01])
        tiny.apply_translation([20, 20, 20])
        combined = trimesh.util.concatenate([large, tiny])
        cleaned = clean_head_mesh(combined)
        self.assertEqual(len(cleaned.faces), len(large.faces))

    def test_trim_mesh_below_z_removes_low_faces(self):
        from bambu.mesh_fusion import trim_mesh_below_z

        mesh = trimesh.creation.box(extents=[2, 2, 4])
        mesh.apply_translation([0, 0, 2])
        trimmed = trim_mesh_below_z(mesh, 1.5)
        self.assertGreaterEqual(float(trimmed.vertices[:, 2].min()), 1.5)

    def test_repair_fused_mesh_returns_mesh_and_report(self):
        from bambu.mesh_fusion import repair_fused_mesh

        mesh = trimesh.creation.icosphere(subdivisions=2, radius=1.0)
        repaired, report = repair_fused_mesh(mesh)
        self.assertIsInstance(repaired, trimesh.Trimesh)
        self.assertIn("watertight_manifold", report)

    def test_woman_stub_gets_default_extra_sink(self):
        from bambu.mesh_fusion import DEFAULT_STUB_EXTRA_SINK_MM, _load_head_specs
        from bambu.mesh_lane import load_fusion_manifest

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "projects" / "demo"
            design = project / "designs" / "v1"
            design.mkdir(parents=True)
            (project / "project.yaml").write_text("slug: demo\narchetype: seated_diorama\ncurrent_revision: v1\n")
            (design / "people.yaml").write_text("schema_version: 2\npeople: []\n")
            (design / "fusion_manifest.yaml").write_text(
                "head_meshes:\n"
                "  - id: woman\n"
                "    source: mesh/woman-head.stl\n"
                "    align: {stub: [20,2,50.5], sink_mm: 5}\n"
                "  - id: dog\n"
                "    source: mesh/dog-head.stl\n"
                "    align: {stub: [0,-4,26], sink_mm: 5}\n"
            )
            (project / "mesh").mkdir(parents=True)
            for head_id in ("woman", "dog"):
                trimesh.creation.icosphere(subdivisions=1, radius=0.2).export(project / "mesh" / f"{head_id}-head.stl")
            fusion = load_fusion_manifest(project, revision="v1")
            specs = _load_head_specs(project, fusion, root, revision="v1")
        woman = next(spec for spec in specs if spec.head_id == "woman")
        dog = next(spec for spec in specs if spec.head_id == "dog")
        self.assertEqual(woman.extra_sink_mm, DEFAULT_STUB_EXTRA_SINK_MM["woman"])
        self.assertEqual(dog.extra_sink_mm, 0.0)

    def test_align_head_to_stub_moves_mesh(self):
        from bambu.mesh_fusion import align_head_to_stub

        mesh = trimesh.creation.box(extents=[2, 2, 2])
        aligned = align_head_to_stub(mesh, (10.0, 5.0, 20.0), target_width_mm=4.0, scale=1.0, sink_mm=1.0)
        self.assertAlmostEqual(float(aligned.bounds[0, 0]), 8.0, places=1)
        self.assertAlmostEqual(float(aligned.bounds[0, 1]), 3.0, places=1)
        self.assertAlmostEqual(float(aligned.bounds[0, 2]), 19.0, places=1)

    def test_fuse_head_specs_unions_fixture_meshes(self):
        from bambu.mesh_fusion import HeadFusionSpec, fuse_head_specs

        body = trimesh.creation.box(extents=[4, 4, 1])
        body.apply_translation([0, 0, 0.5])
        head = trimesh.creation.icosphere(subdivisions=2, radius=0.5)
        with tempfile.TemporaryDirectory() as tmp:
            head_path = Path(tmp) / "head.stl"
            head.export(head_path)
            fused = fuse_head_specs(
                body,
                [
                    HeadFusionSpec(
                        head_id="subject",
                        source=head_path,
                        stub_center=(0.0, 0.0, 1.0),
                        target_width_mm=1.0,
                        scale=1.0,
                        sink_mm=0.2,
                    )
                ],
            )
        self.assertGreater(len(fused.faces), len(body.faces))

    def test_fuse_hybrid_project_writes_manifest_status(self):
        from bambu.mesh_fusion import fuse_hybrid_project

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "projects" / "demo"
            design = project / "designs" / "v1"
            mesh_dir = project / "mesh"
            outputs = root / "outputs"
            design.mkdir(parents=True)
            mesh_dir.mkdir(parents=True)
            outputs.mkdir(parents=True)
            (project / "project.yaml").write_text(
                "slug: demo\narchetype: seated_diorama\ncurrent_revision: v1\n"
            )
            (design / "people.yaml").write_text(
                "schema_version: 2\n"
                "people:\n"
                "  - id: woman\n"
                "    head_mm: {width: 20}\n"
                "    review: {face_center: [1, 2, 3]}\n"
            )
            (design / "fusion_manifest.yaml").write_text(
                "body_artifact: outputs/demo-v1-body.stl\n"
                "head_meshes:\n"
                "  - id: woman\n"
                "    source: mesh/woman-head.stl\n"
                "    align: {stub: [0,0,1], scale: 1.0, sink_mm: 0.2}\n"
                "fused_artifact: outputs/demo-v1-fused.stl\n"
                "fusion_tool: bambu\n"
                "fusion_status: pending\n"
            )
            body_stl = outputs / "demo-v1-body.stl"
            head_stl = mesh_dir / "woman-head.stl"
            _write_watertight_tetrahedron(body_stl)
            _write_watertight_sphere(head_stl, center=(0.0, 0.0, 0.0), radius=0.3)

            with patch("bambu.mesh_fusion.repair_fused_mesh") as repair:
                repair.return_value = (
                    trimesh.creation.box(extents=[1, 1, 1]),
                    {
                        "watertight_manifold": True,
                        "open_edges": 0,
                        "non_manifold_edges": 0,
                    },
                )
                result = fuse_hybrid_project(
                    project,
                    revision="v1",
                    body_stl=body_stl,
                    outputs_root=outputs,
                )

            fused = outputs / "demo-v1-fused.stl"
            self.assertTrue(fused.exists())
            self.assertEqual(result["fused_stl"], str(fused))
            manifest = (design / "fusion_manifest.yaml").read_text()
            self.assertIn("fusion_status: complete", manifest)
            repair.assert_called_once()

    def test_fuse_mesh_cli(self):
        from bambu.cli import main
        import io

        with patch("bambu.mesh_fusion.fuse_hybrid_project") as fuse, patch(
            "bambu.projects.load_project", return_value={"slug": "demo", "current_revision": "v1"}
        ):
            fuse.return_value = {
                "body_stl": "outputs/demo-v1-body.stl",
                "fused_stl": "outputs/demo-v1-fused.stl",
                "heads": [{"id": "woman", "stub_center": [0, 0, 1], "target_width_mm": 20, "scale": 1.0, "sink_mm": 5}],
                "mesh": {"watertight_manifold": True, "open_edges": 0, "non_manifold_edges": 0},
            }
            output = io.StringIO()
            with patch("sys.stdout", output):
                code = main(["fuse-mesh", "projects/demo", "--revision", "v1"])
        self.assertEqual(code, 0)
        self.assertIn("Hybrid mesh fusion", output.getvalue())


if __name__ == "__main__":
    unittest.main()
