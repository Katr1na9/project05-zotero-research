from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = (
    ROOT / "schemas" / "part-b-b2-world-pair-delta-decision.schema.json"
)
CONFIG_PATH = (
    ROOT / "configs" / "part-b-b2-world-pair-delta-decision-v0.8.yaml"
)


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


def canonical_pair(left: str, right: str) -> tuple[str, str]:
    if left == right:
        raise ValueError("self-pairs are forbidden")
    return tuple(sorted((left, right)))


class PartBB2SI003WorldPairDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(SCHEMA_PATH)
        cls.config = load_yaml(CONFIG_PATH)

    def test_decision_schema_and_hash_replay(self) -> None:
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(validate(self.config, self.schema), [])
        self.assertEqual(
            self.config["hash"],
            canonical_document_hash(self.config),
        )

    def test_closure_is_exact_finite_decision_only(self) -> None:
        self.assertEqual(
            self.config["pb_si_003_state"],
            "CLOSED_APPROVED_EXACT_FINITE_ONLY",
        )
        self.assertTrue(self.config["decision_rule_authority"])
        self.assertFalse(self.config["execution_authority"])
        self.assertFalse(self.config["sampling_authority"])
        self.assertEqual(
            self.config["model_boundary"]["estimated_model_acceptance"],
            "UNRESOLVED_PB_B2_SI_003",
        )
        self.assertTrue(
            self.config["model_boundary"][
                "closing_this_issue_does_not_authorize_sampler"
            ]
        )
        self.assertEqual(self.config["stop_authority"], "NONE")

    def test_world_pairs_are_complete_cross_partition_and_canonical(self) -> None:
        policy = self.config["world_pair_policy"]
        self.assertEqual(
            policy["source"],
            "ALL_LEGAL_WORLDS_PARTITIONED_BY_CANDIDATE_Q",
        )
        self.assertFalse(policy["single_witness_pair_sufficient"])
        example = self.config["conformance_example"]
        expected = {
            canonical_pair(left, right)
            for left in example["support_world_ids"]
            for right in example["alternative_world_ids"]
        }
        declared = {
            canonical_pair(row["left_world_id"], row["right_world_id"])
            for row in example["required_pairs"]
        }
        self.assertEqual(declared, expected)
        self.assertEqual(len(declared), len(example["required_pairs"]))
        self.assertTrue(
            all(
                row["left_world_id"] < row["right_world_id"]
                for row in example["required_pairs"]
            )
        )

    def test_delta_is_inclusive_per_action_and_uses_worst_pair(self) -> None:
        example = self.config["conformance_example"]
        delta = rational(example["action_delta"])
        pair_values = [
            rational(row["total_variation"])
            for row in example["required_pairs"]
        ]
        self.assertEqual(
            self.config["delta_policy"]["inclusive_operator"],
            "GREATER_THAN_OR_EQUAL",
        )
        self.assertEqual(
            self.config["multi_pair_rule"]["aggregation"],
            "MINIMUM_TV_WORST_CASE",
        )
        self.assertEqual(min(pair_values), rational(example["minimum_tv"]))
        self.assertEqual(example["decision"], "ELIGIBLE")
        self.assertGreaterEqual(min(pair_values), delta)

    def test_delta_and_tv_values_are_reduced_closed_unit_rationals(self) -> None:
        example = self.config["conformance_example"]
        raw_values = [
            example["action_delta"],
            example["minimum_tv"],
            *[row["total_variation"] for row in example["required_pairs"]],
        ]
        for raw in raw_values:
            with self.subTest(raw=raw):
                parsed = rational(raw)
                self.assertGreaterEqual(parsed, 0)
                self.assertLessEqual(parsed, 1)
                self.assertEqual(parsed.numerator, raw["numerator"])
                self.assertEqual(parsed.denominator, raw["denominator"])

    def test_future_catalog_binding_is_mandatory_not_inferred(self) -> None:
        self.assertEqual(
            self.config["delta_policy"]["binding"],
            "EXECUTABLE_ACTION_CATALOG_HASH_REQUIRED",
        )
        self.assertTrue(self.config["delta_policy"]["defaults_forbidden"])
        self.assertEqual(
            self.config["world_pair_policy"]["comparison_set_binding"],
            "EVALUATION_MANIFEST_HASH_REQUIRED",
        )
        self.assertTrue(
            self.config["world_pair_policy"]["freeze_before_action_outcome"]
        )

    def test_frozen_b2_artifact_hashes_remain_unchanged(self) -> None:
        bindings = self.config["bindings"]
        expected = {
            "b2_catalog_hash": (
                "sha256:200f0ccd89525bcbda89ea77101cdcab"
                "7fda675888938ee106e389a1a8beeab5"
            ),
            "b2_tv_policy_hash": (
                "sha256:b25ed05fdbd9780c1d0de1889e765122"
                "0e8a2fc9ce6a86fcdf4720926a31d3e8"
            ),
            "b2_manifest_hash": (
                "sha256:6d6f67d9722eff1b2e1aa75277b0c390"
                "dc485751067728a347ae89c77f83faed"
            ),
        }
        self.assertEqual(bindings, expected)

    def test_schema_fails_closed_on_authority_expansion(self) -> None:
        for field, value in (
            ("execution_authority", True),
            ("sampling_authority", True),
            ("stop_authority", "STOCHASTIC_POLICY"),
        ):
            invalid = deepcopy(self.config)
            invalid[field] = value
            with self.subTest(field=field):
                self.assertTrue(validate(invalid, self.schema))

        invalid = deepcopy(self.config)
        invalid["delta_policy"]["defaults_forbidden"] = False
        self.assertTrue(validate(invalid, self.schema))

    def test_issue_and_authority_text_preserve_no_sampler_boundary(self) -> None:
        paths = (
            ROOT / "src" / "scope" / "part-b-b0-spec-issues.md",
            ROOT / "src" / "scope" / "part-b-b2-spec-issues.md",
            ROOT / "contracts" / "part-b-b2-boundary-v0.8.md",
            ROOT / "contracts" / "part-b-b2-stochastic-observation-v0.8.md",
            ROOT
            / "contracts"
            / "part-b-b2-world-pair-delta-decision-v0.8.md",
            ROOT
            / "08-writing"
            / "part-b-b2-si003-decision-v0.8-20260723.md",
            ROOT
            / "08-writing"
            / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
        )
        required = (
            "PB-SI-003",
            "CLOSED",
            "support",
            "alternative",
            "MINIMUM_TV_WORST_CASE",
            "sampling_authority=false",
            "UNRESOLVED_PB_B2_SI_003",
            "CERTIFIED_STOP",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in required:
                with self.subTest(path=path.name, token=token):
                    self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
