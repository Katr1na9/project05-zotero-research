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

    @staticmethod
    def holdout_case_dirs():
        root = EXPERIMENT_ROOT / "real_cases"
        return sorted(
            path
            for path in root.iterdir()
            if path.is_dir()
            and path.name.startswith(
                ("C07-", "C08-", "C09-", "C10-", "C11-", "C12-")
            )
        )

    def test_c07_c10_gold_claims_use_declared_schema_vocabulary(self):
        properties = self.schema["properties"]
        source_types = set(properties["source_type"]["enum"])
        claim_types = set(properties["claim_type"]["enum"])
        strengths = set(properties["evidence_strength"]["enum"])
        entity_types = set(self.schema["$defs"]["entity_type"]["enum"])
        required = set(self.schema["required"])
        case_dirs = self.holdout_case_dirs()
        self.assertEqual(
            [
                "C07-darpa-e5-theia-0515",
                "C08-darpa-e5-clearscope-0515",
                "C09-darpa-optc-sysclient0201-0923",
                "C10-darpa-optc-sysclient0351-0925",
                "C11-otrf-apt29-day1-scranton-nashua",
                "C12-witfoo-precinct6-f10c7270",
            ],
            [path.name for path in case_dirs],
        )

        for case_dir in case_dirs:
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

    def test_c07_c10_gold_claims_pass_full_json_schema_validation(self):
        validator = Draft202012Validator(
            self.schema,
            format_checker=FormatChecker(),
        )
        for case_dir in self.holdout_case_dirs():
            claims = json.loads(
                (case_dir / "evidence_claims.json").read_text(encoding="utf-8")
            )
            for claim in claims:
                with self.subTest(case=case_dir.name, claim=claim["claim_id"]):
                    validator.validate(claim)


if __name__ == "__main__":
    unittest.main()
