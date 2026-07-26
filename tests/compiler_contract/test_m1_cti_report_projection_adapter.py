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

from compiler.llm import m1_cti_report_projection_adapter as adapter  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    Path(__file__).with_name("fixtures")
    / "m1_evidence_modality"
    / "synthetic_cti_report_projection_v0.1.json"
)
FIXTURE_ID = "fixture_cti_report_projection_001"


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def descriptor_for(fixture: dict) -> dict:
    return {
        "surface_id": adapter.SURFACE_ID,
        "source_class": adapter.SOURCE_CLASS,
        "adapter_id": adapter.ADAPTER_ID,
        "adapter_version": adapter.ADAPTER_VERSION,
        "opaque_projection_reference": fixture["descriptor"][
            "opaque_record_reference"
        ],
        "projection_pin_declaration": {
            "projection_path": adapter.PROJECTION_PATH,
            "projection_sha256": adapter.PROJECTION_SHA256,
            "fixture_id": FIXTURE_ID,
            "fixture_content_sha256": adapter.canonical_json_sha256(fixture),
        },
        "declared_projected_fields": copy.deepcopy(fixture),
    }


def registry_for(fixture: dict) -> dict:
    reference = fixture["descriptor"]["opaque_record_reference"]
    return {
        reference: {
            "fixture_id": FIXTURE_ID,
            "surface_id": adapter.SURFACE_ID,
            "source_class": adapter.SOURCE_CLASS,
            "fixture_content_sha256": adapter.canonical_json_sha256(fixture),
            "fixture": copy.deepcopy(fixture),
            "test_only": True,
        }
    }


