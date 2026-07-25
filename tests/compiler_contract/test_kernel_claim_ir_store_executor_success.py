import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm.kernel_claim_ir_store_executor import (
    IDEMPOTENCY_KEY,
    INGESTED_FIXTURE_PATH,
    STORE_TARGET_ID,
    TRANSACTION_ID,
    KernelClaimIRStoreError,
    _validate_target_state,
)
from tests.compiler_contract.test_kernel_claim_ir_store_executor import (
    KernelClaimIRStoreExecutorTests,
    activated_authority,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


class KernelClaimIRStoreExecutorSuccessTests(unittest.TestCase):
    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(KernelClaimIRStoreError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def test_valid_single_use_store_preserves_exact_identity(self):
        harness = KernelClaimIRStoreExecutorTests()
        result = harness.execute(activated_authority("valid"), "valid")
        record = result["store_record"]
        package = json.loads(
            (REPO_ROOT / INGESTED_FIXTURE_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(package, record["stored_claim_ir_package"])
        self.assertTrue(record["is_kernel_store_record"])
        self.assertFalse(record["is_e_case"])
        self.assertEqual(STORE_TARGET_ID, record["store_target_id"])
        self.assertEqual(TRANSACTION_ID, record["transaction_id"])
        self.assertEqual(IDEMPOTENCY_KEY, record["idempotency_key"])
        preservation = record["identity_preservation"]
        self.assertTrue(
            all(
                value is True
                for key, value in preservation.items()
                if key != "silent_schema_conversion"
            )
        )
        self.assertFalse(preservation["silent_schema_conversion"])
        side_effects = record["side_effects"]
        self.assertTrue(side_effects["kernel_claim_ir_intake_store_write"])
        self.assertTrue(
            all(
                value is False
                for key, value in side_effects.items()
                if key != "kernel_claim_ir_intake_store_write"
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
        receipt = result["sanitized_store_receipt"]
        self.assertNotIn("claims", receipt)
        self.assertNotIn("stored_claim_ir_package", receipt)
        self.assertFalse(receipt["side_effect_assertions"]["e_case_write"])

    def test_non_idempotent_existing_target_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = activated_authority("collision")["output_policy"]
            record_path = root / policy["store_record_path"]
            receipt_path = root / policy["sanitized_store_receipt_path"]
            record_path.parent.mkdir(parents=True)
            record_path.write_text('{"different":true}\n', encoding="utf-8")
            receipt_path.write_text('{"different":true}\n', encoding="utf-8")
            self.assert_error_code(
                "store_target_collision",
                lambda: _validate_target_state(
                    root,
                    record={"expected": True},
                    receipt={"expected": True},
                    output_policy=policy,
                ),
            )

    def test_exact_existing_target_is_idempotently_equivalent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = activated_authority("equivalent")["output_policy"]
            record = {"expected": True}
            receipt = {"receipt": True}
            record_path = root / policy["store_record_path"]
            receipt_path = root / policy["sanitized_store_receipt_path"]
            record_path.parent.mkdir(parents=True)
            record_path.write_text(json.dumps(record), encoding="utf-8")
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertFalse(
                _validate_target_state(
                    root,
                    record=record,
                    receipt=receipt,
                    output_policy=policy,
                )
            )


if __name__ == "__main__":
    unittest.main()
