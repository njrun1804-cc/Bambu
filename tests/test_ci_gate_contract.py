import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class CheckGateContractTests(unittest.TestCase):
    def test_unittest_gate_rejects_zero_collected_tests(self) -> None:
        check = (ROOT / "scripts" / "check.sh").read_text()
        self.assertIn("countTestCases()", check)
        self.assertIn("No unittest tests collected", check)
