import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_mvp.py"
SPEC = importlib.util.spec_from_file_location("run_mvp", MODULE_PATH)
run_mvp = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(run_mvp)


class ExperimentMatrixTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T01",
            "mask_strategies": ["random", "stage", "discriminative"],
            "mask_intensities": [0.2, 0.4, 0.6],
            "random_seeds": [11, 23],
            "stage_mask_tags": ["stage:late"],
        }
        self.claims = [
            {"claim_id": f"E{i}", "tags": ["hideable", "stage:late" if i > 3 else "stage:early"]}
            for i in range(1, 11)
        ]

    def test_expands_strategy_intensity_seed_product(self):
        conditions = run_mvp.experiment_conditions(self.config)

        self.assertEqual(18, len(conditions))
        self.assertIn(("random", 0.2, 11), conditions)
        self.assertIn(("discriminative", 0.6, 23), conditions)

    def test_explicit_mask_intensity_overrides_case_default(self):
        hidden = run_mvp.build_hidden_claims(
            {**self.config, "mask_intensity": 0.2},
            self.claims,
            "random",
            seed=11,
            mask_intensity=0.6,
        )

        self.assertEqual(6, len(hidden))

    def test_run_id_contains_mask_intensity(self):
        run_id_low = run_mvp.make_run_id("T01", "random", 0.2, 11, "random")
        run_id_high = run_mvp.make_run_id("T01", "random", 0.6, 11, "random")

        self.assertNotEqual(run_id_low, run_id_high)
        self.assertIn("m020", run_id_low)
        self.assertIn("m060", run_id_high)

    def test_stage_mask_respects_requested_intensity(self):
        low = run_mvp.build_hidden_claims(
            self.config,
            self.claims,
            "stage",
            seed=11,
            mask_intensity=0.2,
        )
        high = run_mvp.build_hidden_claims(
            self.config,
            self.claims,
            "stage",
            seed=11,
            mask_intensity=0.6,
        )

        self.assertEqual(2, len(low))
        self.assertEqual(6, len(high))
        self.assertTrue({"E4", "E5"} <= high)


class MultiCaseRunnerTests(unittest.TestCase):
    def write_case(self, root, folder_name, case_id, complete=True):
        case_dir = root / folder_name
        case_dir.mkdir()
        (case_dir / "case_config.json").write_text(
            json.dumps({"case_id": case_id}),
            encoding="utf-8",
        )
        if complete:
            (case_dir / "evidence_claims.json").write_text("[]", encoding="utf-8")
            (case_dir / "acquisition_actions.json").write_text("[]", encoding="utf-8")
        return case_dir

    def test_discovers_complete_case_directories_in_sorted_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_case(root, "C02", "case-2")
            self.write_case(root, "C01", "case-1")
            self.write_case(root, "incomplete", "case-x", complete=False)

            discovered = run_mvp.discover_case_dirs(root)

            self.assertEqual(["C01", "C02"], [path.name for path in discovered])

    def test_duplicate_case_ids_are_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = self.write_case(root, "C01", "duplicate")
            second = self.write_case(root, "C02", "duplicate")

            with self.assertRaisesRegex(ValueError, "Duplicate case_id"):
                run_mvp.validate_unique_case_ids([first, second])


