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

    def test_generates_display_quality_neighbor_cues_for_a1_mini(self):
        from bambu.cli import default_world_cup_scene
        from bambu.figurine import generate_scad

        scad = generate_scad(default_world_cup_scene())

        self.assertIn("A1 mini display-safe", scad)
        self.assertIn("module shared_watch_party_base", scad)
        self.assertIn("module jersey_paint_guides", scad)
        self.assertIn("module short_salt_pepper_hair", scad)
        self.assertIn("module swept_light_hair_with_clip", scad)
        self.assertIn("module crossbody_bag", scad)
        self.assertIn("supportless_pose", scad)
        self.assertIn("minimum raised detail target: 0.8mm", scad)
        self.assertIn("translate([-26.0", scad)
        self.assertIn("translate([26.0", scad)

    def test_default_scene_prints_dan_and_carrie_name_labels(self):
        from bambu.cli import default_world_cup_scene
        from bambu.figurine import generate_scad

        scene = default_world_cup_scene()
        scad = generate_scad(scene)

        self.assertEqual([figure.name for figure in scene.figures], ["Dan", "Carrie"])
        self.assertIn("module base_name_label", scad)
        self.assertIn('base_name_label(label="DAN"', scad)
        self.assertIn('base_name_label(label="CARRIE"', scad)
        self.assertIn('profile="tall_neighbor"', scad)
        self.assertIn('profile="smiling_neighbor"', scad)

    def test_default_scene_adds_supportless_soccer_scene_cues(self):
        from bambu.cli import default_world_cup_scene
        from bambu.figurine import generate_scad

        scad = generate_scad(default_world_cup_scene())

        self.assertIn("module soccer_ball", scad)
        self.assertIn("module shallow_goal_net", scad)
        self.assertIn("supportless raised base details", scad)
        self.assertIn("soccer_ball();", scad)
        self.assertIn("shallow_goal_net();", scad)

    def test_default_scene_embeds_base_contacts_to_avoid_floating_regions(self):
        from bambu.cli import default_world_cup_scene
        from bambu.figurine import generate_scad

        scad = generate_scad(default_world_cup_scene())

        self.assertIn("translate([0, -25.2, 3.92])", scad)
        self.assertIn("translate([x, -15.2, 3.92])", scad)
        self.assertIn("translate([-26.0, 0, 3.212])", scad)
        self.assertIn("translate([26.0, 0, 3.288])", scad)

    def test_rejects_empty_scene(self):
        from bambu.figurine import Scene, generate_scad

        with self.assertRaisesRegex(ValueError, "at least one figurine"):
            generate_scad(Scene(title="empty", figures=[]))


if __name__ == "__main__":
    unittest.main()
