import copy
import hashlib
import json
import sys
import unittest
from collections import defaultdict, deque
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.claim_ir_admission_executor import (  # noqa: E402
    ADAPTER_ID,
    ADMISSION_AUTHORITY_DESIGN_SHA256,
    ADMISSION_CONTRACT_SHA256,
    DUAL_PATH_DISPOSITION_SHA256,
    ELIGIBLE_CANDIDATES,
    PROJECTION_SHA256,
    SCHEMA_SHA256,
    SOURCE_CLASS,
    SURFACE_ID,
    ClaimIRAdmissionError,
    admit_claim_ir_package,
    verify_admission_pins,
)
from compiler.llm.m0_rule_compiler import compile_public_projection  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
M0_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "m0_rule_compiler"
    / "m0_valid_public_projection.json"
)
FROZEN_STRUCTURAL_SOURCE_FIELD_ORDER = (
    "config.case_id",
    "config.budget_total",
    "config.channel_reliability",
    "config.cti_nodes.critical",
    "config.cti_nodes.stage",
    "config.cti_nodes.node_id",
    "config.cti_nodes.critical",
    "config.cti_nodes.stage",
    "config.cti_nodes.node_id",
    "state.case_id",
    "state.step_index",
    "state.matched_cti_node_ids",
    "state.unmatched_cti_node_ids",
    "state.matched_cti_edge_ids",
    "state.unmatched_cti_edge_ids",
    "state.remaining_action_ids",
    "state.coverage.evidence_type_coverage",
    "state.coverage.critical_gap_count",
    "state.coverage.cti_node_coverage",
    "state.coverage.cti_edge_coverage",
    "state.coverage.stage_coverage",
    "state.budget.budget_used",
    "state.budget.budget_remaining",
    "state.budget.budget_total",
    "action.action_id",
    "action.case_id",
    "action.action_type",
    "action.acquisition_channel",
    "action.cost",
    "action.intended_cti_node_ids",
    "action.expected_evidence_types",
    "action.expected_stages",
    "action.status",
    "action.natural_language_request",
    "action.target.target_value",
    "action.target.target_type",
    "action.expected_effects.expected_over_attribution_risk_reduction",
    "action.expected_effects.expected_uncertainty_reduction",
    "action.expected_effects.expected_conflict_resolution",
    "action.expected_effects.expected_granularity_gain",
    "action.expected_effects.expected_coverage_delta",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pretty_json_bytes(value: dict) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def canonical_sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def structural_package_bytes() -> bytes:
    package = compile_public_projection(
        load_json(M0_FIXTURE),
        repo_root=REPO_ROOT,
    )
    claims_by_field = defaultdict(deque)
    for claim in package["claims"]:
        claims_by_field[claim["source_field"]].append(claim)
    package["claims"] = [
        claims_by_field[source_field].popleft()
        for source_field in FROZEN_STRUCTURAL_SOURCE_FIELD_ORDER
    ]
    if any(claims_by_field.values()):
        raise AssertionError("frozen claim ordering did not consume every claim")
    package["manifest"]["content_hash"] = hashlib.sha256(
        json.dumps(
            package["claims"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    encoded = pretty_json_bytes(package)
    expected_sha = ELIGIBLE_CANDIDATES[
        "structural_planner_inputs_package"
    ]["sha256"]
    if hashlib.sha256(encoded).hexdigest() != expected_sha:
        raise AssertionError("structural candidate bytes do not match the frozen SHA")
    return encoded


def selected_structural_candidate() -> dict:
    spec = ELIGIBLE_CANDIDATES["structural_planner_inputs_package"]
    return {
        "candidate_id": "structural_planner_inputs_package",
        "candidate_kind": spec["candidate_kind"],
        "sha256": spec["sha256"],
    }


def pi_approval(selected_candidate: dict | None = None) -> dict:
    selected = (
        copy.deepcopy(selected_candidate)
        if selected_candidate is not None
        else selected_structural_candidate()
    )
    return {
        "artifact_id": "pi_test_approval_structural_candidate_v0_1",
        "artifact_type": "claim_ir_admission_pi_approval",
        "status": "approved_single_admission_candidate",
        "approver_role": "PI",
        "target": {
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
        },
        "selected_candidate": selected,
        "pinned_hashes": {
            "admission_contract_sha256": ADMISSION_CONTRACT_SHA256,
            "admission_authority_design_sha256": (
                ADMISSION_AUTHORITY_DESIGN_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
        },
    }


def activated_authority(approval: dict) -> dict:
    return {
        "status": "activated_single_admission_execute_authorized",
        "target": {
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
            "only_target": True,
        },
        "pinned_hashes": {
            "admission_contract_sha256": ADMISSION_CONTRACT_SHA256,
            "admission_authority_design_sha256": (
                ADMISSION_AUTHORITY_DESIGN_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
            "projection_sha256": PROJECTION_SHA256,
            "dual_path_disposition_sha256": DUAL_PATH_DISPOSITION_SHA256,
        },
        "selected_candidates": [
            copy.deepcopy(approval["selected_candidate"]),
        ],
        "pi_approval_ref": {
            "artifact_id": approval["artifact_id"],
            "sha256": canonical_sha256(approval),
            "approver_role": "PI",
        },
        "execute_ledger": {
            "authorized": 1,
            "maximum": 1,
            "started": 0,
            "consumed": 0,
            "remaining": 1,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "output_policy": {
            "mode": "in_memory_admission_only",
            "file_write": False,
            "mint": False,
            "claim_id_transition": False,
            "kernel_write": False,
            "certificate_generation": False,
        },
        "still_blocked": {
            "kernel_write": True,
            "e_case_write": True,
            "certificate_generation": True,
            "catalog_write": True,
            "source_role_assignment": True,
            "lineage_credit": True,
            "quota_credit": True,
            "l2_gate_change": True,
            "m2_fit": True,
            "four_family_llm_finetune": True,
        },
    }


class ClaimIRAdmissionExecutorTests(unittest.TestCase):
    def test_pins_and_exact_two_candidate_registry(self):
        verify_admission_pins(REPO_ROOT)

        self.assertEqual(
            {
                "structural_planner_inputs_package",
                "minted_planner_inputs_package",
            },
            set(ELIGIBLE_CANDIDATES),
        )
        self.assertEqual(
            "a97dcdd63974cb86afd1cd76de23df41f178fbcedf4657c3345d5253f0e9a650",
            ELIGIBLE_CANDIDATES["structural_planner_inputs_package"]["sha256"],
        )
        self.assertEqual(
            "29a260fe46c3ccf45822e4e2b8d2085cfb6fef0b6a9a0edddfe9a30462cbb1a9",
            ELIGIBLE_CANDIDATES["minted_planner_inputs_package"]["sha256"],
        )

    def test_missing_and_inactive_authority_fail_closed(self):
        package_bytes = structural_package_bytes()

        with self.assertRaises(ClaimIRAdmissionError) as missing_context:
            admit_claim_ir_package(
                package_bytes,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("missing_authority", missing_context.exception.code)

        approval = pi_approval()
        authority = activated_authority(approval)
        authority["status"] = "design_only_admission_authority_not_activated"
        with self.assertRaises(ClaimIRAdmissionError) as inactive_context:
            admit_claim_ir_package(
                package_bytes,
                repo_root=REPO_ROOT,
                authority=authority,
                pi_approval=approval,
            )
        self.assertEqual("not_activated", inactive_context.exception.code)

    def test_authority_pin_selection_candidate_and_ledger_rejections(self):
        package_bytes = structural_package_bytes()
        approval = pi_approval()

        bad_pin = activated_authority(approval)
        bad_pin["pinned_hashes"]["schema_sha256"] = "0" * 64

        dual_candidate = activated_authority(approval)
        minted_spec = ELIGIBLE_CANDIDATES["minted_planner_inputs_package"]
        dual_candidate["selected_candidates"].append(
            {
                "candidate_id": "minted_planner_inputs_package",
                "candidate_kind": minted_spec["candidate_kind"],
                "sha256": minted_spec["sha256"],
            }
        )

        wrong_candidate_sha = activated_authority(approval)
        wrong_candidate_sha["selected_candidates"][0]["sha256"] = "0" * 64

        exhausted = activated_authority(approval)
        exhausted["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )

        wrong_surface = activated_authority(approval)
        wrong_surface["target"]["surface_id"] = "other_surface"

        for authority, expected_code in (
            (bad_pin, "authority_pin"),
            (dual_candidate, "candidate_selection"),
            (wrong_candidate_sha, "candidate_pin"),
            (exhausted, "authority_ledger"),
            (wrong_surface, "authority_target"),
        ):
            with self.subTest(error_code=expected_code):
                with self.assertRaises(ClaimIRAdmissionError) as context:
                    admit_claim_ir_package(
                        package_bytes,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        pi_approval=approval,
                    )
                self.assertEqual(expected_code, context.exception.code)

        valid_authority = activated_authority(approval)
        tampered_package = package_bytes.replace(
            b'"not_admitted"',
            b'"not_admitteD"',
            1,
        )
        with self.assertRaises(ClaimIRAdmissionError) as context:
            admit_claim_ir_package(
                tampered_package,
                repo_root=REPO_ROOT,
                authority=valid_authority,
                pi_approval=approval,
            )
        self.assertEqual("candidate_pin", context.exception.code)

    def test_pi_approval_is_required_and_must_match_selected_candidate(self):
        package_bytes = structural_package_bytes()
        approval = pi_approval()
        authority = activated_authority(approval)

        with self.assertRaises(ClaimIRAdmissionError) as missing_context:
            admit_claim_ir_package(
                package_bytes,
                repo_root=REPO_ROOT,
                authority=authority,
            )
        self.assertEqual("missing_pi_approval", missing_context.exception.code)

        bad_approval = copy.deepcopy(approval)
        bad_approval["approver_role"] = "NOT_PI"
        bad_authority = activated_authority(bad_approval)
        with self.assertRaises(ClaimIRAdmissionError) as mismatch_context:
            admit_claim_ir_package(
                package_bytes,
                repo_root=REPO_ROOT,
                authority=bad_authority,
                pi_approval=bad_approval,
            )
        self.assertEqual("pi_approval", mismatch_context.exception.code)

    def test_valid_structural_candidate_changes_only_admission_in_memory(self):
        package_bytes = structural_package_bytes()
        original = json.loads(package_bytes.decode("utf-8"))
        approval = pi_approval()
        authority = activated_authority(approval)

        admitted = admit_claim_ir_package(
            package_bytes,
            repo_root=REPO_ROOT,
            authority=authority,
            pi_approval=approval,
        )

        self.assertEqual("not_admitted", original["admission_state"])
        self.assertTrue(
            all(
                claim["admission_state"] == "not_admitted"
                for claim in original["claims"]
            )
        )
        self.assertEqual(
            "admitted_under_separate_authority",
            admitted["admission_state"],
        )
        self.assertTrue(
            all(
                claim["admission_state"] == "admitted_under_separate_authority"
                for claim in admitted["claims"]
            )
        )
        self.assertEqual("not_minted", admitted["claim_id_state"])
        self.assertEqual("pending_kernel_schema", admitted["kernel_state"])
        self.assertTrue(
            all(claim["claim_id"] is None for claim in admitted["claims"])
        )
        self.assertEqual(
            [claim["claim_id"] for claim in original["claims"]],
            [claim["claim_id"] for claim in admitted["claims"]],
        )
        self.assertEqual(
            [claim["claim_id_state"] for claim in original["claims"]],
            [claim["claim_id_state"] for claim in admitted["claims"]],
        )
        self.assertNotIn("certificate", admitted)
        self.assertNotIn("certificate_surface", admitted)
        self.assertNotEqual(
            original["manifest"]["content_hash"],
            admitted["manifest"]["content_hash"],
        )


if __name__ == "__main__":
    unittest.main()
