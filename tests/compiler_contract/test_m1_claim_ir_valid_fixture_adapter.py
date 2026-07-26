import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.m1_claim_ir_valid_fixture_adapter import (  # noqa: E402
    ADAPTER_ID,
    ADAPTER_IMPLEMENTATION_PATH,
    ADAPTER_VERSION,
    CONSUMER_CONTRACT_SHA256,
    CONTRACT_SHA256,
    EXTERNAL_SCHEMA_ID,
    EXTERNAL_SCHEMA_PATH,
    EXTERNAL_SCHEMA_SHA256,
    FORBIDDEN_MINTED_PACKAGE_ID,
    KERNEL_SCHEMA_SHA256,
    M1_FRAMEWORK_SHA256,
    M1ClaimIRValidFixtureAdapterError,
    PLANNER_IMPLEMENTATION_PATH,
    PLANNER_IMPLEMENTATION_SHA256,
    RED_ACCEPTANCE_SHA256,
    SELECTION_DESIGN_SHA256,
    SOURCE_CLASS,
    SURFACE_ID,
    TEST_AUTHORITY_STATUS,
    adapt_claim_ir_valid_fixture,
    canonical_json_sha256,
    verify_adapter_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "m1_claim_ir_valid_fixture"
    / "synthetic_unminted_claim_ir_v0.1.json"
)
OPAQUE_REFERENCE = "fixture_ref_synthetic_001"
FIXTURE_ID = "fixture_synthetic_unminted_001"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def descriptor_for(fixture: dict) -> dict:
    manifest = fixture["manifest"]
    return {
        "surface_id": SURFACE_ID,
        "source_class": SOURCE_CLASS,
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "opaque_fixture_reference": OPAQUE_REFERENCE,
        "fixture_pin_declaration": {
            "fixture_id": FIXTURE_ID,
            "fixture_content_sha256": canonical_json_sha256(fixture),
            "claim_ir_schema_id": EXTERNAL_SCHEMA_ID,
            "claim_ir_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "projection_sha256": manifest["projection_sha256"],
            "content_hash": manifest["content_hash"],
        },
        "declared_claim_ir_fields": {
            "schema_version": fixture["schema_version"],
            "package_id": fixture["package_id"],
            "surface_id": fixture["surface_id"],
            "kernel_state": fixture["kernel_state"],
            "claim_id_state": fixture["claim_id_state"],
            "admission_state": fixture["admission_state"],
            "projection_sha256": manifest["projection_sha256"],
            "claim_count": manifest["claim_count"],
            "field_path_set": manifest["field_path_set"],
            "content_hash": manifest["content_hash"],
        },
    }


def registry_for(fixture: dict) -> dict:
    fixture_sha = canonical_json_sha256(fixture)
    return {
        OPAQUE_REFERENCE: {
            "fixture_id": FIXTURE_ID,
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "fixture_content_sha256": fixture_sha,
            "claim_ir_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "fixture": fixture,
            "test_only": True,
        }
    }


