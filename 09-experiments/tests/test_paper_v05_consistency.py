import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PAPER = (
    ROOT
    / "08-writing"
    / "paper-main-draft-v0.5-c11-external-validity-20260713.md"
)
AUTHORITY = ROOT / "08-writing" / "AUTHORITATIVE-DOCUMENTS-20260713.md"
RIGOR_REVIEW = ROOT / "08-writing" / "paper-main-rigor-review-v0.3-20260713.md"
CASE_DIR = (
    ROOT
    / "09-experiments"
    / "real_cases"
    / "C11-otrf-apt29-day1-scranton-nashua"
)
RESULT_ROOT = ROOT / "09-experiments" / "results"
MVP_PATH = ROOT / "09-experiments" / "scripts" / "run_mvp.py"
MVP_SPEC = importlib.util.spec_from_file_location("run_mvp_v05_test", MVP_PATH)
MVP = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(MVP)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PaperV05ConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = PAPER.read_text(encoding="utf-8")
        cls.and_summary = load_json(
            RESULT_ROOT
            / "c11_holdout_v0.1"
            / "c11-otrf-apt29-day1-scranton-nashua_mvp_summary.json"
        )
        cls.or_summary = load_json(
            RESULT_ROOT
            / "c11_or_sensitivity_v0.1"
            / "c11-otrf-apt29-day1-scranton-nashua_mvp_summary.json"
        )

    def test_authority_points_to_v05(self):
        authority = AUTHORITY.read_text(encoding="utf-8")
        self.assertIn(PAPER.name, authority)
        self.assertIn("唯一论文母本", authority)
        self.assertIn(RIGOR_REVIEW.name, authority)

    def test_authority_uses_internal_freeze_wording(self):
        authority = AUTHORITY.read_text(encoding="utf-8")
        self.assertIn("内部冻结 D1-D5", authority)
        self.assertNotIn("预注册 D1-D5", authority)

    def test_c11_table_matches_frozen_and_results(self):
        expected_rows = {
            "Oracle": "oracle_optimal",
            "Coverage greedy": "coverage_greedy",
            "M1": "project05_m1",
            "M3a": "project05_m3a_gap_compat",
            "M2": "project05_m2",
        }
        for label, planner in expected_rows.items():
            row = self.and_summary[planner]
            with self.subTest(planner=planner):
                self.assertIn(
                    f"| {label} | {row['success_rate']:.4f} | "
                    f"{row['mean_cost_to_target']:.4f} |",
                    self.paper,
                )
                self.assertEqual(45, row["runs"])

    def test_c11_or_and_cost_claim_matches_outputs(self):
        and_cost = self.and_summary["project05_m2"]["mean_cost_to_target"]
        or_cost = self.or_summary["project05_m2"]["mean_cost_to_target"]
        self.assertIn(
            f"平均成本却从 {and_cost:.4f} 降至 {or_cost:.4f}",
            self.paper,
        )
        self.assertAlmostEqual(or_cost - and_cost, -2.6445, places=4)

    def test_c11_is_not_merged_with_the_g3_main_mean(self):
        self.assertIn("C11 不并入 G3 主结果均值", self.paper)
        self.assertIn("不把其成本与 C07-C10 求总均值", self.paper)
        self.assertIn("并非最低成本规则", self.paper)
        self.assertNotIn("225 个独立攻击", self.paper)

    def test_holdout_wording_does_not_imply_natural_apt_incidents(self):
        self.assertIn("参数锁定攻击轨迹留出", self.paper)
        self.assertNotIn("图2｜真实留出", self.paper)

    def test_c11_scope_and_unrun_methods_are_explicit(self):
        self.assertIn("不是第三方注册平台可验证的 preregistration", self.paper)
        self.assertIn("不是独立网络传感器 corroboration", self.paper)
        self.assertIn("不能单独证明网络外传", self.paper)
        self.assertIn(
            "XGBoost、AFA-VOI 与 Depth-2 未在 C11 上运行",
            self.paper,
        )

    def test_rigor_review_preserves_the_same_scope_boundaries(self):
        review = RIGOR_REVIEW.read_text(encoding="utf-8")
        self.assertIn("Top 安全 venue 仍为 Weak Reject", review)
        self.assertIn("不能作为 45 个独立攻击样本", review)
        self.assertIn("M2 只称 C07-C10 的透明部署锚点", review)
        self.assertIn("LLM 未进入主实验", review)

    def test_annotation_counts_match_manifest_and_remain_unlabeled(self):
        manifest = load_json(
            ROOT
            / "09-experiments"
            / "annotation"
            / "c07_c11_v0.2"
            / "packet_manifest.json"
        )
        self.assertFalse(manifest["human_labels_present"])
        self.assertEqual("awaiting_annotations", manifest["annotation_status"])
        self.assertIn(
            f"{manifest['claim_item_count']} 个 claim、"
            f"{manifest['intent_item_count']} 个公开意图和 "
            f"{manifest['granularity_item_count']} 个粒度状态",
            self.paper,
        )
        self.assertIn(
            f"共 {manifest['annotation_item_total']} 个 item",
            self.paper,
        )

    def test_runtime_planner_views_enforce_paper_boundary(self):
        actions = load_json(CASE_DIR / "acquisition_actions.json")
        action_view = MVP.planner_action_view(actions[0])
        self.assertNotIn("recoverable_claim_ids", action_view)
        self.assertNotIn("notes", action_view)

        state_view = MVP.planner_state_view(
            {
                "case_id": "C11-test",
                "step_index": 0,
                "visible_claim_ids": [],
                "hidden_claim_ids": ["secret"],
                "mask_strategy": "discriminative",
                "random_seed": 11,
            }
        )
        self.assertNotIn("hidden_claim_ids", state_view)
        self.assertNotIn("mask_strategy", state_view)
        self.assertNotIn("random_seed", state_view)


if __name__ == "__main__":
    unittest.main()
