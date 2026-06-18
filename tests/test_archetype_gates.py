import unittest

from bambu.design_pipeline import load_archetype_profile, load_design_spec, validate_design_spec


class ArchetypeGateTests(unittest.TestCase):
    def test_seated_diorama_profile_loads(self):
        profile = load_archetype_profile("seated_diorama")
        self.assertEqual(profile["id"], "seated_diorama")
        self.assertIn("chair", [e["id"] for e in profile["required_scene_elements"]])

    def test_missing_chair_fails_seated_diorama_gate(self):
        spec = load_design_spec("projects/best-buds-chair", revision="v1")
        design = spec["files"]["design"]
        design["scene"] = {"props": ["base"]}
        design["must_preserve"] = []
        report = validate_design_spec(spec)
        self.assertFalse(report["ok"])
        self.assertTrue(any("chair" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
