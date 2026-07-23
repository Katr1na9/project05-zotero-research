import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[2]
INTERFACE_PATH = ROOT / "src" / "ir" / "candidate-claim-ir-interface-v0.8.json"
MIGRATION_PATH = ROOT / "src" / "ir" / "migration-v0.8.md"
SCHEMA_PATH = ROOT / "schemas" / "claim-ir-kernel.schema.json"
EXPECTED_ERRORS = {
    "CKI-001_SCHEMA_VERSION_UNSUPPORTED",
    "CKI-002_SCHEMA_VALIDATION_FAILED",
    "CKI-003_PROTECTED_FIELD_SET",
    "CKI-004_POINTER_CONTEXT_MISMATCH",
    "CKI-005_BINDING_ABSTENTION_REQUIRED",
    "CKI-006_NON_CANDIDATE_STATUS",
    "CKI-007_MODALITY_OVERRIDE_ATTEMPT",
    "CKI-008_AUTHORITY_OVERRIDE_ATTEMPT",
    "CKI-009_GROUND_TRUTH_FIELD_FORBIDDEN",
}
EXPECTED_FORBIDDEN_FIELDS = {
    "claim_id",
    "modality",
    "truth_status",
    "epistemic_role",
    "certification_authority",
    "pointer",
    "compiler",
    "binding_status",
    "admission_status",
    "promotion_status",
    "promotion_event_id",
    "admissible_levels",
    "support_claim_ids",
    "contradict_claim_ids",
    "rule_trace",
    "confidence",
    "lifecycle_state",
}


def recursive_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from recursive_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from recursive_keys(child)


class CandidateClaimIRInterfaceTests(unittest.TestCase):
    def test_interface_binds_exact_schema_version_and_raw_file_hash(self):
        interface = json.loads(INTERFACE_PATH.read_text(encoding="utf-8"))
        actual = hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest()
        self.assertEqual("0.8.0", interface["interface_version"])
        self.assertEqual("0.8.0", interface["claim_schema_version"])
        self.assertEqual(actual, interface["claim_schema_sha256"])
        self.assertEqual(
            "schemas/claim-ir-kernel.schema.json#/$defs/candidateCompilerResponse",
            interface["compiler_response_schema_ref"],
        )

    def test_interface_examples_validate_and_exclude_kernel_owned_fields(self):
        interface = json.loads(INTERFACE_PATH.read_text(encoding="utf-8"))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        wrapper = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$defs": schema["$defs"],
            "$ref": "#/$defs/candidateCompilerResponse",
        }
        validator = Draft202012Validator(wrapper, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(interface["output_example"])))
        self.assertEqual(
            EXPECTED_FORBIDDEN_FIELDS,
            set(interface["compiler_forbidden_fields"]),
        )
        output_keys = set(recursive_keys(interface["output_example"]))
        self.assertTrue(output_keys.isdisjoint(interface["compiler_forbidden_fields"]))
        self.assertTrue(
            output_keys.isdisjoint(
                {"ground_truth", "recoverable_claim_ids", "oracle_effects", "hidden_claim_ids"}
            )
        )

    def test_interface_has_stable_required_fields_and_error_codes(self):
        interface = json.loads(INTERFACE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "schema_version",
                "request_id",
                "candidates",
            },
            set(interface["compiler_response_required_fields"]),
        )
        self.assertEqual(EXPECTED_ERRORS, set(interface["error_codes"]))
        self.assertEqual("candidate_only", interface["admission_boundary"])

    def test_migration_note_requires_explicit_adapter_not_silent_legacy_reuse(self):
        text = MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn("evidence_claim.schema.json", text)
        self.assertIn("acquisition_action.schema.json", text)
        self.assertIn("不得静默适配", text)
        self.assertIn("pointer", text)


if __name__ == "__main__":
    unittest.main()
