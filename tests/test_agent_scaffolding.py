import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


class AgentScaffoldingTests(unittest.TestCase):
    def test_public_agents_directory_describes_mcp_and_safety_boundary(self):
        readme = (REPO / "agents" / "README.md").read_text()

        self.assertIn("bambu-mcp", readme)
        self.assertIn("does not start print jobs", readme)
        self.assertIn("private/", readme)

    def test_codex_agent_uses_bambu_mcp(self):
        maker = (REPO / ".codex" / "agents" / "bambu-maker.toml").read_text()

        self.assertIn("bambu-maker", maker)
        self.assertIn("bambu-mcp", maker)
        self.assertIn("manual approval", maker)

    def test_shared_skill_points_agents_to_safe_workflow(self):
        skill = (REPO / ".agents" / "skills" / "bambu-operate" / "SKILL.md").read_text()

        self.assertIn("bambu_doctor", skill)
        self.assertIn("bambu_generate_world_cup_figurines", skill)
        self.assertIn("Do not start print jobs", skill)


if __name__ == "__main__":
    unittest.main()

