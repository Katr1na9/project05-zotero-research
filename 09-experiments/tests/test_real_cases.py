import json
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
REAL_CASES_DIR = EXPERIMENT_DIR / "real_cases"
EXPECTED = {
    "C04-darpa-e3-fivedirections": "G3_campaign",
    "C05-darpa-e3-cadets": "G2_tactic_intent",
}


class RealCaseIntegrityTests(unittest.TestCase):
    def test_real_cases_are_complete_and_cross_referenced(self):
        for folder_name, ceiling in EXPECTED.items():
            with self.subTest(case=folder_name):
                case_dir = REAL_CASES_DIR / folder_name
                self.assertTrue(
                    case_dir.is_dir(),
                    f"Missing real case directory: {folder_name}",
                )
                config = self.load(case_dir / "case_config.json")
                claims = self.load(case_dir / "evidence_claims.json")
                actions = self.load(case_dir / "acquisition_actions.json")
                spec = self.load(case_dir / "motif_spec.json")

                self.assertEqual(8, len(spec["motifs"]))
                self.assertEqual(8, len(claims))
                self.assertEqual(ceiling, config["target_granularity"])
                self.assertEqual(ceiling, config["support_ceiling"])

                claim_ids = {
                    claim["claim_id"]
                    for claim in claims
                }
                hideable_ids = {
                    claim["claim_id"]
                    for claim in claims
                    if "hideable" in claim.get("tags", [])
                }
                for claim in claims:
                    self.assertIn("real_cdm", claim.get("tags", []))
                    self.assertIn(
                        "representative_event_uuids=",
                        claim["notes"],
                    )
                for node in config["cti_nodes"]:
                    self.assertTrue(
                        set(node["required_claim_ids"]) <= claim_ids
                    )
                for action in actions:
                    self.assertTrue(
                        set(action["recoverable_claim_ids"])
                        <= hideable_ids
                    )
                self.assertTrue(
                    set(config["discriminative_claim_ids"])
                    <= hideable_ids
                )

    @staticmethod
    def load(path):
        return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
