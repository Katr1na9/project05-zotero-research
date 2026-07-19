import importlib.util
import hashlib
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
    / "m3star-final-blind-protocol-v0.2.json"
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


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_preflight_fixture(runner, root: Path, case_count: int = 79):
    cases_root = root / "cases"
    case_ids = [f"C{index:03d}-blind" for index in range(13, 13 + case_count)]
    file_hashes = {}
    cost_actions = []
    case_provenance = []
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
        case_provenance.append(
            {
                "case_id": case_id,
                "source_cluster_id": f"source-cluster-{case_id}",
                "source_release_id": f"source-release-{case_id}",
                "source_record_locator": f"sealed-record/{case_id}",
                "source_artifact_sha256": digest(f"source-artifact-{case_id}"),
                "scenario_family_id": f"scenario-family-{case_id}",
                "attack_chain_definition_sha256": digest(
                    f"attack-chain-{case_id}"
                ),
                "campaign_execution_id": f"campaign-execution-{case_id}",
                "campaign_execution_sha256": digest(
                    f"campaign-execution-{case_id}"
                ),
                "telemetry_capture_id": f"telemetry-capture-{case_id}",
                "telemetry_capture_sha256": digest(
                    f"telemetry-capture-{case_id}"
                ),
                "event_namespace_id": f"event-namespace-{case_id}",
                "independent_unit": "whole_campaign_execution",
                "independence_basis": (
                    "unique_attack_chain_definition_and_execution"
                ),
                "original_telemetry_present": True,
                "multi_stage_attack_chain_present": True,
                "full_campaign_time_window_included": True,
                "all_in_scope_campaign_hosts_combined": True,
                "not_a_host_slice": True,
                "not_a_time_slice": True,
                "not_a_mask_variant": True,
                "not_a_parameter_only_variant": True,
                "not_used_in_model_development": True,
                "ground_truth_sealed": True,
                "cost_values_sealed_from_model_development": True,
                "ground_truth_seal_id": f"ground-truth-seal-{case_id}",
                "cost_measurement_seal_id": f"cost-seal-{case_id}",
                "parent_campaign_execution_id": None,
                "derived_from_case_id": None,
                "mask_variant_of_case_id": None,
                "parameter_variant_of_scenario_family_id": None,
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
            "intake_contract_version": "0.1.0",
            "case_count": len(case_ids),
            "case_ids": case_ids,
            "case_files_sha256": file_hashes,
            "curation_and_seal_separation": {
                "curation_team_id": "fixture-curation-team",
                "model_development_team_id": "fixture-model-team",
                "ground_truth_custodian_id": "fixture-ground-truth-custodian",
                "teams_are_disjoint": True,
                "curators_blind_to_model_outputs": True,
                "model_developers_blind_to_c13_plus_contents": True,
                "ground_truth_custodian_not_a_model_developer": True,
                "cost_measurement_completed_without_model_output_access": True,
            },
            "independence_review": {
                "whole_campaign_execution_is_the_counting_unit": True,
                "host_time_mask_and_parameter_slices_forbidden": True,
                "same_scenario_family_counted_once": True,
                "prior_campaign_overlap_review_complete": True,
                "source_cluster_recorded_for_sensitivity_analysis": True,
                "used_campaign_registry_sha256": runner.sha256(
                    runner.REPO_ROOT
                    / runner.USED_CAMPAIGN_REGISTRY_RELATIVE_PATH
                ),
            },
            "case_provenance": case_provenance,
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
    amendment_path = runner.REPO_ROOT / runner.STAGED_ACQUISITION_AMENDMENT_RELATIVE_PATH
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    audited_count = max(81, case_count)
    qualification_readiness = root / "qualification_readiness.json"
    write_json(
        qualification_readiness,
        {
            "status": "qualification_complete",
            "acquisition_complete": True,
            "source_search_required": False,
            "candidate_upper_bound": 95,
            "audited_candidate_count": audited_count,
            "actual_qualified_case_count": case_count,
            "actual_not_qualified_count": audited_count - case_count,
            "unaudited_reserve_count": 95 - audited_count,
            "decision_basis": "stop_after_phase_1_minimum_reached",
            "all_qualified_cases_to_be_retained": True,
            "unaudited_reserve_slots_counted_as_failures": False,
            "amendment_id": amendment["amendment_id"],
            "amendment_sha256": runner.sha256(amendment_path),
            "file_contents_returned_to_model_development": False,
            "ground_truth_opened": False,
            "cost_values_opened": False,
            "model_outputs_opened_during_qualification": False,
            "one_shot_evaluation_consumed": False,
        },
    )
    commitment = digest("fixture-qualified-case-identity-commitment")
    qualification_binding = root / "qualification_binding.json"
    write_json(
        qualification_binding,
        {
            "status": "qualification_manifest_binding_complete",
            "staged_amendment_id": amendment["amendment_id"],
            "staged_amendment_sha256": runner.sha256(amendment_path),
            "qualification_readiness_sha256": runner.sha256(
                qualification_readiness
            ),
            "dataset_manifest_sha256": runner.sha256(dataset_manifest),
            "qualified_case_count": case_count,
            "final_manifest_case_count": case_count,
            "qualified_case_identity_commitment_sha256": commitment,
            "manifest_case_identity_commitment_sha256": commitment,
            "identity_sets_match_exactly": True,
            "all_qualified_cases_retained": True,
            "unaudited_reserve_slots_counted_as_failures": False,
            "telemetry_contents_opened_by_binding_audit": False,
            "ground_truth_opened": False,
            "cost_values_opened": False,
            "model_outputs_opened": False,
            "one_shot_evaluation_consumed": False,
        },
    )
    return SimpleNamespace(
        cases_root=cases_root,
        case_ids=case_ids,
        dataset_manifest=dataset_manifest,
        evaluation_cost_profile=evaluation_cost_profile,
        qualification_readiness=qualification_readiness,
        qualification_binding=qualification_binding,
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
        "qualification_readiness_path": fixture.qualification_readiness,
        "qualification_binding_path": fixture.qualification_binding,
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
        self.assertEqual(79, checked["case_count"])
        self.assertEqual(
            79,
            checked["intake_identity_audit"]["unique_campaign_execution_count"],
        )
        self.assertFalse(checked["intake_identity_audit"]["ground_truth_opened"])

    def test_preflight_rejects_dataset_file_hash_mismatch(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            first_case = fixture.cases_root / fixture.case_ids[0]
            write_json(first_case / "evidence_claims.json", [{"tampered": True}])

            with self.assertRaisesRegex(ValueError, "Dataset file hash mismatch"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_fewer_than_power_minimum(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary), case_count=78)

            with self.assertRaisesRegex(ValueError, "between 79 and 95"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_manifest_that_drops_a_qualified_case(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            readiness = json.loads(
                fixture.qualification_readiness.read_text(encoding="utf-8")
            )
            readiness["actual_qualified_case_count"] = 80
            readiness["actual_not_qualified_count"] = 1
            write_json(fixture.qualification_readiness, readiness)

            with self.assertRaisesRegex(ValueError, "exactly all qualified cases"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_unmatched_identity_binding(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            binding = json.loads(
                fixture.qualification_binding.read_text(encoding="utf-8")
            )
            binding["identity_sets_match_exactly"] = False
            write_json(fixture.qualification_binding, binding)

            with self.assertRaisesRegex(ValueError, "identity_sets_match_exactly"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_existing_consumption_ledger(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            fixture.ledger.write_text("already consumed\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "already been consumed"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_same_scenario_parameter_variants(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            manifest = json.loads(
                fixture.dataset_manifest.read_text(encoding="utf-8")
            )
            manifest["case_provenance"][1]["scenario_family_id"] = manifest[
                "case_provenance"
            ][0]["scenario_family_id"]
            write_json(fixture.dataset_manifest, manifest)

            with self.assertRaisesRegex(ValueError, "Duplicate scenario family"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_host_or_time_slice(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            manifest = json.loads(
                fixture.dataset_manifest.read_text(encoding="utf-8")
            )
            manifest["case_provenance"][0]["not_a_host_slice"] = False
            write_json(fixture.dataset_manifest, manifest)

            with self.assertRaisesRegex(ValueError, "not_a_host_slice must be true"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_prior_development_campaign(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            manifest = json.loads(
                fixture.dataset_manifest.read_text(encoding="utf-8")
            )
            manifest["case_provenance"][0][
                "campaign_execution_id"
            ] = "darpa-tc-e3-2018"
            write_json(fixture.dataset_manifest, manifest)

            with self.assertRaisesRegex(ValueError, "used in model development"):
                run_preflight(runner, fixture)

    def test_preflight_rejects_curation_model_team_overlap(self):
        runner = load_runner(self)
        with tempfile.TemporaryDirectory() as temporary:
            fixture = build_preflight_fixture(runner, Path(temporary))
            manifest = json.loads(
                fixture.dataset_manifest.read_text(encoding="utf-8")
            )
            separation = manifest["curation_and_seal_separation"]
            separation["curation_team_id"] = separation[
                "model_development_team_id"
            ]
            write_json(fixture.dataset_manifest, manifest)

            with self.assertRaisesRegex(ValueError, "identities must be distinct"):
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