class StratifiedSummaryTests(unittest.TestCase):
    def test_distinguishes_independent_cases_from_repeated_runs(self):
        rows = [
            self.row("C01", 11, 1, 2),
            self.row("C01", 23, 0, 7),
            self.row("C02", 11, 1, 4),
            self.row("C02", 23, 1, 3),
        ]

        summary = run_mvp.summarize_stratified(rows)
        planner_summary = summary["overall_by_planner"]["project05_m1"]

        self.assertEqual(2, summary["design"]["independent_case_count"])
        self.assertEqual(4, summary["design"]["repeated_run_count"])
        self.assertEqual(2, planner_summary["independent_case_count"])
        self.assertEqual(4, planner_summary["repeated_run_count"])
        self.assertEqual(0.75, planner_summary["success_rate"])
        self.assertEqual(3.0, planner_summary["mean_cost_to_target"])

    def test_adds_oracle_relative_metrics_within_condition(self):
        rows = [
            {
                **self.row("C01", 11, 1, 2),
                "planner": "oracle_optimal",
                "actions_taken": "A|B",
            },
            {
                **self.row("C01", 11, 1, 3),
                "planner": "project05_m1",
                "actions_taken": "A|C",
            },
            {
                **self.row("C01", 11, 0, 7),
                "planner": "random",
                "actions_taken": "D",
            },
            {
                **self.row("C01", 11, 1, 0),
                "planner": "full_evidence",
                "actions_taken": "",
            },
        ]

        enriched = run_mvp.add_oracle_relative_metrics(rows)
        by_planner = {row["planner"]: row for row in enriched}

        self.assertEqual(
            1.0,
            by_planner["project05_m1"]["cost_regret_vs_oracle"],
        )
        self.assertEqual(
            1,
            by_planner["project05_m1"]["oracle_top1_action_hit"],
        )
        self.assertEqual(
            "",
            by_planner["random"]["cost_regret_vs_oracle"],
        )
        self.assertEqual(
            0,
            by_planner["random"]["oracle_top1_action_hit"],
        )
        self.assertEqual(
            "",
            by_planner["full_evidence"]["cost_regret_vs_oracle"],
        )
        self.assertEqual(
            "",
            by_planner["full_evidence"]["oracle_top1_action_hit"],
        )

    def test_registers_all_m1_ablation_variants(self):
        expected = {
            "m1_no_granularity",
            "m1_no_uncertainty",
            "m1_no_risk",
            "m1_no_coverage",
            "m1_no_cost",
        }

        self.assertTrue(expected <= set(run_mvp.PLANNERS))
        self.assertEqual(expected, set(run_mvp.M1_ABLATIONS))

    def test_exact_oracle_is_a_cost_lower_bound_on_c01(self):
        self.assertIn("oracle_optimal", run_mvp.PLANNERS)
        self.assertNotIn("oracle_greedy", run_mvp.PLANNERS)
        case_dir = Path(__file__).resolve().parents[1] / "examples" / "C01"

        rows, _ = run_mvp.execute_case(case_dir)
        comparable = [
            float(row["cost_regret_vs_oracle"])
            for row in rows
            if row["planner"] != "full_evidence"
            and row["cost_regret_vs_oracle"] != ""
        ]

        self.assertTrue(comparable)
        self.assertGreaterEqual(min(comparable), 0.0)

    @staticmethod
    def row(case_id, seed, reached_target, budget_used):
        return {
            "case_id": case_id,
            "mask_strategy": "random",
            "mask_intensity": 0.4,
            "seed": seed,
            "planner": "project05_m1",
            "reached_target": reached_target,
            "cost_to_target": budget_used if reached_target else "",
            "budget_used": budget_used,
            "steps_to_target": 1 if reached_target else "",
            "final_node_coverage": 1.0 if reached_target else 0.5,
        }


class CaseIntegrityTests(unittest.TestCase):
    def test_c01_c02_c03_references_are_complete(self):
        examples_dir = Path(__file__).resolve().parents[1] / "examples"
        for folder_name in ("C01", "C02", "C03"):
            with self.subTest(case=folder_name):
                case_dir = examples_dir / folder_name
                config = run_mvp.load_json(case_dir / "case_config.json")
                claims = run_mvp.load_json(case_dir / "evidence_claims.json")
                actions = run_mvp.load_json(
                    case_dir / "acquisition_actions.json"
                )

                claim_ids = [claim["claim_id"] for claim in claims]
                action_ids = [action["action_id"] for action in actions]
                hideable_ids = {
                    claim["claim_id"]
                    for claim in claims
                    if "hideable" in claim.get("tags", [])
                }

                self.assertEqual(len(claim_ids), len(set(claim_ids)))
                self.assertEqual(len(action_ids), len(set(action_ids)))
                for node in config["cti_nodes"]:
                    self.assertTrue(set(node["required_claim_ids"]) <= set(claim_ids))
                for action in actions:
                    self.assertTrue(
                        set(action["recoverable_claim_ids"]) <= hideable_ids
                    )
                self.assertTrue(
                    set(config["discriminative_claim_ids"]) <= hideable_ids
                )


class SupportCeilingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        case_dir = Path(__file__).resolve().parents[1] / "examples" / "C01"
        cls.config = run_mvp.load_json(case_dir / "case_config.json")
        cls.claims = run_mvp.load_json(case_dir / "evidence_claims.json")
        cls.actions = run_mvp.load_json(
            case_dir / "acquisition_actions.json"
        )
        cls.all_ids = {
            claim["claim_id"]
            for claim in cls.claims
        }

    def test_clamps_structural_granularity_to_support_ceiling(self):
        config = {
            **self.config,
            "target_granularity": "G2_tactic_intent",
            "support_ceiling": "G2_tactic_intent",
        }

        granularity = run_mvp.supportable_granularity(
            config,
            self.all_ids,
        )

        self.assertEqual("G2_tactic_intent", granularity)

    def test_reports_correct_stop_without_ceiling_violation(self):
        config = {
            **self.config,
            "target_granularity": "G2_tactic_intent",
            "support_ceiling": "G2_tactic_intent",
        }

        result, _ = run_mvp.run_episode(
            config,
            self.claims,
            self.actions,
            "random",
            0.2,
            11,
            "full_evidence",
        )

        self.assertEqual("G2_tactic_intent", result["final_granularity"])
        self.assertEqual("G2_tactic_intent", result["support_ceiling"])
        self.assertEqual(1, result["correct_stop"])
        self.assertEqual(0, result["ceiling_violation"])


