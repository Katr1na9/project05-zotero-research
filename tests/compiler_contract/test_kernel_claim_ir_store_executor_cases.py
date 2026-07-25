import ast
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm.kernel_claim_ir_store_executor import (
    ASSISTED_DRAFT_SHA256,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    EXECUTOR_PATH,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    INGESTION_RECEIPT_PATH,
    INGESTION_RECEIPT_SHA256,
    IDEMPOTENCY_KEY,
    REVISION_PACKET_SHA256,
    STORE_TARGET_ID,
    TRANSACTION_ID,
    KernelClaimIRStoreError,
    _validate_target_state,
    execute_kernel_claim_ir_store,
    verify_kernel_claim_ir_store_pins,
)
from tests.compiler_contract.test_kernel_claim_ir_store_executor import (
    activated_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class KernelClaimIRStoreExecutorCases(unittest.TestCase):
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

    def test_frozen_pins_and_reference_only_ingestion_executor(self):
        verify_kernel_claim_ir_store_pins(REPO_ROOT)
        for relative_path, expected in (
            (AUTHORITY_DESIGN_PATH, AUTHORITY_DESIGN_SHA256),
            (INGESTED_FIXTURE_PATH, INGESTED_FIXTURE_SHA256),
            (INGESTION_RECEIPT_PATH, INGESTION_RECEIPT_SHA256),
        ):
            self.assertEqual(
                expected,
                hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest(),
            )
        design = json.loads(
            (REPO_ROOT / AUTHORITY_DESIGN_PATH).read_text(encoding="utf-8")
        )
        ingestion_ref = design["pinned_authority_chain"][
            "kernel_claim_ir_ingestion_executor"
        ]
        self.assertFalse(ingestion_ref["production_kernel_store_write_supported"])
        self.assertFalse(ingestion_ref["may_be_reinterpreted_as_store_executor"])

    def test_executor_has_no_direct_filesystem_write_surface(self):
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
            "missing_activation",
            lambda: execute_kernel_claim_ir_store(repo_root=REPO_ROOT),
        )

    def test_wrong_pin_and_draft_contract_masquerade_fail_closed(self):
        wrong = activated_authority("wrong_pin")
        wrong["pinned_hashes"]["ingested_fixture_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin", lambda: self.execute(wrong, "wrong_pin")
        )
        for index, forbidden_sha in enumerate(
            (ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256)
        ):
            draft = activated_authority(f"draft_{index}")
            draft["pinned_hashes"][
                "effective_consumer_contract_sha256"
            ] = forbidden_sha
            self.assert_error_code(
                "non_effective_contract_identity",
                lambda value=draft, case=f"draft_{index}": self.execute(
                    value, case
                ),
            )

    def test_consumed_activation_rejects_second_execute(self):
        exhausted = activated_authority("exhausted")
        exhausted["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        exhausted["execution_audit"] = {"decision": "already_consumed"}
        self.assert_error_code(
            "activation_ledger",
            lambda: self.execute(exhausted, "exhausted"),
        )

    def test_e_case_and_lifecycle_output_policy_fail_closed(self):
        for field in (
            "is_e_case",
            "e_case_write",
            "certificate_generation",
            "claim_lifecycle_mutation",
        ):
            authority = activated_authority(f"forbidden_{field}")
            authority["output_policy"][field] = True
            self.assert_error_code(
                "output_policy",
                lambda value=authority, case=f"forbidden_{field}": self.execute(
                    value, case
                ),
            )

    def test_wrong_input_state_identity_fails_closed(self):
        for field, value in (
            ("package_id", "pkg_wrong"),
            ("kernel_state", "pending_kernel_schema"),
            ("claim_id_state", "pending"),
            ("admission_state", "not_admitted"),
        ):
            authority = activated_authority(f"wrong_{field}")
            authority["selected_input"]["ingested_package"][field] = value
            self.assert_error_code(
                "selected_input",
                lambda item=authority, case=f"wrong_{field}": self.execute(
                    item, case
                ),
            )

