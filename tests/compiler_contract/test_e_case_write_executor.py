import ast
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from src.compiler.llm.e_case_write_executor import (
    ACTIVATION_STATUS,
    ASSISTED_SCHEMA_SHA256,
    ASSISTED_WRITE_CONTRACT_SHA256,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EFFECTIVE_SCHEMA_PATH,
    EFFECTIVE_SCHEMA_SHA256,
    EFFECTIVE_WRITE_CONTRACT_SHA256,
    E_CASE_RECORD_PATH,
    E_CASE_RECEIPT_PATH,
    E_CASE_TARGET_ID,
    EXECUTOR_PATH,
    EXTERNAL_SCHEMA_SHA256,
    IDEMPOTENCY_KEY,
    INGESTED_PACKAGE_SHA256,
    KERNEL_SCHEMA_SHA256,
    OWNER_RESPONSE_ARTIFACT_ID,
    OWNER_RESPONSE_PATH,
    OWNER_RESPONSE_SHA256,
    OWNER_RESPONSE_STATUS,
    PACKAGE_ID,
    REVIEW_PACKET_SHA256,
    SOURCE_STORE_RECORD_ID,
    SOURCE_STORE_RECORD_PATH,
    SOURCE_STORE_RECORD_SHA256,
    SOURCE_STORE_RECEIPT_PATH,
    SOURCE_STORE_RECEIPT_SHA256,
    SOURCE_STORE_TARGET_ID,
    ECaseWriteError,
    _pretty_json_bytes,
    _validate_target_state,
    execute_e_case_write,
    verify_e_case_write_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def executor_sha256() -> str:
    return hashlib.sha256((REPO_ROOT / EXECUTOR_PATH).read_bytes()).hexdigest()


def activated_authority(case: str) -> dict:
    output_root = f".tmp/compiler-contract/e-case/{case}"
    return {
        "artifact_id": f"production_e_case_test_{case}",
        "artifact_type": "production_e_case_single_execute_activation",
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
            "owner": "Kernel/M3*",
            "overall_decision": "accept",
            "e_case_write_authorized_by_response": False,
        },
        "target": {
            "surface_id": "project05_depth2_public",
            "source_class": "planner_experiment_inputs",
            "adapter_id": "m1a_planner_inputs_v0_1",
            "package_id": PACKAGE_ID,
            "source_record_class": "kernel_claim_ir_intake_store",
            "target_record_class": "e_case",
            "e_case_target_id": E_CASE_TARGET_ID,
            "operation": "construct_and_write_one_separately_typed_e_case_record",
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "owner_response_sha256": OWNER_RESPONSE_SHA256,
            "effective_e_case_schema_sha256": EFFECTIVE_SCHEMA_SHA256,
            "effective_e_case_write_contract_sha256": EFFECTIVE_WRITE_CONTRACT_SHA256,
            "effective_consumer_contract_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "ingested_package_sha256": INGESTED_PACKAGE_SHA256,
            "source_store_record_sha256": SOURCE_STORE_RECORD_SHA256,
            "source_store_receipt_sha256": SOURCE_STORE_RECEIPT_SHA256,
            "e_case_write_executor_sha256": executor_sha256(),
        },
        "selected_source": {
            "store_record": {
                "path": SOURCE_STORE_RECORD_PATH,
                "sha256": SOURCE_STORE_RECORD_SHA256,
                "store_record_id": SOURCE_STORE_RECORD_ID,
                "store_target_id": SOURCE_STORE_TARGET_ID,
                "package_id": PACKAGE_ID,
                "surface_id": "project05_depth2_public",
                "is_kernel_store_record": True,
                "is_e_case": False,
            },
            "sanitized_store_receipt": {
                "path": SOURCE_STORE_RECEIPT_PATH,
                "sha256": SOURCE_STORE_RECEIPT_SHA256,
            },
        },
        "transaction_contract": {
            "e_case_target_id": E_CASE_TARGET_ID,
            "idempotency_key": IDEMPOTENCY_KEY,
            "transaction_id_derivation": (
                "ecase_txn_ + first_32_hex(sha256(effective_contract_sha256 NUL "
                "source_record_sha256 NUL e_case_target_id NUL activation_sha256_before))"
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
            "mode": "versioned_e_case_record_and_sanitized_receipt",
            "e_case_record_path": f"{output_root}/e-case-record.json",
            "sanitized_receipt_path": f"{output_root}/sanitized-receipt.json",
            "file_write": True,
            "e_case_write": True,
            "new_separately_typed_target": True,
            "source_store_write": False,
            "source_store_mutation_or_relabel": False,
            "kernel_store_reexecution": False,
            "checker_or_promotion": False,
            "certificate_generation": False,
            "certified_stop": False,
            "si_llm_001_closure": False,
            "l2_or_part_b_change": False,
        },
        "still_blocked": {
            "second_e_case_execute": True,
            "source_store_mutation_or_relabel": True,
            "kernel_store_reexecution": True,
            "checker_or_promotion": True,
            "certificate": True,
            "certified_stop": True,
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


class ECaseWriteExecutorTests(unittest.TestCase):
    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ECaseWriteError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def execute(self, authority: dict, case: str):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / f"{case}.json"
            activation_path.write_text(
                json.dumps(authority, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return execute_e_case_write(
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

    def test_frozen_pins_validate(self):
        verify_e_case_write_pins(REPO_ROOT)
        for relative_path, expected in (
            (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
            (EFFECTIVE_SCHEMA_PATH, EFFECTIVE_SCHEMA_SHA256),
            (SOURCE_STORE_RECORD_PATH, SOURCE_STORE_RECORD_SHA256),
            (SOURCE_STORE_RECEIPT_PATH, SOURCE_STORE_RECEIPT_SHA256),
        ):
            self.assertEqual(
                expected,
                hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest(),
            )

    def test_executor_has_no_direct_write_or_source_mutation_surface(self):
        tree = ast.parse((REPO_ROOT / EXECUTOR_PATH).read_text(encoding="utf-8"))
        forbidden = {"write_bytes", "write_text", "mkdir", "rename", "unlink"}
        observed = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden
        }
        self.assertEqual(set(), observed)

    def test_missing_activation_fails_closed(self):
        self.assert_error_code(
            "missing_activation", lambda: execute_e_case_write(repo_root=REPO_ROOT)
        )

    def test_assisted_artifacts_cannot_masquerade_as_effective(self):
        schema = activated_authority("assisted_schema")
        schema["pinned_hashes"]["effective_e_case_schema_sha256"] = (
            ASSISTED_SCHEMA_SHA256
        )
        self.assert_error_code(
            "non_effective_schema_identity",
            lambda: self.execute(schema, "assisted_schema"),
        )
        for index, forbidden_sha in enumerate(
            (ASSISTED_WRITE_CONTRACT_SHA256, REVIEW_PACKET_SHA256)
        ):
            contract = activated_authority(f"assisted_contract_{index}")
            contract["pinned_hashes"][
                "effective_e_case_write_contract_sha256"
            ] = forbidden_sha
            self.assert_error_code(
                "non_effective_contract_identity",
                lambda value=contract, case=f"assisted_contract_{index}": self.execute(
                    value, case
                ),
            )

    def test_missing_or_wrong_pin_fails_closed(self):
        missing = activated_authority("missing_pin")
        del missing["pinned_hashes"]["source_store_receipt_sha256"]
        self.assert_error_code(
            "activation_pin", lambda: self.execute(missing, "missing_pin")
        )
        wrong = activated_authority("wrong_pin")
        wrong["pinned_hashes"]["source_store_record_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin", lambda: self.execute(wrong, "wrong_pin")
        )

    def test_consumed_activation_rejects_second_execute(self):
        exhausted = activated_authority("exhausted")
        exhausted["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        exhausted["execution_audit"] = {"decision": "already_consumed"}
        self.assert_error_code(
            "activation_ledger", lambda: self.execute(exhausted, "exhausted")
        )

    def test_forbidden_side_effect_requests_fail_closed(self):
        for field in (
            "source_store_write",
            "source_store_mutation_or_relabel",
            "kernel_store_reexecution",
            "checker_or_promotion",
            "certificate_generation",
            "certified_stop",
            "si_llm_001_closure",
            "l2_or_part_b_change",
        ):
            activation = activated_authority(f"forbidden_{field}")
            activation["output_policy"][field] = True
            self.assert_error_code(
                "output_policy",
                lambda value=activation, case=f"forbidden_{field}": self.execute(
                    value, case
                ),
            )

    def test_modified_store_bytes_fail_closed_and_source_files_remain_exact(self):
        authority = activated_authority("modified_source")
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_text(
                json.dumps(authority, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            source = json.loads(
                (REPO_ROOT / SOURCE_STORE_RECORD_PATH).read_text(encoding="utf-8")
            )
            source["is_e_case"] = True
            modified = (json.dumps(source, ensure_ascii=False, indent=2) + "\n").encode()
            before_record = hashlib.sha256(
                (REPO_ROOT / SOURCE_STORE_RECORD_PATH).read_bytes()
            ).hexdigest()
            before_receipt = hashlib.sha256(
                (REPO_ROOT / SOURCE_STORE_RECEIPT_PATH).read_bytes()
            ).hexdigest()
            self.assert_error_code(
                "source_record_pin",
                lambda: execute_e_case_write(
                    repo_root=REPO_ROOT,
                    activation_path=activation_path,
                    source_record_bytes=modified,
                ),
            )
            self.assertEqual(
                before_record,
                hashlib.sha256(
                    (REPO_ROOT / SOURCE_STORE_RECORD_PATH).read_bytes()
                ).hexdigest(),
            )
            self.assertEqual(
                before_receipt,
                hashlib.sha256(
                    (REPO_ROOT / SOURCE_STORE_RECEIPT_PATH).read_bytes()
                ).hexdigest(),
            )

    def test_happy_path_constructs_new_schema_valid_identity_only_target(self):
        before_record = (REPO_ROOT / SOURCE_STORE_RECORD_PATH).read_bytes()
        before_receipt = (REPO_ROOT / SOURCE_STORE_RECEIPT_PATH).read_bytes()
        result = self.execute(activated_authority("happy"), "happy")
        record = result["e_case_record"]
        receipt = result["sanitized_receipt"]
        schema = json.loads(
            (REPO_ROOT / EFFECTIVE_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(record)))
        self.assertTrue(record["is_e_case"])
        self.assertFalse(record["is_kernel_store_record"])
        self.assertEqual(PACKAGE_ID, record["package_id"])
        self.assertEqual(41, len(record["claim_identity_refs"]))
        self.assertEqual(
            {
                "claim_id",
                "source_claim_index",
                "source_claim_id_state",
                "source_admission_state",
            },
            set(record["claim_identity_refs"][0]),
        )
        serialized = json.dumps(record, ensure_ascii=False)
        for forbidden in (
            '"stored_claim_ir_package"',
            '"value"',
            '"claim_kind"',
            '"checker_decision"',
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(record["separation_assertions"]["certified_stop"])
        self.assertFalse(record["separation_assertions"]["certificate_generated"])
        self.assertEqual(
            hashlib.sha256(_pretty_json_bytes(record)).hexdigest(),
            receipt["target"]["record_file_sha256"],
        )
        self.assertTrue(receipt["side_effect_assertions"]["e_case_write"])
        self.assertTrue(
            all(
                value is False
                for key, value in receipt["side_effect_assertions"].items()
                if key != "e_case_write"
            )
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
        self.assertEqual(before_record, (REPO_ROOT / SOURCE_STORE_RECORD_PATH).read_bytes())
        self.assertEqual(before_receipt, (REPO_ROOT / SOURCE_STORE_RECEIPT_PATH).read_bytes())

    def test_existing_non_idempotent_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = copy.deepcopy(activated_authority("collision")["output_policy"])
            policy["e_case_record_path"] = E_CASE_RECORD_PATH
            policy["sanitized_receipt_path"] = E_CASE_RECEIPT_PATH
            record_path = root / E_CASE_RECORD_PATH
            receipt_path = root / E_CASE_RECEIPT_PATH
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


if __name__ == "__main__":
    unittest.main()
