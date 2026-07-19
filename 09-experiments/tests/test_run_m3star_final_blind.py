import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_m3star_final_blind.py"
)
REPO_ROOT = SCRIPT.parents[2]
PROTOCOL = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "contracts"
    / "m3star-final-blind-protocol-v0.1.json"
)
TRAINING_COST_PROFILE = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "profiles"
    / "cost-replay-scan-equivalent-v0.1.json"
)
FROZEN_MODEL_RESULT = (
    REPO_ROOT
    / "09-experiments"
    / "results"
    / "m3star_measured_replay_majority_sixcase_v0.9"
)


def load_runner(testcase: unittest.TestCase):
    testcase.assertTrue(SCRIPT.is_file())
    spec = importlib.util.spec_from_file_location("run_m3star_final_blind", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_preflight_fixture(runner, root: Path, case_count: int = 96):
    cases_root = root / "cases"
    case_ids = [f"C{index:03d}-blind" for index in range(13, 13 + case_count)]
    file_hashes = {}
    cost_actions = []
    for case_id in case_ids:
        case_dir = cases_root / case_id
        action_id = f"{case_id}-AA-001"
        write_json(case_dir / "case_config.json", {"case_id": case_id})
        write_json(case_dir / "evidence_claims.json", [])
        write_json(
            case_dir / "acquisition_actions.json",
            [
                {
                    "action_id": action_id,
                    "action_type": "query_host_subgraph",
                    "cost": 1.0,
                }
            ],
        )
        file_hashes[case_id] = {
            filename: runner.sha256(case_dir / filename)
            for filename in runner.run_mvp.CASE_FILENAMES
        }
        cost_actions.append(
            {
                "case_id": case_id,
                "action_id": action_id,
                "measured_cost": 1.0,
            }
        )
    dataset_manifest = root / "dataset_manifest.json"
    write_json(
        dataset_manifest,
        {
            "status": "frozen",
            "curation_blind_to_model_development": True,
            "ground_truth_sealed_until_execution": True,
            "all_cases_new_and_unseen": True,
            "source_and_attack_chain_deduplication_complete": True,
            "case_count": len(case_ids),
            "case_ids": case_ids,
            "case_files_sha256": file_hashes,
        },
    )
    evaluation_cost_profile = root / "evaluation_cost_profile.json"
    write_json(
        evaluation_cost_profile,
        {
            "profile_id": "project05-final-blind-test-cost-v0.1",
            "version": "0.1.0",
            "status": "frozen",
            "regime": "measured",
            "scope": {"case_ids": case_ids},
            "scoring": {},
            "actions": cost_actions,
        },
    )
    return SimpleNamespace(
        cases_root=cases_root,
        case_ids=case_ids,
        dataset_manifest=dataset_manifest,
        evaluation_cost_profile=evaluation_cost_profile,
        output_dir=root / "output",
        ledger=root / "consumed.json",
    )


def run_preflight(runner, fixture, **overrides):
    arguments = {
        "protocol_path": PROTOCOL,
        "cases_root": fixture.cases_root,
        "dataset_manifest_path": fixture.dataset_manifest,
        "training_cost_profile_path": TRAINING_COST_PROFILE,
        "evaluation_cost_profile_path": fixture.evaluation_cost_profile,
        "frozen_model_result_dir": FROZEN_MODEL_RESULT,
        "output_dir": fixture.output_dir,
        "consumption_ledger": fixture.ledger,
    }
    arguments.update(overrides)
    return runner.preflight(**arguments)


class FinalBlindRunnerTests(unittest.TestCase):
    def test_case_boundary_parser_rejects_noncanonical_ids(self):
        runner = load_runner(self)
        self.assertEqual(13, runner.case_number("C13-unseen"))
        self.assertEqual(108, runner.case_number("C108-unseen"))
        self.assertIsNone(runner.case_number("case13"))

    def test_one_sided_upper_mean_handles_constant_superiority(self):
        runner = load_runner(self)
        self.assertEqual(-1.0, runner.one_sided_upper_mean([-1.0, -1.0, -1.0]))

    def test_case_level_intersection_union_gate_requires_every_baseline(self):
        runner = load_runner(self)
        protocol = {
            "sample_size": {"minimum_valid_complete_cases": 3},
            "analysis_gate": {"minimum_joint_success_conditions_per_case": 2},
        }
        rows = []
        for case_index in range(13, 16):
            for condition_index in range(2):
                common = {
                    "case_id": f"C{case_index}-blind",
                    "mask_strategy": "random",
                    "mask_intensity": 0.2,
                    "seed": condition_index,
                    "reached_target": 1,
                    "budget_total": 10,
                    "ceiling_violation": 0,
                }
                rows.append(
                    {
                        **common,
                        "planner": runner.m3_runner.CORE_METHOD,
                        "cost_to_target": 1.0,
                        "budget_used": 1.0,
                    }
                )
                for baseline in runner.PRIMARY_BASELINES:
                    rows.append(
                        {
                            **common,
                            "planner": baseline,
                            "cost_to_target": 2.0,
                            "budget_used": 2.0,
                        }
                    )

        passed = runner.analyze_final_rows(rows, protocol)

        self.assertTrue(passed["global_confirmatory_gate_pass"])
        self.assertTrue(passed["formal_external_superiority_claim_allowed"])
        self.assertTrue(
            all(
                result["all_gates_pass"]
                for result in passed["comparisons"].values()
            )
        )

        rows[0]["reached_target"] = 0
        failed = runner.analyze_final_rows(rows, protocol)
        self.assertFalse(failed["global_confirmatory_gate_pass"])
        self.assertGreater(
            failed["comparisons"][runner.PRIMARY_BASELINES[0]][
                "case_success_loss_count"
            ],
            0,
        )

    def test_frozen_protocol_and_complete_preflight_fixture_pass(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            checked = run_preflight(runner, fixture)

        self.assertEqual("ready_for_one_shot_execution", checked["status"])
        self.assertEqual(96, checked["case_count"])

    def test_preflight_rejects_dataset_file_hash_mismatch(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            first_case = fixture.cases_root / fixture.case_ids[0]
            write_json(first_case / "evidence_claims.json", [{"tampered": True}])

            with self.assertRaisesRegex(ValueError, "Dataset file hash mismatch"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_fewer_than_operational_target(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary), case_count=95)

            with self.assertRaisesRegex(ValueError, "95 cases; 96 are required"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_existing_consumption_ledger(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            fixture.ledger.write_text("already consumed\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "already been consumed"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_missing_frozen_model(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = build_preflight_fixture(runner, root)

            with self.assertRaisesRegex(ValueError, "Frozen model source is incomplete"):
                run_preflight(
                    runner,
                    fixture,
                    frozen_model_result_dir=root / "missing-model",
                )

    def test_preflight_rejects_training_profile_bound_as_evaluation_profile(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))

            with self.assertRaisesRegex(ValueError, "cost profiles must differ"):
                run_preflight(
                    runner,
                    fixture,
                    evaluation_cost_profile_path=TRAINING_COST_PROFILE,
                )

    def test_protocol_rejects_primary_baseline_mutation(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
            protocol["primary_baselines"] = protocol["primary_baselines"][:-1]
            changed_protocol = root / "changed_protocol.json"
            write_json(changed_protocol, protocol)

            with self.assertRaisesRegex(ValueError, "primary baselines differ"):
                runner.static_protocol_checks(
                    changed_protocol,
                    FROZEN_MODEL_RESULT,
                    TRAINING_COST_PROFILE,
                )


if __name__ == "__main__":
    unittest.main()
