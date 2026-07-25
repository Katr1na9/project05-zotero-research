import ast
import copy
import hashlib
import json
import unittest
from pathlib import Path

from src.compiler.llm.kernel_claim_ir_ingestion_executor import (
    ADMITTED_FIXTURE_PATH,
    ADMITTED_FIXTURE_SHA256,
    ASSISTED_DRAFT_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_PATH,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS,
    PACKAGE_ID,
    REVISION_PACKET_SHA256,
    SCHEMA_PATH,
    SCHEMA_SHA256,
    KernelClaimIRIngestionError,
    ingest_claim_ir_package,
    verify_kernel_ingestion_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / ADMITTED_FIXTURE_PATH


def activated_in_memory_authority() -> dict:
    return {
        "artifact_id": "kernel_ingestion_test_authority_v0_1",
        "status": "activated_single_kernel_ingestion_execute_authorized",
        "target": {
            "surface_id": "project05_depth2_public",
            "source_class": "planner_experiment_inputs",
            "adapter_id": "m1a_planner_inputs_v0_1",
            "package_id": PACKAGE_ID,
            "target_token": "ingested_under_separate_authority",
            "execution_scope": "in_memory_test_only",
        },
        "pinned_hashes": {
            "effective_consumer_contract_sha256": (
                EFFECTIVE_CONSUMER_CONTRACT_SHA256
            ),
            "schema_sha256": SCHEMA_SHA256,
            "admitted_fixture_sha256": ADMITTED_FIXTURE_SHA256,
        },
        "selected_input": {
            "path": ADMITTED_FIXTURE_PATH,
            "sha256": ADMITTED_FIXTURE_SHA256,
            "package_id": PACKAGE_ID,
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
            "mode": "in_memory_test_only",
            "file_write": False,
            "kernel_store_write": False,
            "e_case_write": False,
            "certificate_generation": False,
            "certified_stop": False,
            "sanitized_receipt": True,
        },
        "still_blocked": {
            "production_kernel_ingestion": True,
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
    }


def compact_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class KernelClaimIRIngestionExecutorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_bytes = FIXTURE_PATH.read_bytes()
        cls.fixture = json.loads(cls.fixture_bytes.decode("utf-8"))

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(KernelClaimIRIngestionError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def test_pins_effective_identity_and_non_effective_identity_denylist(self):
        verify_kernel_ingestion_pins(REPO_ROOT)

        self.assertEqual(
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            hashlib.sha256(
                (REPO_ROOT / EFFECTIVE_CONSUMER_CONTRACT_PATH).read_bytes()
            ).hexdigest(),
        )
        self.assertEqual(
            SCHEMA_SHA256,
            hashlib.sha256((REPO_ROOT / SCHEMA_PATH).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            ADMITTED_FIXTURE_SHA256,
            hashlib.sha256(self.fixture_bytes).hexdigest(),
        )
        self.assertEqual(
            {ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256},
            set(FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS),
        )
        self.assertNotIn(
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS,
        )

    def test_executor_has_no_persistent_write_surface(self):
        source_path = (
            REPO_ROOT
            / "src"
            / "compiler"
            / "llm"
            / "kernel_claim_ir_ingestion_executor.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_methods = {
            "write_bytes",
            "write_text",
            "mkdir",
            "rename",
            "unlink",
        }
        observed = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(
                node.func, ast.Attribute
            ):
                continue
            if node.func.attr in forbidden_methods:
                observed.add(node.func.attr)
            if node.func.attr == "replace" and len(node.args) <= 1:
                observed.add("filesystem_style_replace")

        self.assertEqual(set(), observed)

    def test_missing_and_inactive_authority_fail_closed(self):
        self.assert_error_code(
            "missing_authority",
            lambda: ingest_claim_ir_package(
                self.fixture_bytes,
                repo_root=REPO_ROOT,
            ),
        )

        inactive = activated_in_memory_authority()
        inactive["status"] = "design_only_kernel_ingestion_not_authorized"
        self.assert_error_code(
            "not_activated",
            lambda: ingest_claim_ir_package(
                self.fixture_bytes,
                repo_root=REPO_ROOT,
                authority=inactive,
            ),
        )

    def test_wrong_effective_pin_and_non_effective_shas_fail_closed(self):
        wrong = activated_in_memory_authority()
        wrong["pinned_hashes"]["effective_consumer_contract_sha256"] = "0" * 64
        self.assert_error_code(
            "effective_contract_pin",
            lambda: ingest_claim_ir_package(
                self.fixture_bytes,
                repo_root=REPO_ROOT,
                authority=wrong,
            ),
        )

        for forbidden_sha in (ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256):
            masquerading = activated_in_memory_authority()
            masquerading["pinned_hashes"][
                "effective_consumer_contract_sha256"
            ] = forbidden_sha
            self.assert_error_code(
                "non_effective_contract_identity",
                lambda authority=masquerading: ingest_claim_ir_package(
                    self.fixture_bytes,
                    repo_root=REPO_ROOT,
                    authority=authority,
                ),
            )

    def test_wrong_selected_fixture_and_consumed_ledger_fail_closed(self):
        wrong_fixture = activated_in_memory_authority()
        wrong_fixture["selected_input"]["sha256"] = "f" * 64
        self.assert_error_code(
            "fixture_pin",
            lambda: ingest_claim_ir_package(
                self.fixture_bytes,
                repo_root=REPO_ROOT,
                authority=wrong_fixture,
            ),
        )

        consumed = activated_in_memory_authority()
        consumed["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        self.assert_error_code(
            "authority_ledger",
            lambda: ingest_claim_ir_package(
                self.fixture_bytes,
                repo_root=REPO_ROOT,
                authority=consumed,
            ),
        )

    def test_wrong_fixture_bytes_and_wrong_states_fail_closed(self):
        byte_reencoded = compact_json_bytes(self.fixture)
        self.assertNotEqual(ADMITTED_FIXTURE_SHA256, hashlib.sha256(byte_reencoded).hexdigest())
        self.assert_error_code(
            "fixture_pin",
            lambda: ingest_claim_ir_package(
                byte_reencoded,
                repo_root=REPO_ROOT,
                authority=activated_in_memory_authority(),
            ),
        )

        for field, invalid_value in (
            ("kernel_state", "rejected"),
            ("claim_id_state", "pending_review"),
            ("admission_state", "not_admitted"),
        ):
            invalid = copy.deepcopy(self.fixture)
            invalid[field] = invalid_value
            self.assert_error_code(
                "package_state",
                lambda value=invalid: ingest_claim_ir_package(
                    compact_json_bytes(value),
                    repo_root=REPO_ROOT,
                    authority=activated_in_memory_authority(),
                ),
            )

    def test_valid_in_memory_transition_changes_only_kernel_state(self):
        authority = activated_in_memory_authority()
        authority_before = copy.deepcopy(authority)

        result = ingest_claim_ir_package(
            self.fixture_bytes,
            repo_root=REPO_ROOT,
            authority=authority,
        )

        expected = copy.deepcopy(self.fixture)
        expected["kernel_state"] = "ingested_under_separate_authority"
        self.assertEqual(expected, result["ingested_package"])
        self.assertEqual(authority_before, authority)
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

        receipt = result["receipt"]
        self.assertEqual(
            "sanitized_in_memory_test_only",
            receipt["receipt_scope"],
        )
        self.assertEqual(
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            receipt["effective_consumer_contract"]["sha256"],
        )
        self.assertEqual(
            ADMITTED_FIXTURE_SHA256,
            receipt["input"]["sha256"],
        )
        self.assertEqual(
            {
                "field": "package.kernel_state",
                "before": "pending_kernel_schema",
                "after": "ingested_under_separate_authority",
            },
            receipt["state_transition"],
        )
        self.assertTrue(all(receipt["identity_preservation"].values()))
        self.assertTrue(
            receipt["transaction"]["kernel_intake_committed_in_memory_test_double"]
        )
        self.assertFalse(receipt["transaction"]["production_kernel_store_write"])
        self.assertTrue(all(value is False for value in receipt["side_effects"].values()))
        self.assertNotIn("claims", receipt)
        self.assertNotIn("claim_values", receipt)


if __name__ == "__main__":
    unittest.main()
