import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "08-writing" / "patent-work" / "07-structured-draft-v0.4.json"


class PatentStructuredDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DRAFT.read_text(encoding="utf-8"))

    def test_claims_and_maps_are_complete(self):
        claims = self.data["claims"]
        self.assertEqual([claim["number"] for claim in claims], list(range(1, 13)))
        mapped = {item["claim_number"] for item in self.data["claim_feature_map"]}
        self.assertEqual(mapped, set(range(1, 13)))

    def test_figures_and_abstract_meet_package_contract(self):
        figures = self.data["figures"]
        self.assertEqual([figure["number"] for figure in figures], [1, 2, 3, 4, 5])
        abstract_figure = next(
            figure
            for figure in figures
            if figure["number"] == self.data["abstract_figure_number"]
        )
        self.assertTrue(abstract_figure["complete_claim_flow"])
        self.assertLessEqual(len("".join(self.data["abstract"].split())), 300)

    def test_unsupported_models_are_absent_from_independent_claims(self):
        independent = "\n".join(
            claim["text"] for claim in self.data["claims"] if claim["number"] in {1, 10}
        )
        for forbidden in ("LLM", "大语言模型", "DQN", "XGBoost", "DARPA", "OpTC"):
            self.assertNotIn(forbidden, independent)


if __name__ == "__main__":
    unittest.main()