class ActionFeedbackTests(unittest.TestCase):
    def test_exposes_zero_yield_feedback_after_action_execution(self):
        config = {
            "case_id": "T-feedback",
            "target_granularity": "G3_campaign",
            "budget_total": 3,
            "fixed_action_order": ["A-zero", "A-recover"],
            "cti_nodes": [
                {
                    "node_id": f"N{i}",
                    "stage": "execution" if i < 3 else "collection",
                    "required_claim_ids": [f"E{i}"],
                    "critical": False,
                }
                for i in range(1, 5)
            ],
            "cti_edges": [
                {"edge_id": "X1", "source": "N1", "target": "N2"},
                {"edge_id": "X2", "source": "N2", "target": "N3"},
                {"edge_id": "X3", "source": "N3", "target": "N4"},
            ],
            "granularity_order": [
                "G0_unknown",
                "G1_technique",
                "G2_tactic_intent",
                "G3_campaign",
                "G4_actor_cluster",
                "G5_named_actor",
            ],
            "discriminative_claim_ids": [],
            "stage_mask_tags": ["stage:execution"],
        }
        claims = [
            {
                "claim_id": f"E{i}",
                "source_type": "provenance_graph",
                "tags": ["hideable", "stage:execution"],
            }
            for i in range(1, 5)
        ]
        actions = [
            {
                "action_id": "A-zero",
                "action_type": "extend_log_window",
                "cost": 1,
                "recoverable_claim_ids": [],
                "expected_effects": {},
            },
            {
                "action_id": "A-recover",
                "action_type": "query_host_subgraph",
                "cost": 2,
                "recoverable_claim_ids": ["E1", "E2", "E3", "E4"],
                "expected_effects": {},
            },
        ]

        _, trace = run_mvp.run_episode(
            config,
            claims,
            actions,
            "random",
            0.5,
            11,
            "fixed_order",
        )

        self.assertGreaterEqual(len(trace), 2)
        self.assertEqual(
            [
                {
                    "action_id": "A-zero",
                    "action_type": "extend_log_window",
                    "recovered_count": 0,
                }
            ],
            trace[1]["state"]["action_feedback"],
        )


class PlannerInformationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        case_dir = Path(__file__).resolve().parents[1] / "examples" / "C01"
        cls.config = run_mvp.load_json(case_dir / "case_config.json")
        cls.claims = run_mvp.load_json(case_dir / "evidence_claims.json")
        cls.actions = run_mvp.load_json(case_dir / "acquisition_actions.json")
        all_ids = {claim["claim_id"] for claim in cls.claims}
        cls.visible_ids = all_ids - {"C01-EC-002", "C01-EC-011"}
        cls.state = run_mvp.build_state(
            cls.config,
            cls.claims,
            cls.actions,
            "boundary-test",
            0,
            "random",
            0.2,
            11,
            cls.visible_ids,
            {"C01-EC-002", "C01-EC-011"},
            set(),
            [],
            0,
        )

    def test_ordinary_planners_ignore_changed_hidden_outcomes(self):
        for planner in ("coverage_greedy", "project05_m1"):
            with self.subTest(planner=planner):
                first = self.select(planner, {"C01-EC-002"})
                second = self.select(planner, {"C01-EC-011"})
                self.assertEqual(first["action_id"], second["action_id"])

    def test_oracle_reacts_to_changed_hidden_outcomes(self):
        first = self.select("oracle_optimal", {"C01-EC-002"})
        second = self.select("oracle_optimal", {"C01-EC-011"})

        self.assertNotEqual(first["action_id"], second["action_id"])

    def test_cmi_proxy_uses_expected_uncertainty_reduction_per_cost(self):
        actions = [
            {
                "action_id": "expensive",
                "action_type": "other",
                "cost": 2,
                "recoverable_claim_ids": [],
                "expected_effects": {
                    "expected_uncertainty_reduction": 0.4,
                },
            },
            {
                "action_id": "efficient",
                "action_type": "other",
                "cost": 1,
                "recoverable_claim_ids": [],
                "expected_effects": {
                    "expected_uncertainty_reduction": 0.3,
                },
            },
        ]

        selected = run_mvp.select_action(
            "cmi_proxy",
            self.config,
            self.claims,
            actions,
            self.state,
            self.visible_ids,
            set(),
            [],
            11,
        )

        self.assertEqual("efficient", selected["action_id"])

    def select(self, planner, hidden_ids):
        return run_mvp.select_action(
            planner,
            self.config,
            self.claims,
            self.actions,
            self.state,
            self.visible_ids,
            hidden_ids,
            [],
            11,
        )


if __name__ == "__main__":
    unittest.main()
