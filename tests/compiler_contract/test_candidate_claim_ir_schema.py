import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.constrained_decoder.canonical_validator import (
        CANDIDATE_CLAIM_IR_SCHEMA,
        CandidateClaimIRValidationError,
        validate_candidate_claim_ir,
    )
except ModuleNotFoundError:
    CANDIDATE_CLAIM_IR_SCHEMA = None
    CandidateClaimIRValidationError = ValueError
    validate_candidate_claim_ir = None


FIXTURES = Path(__file__).with_name("fixtures")


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class CandidateClaimIRSchemaTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            validate_candidate_claim_ir,
            "canonical Candidate Claim IR validator has not been implemented",
        )

    def test_local_schema_and_validator_are_available(self):
        self.assertIsNotNone(CANDIDATE_CLAIM_IR_SCHEMA)
        self.assertIsNotNone(validate_candidate_claim_ir)
        self.assertEqual(
            "pending_kernel_schema",
            CANDIDATE_CLAIM_IR_SCHEMA["properties"]["compatibility_status"]["const"],
        )

    def test_accepts_valid_candidate_fixtures_without_mutation(self):
        for fixture_name in (
            "valid_candidate_unbound.json",
            "valid_candidate_ambiguous.json",
        ):
            with self.subTest(fixture=fixture_name):
                document = load_fixture(fixture_name)
                original = copy.deepcopy(document)
                self.assertIs(document, validate_candidate_claim_ir(document))
                self.assertEqual(original, document)

    def test_rejects_each_fail_closed_fixture(self):
        invalid_fixtures = {
            "invalid_unknown_field.json": "unknown",
            "invalid_wrong_type.json": "candidate_id",
            "invalid_authority_leakage.json": "certification_authority",
            "invalid_modality_leakage.json": "modality",
            "invalid_pointer_suggestion.json": "pointer_suggestion",
            "invalid_candidate_constants.json": "admission_status",
        }
        for fixture_name, message in invalid_fixtures.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaisesRegex(CandidateClaimIRValidationError, message):
                    validate_candidate_claim_ir(load_fixture(fixture_name))

    def test_rejects_binding_status_that_disagrees_with_pointer_suggestion(self):
        document = load_fixture("valid_candidate_unbound.json")
        document["binding_status"] = "ambiguous"

        with self.assertRaisesRegex(CandidateClaimIRValidationError, "binding_status"):
            validate_candidate_claim_ir(document)

    def test_rejects_noncanonical_epistemic_role_and_truth_status(self):
        for field, value in (
            ("epistemic_role", "model_selected_case_fact"),
            ("truth_status", "certain"),
        ):
            with self.subTest(field=field):
                document = load_fixture("valid_candidate_unbound.json")
                document[field] = value
                with self.assertRaisesRegex(CandidateClaimIRValidationError, field):
                    validate_candidate_claim_ir(document)

    def test_validator_source_has_no_model_runtime_dependency(self):
        module_path = SRC_ROOT / "compiler" / "constrained_decoder" / "canonical_validator.py"
        self.assertTrue(module_path.exists(), "canonical validator has not been implemented")
        source = module_path.read_text(encoding="utf-8").casefold()
        for forbidden_import in ("torch", "transformers", "peft"):
            with self.subTest(import_name=forbidden_import):
                self.assertNotIn(forbidden_import, source)

        self.assertIsNone(importlib.util.find_spec("compiler.constrained_decoder.runtime"))


if __name__ == "__main__":
    unittest.main()
