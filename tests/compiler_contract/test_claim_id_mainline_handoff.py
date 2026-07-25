import ast
import copy
import hashlib
import json
import unittest
from pathlib import Path

from src.compiler.llm.claim_id_mainline_handoff import (
    ASSISTED_DRAFT_SHA256,
    CLAIMS_CONTENT_HASH,
    CLAIM_COUNT,
    CLAIM_ID_LIST_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    EFFECTIVE_CONSUMER_CONTRACT_VERSION,
    FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS,
    HANDOFF_DESIGN_PATH,
    HANDOFF_DESIGN_SHA256,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    PACKAGE_ID,
    PRODUCTION_REGISTRATION_ENABLED,
    REVISION_PACKET_SHA256,
    SANITIZED_RECEIPT_PATH,
    SANITIZED_RECEIPT_SHA256,
    SURFACE_ID,
    ClaimIDMainlineHandoffError,
    build_claim_id_mainline_handoff,
    verify_mainline_handoff_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = REPO_ROOT / INGESTED_FIXTURE_PATH
RECEIPT_PATH = REPO_ROOT / SANITIZED_RECEIPT_PATH


def effective_consumer_contract_ref() -> dict:
    return {
        "effective_artifact_id": EFFECTIVE_CONSUMER_CONTRACT_ARTIFACT_ID,
        "effective_version": EFFECTIVE_CONSUMER_CONTRACT_VERSION,
        "effective_sha256": EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    }


def pretty_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


class ClaimIDMainlineHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package_bytes = PACKAGE_PATH.read_bytes()
        cls.receipt_bytes = RECEIPT_PATH.read_bytes()
        cls.package = json.loads(cls.package_bytes.decode("utf-8"))
        cls.receipt = json.loads(cls.receipt_bytes.decode("utf-8"))

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ClaimIDMainlineHandoffError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def build(self, **overrides):
        arguments = {
            "package_bytes": self.package_bytes,
            "receipt_bytes": self.receipt_bytes,
            "repo_root": REPO_ROOT,
            "consumer_contract_ref": effective_consumer_contract_ref(),
        }
        arguments.update(overrides)
        return build_claim_id_mainline_handoff(**arguments)

    def test_pins_and_versioned_ingestion_artifacts(self):
        verify_mainline_handoff_pins(REPO_ROOT)

        self.assertEqual(
            HANDOFF_DESIGN_SHA256,
            hashlib.sha256((REPO_ROOT / HANDOFF_DESIGN_PATH).read_bytes()).hexdigest(),
        )
        self.assertEqual(
            INGESTED_FIXTURE_SHA256,
            hashlib.sha256(self.package_bytes).hexdigest(),
        )
        self.assertEqual(
            SANITIZED_RECEIPT_SHA256,
            hashlib.sha256(self.receipt_bytes).hexdigest(),
        )
        self.assertEqual(
            {ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256},
            set(FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS),
        )
        self.assertNotIn(
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            FORBIDDEN_NON_EFFECTIVE_CONTRACT_SHAS,
        )
        self.assertFalse(PRODUCTION_REGISTRATION_ENABLED)

    def test_module_has_no_persistent_write_or_registration_surface(self):
        source_path = (
            REPO_ROOT
            / "src"
            / "compiler"
            / "llm"
            / "claim_id_mainline_handoff.py"
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

        self.assertEqual(set(), observed)

    def test_valid_ingested_package_emits_only_minimal_identity_payload(self):
        package_before = bytes(self.package_bytes)
        receipt_before = bytes(self.receipt_bytes)

        payload = self.build()

        self.assertEqual(
            {
                "surface_id": SURFACE_ID,
                "package_id": PACKAGE_ID,
                "claim_reference": {
                    "claims_content_hash": CLAIMS_CONTENT_HASH,
                    "full_claim_id_list_sha256": CLAIM_ID_LIST_SHA256,
                    "claim_count": CLAIM_COUNT,
                },
                "claim_id_state": "minted_opaque",
                "admission_state": "admitted_under_separate_authority",
                "kernel_state": "ingested_under_separate_authority",
                "consumer_contract_ref": effective_consumer_contract_ref(),
            },
            payload,
        )
        self.assertEqual(package_before, self.package_bytes)
        self.assertEqual(receipt_before, self.receipt_bytes)
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            '"claims"',
            '"value"',
            '"label"',
            '"outcome"',
            '"oracle"',
            '"path"',
            '"certificate"',
            '"e_case"',
        ):
            self.assertNotIn(forbidden, serialized)

    def test_missing_and_unbound_consumer_contract_fail_closed(self):
        self.assert_error_code(
            "missing_consumer_contract",
            lambda: self.build(consumer_contract_ref=None),
        )

        unbound = effective_consumer_contract_ref()
        unbound["effective_sha256"] = None
        self.assert_error_code(
            "unbound_consumer_contract",
            lambda: self.build(consumer_contract_ref=unbound),
        )

        missing_pin = effective_consumer_contract_ref()
        del missing_pin["effective_sha256"]
        self.assert_error_code(
            "unbound_consumer_contract",
            lambda: self.build(consumer_contract_ref=missing_pin),
        )

    def test_non_ingested_and_wrong_package_identity_fail_closed(self):
        non_ingested = copy.deepcopy(self.package)
        non_ingested["kernel_state"] = "pending_kernel_schema"
        self.assert_error_code(
            "package_state",
            lambda: self.build(package_bytes=pretty_json_bytes(non_ingested)),
        )

        wrong_package = copy.deepcopy(self.package)
        wrong_package["package_id"] = "pkg_wrong"
        self.assert_error_code(
            "package_identity",
            lambda: self.build(package_bytes=pretty_json_bytes(wrong_package)),
        )

        byte_reencoded = json.dumps(
            self.package,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assertNotEqual(
            INGESTED_FIXTURE_SHA256, hashlib.sha256(byte_reencoded).hexdigest()
        )
        self.assert_error_code(
            "fixture_pin",
            lambda: self.build(package_bytes=byte_reencoded),
        )

    def test_wrong_or_non_effective_contract_sha_fails_closed(self):
        wrong = effective_consumer_contract_ref()
        wrong["effective_sha256"] = "0" * 64
        self.assert_error_code(
            "consumer_contract_pin",
            lambda: self.build(consumer_contract_ref=wrong),
        )

        for forbidden_sha in (ASSISTED_DRAFT_SHA256, REVISION_PACKET_SHA256):
            masquerading = effective_consumer_contract_ref()
            masquerading["effective_sha256"] = forbidden_sha
            self.assert_error_code(
                "non_effective_contract_identity",
                lambda value=masquerading: self.build(
                    consumer_contract_ref=value
                ),
            )

    def test_wrong_receipt_binding_and_bytes_fail_closed(self):
        wrong_binding = copy.deepcopy(self.receipt)
        wrong_binding["effective_consumer_contract"]["sha256"] = "f" * 64
        self.assert_error_code(
            "receipt_binding",
            lambda: self.build(receipt_bytes=pretty_json_bytes(wrong_binding)),
        )

        byte_reencoded = json.dumps(
            self.receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        self.assert_error_code(
            "receipt_pin",
            lambda: self.build(receipt_bytes=byte_reencoded),
        )


if __name__ == "__main__":
    unittest.main()
