import importlib.util
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
SCORER_PATH = EXPERIMENT_ROOT / "scripts" / "score_llm_phase1.py"


def load_scorer():
    spec = importlib.util.spec_from_file_location("score_llm_phase1", SCORER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


scorer = load_scorer()


def observation(subject, predicate, object_value, record_id="event-1"):
    return {
        "source_type": "local_log",
        "subject": {"entity_type": "process", "value": subject},
        "predicate": predicate,
        "object": {"entity_type": "file", "value": object_value},
        "source_pointer": {
            "artifact_id": "SRC-C07-01",
            "record_id": record_id,
        },
    }


class MultiGoldScoringTests(unittest.TestCase):
    def test_candidate_matches_any_acceptable_gold_after_frozen_normalization(self):
        candidate = observation(
            " PowerShell.EXE ", "CREATED", " C:\\Temp\\A.zip ", "event-1"
        )
        gold = [
            observation("other.exe", "connected", "10.0.0.1", "event-2"),
            observation(
                "powershell.exe", "created", "C:\\Temp\\A.zip", "EVENT-1"
            ),
        ]

        self.assertTrue(scorer.matches_any_acceptable_gold(candidate, gold))

    def test_partial_field_match_is_not_semantic_match(self):
        candidate = observation(
            "powershell.exe", "created", "C:\\Temp\\wrong.zip", "event-1"
        )
        gold = [
            observation(
                "powershell.exe", "created", "C:\\Temp\\A.zip", "event-1"
            )
        ]

        self.assertFalse(scorer.matches_any_acceptable_gold(candidate, gold))

    def test_positive_proxy_rejects_any_outside_gold_candidate(self):
        good = observation("powershell.exe", "created", "C:\\Temp\\A.zip")
        unsupported = observation(
            "powershell.exe", "created", "C:\\Temp\\other.zip"
        )
        packet = {
            "case_id": "C07-evaluation-case",
            "packet_role": "positive",
            "compiler_status": "completed",
        }
        private = {"acceptable_observations": [good]}

        result = scorer.score_project_gold_packet(
            packet, [good, unsupported], private
        )

        self.assertFalse(result["packet_success"])
        self.assertEqual(1, result["matched_count"])
        self.assertEqual(1, result["unsupported_count"])

    def test_null_proxy_requires_explicit_abstain_and_zero_claims(self):
        private = {"acceptable_observations": []}
        completed_empty = {
            "case_id": "C07-evaluation-case",
            "packet_role": "null",
            "compiler_status": "completed",
        }
        abstained = dict(completed_empty, compiler_status="abstain")

        self.assertFalse(
            scorer.score_project_gold_packet(completed_empty, [], private)[
                "packet_success"
            ]
        )
        self.assertTrue(
            scorer.score_project_gold_packet(abstained, [], private)[
                "packet_success"
            ]
        )

    def test_case_macro_is_unweighted_across_cases(self):
        rows = [
            {"case_id": "C07", "score": 1.0},
            {"case_id": "C07", "score": 1.0},
            {"case_id": "C08", "score": 0.0},
        ]

        self.assertEqual(0.5, scorer.case_macro(rows, "score"))

    def test_g2_absence_forbids_gps_and_ucr_names(self):
        report = scorer.name_metrics(
            {"agreement": 0.5, "ceiling": 0.1, "invalid_pointer": 0.0},
            g2_valid=False,
        )

        self.assertNotIn("GPS", report)
        self.assertNotIn("UCR", report)
        self.assertIn("project_gold_packet_agreement", report)
        self.assertIn("ceiling_violation_rate", report)

    def test_g2_valid_ucr_uses_unsupported_rate_not_ceiling_rate(self):
        report = scorer.name_metrics(
            {
                "agreement": 0.7,
                "unsupported": 0.2,
                "ceiling": 0.1,
                "invalid_pointer": 0.0,
            },
            g2_valid=True,
        )

        self.assertEqual(0.2, report["UCR"])
        self.assertEqual(0.1, report["ceiling_violation_rate"])


class ClaimGateTests(unittest.TestCase):
    def passing_summary(self):
        return {
            "llm_over_rule": {
                "delta_gps": 0.05,
                "noninferior_cases": 4,
                "case_count": 6,
                "unsupported_rate_no_worse": True,
                "invalid_pointer_rate_no_worse": True,
                "refusal_only_win": False,
            },
            "structured_over_direct": {
                "delta_ucr": -0.05,
                "favorable_cases": 4,
                "case_count": 6,
                "positive_coverage_drop": 0.05,
            },
        }

    def test_all_three_gates_are_required_for_title(self):
        gates = scorer.evaluate_claim_gates(
            self.passing_summary(),
            {"valid": True, "kappa": 0.70, "unassessable_rate": 0.20},
        )

        self.assertTrue(gates["g2_gate"])
        self.assertTrue(gates["llm_over_rule"])
        self.assertTrue(gates["structured_over_direct"])
        self.assertTrue(gates["title_gate"])
        self.assertEqual([], gates["failure_reasons"])

    def test_empty_or_invalid_inputs_never_default_positive(self):
        gates = scorer.evaluate_claim_gates({}, {"valid": False})

        self.assertFalse(gates["g2_gate"])
        self.assertFalse(gates["llm_over_rule"])
        self.assertFalse(gates["structured_over_direct"])
        self.assertFalse(gates["title_gate"])
        self.assertGreaterEqual(len(gates["failure_reasons"]), 3)

    def test_refusal_only_win_blocks_rule_gate(self):
        summary = self.passing_summary()
        summary["llm_over_rule"]["refusal_only_win"] = True

        gates = scorer.evaluate_claim_gates(summary, {"valid": True})

        self.assertFalse(gates["llm_over_rule"])
        self.assertFalse(gates["title_gate"])
        self.assertIn("llm_over_rule:refusal_only_win", gates["failure_reasons"])


if __name__ == "__main__":
    unittest.main()
