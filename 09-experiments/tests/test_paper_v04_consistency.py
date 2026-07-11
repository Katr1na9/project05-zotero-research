import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "08-writing" / "paper-main-draft-v0.4-major-revision-20260711.md"
BIB = ROOT / "08-writing" / "paper-main-references-v0.3.bib"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PaperV04ConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = PAPER.read_text(encoding="utf-8")

    def test_title_and_scope_do_not_claim_actor_attribution_sota(self):
        self.assertIn("# 不完整证据下的 APT 调查控制", self.paper)
        self.assertIn("本文不声称提高了攻击者识别准确率", self.paper)
        self.assertIn("不是新的 actor attribution SOTA", self.paper)
        self.assertNotIn("180 个独立攻击", self.paper)
        self.assertNotIn("M2 是全局最优", self.paper)

    def test_sequential_policy_table_matches_frozen_results(self):
        summary = load_json(
            ROOT
            / "09-experiments"
            / "results"
            / "xgboost_c01_c06_train_c07_c10_test"
            / "xgboost_experiment_summary.json"
        )["policy_summary"]["overall_by_planner"]
        m2 = summary["project05_m2"]
        xgb = summary["project05_xgboost_policy"]
        m3a = summary["project05_m3a_gap_compat"]

        self.assertIn(
            f"| **M2** | **{m2['success_rate']:.4f}** | "
            f"**{m2['mean_cost_to_target']:.4f}** | **{m2['mean_cost_regret_vs_oracle']:.4f}**",
            self.paper,
        )
        self.assertIn(
            f"| XGBoost | **{xgb['success_rate']:.4f}** | "
            f"{xgb['mean_cost_to_target']:.4f} | {xgb['mean_cost_regret_vs_oracle']:.4f}",
            self.paper,
        )
        self.assertIn(
            f"| M3a | {m3a['success_rate']:.4f} | "
            f"{m3a['mean_cost_to_target']:.4f} | {m3a['mean_cost_regret_vs_oracle']:.4f}",
            self.paper,
        )

    def test_afa_claims_match_frozen_results(self):
        result_root = (
            ROOT / "09-experiments" / "results" / "afa_voi_c07_c10_v0.1"
        )
        summary = load_json(result_root / "afa_voi_policy_summary.json")
        paired = load_json(result_root / "afa_voi_paired_vs_m2.json")
        m2 = summary["overall_by_planner"]["project05_m2"]
        afa = summary["overall_by_planner"]["afa_voi_myopic"]
        comparison = paired["afa_voi_myopic"]

        self.assertEqual(summary["design"]["independent_case_count"], 4)
        self.assertEqual(summary["design"]["repeated_run_count"], 720)
        self.assertIn(
            f"平均成功成本比 M2 高 "
            f"{comparison['mean_cost_difference_vs_m2_on_joint_success']:.4f}",
            self.paper,
        )
        self.assertIn(
            f"逐条件比较均为 {comparison['cost_wins_vs_m2']} 次成本胜、"
            f"{comparison['cost_ties_vs_m2']} 次平、"
            f"{comparison['cost_losses_vs_m2']} 次负",
            self.paper,
        )
        self.assertAlmostEqual(
            afa["mean_cost_to_target"] - m2["mean_cost_to_target"], 0.4389, places=4
        )

    def test_sensitivity_claims_match_frozen_results(self):
        result_root = ROOT / "09-experiments" / "results" / "m2_sensitivity_v0.1"
        weights = load_json(result_root / "m2_weight_comparison.json")
        dev = load_json(result_root / "coverage_semantics_dev_summary.json")

        unchanged = [
            row
            for row in weights.values()
            if row["first_action_agreement_rate"] == 1.0
            and row["mean_cost_difference_vs_base"] == 0.0
        ]
        changed = [
            row
            for row in weights.values()
            if row["first_action_agreement_rate"] == 0.8778
            and row["mean_cost_difference_vs_base"] == 0.0222
        ]
        self.assertEqual(len(unchanged), 13)
        self.assertEqual(len(changed), 3)
        self.assertIn("13 个变体与原始 M2", self.paper)
        self.assertIn(
            f"M2 success 从 "
            f"{dev['OR_default']['project05_m2']['success_rate']:.4f} 降至 "
            f"{dev['AND_default']['project05_m2']['success_rate']:.4f}",
            self.paper,
        )

    def test_every_pandoc_citation_key_exists_in_bibliography(self):
        citation_keys = set(re.findall(r"@([A-Za-z0-9_.:-]+)", self.paper))
        bibliography = BIB.read_text(encoding="utf-8")
        bib_keys = set(re.findall(r"@\w+\{([^,]+),", bibliography))
        self.assertEqual(citation_keys - bib_keys, set())


if __name__ == "__main__":
    unittest.main()
