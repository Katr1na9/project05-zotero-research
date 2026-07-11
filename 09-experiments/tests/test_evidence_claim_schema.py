import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = EXPERIMENT_ROOT / "data_schema" / "evidence_claim.schema.json"


class EvidenceClaimSchemaVocabularyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_c07_c09_gold_claims_use_declared_schema_vocabulary(self):
        properties = self.schema["properties"]
        source_types = set(properties["source_type"]["enum"])
        claim_types = set(properties["claim_type"]["enum"])
        strengths = set(properties["evidence_strength"]["enum"])
        entity_types = set(self.schema["$defs"]["entity_type"]["enum"])
        required = set(self.schema["required"])

        for case_dir in sorted((EXPERIMENT_ROOT / "real_cases").glob("C0[789]-*")):
            claims = json.loads(
                (case_dir / "evidence_claims.json").read_text(encoding="utf-8")
            )
            for claim in claims:
                with self.subTest(case=case_dir.name, claim=claim["claim_id"]):
                    self.assertTrue(required <= set(claim))
                    self.assertIn(claim["source_type"], source_types)
                    self.assertIn(claim["claim_type"], claim_types)
                    self.assertIn(claim["evidence_strength"], strengths)
                    self.assertIn(claim["subject"]["entity_type"], entity_types)
                    self.assertIn(claim["object"]["entity_type"], entity_types)

    def test_c07_c09_gold_claims_pass_full_json_schema_validation(self):
        validator = Draft202012Validator(
            self.schema,
            format_checker=FormatChecker(),
        )
        for case_dir in sorted((EXPERIMENT_ROOT / "real_cases").glob("C0[789]-*")):
            claims = json.loads(
                (case_dir / "evidence_claims.json").read_text(encoding="utf-8")
            )
            for claim in claims:
                with self.subTest(case=case_dir.name, claim=claim["claim_id"]):
                    validator.validate(claim)


if __name__ == "__main__":
    unittest.main()
