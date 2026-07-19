import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INTAKE_DIR = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
)
BASE_AMENDMENT = INTAKE_DIR / "staged-acquisition-protocol-amendment-v0.2.json"
STOPPING_AMENDMENT = INTAKE_DIR / "sample-size-and-stopping-amendment-v0.3.json"
CHECKPOINT_REPORT = (
    INTAKE_DIR / "curator-staged-candidate-qualification-report-v0.6.json"
)
POWER_DESIGN = (
    REPO_ROOT
    / "09-experiments"
    / "results"
    / "m3star_final_blind_power_design_v0.2"
    / "power_design.json"
)
PROTOCOL = (
    REPO_ROOT
    / "09-experiments"
    / "governance"
    / "contracts"
    / "m3star-final-blind-protocol-v0.3.json"
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


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


STAGED = load_module(
    "audit_m3star_blind_staged_candidate_qualification_v03_test",
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_m3star_blind_staged_candidate_qualification_v03.py",
)
RUNNER = load_module(
    "run_m3star_final_blind_v03_test",
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "run_m3star_final_blind_v03.py",
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def append_qualified_candidate(report: dict, candidate: dict, case_index: int) -> None:
    report["sequential_candidate_results"].append(
        {
            "phase": candidate["phase"],
            "phase_candidate_index": candidate["phase_candidate_index"],
            "source_id": candidate["source_id"],
            "candidate_key": candidate["candidate_key"],
            "qualification_status": "qualified",
            "attrition_reason": None,
        }
    )
    case = copy.deepcopy(report["qualified_cases"][-1])
    case["qualification_case_id"] = f"QB-{case_index:03d}"
    case["source_id"] = candidate["source_id"]
    case["candidate_key"] = candidate["candidate_key"]
    case["source_cluster_id"] = f"cluster-v03-{case_index}"
    case["source_release_id"] = f"release-v03-{case_index}"
    for field in STAGED.legacy.CASE_HASH_FIELDS:
        case[field] = digest(f"v03-{field}-{case_index}")
    case["ground_truth_seal_id"] = f"GTSEAL-v03-{case_index}"
    case["cost_measurement_seal_id"] = f"COSTSEAL-v03-{case_index}"
    report["qualified_cases"].append(case)
    report["audited_candidate_count"] += 1
    report["reported_qualified_count"] += 1
    report["unaudited_reserve_count"] -= 1


def report_reaching_59() -> dict:
    report = json.loads(CHECKPOINT_REPORT.read_text(encoding="utf-8"))
    base = json.loads(BASE_AMENDMENT.read_text(encoding="utf-8"))
    frozen = [
        {"phase": phase["phase"], "phase_candidate_index": index, **candidate}
        for phase in base["phases"][1:]
        for index, candidate in enumerate(phase["candidate_order"], start=1)
    ]
    for candidate in frozen[5:12]:
        append_qualified_candidate(
            report, candidate, report["reported_qualified_count"] + 1
        )
    return report


class M3StarFinalBlindV03GovernanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(BASE_AMENDMENT.read_text(encoding="utf-8"))
        cls.stopping = json.loads(STOPPING_AMENDMENT.read_text(encoding="utf-8"))

    def test_outcome_free_overlay_resumes_exactly_at_wardbeck(self):
        audit = STAGED.validate_qualification_report(
            json.loads(CHECKPOINT_REPORT.read_text(encoding="utf-8")),
            self.base,
            BASE_AMENDMENT,
            self.stopping,
            STOPPING_AMENDMENT,
        )
        self.assertEqual(52, audit["actual_qualified_case_count"])
        self.assertEqual(7, audit["additional_qualified_cases_required_to_reach_power_minimum"])
        self.assertEqual("wardbeck", audit["next_frozen_candidate"]["candidate_key"])
        self.assertEqual(59, audit["minimum_valid_complete_cases_for_effective_power_design"])
        self.assertFalse(audit["acquisition_complete"])

    def test_first_checkpoint_reaching_59_stops(self):
        audit = STAGED.validate_qualification_report(
            report_reaching_59(),
            self.base,
            BASE_AMENDMENT,
            self.stopping,
            STOPPING_AMENDMENT,
        )
        self.assertEqual("qualification_complete", audit["status"])
        self.assertEqual(59, audit["actual_qualified_case_count"])
        self.assertEqual(
            "stop_at_first_sequential_candidate_reaching_59",
            audit["decision_basis"],
        )
        self.assertIsNone(audit["next_frozen_candidate"])
        self.assertFalse(audit["source_search_required"])

    def test_candidate_after_reaching_59_is_rejected(self):
        report = report_reaching_59()
        base = self.base
        next_candidate = {
            "phase": 3,
            "phase_candidate_index": 5,
            **base["phases"][2]["candidate_order"][4],
        }
        report["sequential_candidate_results"].append(
            {
                "phase": next_candidate["phase"],
                "phase_candidate_index": next_candidate["phase_candidate_index"],
                "source_id": next_candidate["source_id"],
                "candidate_key": next_candidate["candidate_key"],
                "qualification_status": "not_qualified",
                "attrition_reason": "incomplete_campaign_boundary",
            }
        )
        report["audited_candidate_count"] += 1
        report["reported_not_qualified_count"] += 1
        report["unaudited_reserve_count"] -= 1
        with self.assertRaisesRegex(ValueError, "continued after the 59-case"):
            STAGED.validate_qualification_report(
                report,
                self.base,
                BASE_AMENDMENT,
                self.stopping,
                STOPPING_AMENDMENT,
            )

    def test_outcome_opening_attestation_cannot_be_changed(self):
        changed = copy.deepcopy(self.stopping)
        changed["blinding_attestation"]["cost_values_opened"] = True
        with self.assertRaisesRegex(ValueError, "cost_values_opened must be false"):
            STAGED.validate_stopping_amendment(changed, STOPPING_AMENDMENT)

    def test_power_design_combines_58_cost_and_59_precision_gates(self):
        design = json.loads(POWER_DESIGN.read_text(encoding="utf-8"))
        self.assertEqual(58, design["cost_power_model"]["minimum_complete_independent_cases"])
        self.assertEqual(59, design["success_safety_precision"]["minimum_complete_independent_cases"])
        self.assertEqual(59, design["sample_size_decision"]["minimum_valid_complete_independent_cases"])
        self.assertTrue(
            design["sample_size_decision"][
                "ninety_percent_power_reference_is_not_an_active_acquisition_target"
            ]
        )

    def test_v03_protocol_and_hash_chain_pass_static_checks(self):
        checked = RUNNER.static_protocol_checks(
            PROTOCOL, FROZEN_MODEL_RESULT, TRAINING_COST_PROFILE
        )
        self.assertEqual(
            "project05-m3star-final-blind-protocol-v0.3",
            checked["protocol"]["protocol_id"],
        )
        self.assertEqual(59, RUNNER.MINIMUM_VALID_COMPLETE_CASES)

    def test_v03_non_consuming_preflight_accepts_exactly_59_bound_cases(self):
        helpers = load_module(
            "test_run_m3star_final_blind_helpers_for_v03",
            REPO_ROOT
            / "09-experiments"
            / "tests"
            / "test_run_m3star_final_blind.py",
        )
        with tempfile.TemporaryDirectory() as temporary:
            fixture = helpers.build_preflight_fixture(
                RUNNER, Path(temporary), case_count=59
            )
            readiness = json.loads(
                fixture.qualification_readiness.read_text(encoding="utf-8")
            )
            readiness["stopping_amendment_id"] = self.stopping["amendment_id"]
            readiness["stopping_amendment_sha256"] = RUNNER.sha256(
                STOPPING_AMENDMENT
            )
            helpers.write_json(fixture.qualification_readiness, readiness)
            binding = json.loads(
                fixture.qualification_binding.read_text(encoding="utf-8")
            )
            binding["stopping_amendment_id"] = self.stopping["amendment_id"]
            binding["stopping_amendment_sha256"] = RUNNER.sha256(
                STOPPING_AMENDMENT
            )
            binding["qualification_readiness_sha256"] = RUNNER.sha256(
                fixture.qualification_readiness
            )
            helpers.write_json(fixture.qualification_binding, binding)
            checked = RUNNER.preflight(
                PROTOCOL,
                fixture.cases_root,
                fixture.dataset_manifest,
                TRAINING_COST_PROFILE,
                fixture.evaluation_cost_profile,
                FROZEN_MODEL_RESULT,
                fixture.output_dir,
                fixture.ledger,
                fixture.qualification_readiness,
                fixture.qualification_binding,
            )
        self.assertEqual("ready_for_one_shot_execution", checked["status"])
        self.assertEqual(59, checked["case_count"])


if __name__ == "__main__":
    unittest.main()
