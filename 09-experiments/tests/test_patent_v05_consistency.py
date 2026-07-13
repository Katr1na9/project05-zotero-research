import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITING = ROOT / "08-writing"
WORK = WRITING / "patent-work"
DRAFT = WORK / "07-structured-draft-v0.5.json"
MAIN = WRITING / "patent-main-draft-v0.5-20260713.md"
AUTHORITY = WRITING / "AUTHORITATIVE-DOCUMENTS-20260713.md"


class PatentV05ConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DRAFT.read_text(encoding="utf-8"))
        cls.main = MAIN.read_text(encoding="utf-8")

    def test_claims_are_exactly_frozen_from_v04(self):
        old = (WORK / "06-claims-v0.4.txt").read_bytes()
        new = (WORK / "06-claims-v0.5.txt").read_bytes()
        self.assertEqual(new, old)

    def test_structured_package_contract_is_complete(self):
        self.assertEqual([claim["number"] for claim in self.data["claims"]], list(range(1, 13)))
        self.assertEqual([figure["number"] for figure in self.data["figures"]], [1, 2, 3, 4, 5])
        self.assertEqual(len(self.data["claim_feature_map"]), 12)

    def test_incremental_sources_and_optional_feature_are_traced(self):
        source_ids = {source["id"] for source in self.data["source_map"]}
        self.assertTrue({"P010", "P011", "P012", "P013", "C007"}.issubset(source_ids))
        feature = next(item for item in self.data["evidence_ledger"] if item["id"] == "F010")
        self.assertIn("optional embodiment", feature["technical_role"])
        claimed_ids = {
            evidence_id
            for item in self.data["claim_feature_map"]
            for evidence_id in item["evidence_ids"]
        }
        self.assertNotIn("F010", claimed_ids)

    def test_independent_claims_remain_implementation_neutral(self):
        independent = "\n".join(
            claim["text"] for claim in self.data["claims"] if claim["number"] in {1, 10}
        )
        for forbidden in (
            "LLM",
            "大语言模型",
            "DQN",
            "XGBoost",
            "AFA",
            "WinRegRL",
            "WitFoo",
            "DARPA",
            "OpTC",
        ):
            self.assertNotIn(forbidden, independent)

    def test_specification_contains_new_boundaries(self):
        for required in (
            "#### 5.8 真实安全事件实施例",
            "#### 5.9 多源证据来源核验实施例",
            "#### 5.10 可选语义编译接口",
            "13119",
            "不对三组案例计算混合平均值",
            "不据此主张任一具体规划器在所有场景中普遍降低成本",
        ):
            self.assertIn(required, self.main)

    def test_authority_points_to_v05(self):
        authority = AUTHORITY.read_text(encoding="utf-8")
        self.assertIn("patent-main-draft-v0.5-20260713.md", authority)
        self.assertIn("patent-package-v0.5/", authority)
        self.assertIn("patent-claim-collision-matrix-v0.3-20260713.md", authority)

    def test_validation_report_passed(self):
        report = (WORK / "08-validation-report-v0.5.txt").read_text(encoding="utf-8")
        self.assertIn("PASS", report)


if __name__ == "__main__":
    unittest.main()
