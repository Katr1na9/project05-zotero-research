import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


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
                with self.assertRaises(Exception):
                    self.decoder_validator.validate(document)
                with self.assertRaises(CandidateClaimIRValidationError):
                    validate_candidate_claim_ir(document)

    def test_every_decoder_accepted_boundary_document_is_canonical(self):
        valid = load_fixture("valid_candidate_unbound.json")
        boundary_documents = [
            valid,
            {**valid, "binding_status": "ambiguous"},
            {**valid, "modality": "observed"},
            {**valid, "modality": "invented"},
            {**valid, "compatibility_status": "kernel_compatible"},
            {**valid, "extra": True},
        ]

        for index, document in enumerate(boundary_documents):
            with self.subTest(index=index):
                if self.decoder_validator.is_valid(document):
                    self.assertIs(document, validate_candidate_claim_ir(document))


if __name__ == "__main__":
    unittest.main()
