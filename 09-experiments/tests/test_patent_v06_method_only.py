import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITING = ROOT / "08-writing"
WORK = WRITING / "patent-work"
DRAFT = WORK / "07-structured-draft-v0.6.json"
MAIN = WRITING / "patent-main-draft-v0.6-method-only-20260713.md"
CLAIMS = WORK / "06-claims-v0.6.txt"
AUTHORITY = WRITING / "AUTHORITATIVE-DOCUMENTS-20260713.md"


class PatentV06MethodOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DRAFT.read_text(encoding="utf-8"))
        cls.main = MAIN.read_text(encoding="utf-8")
        cls.claims_text = CLAIMS.read_text(encoding="utf-8-sig")

    def test_title_is_method_only(self):
        expected = "一种面向不完整安全证据的归因取证动作规划方法"
        self.assertEqual(self.data["title"], expected)
        self.assertTrue(self.main.startswith(f"# {expected}\n"))

    def test_only_nine_method_claims_exist(self):
        self.assertEqual([claim["number"] for claim in self.data["claims"]], list(range(1, 10)))
        self.assertEqual(
            [item["claim_number"] for item in self.data["claim_feature_map"]],
            list(range(1, 10)),
        )
        self.assertEqual(re.findall(r"(?m)^(\d+)\.\s", self.claims_text), [str(i) for i in range(1, 10)])

    def test_parallel_claim_categories_are_absent(self):
        self.assertNotIn("### 3. 系统、设备及介质权利要求", self.main)
        self.assertNotRegex(self.claims_text, r"(?m)^\d+\.\s+一种.*系统")
        self.assertNotIn("一种电子设备，包括处理器和存储器", self.claims_text)
        self.assertNotIn("一种计算机可读存储介质", self.claims_text)

    def test_computer_implemented_method_language_is_retained(self):
        independent = self.data["claims"][0]["text"]
        self.assertIn("由计算设备执行", independent)
        self.assertIn("获取攻击行为图", independent)

    def test_quality_record_identifies_method_only_architecture(self):
        findings = "\n".join(self.data["audit"]["consistency_findings"])
        architecture = self.data["quality_assessment"]["scores"]["claim_architecture"]["evidence"]
        self.assertIn("当前草稿仅保留方法权利要求", findings)
        self.assertIn("方法独立权利要求及八项从属", architecture)

    def test_authority_points_to_v06(self):
        authority = AUTHORITY.read_text(encoding="utf-8")
        self.assertIn("patent-main-draft-v0.6-method-only-20260713.md", authority)
        self.assertIn("patent-package-v0.6-method-only/", authority)
        self.assertIn("系统、设备及存储介质权利要求已删除", authority)

    def test_validation_report_passed(self):
        report = (WORK / "08-validation-report-v0.6.txt").read_text(encoding="utf-8")
        self.assertIn("PASS", report)


if __name__ == "__main__":
    unittest.main()