def test_authority(descriptor: dict) -> dict:
    return {
        "status": TEST_AUTHORITY_STATUS,
        "scope": {
            "test_only": True,
            "in_memory_only": True,
            "surface_id": SURFACE_ID,
            "source_class": SOURCE_CLASS,
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "registry_activation": False,
            "production_execute": False,
        },
        "pinned_hashes": {
            "red_acceptance_sha256": RED_ACCEPTANCE_SHA256,
            "adapter_contract_sha256": CONTRACT_SHA256,
            "m1_framework_sha256": M1_FRAMEWORK_SHA256,
            "selection_design_sha256": SELECTION_DESIGN_SHA256,
            "external_schema_sha256": EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
            "consumer_contract_sha256": CONSUMER_CONTRACT_SHA256,
            "adapter_implementation_sha256": hashlib.sha256(
                (REPO_ROOT / ADAPTER_IMPLEMENTATION_PATH).read_bytes()
            ).hexdigest(),
        },
        "pinned_inputs": {
            "descriptor_sha256": canonical_json_sha256(descriptor),
            "opaque_fixture_reference": descriptor["opaque_fixture_reference"],
            "fixture_content_sha256": descriptor["fixture_pin_declaration"][
                "fixture_content_sha256"
            ],
        },
        "output_policy": {
            "mode": "in_memory_structural_only",
            "file_write": False,
            "mint": False,
            "kernel_write": False,
            "e_case_write": False,
            "certificate": False,
            "certified_stop": False,
            "admission": False,
        },
        "still_blocked": {
            "effective_registry_activation": True,
            "production_single_execute": True,
            "claim_id_mint": True,
            "kernel_store_write": True,
            "e_case_write": True,
            "certificate_generation": True,
            "certified_stop": True,
            "durable_attach": True,
            "checker_non_null": True,
            "evidence_sufficiency_non_null": True,
            "production_registration_enablement": True,
            "l2_gate_change": True,
            "part_b_elevation": True,
            "m2": True,
            "four_family_finetune_or_kernel_admission": True,
        },
    }


def execution_bundle(fixture: dict) -> tuple[dict, dict, dict]:
    descriptor = descriptor_for(fixture)
    return descriptor, registry_for(fixture), test_authority(descriptor)


