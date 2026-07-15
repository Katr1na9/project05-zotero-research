import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = EXPERIMENT_ROOT / "data_schema"
CONTRACT_PATH = (
    EXPERIMENT_ROOT
    / "governance"
    / "contracts"
    / "llm-compiler-contract-v0.2.json"
)
CONFIG_PATH = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "experiment_config.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class LlmPhase1ContractTests(unittest.TestCase):
    def test_public_packet_schema_has_no_gold_or_canonical_claim_id(self):
        schema = load_json(SCHEMA_DIR / "llm_context_packet.schema.json")
        serialized = json.dumps(schema, sort_keys=True)

        self.assertNotIn("gold_claim_id", serialized)
        self.assertNotIn('"claim_id"', serialized)
        self.assertEqual("object", schema["type"])
        self.assertFalse(schema["additionalProperties"])
        self.assertIn("request_id", schema["required"])
        self.assertIn("records", schema["required"])

    def test_admission_is_g0_only_and_g1_is_scorer_only(self):
        contract = load_json(CONTRACT_PATH)

        self.assertEqual(
            "project05-llm-compiler-contract-v0.2",
            contract["contract_version"],
        )
        self.assertEqual("G0", contract["admission"]["maximum_gold_level"])
        self.assertEqual(
            ["score_llm_phase1.py"], contract["g1"]["authorized_readers"]
        )
        self.assertFalse(contract["structured_stage_2"]["raw_packet_visible"])
        self.assertFalse(
            contract["structured_stage_2"]["rejected_claims_visible"]
        )
        self.assertFalse(contract["structured_stage_2"]["private_gold_visible"])

    def test_multigold_match_fields_and_normalizer_are_frozen(self):
        contract = load_json(CONTRACT_PATH)

        self.assertEqual("any_acceptable_gold", contract["g1"]["match_policy"])
        self.assertEqual(
            ["unicode_nfkc", "strip", "collapse_whitespace", "casefold"],
            contract["g1"]["normalization"],
        )
        self.assertEqual(
            [
                "source_type",
                "subject.entity_type",
                "subject.value",
                "predicate",
                "object.entity_type",
                "object.value",
                "source_pointer.artifact_id",
                "source_pointer.record_id",
            ],
            contract["g1"]["match_fields"],
        )

    def test_four_repeat_conditions_and_call_budget_are_exact(self):
        config = load_json(CONFIG_PATH)

        self.assertEqual(
            [
                "general_compiler",
                "security_compiler",
                "general_structured",
                "general_direct",
            ],
            config["repeat_panel"]["conditions"],
        )
        self.assertEqual(256, config["call_budget"]["first_pass"])
        self.assertEqual(192, config["call_budget"]["repeat_diagnostic"])
        self.assertEqual(448, config["call_budget"]["maximum_formal"])
        self.assertEqual(
            "pre_model_infrastructure", config["status"]
        )

    def test_all_phase1_schemas_are_strict_objects(self):
        names = (
            "llm_context_packet.schema.json",
            "llm_compiler_result.schema.json",
            "llm_conclusion_result.schema.json",
            "llm_run_manifest.schema.json",
        )
        for name in names:
            with self.subTest(schema=name):
                schema = load_json(SCHEMA_DIR / name)
                self.assertEqual(
                    "https://json-schema.org/draft/2020-12/schema",
                    schema["$schema"],
                )
                self.assertEqual("object", schema["type"])
                self.assertFalse(schema["additionalProperties"])
                self.assertTrue(schema["required"])


if __name__ == "__main__":
    unittest.main()
