import ast
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.compiler.llm.certificate_issue_executor import (
    ACTIVATION_STATUS,
    ASSISTED_CONTRACT_SHA256,
    ASSISTED_SCHEMA_SHA256,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    CERTIFICATE_RECORD_PATH,
    CERTIFICATE_RECEIPT_PATH,
    CERTIFICATE_SCOPE,
    CERTIFICATE_TARGET_ID,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EFFECTIVE_ISSUE_CONTRACT_SHA256,
    EFFECTIVE_SCHEMA_PATH,
    EFFECTIVE_SCHEMA_SHA256,
    EFFECTIVE_SOURCE_CONTRACT_SHA256,
    EFFECTIVE_SOURCE_SCHEMA_SHA256,
    EXHAUSTED_SOURCE_ACTIVATION_SHA256,
    EXECUTOR_PATH,
    EXTERNAL_SCHEMA_SHA256,
    IDEMPOTENCY_KEY,
    INVENTORY_SCHEMA_SHA256,
    KERNEL_SCHEMA_SHA256,
    OWNER_RESPONSE_ARTIFACT_ID,
    OWNER_RESPONSE_PATH,
    OWNER_RESPONSE_SHA256,
    OWNER_RESPONSE_STATUS,
    PACKAGE_ID,
    SOURCE_ID,
    SOURCE_RECORD_PATH,
    SOURCE_RECORD_SHA256,
    SOURCE_RECEIPT_PATH,
    SOURCE_RECEIPT_SHA256,
    CertificateIssueError,
    _pretty_json_bytes,
    _validate_target_state,
    execute_certificate_issue,
    verify_certificate_issue_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def executor_sha256() -> str:
    return hashlib.sha256((REPO_ROOT / EXECUTOR_PATH).read_bytes()).hexdigest()


def activated_authority(case: str) -> dict:
    output_root = f".tmp/compiler-contract/certificate/{case}"
    return {
        "artifact_id": f"production_certificate_test_{case}",
        "artifact_type": "production_certificate_single_execute_activation",
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
        "owner_approval": {
            "artifact_id": OWNER_RESPONSE_ARTIFACT_ID,
            "path": OWNER_RESPONSE_PATH,
            "sha256": OWNER_RESPONSE_SHA256,
            "status": OWNER_RESPONSE_STATUS,
            "owner": "Kernel/Checker",
            "overall_decision": "accept",
            "certificate_issue_authorized_by_response": False,
            "checker_invocation_authorized_by_response": False,
            "certified_stop_authorized_by_response": False,
        },
        "target": {
            "surface_id": "project05_depth2_public",
            "source_class": "planner_experiment_inputs",
            "adapter_id": "m1a_planner_inputs_v0_1",
            "package_id": PACKAGE_ID,
            "source_record_class": "e_case",
            "target_record_class": "certificate",
            "certificate_target_id": CERTIFICATE_TARGET_ID,
            "certificate_scope": CERTIFICATE_SCOPE,
            "operation": "construct_and_issue_one_separately_typed_certificate_record",
            "checker_decision_ref": None,
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "owner_response_sha256": OWNER_RESPONSE_SHA256,
            "effective_certificate_schema_sha256": EFFECTIVE_SCHEMA_SHA256,
            "effective_certificate_issue_write_contract_sha256": EFFECTIVE_ISSUE_CONTRACT_SHA256,
            "source_e_case_record_sha256": SOURCE_RECORD_SHA256,
            "source_e_case_receipt_sha256": SOURCE_RECEIPT_SHA256,
            "effective_e_case_schema_sha256": EFFECTIVE_SOURCE_SCHEMA_SHA256,
            "effective_e_case_write_contract_sha256": EFFECTIVE_SOURCE_CONTRACT_SHA256,
            "exhausted_e_case_activation_sha256": EXHAUSTED_SOURCE_ACTIVATION_SHA256,
            "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "certificate_issue_executor_sha256": executor_sha256(),
        },
        "selected_source": {
            "e_case_record": {
                "path": SOURCE_RECORD_PATH,
                "sha256": SOURCE_RECORD_SHA256,
                "e_case_id": SOURCE_ID,
                "package_id": PACKAGE_ID,
                "surface_id": "project05_depth2_public",
                "is_e_case": True,
                "is_kernel_store_record": False,
                "is_certificate": False,
            },
            "sanitized_e_case_receipt": {
                "path": SOURCE_RECEIPT_PATH,
                "sha256": SOURCE_RECEIPT_SHA256,
            },
        },
        "transaction_contract": {
            "certificate_target_id": CERTIFICATE_TARGET_ID,
            "idempotency_key": IDEMPOTENCY_KEY,
            "transaction_id_derivation": (
                "cert_txn_ + first_32_hex(sha256(effective_contract_sha256 NUL "
                "source_e_case_sha256 NUL certificate_target_id NUL activation_sha256_before))"
            ),
            "atomic_all_or_nothing": True,
            "target_empty_or_idempotently_equivalent_required": True,
            "partial_write": False,
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
            "mode": "versioned_certificate_record_and_sanitized_receipt",
            "file_write": True,
            "certificate_generation": True,
            "certificate_write": True,
            "new_separately_typed_target": True,
            "source_e_case_write_or_mutation": False,
            "kernel_store_write_or_mutation": False,
            "checker_invocation": False,
            "checker_acceptance_or_promotion": False,
            "evidence_sufficiency_assertion": False,
            "certified_stop": False,
            "si_llm_001_closure": False,
            "l2_or_part_b_change": False,
            "certificate_record_path": f"{output_root}/certificate-record.json",
            "sanitized_receipt_path": f"{output_root}/sanitized-receipt.json",
        },
        "still_blocked": {
            "second_certificate_execute": True,
            "checker_invocation": True,
            "checker_acceptance_or_promotion": True,
            "evidence_sufficiency_assertion": True,
            "certified_stop": True,
            "source_e_case_write_or_mutation": True,
            "kernel_store_write_or_mutation": True,
            "si_llm_001_closure": True,
            "l2": True,
            "part_b_elevation": True,
            "production_registration_execution": True,
            "catalog_role_credit": True,
            "m2_fit": True,
            "four_family_llm_finetune": True,
        },
        "execution_audit": None,
    }


class CertificateIssueExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        verify_certificate_issue_pins(REPO_ROOT)

    def execute(self, activation: dict, case: str, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{case}.json"
            path.write_text(json.dumps(activation), encoding="utf-8")
            return execute_certificate_issue(
                repo_root=REPO_ROOT,
                activation_path=path,
                **kwargs,
            )

    def assert_error_code(self, code: str, callable_):
        with self.assertRaises(CertificateIssueError) as raised:
            callable_()
        self.assertEqual(code, raised.exception.code)

    def test_missing_activation_fails_closed(self):
        self.assert_error_code(
            "missing_activation",
            lambda: execute_certificate_issue(repo_root=REPO_ROOT),
        )

    def test_non_effective_schema_and_contract_masquerades_fail_closed(self):
        for sha in (ASSISTED_SCHEMA_SHA256, INVENTORY_SCHEMA_SHA256):
            with self.subTest(schema_sha=sha):
                activation = activated_authority("wrong_schema")
                activation["pinned_hashes"]["effective_certificate_schema_sha256"] = sha
                self.assert_error_code(
                    "non_effective_schema_identity",
                    lambda a=activation: self.execute(a, "wrong_schema"),
                )
        activation = activated_authority("wrong_contract")
        activation["pinned_hashes"][
            "effective_certificate_issue_write_contract_sha256"
        ] = ASSISTED_CONTRACT_SHA256
        self.assert_error_code(
            "non_effective_contract_identity",
            lambda: self.execute(activation, "wrong_contract"),
        )

    def test_missing_or_wrong_pin_fails_closed(self):
        activation = activated_authority("missing_pin")
        del activation["pinned_hashes"]["owner_response_sha256"]
        self.assert_error_code(
            "activation_pin", lambda: self.execute(activation, "missing_pin")
        )
        activation = activated_authority("wrong_pin")
        activation["pinned_hashes"]["source_e_case_receipt_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin", lambda: self.execute(activation, "wrong_pin")
        )

    def test_non_null_checker_decision_ref_fails_closed(self):
        self.assert_error_code(
            "non_null_checker_decision_ref",
            lambda: self.execute(
                activated_authority("decision"),
                "decision",
                checker_decision_ref={"decision": "accept"},
            ),
        )

    def test_consumed_activation_and_second_execute_fail_closed(self):
        activation = activated_authority("consumed")
        activation["execute_ledger"].update(started=1, consumed=1, remaining=0)
        activation["execution_audit"] = {"invocation_count": 1}
        self.assert_error_code(
            "activation_ledger", lambda: self.execute(activation, "consumed")
        )

    def test_changed_source_record_or_receipt_fails_closed(self):
        record = bytearray((REPO_ROOT / SOURCE_RECORD_PATH).read_bytes())
        record[-2] ^= 1
        self.assert_error_code(
            "source_record_pin",
            lambda: self.execute(
                activated_authority("changed_record"),
                "changed_record",
                source_record_bytes=bytes(record),
            ),
        )
        receipt = bytearray((REPO_ROOT / SOURCE_RECEIPT_PATH).read_bytes())
        receipt[-2] ^= 1
        self.assert_error_code(
            "source_receipt_pin",
            lambda: self.execute(
                activated_authority("changed_receipt"),
                "changed_receipt",
                source_receipt_bytes=bytes(receipt),
            ),
        )

    def test_forbidden_side_effect_requests_fail_closed(self):
        for field in (
            "source_e_case_write_or_mutation",
            "kernel_store_write_or_mutation",
            "checker_invocation",
            "checker_acceptance_or_promotion",
            "evidence_sufficiency_assertion",
            "certified_stop",
            "si_llm_001_closure",
            "l2_or_part_b_change",
        ):
            with self.subTest(field=field):
                activation = activated_authority(f"effect_{field}")
                activation["output_policy"][field] = True
                self.assert_error_code(
                    "output_policy",
                    lambda a=activation, f=field: self.execute(a, f"effect_{f}"),
                )

    def test_happy_path_builds_schema_valid_provenance_only_certificate(self):
        before_record = (REPO_ROOT / SOURCE_RECORD_PATH).read_bytes()
        before_receipt = (REPO_ROOT / SOURCE_RECEIPT_PATH).read_bytes()
        result = self.execute(activated_authority("happy"), "happy")
        record = result["certificate_record"]
        receipt = result["sanitized_receipt"]
        schema = json.loads((REPO_ROOT / EFFECTIVE_SCHEMA_PATH).read_text(encoding="utf-8"))
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(record)))
        self.assertTrue(record["is_certificate"])
        self.assertFalse(record["is_e_case"])
        self.assertFalse(record["is_kernel_store_record"])
        self.assertIsNone(record["checker_decision_ref"])
        self.assertEqual(CERTIFICATE_SCOPE, record["certificate_subject"]["certificate_scope"])
        self.assertEqual(41, record["claim_identity_summary"]["claim_count"])
        self.assertFalse(record["claim_identity_summary"]["claim_values_copied"])
        serialized = json.dumps(record, ensure_ascii=False)
        for forbidden in (
            '"claim_identity_refs"',
            '"claim_values"',
            '"labels"',
            '"realized_outcomes"',
            '"checker_decision"',
            '"certified_stop"',
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(record["separation_assertions"]["certified_stop_declared"])
        self.assertFalse(
            record["separation_assertions"]["checker_invoked_by_certificate_writer"]
        )
        self.assertEqual(
            hashlib.sha256(_pretty_json_bytes(record)).hexdigest(),
            receipt["target"]["record_file_sha256"],
        )
        self.assertTrue(receipt["side_effect_assertions"]["certificate_generation"])
        self.assertTrue(receipt["side_effect_assertions"]["certificate_write"])
        for field, value in receipt["side_effect_assertions"].items():
            if field not in {"certificate_generation", "certificate_write"}:
                self.assertFalse(value, field)
        self.assertEqual(1, result["execute_ledger_after_required"]["consumed"])
        self.assertEqual(0, result["execute_ledger_after_required"]["remaining"])
        self.assertEqual(before_record, (REPO_ROOT / SOURCE_RECORD_PATH).read_bytes())
        self.assertEqual(before_receipt, (REPO_ROOT / SOURCE_RECEIPT_PATH).read_bytes())

    def test_existing_non_idempotent_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = copy.deepcopy(activated_authority("collision")["output_policy"])
            policy["certificate_record_path"] = CERTIFICATE_RECORD_PATH
            policy["sanitized_receipt_path"] = CERTIFICATE_RECEIPT_PATH
            record_path = root / CERTIFICATE_RECORD_PATH
            receipt_path = root / CERTIFICATE_RECEIPT_PATH
            record_path.parent.mkdir(parents=True)
            record_path.write_text('{"different":true}\n', encoding="utf-8")
            receipt_path.write_text('{"different":true}\n', encoding="utf-8")
            self.assert_error_code(
                "target_collision",
                lambda: _validate_target_state(
                    root,
                    record={"expected": True},
                    receipt={"expected": True},
                    output_policy=policy,
                ),
            )

    def test_executor_has_no_direct_write_or_checker_call_surface(self):
        source = (REPO_ROOT / EXECUTOR_PATH).read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_calls = {
            "write_text",
            "write_bytes",
            "unlink",
            "rename",
            "invoke_checker",
            "certified_stop",
        }
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertTrue(forbidden_calls.isdisjoint(calls))


if __name__ == "__main__":
    unittest.main()
