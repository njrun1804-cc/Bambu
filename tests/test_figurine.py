import unittest


class FigurineTests(unittest.TestCase):
    def test_generates_two_brazil_supporter_figurines(self):
        from bambu.figurine import Figurine, Scene, generate_scad

        scene = Scene(
            title="World Cup neighbors",
            figures=[
                Figurine(
                    name="tall_neighbor",
                    height_mm=72,
                    body_shape="slim",
                    hair="short gray hair",
                    accessories=["glasses"],
                    jersey_number="10",
                ),
                Figurine(
                    name="smiling_neighbor",
                    height_mm=64,
                    body_shape="curvy",
                    hair="short light hair",
                    accessories=["sunglasses"],
                    jersey_number="9",
                ),
            ],
        )

        scad = generate_scad(scene)

        self.assertIn("module figurine", scad)
        self.assertIn("Brazil-inspired", scad)
        self.assertIn("tall_neighbor", scad)
        self.assertIn("smiling_neighbor", scad)
        self.assertIn("number_10", scad)
        self.assertIn("number_9", scad)
        self.assertIn("glasses", scad)

    def test_rejects_empty_scene(self):
        from bambu.figurine import Scene, generate_scad

        with self.assertRaisesRegex(ValueError, "at least one figurine"):
            generate_scad(Scene(title="empty", figures=[]))


if __name__ == "__main__":
    unittest.main()

