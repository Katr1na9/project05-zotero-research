from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def rational(value: dict[str, int]) -> Fraction:
    return Fraction(value["numerator"], value["denominator"])


class PartBB2StochasticObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog_schema = load_json(
            SCHEMA_DIR / "part-b-stochastic-observation-catalog.schema.json"
        )
        cls.policy_schema = load_json(
            SCHEMA_DIR / "part-b-stochastic-tv-policy.schema.json"
        )
        cls.catalog = load_yaml(
            CONFIG_DIR / "part-b-stochastic-observation-catalog-v0.8.yaml"
        )
        cls.policy = load_yaml(
            CONFIG_DIR / "part-b-stochastic-tv-policy-v0.8.yaml"
        )

    def test_catalog_domains_are_finite_unique_and_complete(self) -> None:
        self.assertEqual(
            self.catalog["domain_kind"],
            "FINITE_EXACT_CONTRACT_EXAMPLES",
        )
        self.assertGreaterEqual(len(self.catalog["entries"]), 1)
        action_ids = [entry["action_id"] for entry in self.catalog["entries"]]
        self.assertEqual(len(action_ids), len(set(action_ids)))

        for entry in self.catalog["entries"]:
            worlds = entry["finite_worlds"]
            outcomes = entry["finite_outcomes"]
            rows = entry["conditional_distribution"]
            self.assertEqual(len(worlds), len(set(worlds)))
            self.assertEqual(len(outcomes), len(set(outcomes)))
            self.assertEqual({row["world_id"] for row in rows}, set(worlds))
            for row in rows:
                self.assertEqual(
                    {item["outcome_id"] for item in row["probabilities"]},
                    set(outcomes),
                )

    def test_probability_rows_use_exact_rationals_and_normalize(self) -> None:
        self.assertEqual(self.catalog["probability_encoding"], "EXACT_RATIONAL")
        for entry in self.catalog["entries"]:
            for row in entry["conditional_distribution"]:
                probabilities = [
                    rational(item["probability"])
                    for item in row["probabilities"]
                ]
                self.assertTrue(all(value >= 0 for value in probabilities))
                self.assertEqual(sum(probabilities, Fraction(0, 1)), Fraction(1, 1))

    def test_registered_design_tv_replays_exactly(self) -> None:
        for entry in self.catalog["entries"]:
            rows = {
                row["world_id"]: {
                    item["outcome_id"]: rational(item["probability"])
                    for item in row["probabilities"]
                }
                for row in entry["conditional_distribution"]
            }
            for comparison in entry["design_tv_comparisons"]:
                left = rows[comparison["left_world_id"]]
                right = rows[comparison["right_world_id"]]
                tv = sum(
                    abs(left[outcome] - right[outcome])
                    for outcome in entry["finite_outcomes"]
                ) / 2
                self.assertEqual(tv, rational(comparison["registered_tv"]))

    def test_pb_si_003_choices_remain_open_and_fail_closed(self) -> None:
        unresolved = self.policy["unresolved_production_semantics"]
        self.assertEqual(
            self.policy["pb_si_003_state"],
            "OPEN_BLOCKS_STOCHASTIC_EXECUTION",
        )
        self.assertEqual(
            unresolved,
            {
                "world_pair_selection": "UNRESOLVED_PB_SI_003",
                "threshold_scope": "UNRESOLVED_PB_SI_003",
                "multi_pair_aggregation": "UNRESOLVED_PB_SI_003",
                "estimated_model_acceptance": "UNRESOLVED_PB_SI_003",
            },
        )
        self.assertEqual(
            self.policy["missing_decision_behavior"],
            "FAIL_CLOSED_NO_SAMPLING",
        )
        self.assertFalse(self.policy["decision_rule_authority"])

    def test_design_entries_cannot_be_executed_or_sampled(self) -> None:
        self.assertFalse(self.catalog["execution_authority"])
        self.assertFalse(self.catalog["sampling_authority"])
        self.assertFalse(self.policy["execution_authority"])
        self.assertFalse(self.policy["sampling_authority"])
        for entry in self.catalog["entries"]:
            self.assertEqual(
                entry["entry_status"],
                "NON_EXECUTABLE_CONTRACT_EXAMPLE",
            )
            self.assertTrue(entry["not_executable"])
            self.assertFalse(entry["catalog_ceiling_eligible"])

    def test_failure_channels_are_not_observation_outcomes(self) -> None:
        forbidden_outcomes = {
            "TIMEOUT",
            "RESOURCE_EXHAUSTED",
            "MODEL_INVALID",
            "INFEASIBLE",
            "UNKNOWN",
        }
        expected_failures = [
            "TIMEOUT_UNKNOWN",
            "RESOURCE_EXHAUSTED_UNKNOWN",
            "MODEL_INVALID_UNKNOWN",
            "INFEASIBLE_SEPARATE",
        ]
        for entry in self.catalog["entries"]:
            self.assertTrue(forbidden_outcomes.isdisjoint(entry["finite_outcomes"]))
            self.assertEqual(entry["failure_channels"], expected_failures)

    def test_schema_rejects_float_probabilities_and_runtime_fields(self) -> None:
        invalid_probability = deepcopy(self.catalog)
        invalid_probability["entries"][0]["conditional_distribution"][0][
            "probabilities"
        ][0]["probability"] = 0.9
        self.assertTrue(validate(invalid_probability, self.catalog_schema))

        invalid_denominator = deepcopy(self.catalog)
        invalid_denominator["entries"][0]["conditional_distribution"][0][
            "probabilities"
        ][0]["probability"]["denominator"] = 0
        self.assertTrue(validate(invalid_denominator, self.catalog_schema))

        invalid_runtime = deepcopy(self.catalog)
        invalid_runtime["sampler"] = {"seed": 7}
        self.assertTrue(validate(invalid_runtime, self.catalog_schema))

    def test_contract_emits_no_certificate_system_state_or_stop(self) -> None:
        forbidden = {
            "certificate",
            "level_certificate",
            "system_status",
            "system_state",
            "stop_result",
        }

        def visit(value: object) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(str(key).lower(), forbidden)
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str):
                self.assertNotEqual(value, "CERTIFIED_STOP")

        visit(self.catalog)
        visit(self.policy)


if __name__ == "__main__":
    unittest.main()