def authority_for(descriptor: dict) -> dict:
    return {
        "status": adapter.TEST_AUTHORITY_STATUS,
        "scope": {
            "test_only": True,
            "in_memory_only": True,
            "surface_id": adapter.SURFACE_ID,
            "source_class": adapter.SOURCE_CLASS,
            "adapter_id": adapter.ADAPTER_ID,
            "adapter_version": adapter.ADAPTER_VERSION,
            "registry_activation": False,
            "production_execute": False,
        },
        "pinned_hashes": {
            "red_acceptance_sha256": adapter.RED_ACCEPTANCE_SHA256,
            "framework_sha256": adapter.FRAMEWORK_SHA256,
            "projection_sha256": adapter.PROJECTION_SHA256,
            "adapter_contract_sha256": adapter.CONTRACT_SHA256,
            "external_schema_sha256": adapter.EXTERNAL_SCHEMA_SHA256,
            "kernel_schema_sha256": adapter.KERNEL_SCHEMA_SHA256,
            "consumer_contract_sha256": adapter.CONSUMER_CONTRACT_SHA256,
            "m0_projection_sha256": adapter.M0_PROJECTION_SHA256,
            "adapter_implementation_sha256": hashlib.sha256(
                (REPO_ROOT / adapter.ADAPTER_IMPLEMENTATION_PATH).read_bytes()
            ).hexdigest(),
            "support_implementation_sha256": (
                adapter.SUPPORT_IMPLEMENTATION_SHA256
            ),
        },
        "pinned_inputs": {
            "descriptor_sha256": adapter.canonical_json_sha256(descriptor),
            "opaque_projection_reference": descriptor[
                "opaque_projection_reference"
            ],
            "fixture_content_sha256": descriptor[
                "projection_pin_declaration"
            ]["fixture_content_sha256"],
        },
        "output_policy": {
            "mode": "in_memory_structural_only",
            "file_write": False,
            "raw_source_read": False,
            "raw_source_persist": False,
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
            "activation_ledger_write": True,
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
    return descriptor, registry_for(fixture), authority_for(descriptor)


class M1CTIReportProjectionAdapterTests(unittest.TestCase):
    def test_pins_and_existing_ingress_bytes_are_exact(self):
        adapter.verify_adapter_pins(REPO_ROOT)
        expected = {
            adapter.RED_ACCEPTANCE_PATH: adapter.RED_ACCEPTANCE_SHA256,
            adapter.FRAMEWORK_PATH: adapter.FRAMEWORK_SHA256,
            adapter.PROJECTION_PATH: adapter.PROJECTION_SHA256,
            adapter.CONTRACT_PATH: adapter.CONTRACT_SHA256,
            adapter.EXTERNAL_SCHEMA_PATH: adapter.EXTERNAL_SCHEMA_SHA256,
            adapter.KERNEL_SCHEMA_PATH: adapter.KERNEL_SCHEMA_SHA256,
            adapter.PLANNER_IMPLEMENTATION_PATH: (
                adapter.PLANNER_IMPLEMENTATION_SHA256
            ),
            adapter.VALID_FIXTURE_IMPLEMENTATION_PATH: (
                adapter.VALID_FIXTURE_IMPLEMENTATION_SHA256
            ),
            adapter.SUPPORT_IMPLEMENTATION_PATH: (
                adapter.SUPPORT_IMPLEMENTATION_SHA256
            ),
        }
        actual = {
            path: hashlib.sha256((REPO_ROOT / path).read_bytes()).hexdigest()
            for path in expected
        }
        self.assertEqual(expected, actual)

    def test_fixture_is_reported_declaration_only(self):
        fixture = load_fixture()
        self.assertIs(fixture["report"]["reported_marker"], True)
        self.assertEqual(
            "reported",
            fixture["source_metadata"]["epistemic_modality"],
        )
        text = json.dumps(fixture, sort_keys=True)
        for forbidden in (
            '"body"',
            '"full_text"',
            '"raw_stix"',
            '"payload"',
            '"labels"',
            '"secret"',
        ):
            self.assertNotIn(forbidden, text)

    def test_missing_authority_rejects(self):
        fixture = load_fixture()
        with self.assertRaises(
            adapter.M1CTIReportProjectionAdapterError
        ) as context:
            adapter.adapt_cti_report_projection(
                descriptor_for(fixture),
                repo_root=REPO_ROOT,
                fixture_registry=registry_for(fixture),
            )
        self.assertEqual("missing_authority", context.exception.code)

    def test_happy_path_returns_schema_valid_unminted_envelope(self):
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)
        result = adapter.adapt_cti_report_projection(
            descriptor,
            repo_root=REPO_ROOT,
            authority=authority,
            fixture_registry=registry,
        )
        schema = json.loads(
            (REPO_ROOT / adapter.EXTERNAL_SCHEMA_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual([], list(Draft202012Validator(schema).iter_errors(result)))
        self.assertEqual("not_minted", result["claim_id_state"])
        self.assertEqual("not_admitted", result["admission_state"])
        self.assertEqual("pending_kernel_schema", result["kernel_state"])
        self.assertEqual([], result["claims"])
        self.assertEqual(adapter.PROJECTION_SHA256, result["manifest"]["projection_sha256"])
        self.assertNotIn("report", result)

    def test_observed_and_derived_modality_laundering_fail_closed(self):
        for modality in ("observed", "derived"):
            fixture = load_fixture()
            fixture["source_metadata"]["epistemic_modality"] = modality
            descriptor, registry, authority = execution_bundle(fixture)
            with self.subTest(modality=modality):
                with self.assertRaises(
                    adapter.M1CTIReportProjectionAdapterError
                ) as context:
                    adapter.adapt_cti_report_projection(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual("modality_laundering", context.exception.code)

    def test_false_reported_marker_and_unknown_field_fail_closed(self):
        marker = load_fixture()
        marker["report"]["reported_marker"] = False
        unknown = load_fixture()
        unknown["report"]["unexpected"] = "x"
        for fixture, expected_code in (
            (marker, "constant"),
            (unknown, "unknown_field"),
        ):
            descriptor, registry, authority = execution_bundle(fixture)
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    adapter.M1CTIReportProjectionAdapterError
                ) as context:
                    adapter.adapt_cti_report_projection(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_path_uri_raw_bytes_labels_and_secrets_fail_closed(self):
        fixture = load_fixture()
        valid, registry, authority = execution_bundle(fixture)
        cases = []
        path_case = copy.deepcopy(valid)
        path_case["declared_projected_fields"]["filesystem_path"] = "/private/c"
        cases.append((path_case, "forbidden_descriptor_field"))
        uri_case = copy.deepcopy(valid)
        uri_case["declared_projected_fields"]["report"]["publisher_ref"] = (
            "https://example.invalid"
        )
        cases.append((uri_case, "path_or_uri"))
        bytes_case = copy.deepcopy(valid)
        bytes_case["declared_projected_fields"]["report"]["raw_bytes"] = b"x"
        cases.append((bytes_case, "forbidden_descriptor_field"))
        label_case = copy.deepcopy(valid)
        label_case["declared_projected_fields"]["labels"] = ["truth"]
        cases.append((label_case, "forbidden_descriptor_field"))
        secret_case = copy.deepcopy(valid)
        secret_case["declared_projected_fields"]["secret"] = "x"
        cases.append((secret_case, "forbidden_descriptor_field"))
        for candidate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    adapter.M1CTIReportProjectionAdapterError
                ) as context:
                    adapter.adapt_cti_report_projection(
                        candidate,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_non_null_claim_id_admission_and_ledger_fail_closed(self):
        for field, value in (
            ("claim_id", "clm_ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            ("admission_state", "admitted_under_separate_authority"),
        ):
            fixture = load_fixture()
            fixture[field] = value
            descriptor, registry, authority = execution_bundle(fixture)
            with self.subTest(field=field):
                with self.assertRaises(
                    adapter.M1CTIReportProjectionAdapterError
                ) as context:
                    adapter.adapt_cti_report_projection(
                        descriptor,
                        repo_root=REPO_ROOT,
                        authority=authority,
                        fixture_registry=registry,
                    )
                self.assertEqual("authority_elevation", context.exception.code)

        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)
        authority["activation_ledger"] = {"remaining": 1}
        with self.assertRaises(
            adapter.M1CTIReportProjectionAdapterError
        ) as context:
            adapter.adapt_cti_report_projection(
                descriptor,
                repo_root=REPO_ROOT,
                authority=authority,
                fixture_registry=registry,
            )
        self.assertEqual("forbidden_authority_field", context.exception.code)

    def test_registry_hash_mismatch_fails_closed(self):
        fixture = load_fixture()
        descriptor, registry, authority = execution_bundle(fixture)
        registry[descriptor["opaque_projection_reference"]][
            "fixture_content_sha256"
        ] = "0" * 64
        with self.assertRaises(
            adapter.M1CTIReportProjectionAdapterError
        ) as context:
            adapter.adapt_cti_report_projection(
                descriptor,
                repo_root=REPO_ROOT,
                authority=authority,
                fixture_registry=registry,
            )
        self.assertEqual("constant", context.exception.code)


if __name__ == "__main__":
    unittest.main()