class M1ClaimIRValidFixtureAdapterTests(unittest.TestCase):
    def test_adapter_pins_and_planner_bytes_are_verified(self):
        verify_adapter_pins(REPO_ROOT)
        planner_sha = hashlib.sha256(
            (REPO_ROOT / PLANNER_IMPLEMENTATION_PATH).read_bytes()
        ).hexdigest()
        self.assertEqual(PLANNER_IMPLEMENTATION_SHA256, planner_sha)

    def test_synthetic_fixture_is_schema_valid_unminted_and_distinct(self):
        fixture = load_fixture()
        schema = json.loads(
            (REPO_ROOT / EXTERNAL_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        errors = list(Draft202012Validator(schema).iter_errors(fixture))

        self.assertEqual([], errors)
        self.assertNotEqual(FORBIDDEN_MINTED_PACKAGE_ID, fixture["package_id"])
        self.assertEqual("not_minted", fixture["claim_id_state"])
        self.assertEqual("not_admitted", fixture["admission_state"])
        self.assertEqual("pending_kernel_schema", fixture["kernel_state"])
        self.assertTrue(all(claim["claim_id"] is None for claim in fixture["claims"]))

    def test_missing_authority_rejects_before_registry_resolution(self):
        fixture = load_fixture()
        descriptor = descriptor_for(fixture)

        with self.assertRaises(M1ClaimIRValidFixtureAdapterError) as context:
            adapt_claim_ir_valid_fixture(
                descriptor,
                repo_root=REPO_ROOT,
                fixture_registry=registry_for(fixture),
            )

        self.assertEqual("missing_authority", context.exception.code)

    def test_valid_test_authority_returns_only_unminted_m0_envelope(self):
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)

        result = adapt_claim_ir_valid_fixture(
            descriptor,
            repo_root=REPO_ROOT,
            authority=authority,
            fixture_registry=registry,
        )

        self.assertEqual(fixture, result)
        self.assertIsNot(fixture, result)
        self.assertEqual(SURFACE_ID, result["surface_id"])
        self.assertEqual("not_minted", result["claim_id_state"])
        self.assertEqual("not_admitted", result["admission_state"])
        self.assertEqual("pending_kernel_schema", result["kernel_state"])
        self.assertTrue(all(claim["claim_id"] is None for claim in result["claims"]))
        self.assertFalse("adapter_id" in result)
        self.assertFalse("source_class" in result)

    def test_path_uri_raw_bytes_and_labels_fail_closed(self):
        fixture = load_fixture()
        valid_descriptor, registry, authority = execution_bundle(fixture)
        path_descriptor = copy.deepcopy(valid_descriptor)
        path_descriptor["filesystem_path"] = "C:\\private\\fixture.json"
        uri_descriptor = copy.deepcopy(valid_descriptor)
        uri_descriptor["opaque_fixture_reference"] = "https://example.invalid/fixture"
        bytes_descriptor = copy.deepcopy(valid_descriptor)
        bytes_descriptor["raw_bytes"] = b"fixture"
        label_descriptor = copy.deepcopy(valid_descriptor)
        label_descriptor["declared_claim_ir_fields"]["label"] = "ground_truth"

        for descriptor, expected_code in (
            (path_descriptor, "forbidden_descriptor_field"),
            (uri_descriptor, "path_or_uri"),
            (bytes_descriptor, "raw_bytes"),
            (label_descriptor, "forbidden_descriptor_field"),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    M1ClaimIRValidFixtureAdapterError
                ) as context:
                    adapt_claim_ir_valid_fixture(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_non_null_claim_admitted_state_and_minted_package_fail_closed(self):
        non_null = load_fixture()
        non_null["claims"][0]["claim_id"] = "clm_ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        admitted = load_fixture()
        admitted["admission_state"] = "admitted_under_separate_authority"
        admitted["claims"][0]["admission_state"] = (
            "admitted_under_separate_authority"
        )
        minted_package = load_fixture()
        minted_package["package_id"] = FORBIDDEN_MINTED_PACKAGE_ID

        for fixture, expected_code in (
            (non_null, "fixture_schema"),
            (admitted, "constant"),
            (minted_package, "minted_package_forbidden"),
        ):
            descriptor, registry, authority = execution_bundle(fixture)
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    M1ClaimIRValidFixtureAdapterError
                ) as context:
                    adapt_claim_ir_valid_fixture(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_bad_authority_pin_and_activation_ledger_fail_closed(self):
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)
        bad_pin = copy.deepcopy(authority)
        bad_pin["pinned_hashes"]["external_schema_sha256"] = "0" * 64
        ledger = copy.deepcopy(authority)
        ledger["execute_ledger"] = {
            "authorized": 1,
            "remaining": 1,
        }

        for candidate, expected_code in (
            (bad_pin, "authority_pin"),
            (ledger, "forbidden_authority_field"),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    M1ClaimIRValidFixtureAdapterError
                ) as context:
                    adapt_claim_ir_valid_fixture(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=candidate,
                        fixture_registry=registry,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_unknown_or_sha_mismatched_registry_record_fails_closed(self):
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)
        unknown = {"another_reference": next(iter(registry.values()))}
        mismatch = copy.deepcopy(registry)
        mismatch[OPAQUE_REFERENCE]["fixture_content_sha256"] = "0" * 64

        for candidate, expected_code in (
            (unknown, "unknown_fixture"),
            (mismatch, "constant"),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    M1ClaimIRValidFixtureAdapterError
                ) as context:
                    adapt_claim_ir_valid_fixture(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=candidate,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_protected_pins_are_byte_identical_before_and_after(self):
        protected = (
            REPO_ROOT / PLANNER_IMPLEMENTATION_PATH,
            REPO_ROOT
            / "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-multi-adapter-framework-design-v0.1-20260724.json",
            REPO_ROOT
            / "docs/llm-editor/"
            "llm-editor-v0.8-l2-m1-claim-ir-valid-fixture-adapter-contract-v0.1-20260726.json",
            REPO_ROOT / EXTERNAL_SCHEMA_PATH,
            REPO_ROOT / "schemas/claim-ir-kernel.schema.json",
        )
        before = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in protected
        }
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)

        adapt_claim_ir_valid_fixture(
            descriptor,
            repo_root=REPO_ROOT,
            authority=authority,
            fixture_registry=registry,
        )

        after = {
            path: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in protected
        }
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
