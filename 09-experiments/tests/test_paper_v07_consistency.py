import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WRITING = ROOT / "08-writing"
RESULTS = ROOT / "09-experiments" / "results"
PAPER = WRITING / "paper-main-draft-v0.7-c12-operational-stress-20260713.md"
AUTHORITY = WRITING / "AUTHORITATIVE-DOCUMENTS-20260713.md"
AUTHORING = WRITING / "paper-main-authoring-record-v0.7-20260713.md"
REVIEWER_RESPONSE = WRITING / "reviewer-response-major-revision-v0.3-20260713.md"
RIGOR_REVIEW = WRITING / "paper-main-rigor-review-v0.5-20260713.md"
BIBLIOGRAPHY = WRITING / "paper-main-references-v0.3.bib"
C12_CASE = ROOT / "09-experiments" / "real_cases" / "C12-witfoo-precinct6-f10c7270"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class PaperV07ConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.paper = PAPER.read_text(encoding="utf-8")
        cls.authority = AUTHORITY.read_text(encoding="utf-8")
        cls.extended = load_json(
            RESULTS / "c12_extended_policies_v0.1" / "summary.json"
        )
        cls.rows = {row["planner"]: row for row in cls.extended["planner_results"]}
        cls.screen = load_json(
            RESULTS / "c12_witfoo_screen_v0.1" / "candidate_index.json"
        )
        cls.event_audit = load_json(
            RESULTS / "c12_witfoo_event_audit_v0.1" / "audit.json"
        )
        cls.external_audit = load_json(
            RESULTS / "external_afa_baseline_audit_v0.1" / "audit.json"
        )

    def test_v07_package_is_preserved_as_history(self):
        for path in (PAPER, AUTHORING, REVIEWER_RESPONSE, RIGOR_REVIEW):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
        self.assertNotIn(PAPER.name, self.authority)
        self.assertIn("论文 v0.8 为唯一母本", self.authority)

    def test_c12_remains_a_separate_single_incident_g1_stress(self):
        self.assertIn("C12 始终作为单独的 G1 运营数据压力", self.paper)
        self.assertIn("二者均不并入 C07-C10 的 G3 主结果均值", self.paper)
        self.assertIn("独立单位仍只有一个生产 SOC incident", self.paper)
        self.assertIn("不能作为独立攻击样本重新计数", self.paper)
        self.assertNotIn("45 个真实攻击", self.paper)
        self.assertEqual(1, self.extended["design"]["independent_incident_count"])
        self.assertEqual(45, self.extended["design"]["repeated_condition_count"])
        self.assertEqual("G1_technique", self.extended["design"]["target_granularity"])

    def test_c12_screen_and_event_gate_claims_match_outputs(self):
        self.assertEqual(13119, self.screen["counts"]["records_scanned"])
        self.assertEqual(5, self.screen["counts"]["selected"])
        gates = self.event_audit["candidate_gates"]
        self.assertEqual(2, sum(row["lead_recoverability_pass"] for row in gates))
        self.assertIn("13,119 条模板报告中保留 5 条候选", self.paper)
        self.assertIn("最终 2 条通过", self.paper)
        self.assertIn("产品标签多源、原始事件单源", self.paper)

    def test_c12_selected_source_and_projection_boundary_match(self):
        selected = self.event_audit["decision"]["selected_primary_incident_id"]
        self.assertEqual("f10c7270-1228-11ed-99ed-adca11e4059c", selected)
        incident = next(
            row
            for row in self.event_audit["incident_scan"]["incidents"]
            if row["incident_id"] == selected
        )
        self.assertEqual(119, incident["extracted_lead_count"])
        self.assertEqual(117, incident["lead_products"]["ASA Firewall"])
        self.assertEqual(2, incident["lead_products"]["Windows Active Directory"])
        graph = next(
            row
            for row in self.event_audit["graphml_audits"]
            if row["incident_id"] == selected
        )
        self.assertTrue(graph["projection_only"])
        self.assertEqual(49, graph["edge_types"]["INCIDENT_LINK"])
        self.assertEqual(0, graph["telemetry_edge_count"])
        self.assertIn("117 条来自 ASA Firewall，2 条来自 Windows AD", self.paper)
        self.assertIn("49 条 GraphML 边全部是 `INCIDENT_LINK`", self.paper)

    def test_cached_source_audit_does_not_fabricate_byte_offsets(self):
        scan = self.event_audit["incident_scan"]
        self.assertEqual(5, scan["cache_hit_count"])
        self.assertTrue(all(value is None for value in scan["byte_offsets"].values()))
        self.assertEqual([], scan["missing_incident_ids"])

    def test_c12_table_matches_frozen_transfer_results(self):
        labels = {
            "Oracle": "oracle_optimal",
            "Depth-2 Public": "project05_depth2_public",
            "AFA-VOI Rollout-H3": "afa_voi_rollout_h3",
            "XGBoost（C01-C06 冻结迁移）": "project05_xgboost_policy",
            "Logistic（C01-C06 冻结迁移）": "project05_m3b_policy",
            "M2": "project05_m2",
            "AFA-VOI Myopic": "afa_voi_myopic",
        }
        paired = self.extended["paired_vs_m2"]
        for label, planner in labels.items():
            row = self.rows[planner]
            with self.subTest(planner=planner):
                self.assertIn(
                    f"| {label} | {row['success_rate']:.4f} | "
                    f"{row['mean_cost_to_target']:.4f} |",
                    self.paper,
                )
                self.assertEqual(45, row["repeated_run_count"])
                self.assertEqual(0.0, row["ceiling_violation_rate"])
        depth2 = paired["project05_depth2_public"]
        self.assertEqual((12, 33, 0), (
            depth2["cost_wins_vs_m2"],
            depth2["cost_ties_vs_m2"],
            depth2["cost_losses_vs_m2"],
        ))
        self.assertIn("12 次成本胜、33 次平、0 次负", self.paper)

    def test_c12_case_has_no_actor_or_attack_mapping_gold(self):
        config = load_json(C12_CASE / "case_config.json")
        claims = load_json(C12_CASE / "evidence_claims.json")
        self.assertEqual("G1_technique", config["target_granularity"])
        self.assertEqual("G1_technique", config["support_ceiling"])
        self.assertTrue(
            all(not claim["mapped_tactic"] and not claim["mapped_technique"] for claim in claims)
        )
        self.assertIn("不表示系统正确识别了 ATT&CK technique ID", self.paper)
        self.assertIn("不是新的 APT actor benchmark", self.paper)

    def test_external_audit_forbids_same_task_claim(self):
        self.assertTrue(self.external_audit["source_gate"]["pass"])
        self.assertTrue(self.external_audit["action_family_gate"]["pass"])
        decision = self.external_audit["comparability_decision"]
        self.assertFalse(decision["direct_same_task_claim_allowed"])
        self.assertIn("不制造 AFABench、AACO 或 WinRegRL 的“官方同任务复现”结果", self.paper)
        self.assertIn("任务等价性不通过", self.paper)

    def test_new_references_are_present(self):
        bibliography = BIBLIOGRAPHY.read_text(encoding="utf-8")
        for key in (
            "schutz_afabench_2026",
            "valancius_acquisition_2024",
            "witfoo_precinct6_2025",
        ):
            with self.subTest(key=key):
                self.assertIn(key, bibliography)
                self.assertIn(f"@{key}", self.paper)

    def test_rigor_review_keeps_reviewer_posture_and_red_lines(self):
        review = RIGOR_REVIEW.read_text(encoding="utf-8")
        self.assertIn("Top 安全 venue 仍为 Weak Reject", review)
        self.assertIn("C12 只称生产 SOC 衍生", review)
        self.assertIn("45 个 C12 条件不得重计为 45 个真实攻击", review)
        self.assertIn("LLM 未进入主实验", review)


if __name__ == "__main__":
    unittest.main()
