import unittest
from pathlib import Path

import yaml


class WorldCupV4SpecTests(unittest.TestCase):
    def setUp(self):
        self.project = Path("projects/world-cup-neighbors")
        self.design = self.project / "designs" / "v4"

    def test_v4_specs_declare_blender_as_visual_source_of_truth(self):
        scene = yaml.safe_load((self.design / "scene.yaml").read_text())
        acceptance = yaml.safe_load((self.design / "acceptance.yaml").read_text())

        self.assertEqual(scene["generation"]["visual_source_of_truth"], "blender")
        self.assertEqual(scene["generation"]["cad_role"], "mechanical_validation_only")
        self.assertFalse(scene["safety"]["printer_contact_allowed"])
        self.assertIn("front", acceptance["required_views"])
        self.assertIn("dan-head", acceptance["required_views"])
        self.assertGreaterEqual(acceptance["minimum_scores"]["same_ballpark"], 7)

    def test_v4_visual_targets_point_to_real_chatgpt_concept_and_crops(self):
        visual_targets = yaml.safe_load((self.design / "visual_targets.yaml").read_text())

        target_path = self.project / visual_targets["primary_target"]["path"]
        self.assertTrue(target_path.exists())
        self.assertEqual(visual_targets["primary_target"]["role"], "visual_contract")
        self.assertEqual(set(visual_targets["crop_views"]), {"front", "front-angle", "dan-head", "carrie-head", "top"})

    def test_v4_people_encode_distinct_silhouette_requirements(self):
        people = yaml.safe_load((self.design / "people.yaml").read_text())
        by_id = {person["id"]: person for person in people["people"]}

        self.assertEqual(set(by_id), {"dan", "carrie"})
        self.assertEqual(by_id["dan"]["hair"]["style"], "short_side_part_swept")
        self.assertEqual(by_id["carrie"]["hair"]["style"], "rounded_bob_side_part")
        self.assertGreater(by_id["carrie"]["body"]["torso_width_mm"], by_id["dan"]["body"]["torso_width_mm"])
        for person in by_id.values():
            self.assertTrue(person["face"]["glasses"])
            self.assertGreaterEqual(person["face"]["glasses_frame_mm"], 1.2)


if __name__ == "__main__":
    unittest.main()
