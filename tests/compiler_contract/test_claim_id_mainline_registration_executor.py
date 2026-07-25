import ast
import copy
import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_mainline_registration_executor import (
    ACTIVATION_STATUS,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EXECUTOR_PATH,
    HANDOFF_DESIGN_SHA256,
    HANDOFF_IMPLEMENTATION_SHA256,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    MERGE_READINESS_SHA256,
    PACKAGE_ID,
    RECORD_STATUS,
    SANITIZED_RECEIPT_PATH,
    SANITIZED_RECEIPT_SHA256,
    SCHEMA_SHA256,
    ClaimIDMainlineRegistrationError,
    execute_claim_id_mainline_registration,
    verify_registration_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def activated_authority(case: str) -> dict:
    output_root = (
        f".tmp/compiler-contract/claim-id-mainline-registration-{case}-"
        f"{uuid.uuid4().hex}"
    )
    return {
        "artifact_id": f"claim_id_mainline_registration_test_{case}_v0_1",
        "artifact_type": (
            "production_claim_id_mainline_registration_single_execute_activation"
        ),
        "version": "0.1",
        "created_date": "2026-07-25",
        "authority_base_commit": AUTHORITY_BASE_COMMIT,
        "status": ACTIVATION_STATUS,
        "authority_design": {
            "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "path": AUTHORITY_DESIGN_PATH,
            "sha256": AUTHORITY_DESIGN_SHA256,
            "status": AUTHORITY_DESIGN_STATUS,
        },
        "target": {
            "surface_id": "project05_depth2_public",
            "source_class": "planner_experiment_inputs",
            "adapter_id": "m1a_planner_inputs_v0_1",
            "package_id": PACKAGE_ID,
            "registration_target": "claim_id_mainline_read_only_reference",
            "execution_scope": "single_versioned_audit_registration_only",
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "mainline_handoff_implementation_sha256": (
                HANDOFF_IMPLEMENTATION_SHA256
            ),
            "mainline_handoff_design_sha256": HANDOFF_DESIGN_SHA256,
            "merge_readiness_disposition_sha256": MERGE_READINESS_SHA256,
            "effective_consumer_contract_sha256": (
                EFFECTIVE_CONSUMER_CONTRACT_SHA256
            ),
            "external_envelope_schema_sha256": SCHEMA_SHA256,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": SANITIZED_RECEIPT_SHA256,
            "registration_executor_sha256": file_sha256(REPO_ROOT / EXECUTOR_PATH),
        },
        "selected_input": {
            "package": {
                "path": INGESTED_FIXTURE_PATH,
                "sha256": INGESTED_FIXTURE_SHA256,
                "package_id": PACKAGE_ID,
            },
            "ingestion_receipt": {
                "path": SANITIZED_RECEIPT_PATH,
                "sha256": SANITIZED_RECEIPT_SHA256,
            },
            "handoff_reference": {
                "surface_id": "project05_depth2_public",
                "package_id": PACKAGE_ID,
                "effective_consumer_contract_sha256": (
                    EFFECTIVE_CONSUMER_CONTRACT_SHA256
                ),
            },
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
            "mode": "versioned_audit_registration_only",
            "registration_record_path": f"{output_root}/registration-record.json",
            "sanitized_receipt_path": f"{output_root}/sanitized-receipt.json",
            "registration_record_write": True,
            "sanitized_receipt_write": True,
            "kernel_store_write": False,
            "e_case_write": False,
            "certificate_generation": False,
            "certified_stop": False,
            "production_control_loop_wiring": False,
            "planner_wiring": False,
            "claim_lifecycle_mutation": False,
        },
        "still_blocked": {
            "second_registration_execute": True,
            "permanent_registration_switch": True,
            "production_control_loop_wiring": True,
            "planner_wiring": True,
            "kernel_store_write": True,
            "e_case_write": True,
            "checker_or_promotion": True,
            "certificate_generation": True,
            "certified_stop": True,
            "si_llm_001_closure": True,
            "catalog_role_credit_l2": True,
            "m2_fit": True,
            "four_family_llm_finetune": True,
        },
        "execution_audit": None,
    }


def pretty_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


class ClaimIDMainlineRegistrationExecutorTests(unittest.TestCase):
    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ClaimIDMainlineRegistrationError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def execute_with(self, authority: dict):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_text(pretty_json(authority), encoding="utf-8")
            return execute_claim_id_mainline_registration(
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

    def test_frozen_pins_and_executor_has_no_write_surface(self):
        verify_registration_pins(REPO_ROOT)
        self.assertEqual(
            AUTHORITY_DESIGN_SHA256,
            file_sha256(REPO_ROOT / AUTHORITY_DESIGN_PATH),
        )
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)

        tree = ast.parse((REPO_ROOT / EXECUTOR_PATH).read_text(encoding="utf-8"))
        forbidden_methods = {
            "write_bytes",
            "write_text",
            "mkdir",
            "rename",
            "unlink",
        }
        observed = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_methods
        }
        self.assertEqual(set(), observed)

    def test_missing_activation_fails_closed(self):
        self.assert_error_code(
            "missing_activation",
            lambda: execute_claim_id_mainline_registration(repo_root=REPO_ROOT),
        )

    def test_wrong_pin_fails_closed(self):
        authority = activated_authority("wrong_pin")
        authority["pinned_hashes"]["authority_design_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin",
            lambda: self.execute_with(authority),
        )

    def test_consumed_ledger_rejects_second_execute(self):
        authority = activated_authority("consumed")
        authority["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        authority["execution_audit"] = {
            "decision": "already_consumed",
        }
        self.assert_error_code(
            "activation_ledger",
            lambda: self.execute_with(authority),
        )

    def test_global_switch_bypass_fails_closed(self):
        authority = activated_authority("switch_bypass")
        with mock.patch.object(
            handoff_module,
            "PRODUCTION_REGISTRATION_ENABLED",
            True,
        ):
            self.assert_error_code(
                "global_kill_switch",
                lambda: self.execute_with(authority),
            )
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)

    def test_valid_activation_registers_exact_reference_once(self):
        authority = activated_authority("happy")
        authority_before = copy.deepcopy(authority)
        package_before = (REPO_ROOT / INGESTED_FIXTURE_PATH).read_bytes()
        ingestion_receipt_before = (REPO_ROOT / SANITIZED_RECEIPT_PATH).read_bytes()

        result = self.execute_with(authority)

        self.assertEqual(authority_before, authority)
        self.assertEqual(
            package_before,
            (REPO_ROOT / INGESTED_FIXTURE_PATH).read_bytes(),
        )
        self.assertEqual(
            ingestion_receipt_before,
            (REPO_ROOT / SANITIZED_RECEIPT_PATH).read_bytes(),
        )
        self.assertEqual(
            {
                "authorized": 1,
                "maximum": 1,
                "started": 1,
                "consumed": 1,
                "remaining": 0,
                "retry": False,
                "resume": False,
                "fallback": False,
            },
            result["execute_ledger_after_required"],
        )

        record = result["registration_record"]
        self.assertEqual(RECORD_STATUS, record["status"])
        self.assertEqual(PACKAGE_ID, record["package_id"])
        self.assertEqual(
            "ingested_under_separate_authority",
            record["handoff_reference"]["kernel_state"],
        )
        self.assertNotIn("claims", record["handoff_reference"])
        self.assertTrue(all(record["identity_preservation"].values()))
        self.assertTrue(
            record["registration_effect"][
                "exact_pinned_handoff_reference_recorded"
            ]
        )
        self.assertFalse(
            record["registration_effect"]["production_control_loop_wiring"]
        )
        self.assertTrue(
            all(value is False for value in record["side_effects"].values())
        )

        receipt = result["sanitized_receipt"]
        self.assertEqual(
            "registered_once_under_single_execute_authority",
            receipt["decision"],
        )
        self.assertFalse(
            receipt["registration_switch_boundary"][
                "permanent_registration_enabled"
            ]
        )
        self.assertFalse(
            receipt["registration_switch_boundary"]["mutated_during_execution"]
        )
        self.assertTrue(
            all(value is False for value in receipt["side_effects"].values())
        )


if __name__ == "__main__":
    unittest.main()
