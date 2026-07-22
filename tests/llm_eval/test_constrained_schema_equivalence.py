import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.constrained_decoder.canonical_validator import (
        CANDIDATE_CLAIM_IR_SCHEMA,
        CandidateClaimIRValidationError,
        validate_candidate_claim_ir,
    )
    from compiler.constrained_decoder.schema_projection import (
        build_decoder_compatibility_schema,
    )
except ModuleNotFoundError:
    CANDIDATE_CLAIM_IR_SCHEMA = None
    CandidateClaimIRValidationError = ValueError
    validate_candidate_claim_ir = None
    build_decoder_compatibility_schema = None


FIXTURES = Path(__file__).resolve().parents[1] / "compiler_contract" / "fixtures"
VALID_FIXTURES = (
    "valid_candidate_unbound.json",
    "valid_candidate_ambiguous.json",
)
INVALID_FIXTURES = (
    "invalid_unknown_field.json",
    "invalid_wrong_type.json",
    "invalid_authority_leakage.json",
    "invalid_modality_leakage.json",
    "invalid_pointer_suggestion.json",
    "invalid_candidate_constants.json",
)


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ConstrainedSchemaEquivalenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(build_decoder_compatibility_schema)
        self.decoder_schema = build_decoder_compatibility_schema()
        self.decoder_validator = Draft202012Validator(self.decoder_schema)

    def test_projection_is_a_detached_decoder_facing_view(self):
        self.assertEqual(CANDIDATE_CLAIM_IR_SCHEMA, self.decoder_schema)
        self.assertIsNot(CANDIDATE_CLAIM_IR_SCHEMA, self.decoder_schema)
        self.decoder_schema["properties"]["candidate_id"]["type"] = "number"
        self.assertEqual(
            "string",
            CANDIDATE_CLAIM_IR_SCHEMA["properties"]["candidate_id"]["type"],
        )

    def test_canonical_and_decoder_views_accept_the_same_valid_fixtures(self):
        for fixture_name in VALID_FIXTURES:
            with self.subTest(fixture=fixture_name):
                document = load_fixture(fixture_name)
                self.decoder_validator.validate(document)
                self.assertIs(document, validate_candidate_claim_ir(document))

    def test_decoder_view_rejects_all_canonical_invalid_fixtures(self):
        for fixture_name in INVALID_FIXTURES:
            with self.subTest(fixture=fixture_name):
                document = load_fixture(fixture_name)
                with self.assertRaises(ValidationError):
                    self.decoder_validator.validate(document)
                with self.assertRaises(CandidateClaimIRValidationError):
                    validate_candidate_claim_ir(document)

    def test_boundary_matrix_has_matching_canonical_and_decoder_results(self):
        valid = load_fixture("valid_candidate_unbound.json")
        wrong_allowed = copy.deepcopy(valid)
        wrong_allowed["certification_authority"]["allowed"] = True
        wrong_levels = copy.deepcopy(valid)
        wrong_levels["certification_authority"]["levels"] = ["case"]
        inconsistent_pointer = copy.deepcopy(valid)
        inconsistent_pointer["binding_status"] = "ambiguous"
        nested_unknown = copy.deepcopy(valid)
        nested_unknown["claim"]["modality"] = "observed"
        contradictory_without_status = copy.deepcopy(valid)
        contradictory_without_status["contradict_claim_ids"] = ["candidate-002"]
        boundary_documents = {
            "valid": (valid, True),
            "unknown top-level": ({**valid, "extra": True}, False),
            "wrong candidate constant": (
                {**valid, "admission_status": "admitted"},
                False,
            ),
            "authority allowed": (wrong_allowed, False),
            "authority levels": (wrong_levels, False),
            "invalid binding state": ({**valid, "binding_status": "bound"}, False),
            "pointer inconsistency": (inconsistent_pointer, False),
            "nested unknown claim field": (nested_unknown, False),
            "contradiction without conflicted status": (
                contradictory_without_status,
                False,
            ),
        }

        for case, (document, expected) in boundary_documents.items():
            with self.subTest(case=case):
                decoder_accepts = self.decoder_validator.is_valid(document)
                try:
                    validate_candidate_claim_ir(document)
                    canonical_accepts = True
                except CandidateClaimIRValidationError:
                    canonical_accepts = False
                self.assertEqual(expected, decoder_accepts)
                self.assertEqual(expected, canonical_accepts)

    def test_mutating_exported_canonical_schema_cannot_widen_new_decoder_views(self):
        original = copy.deepcopy(CANDIDATE_CLAIM_IR_SCHEMA)
        document = load_fixture("valid_candidate_unbound.json")
        document["extra"] = True
        try:
            CANDIDATE_CLAIM_IR_SCHEMA["additionalProperties"] = True

            fresh_schema = build_decoder_compatibility_schema()
            fresh_validator = Draft202012Validator(fresh_schema)

            self.assertFalse(fresh_schema["additionalProperties"])
            with self.assertRaises(ValidationError):
                fresh_validator.validate(document)
            with self.assertRaises(CandidateClaimIRValidationError):
                validate_candidate_claim_ir(document)
        finally:
            CANDIDATE_CLAIM_IR_SCHEMA.clear()
            CANDIDATE_CLAIM_IR_SCHEMA.update(original)


if __name__ == "__main__":
    unittest.main()
