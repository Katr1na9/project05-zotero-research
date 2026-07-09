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


if __name__ == "__main__":
    unittest.main()
