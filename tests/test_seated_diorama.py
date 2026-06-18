import unittest


class SeatedDioramaTests(unittest.TestCase):
    def test_dog_geometry_is_single_solid(self):
        from bambu.cad.animals import validate_dog_geometry

        validate_dog_geometry()

    def test_seated_diorama_builds_single_solid(self):
        from bambu.cad.archetypes.seated_diorama import build_seated_diorama

        scene = build_seated_diorama()
        self.assertEqual(len(scene.solids()), 1)

    def test_best_buds_model_exports_bounding_box(self):
        from bambu.cad import load_build123d_model

        model = load_build123d_model("projects/best-buds-chair/source/v1/model.py")
        box = model.bounding_box()
        self.assertLessEqual(float(box.size.X), 125)
        self.assertLessEqual(float(box.size.Y), 70)
        self.assertLessEqual(float(box.size.Z), 70)


if __name__ == "__main__":
    unittest.main()
