import ast
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm.kernel_claim_ir_store_executor import (
    ACTIVATION_STATUS,
    ASSISTED_DRAFT_SHA256,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    EFFECTIVE_CONTRACT_SHA256,
    EXECUTOR_PATH,
    EXTERNAL_SCHEMA_SHA256,
    IDEMPOTENCY_KEY,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    INGESTION_RECEIPT_PATH,
    INGESTION_RECEIPT_SHA256,
    IN_MEMORY_INGESTION_EXECUTOR_SHA256,
    KERNEL_SCHEMA_SHA256,
    PACKAGE_ID,
    REVISION_PACKET_SHA256,
    STORE_TARGET_ID,
    TRANSACTION_ID,
    KernelClaimIRStoreError,
    _validate_target_state,
    execute_kernel_claim_ir_store,
    verify_kernel_claim_ir_store_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTOR_SHA256 = hashlib.sha256((REPO_ROOT / EXECUTOR_PATH).read_bytes()).hexdigest()


def activated_authority(case: str) -> dict:
    output_root = f".tmp/compiler-contract/kernel-claim-ir-store/{case}"
    return {
        "artifact_id": f"kernel_claim_ir_store_test_{case}",
        "artifact_type": "production_kernel_claim_ir_store_single_execute_activation",
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
            "target_store_class": "kernel_claim_ir_intake_store",
            "operation": "persist_exact_ingested_claim_ir_identity_once",
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "effective_consumer_contract_sha256": EFFECTIVE_CONTRACT_SHA256,
            "external_envelope_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
            "in_memory_ingestion_executor_sha256": IN_MEMORY_INGESTION_EXECUTOR_SHA256,
            "production_store_executor_sha256": EXECUTOR_SHA256,
        },
        "selected_input": {
            "ingested_package": {
                "path": INGESTED_FIXTURE_PATH,
                "sha256": INGESTED_FIXTURE_SHA256,
                "package_id": PACKAGE_ID,
                "surface_id": "project05_depth2_public",
                "claim_id_state": "minted_opaque",
                "admission_state": "admitted_under_separate_authority",
                "kernel_state": "ingested_under_separate_authority",
            },
            "sanitized_ingestion_receipt": {
                "path": INGESTION_RECEIPT_PATH,
                "sha256": INGESTION_RECEIPT_SHA256,
            },
        },
        "store_transaction": {
            "store_target_id": STORE_TARGET_ID,
            "transaction_id": TRANSACTION_ID,
            "idempotency_key": IDEMPOTENCY_KEY,
            "atomic_all_or_nothing": True,
            "store_target_empty_or_idempotently_equivalent_required": True,
            "partial_claim_store": False,
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
            "mode": "versioned_kernel_claim_ir_intake_store_record",
            "store_record_path": f"{output_root}/store-record.json",
            "sanitized_store_receipt_path": f"{output_root}/sanitized-receipt.json",
            "file_write": True,
            "kernel_claim_ir_intake_store_write": True,
            "is_kernel_store_record": True,
            "is_e_case": False,
            "e_case_write": False,
            "certificate_generation": False,
            "certified_stop": False,
            "claim_lifecycle_mutation": False,
            "production_registration": False,
        },
        "still_blocked": {
            "second_store_execute": True,
            "e_case": True,
            "certificate": True,
            "certified_stop": True,
            "production_registration_execution": True,
            "si_llm_001_closure": True,
            "l2": True,
            "part_b_elevation": True,
            "checker_or_promotion": True,
            "catalog_role_credit": True,
            "m2_fit": True,
            "four_family_llm_finetune": True,
        },
        "execution_audit": None,
    }


class KernelClaimIRStoreExecutorTests(unittest.TestCase):
    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(KernelClaimIRStoreError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def execute(self, authority: dict, case: str):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / f"{case}.json"
            activation_path.write_text(
                json.dumps(authority, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return execute_kernel_claim_ir_store(
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

