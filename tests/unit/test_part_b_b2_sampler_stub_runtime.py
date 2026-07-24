from __future__ import annotations

from collections import Counter
import importlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]

CATALOG_PATH = (
    ROOT / "configs" / "part-b-stochastic-observation-catalog-v0.8.yaml"
)
POLICY_PATH = ROOT / "configs" / "part-b-b2-sampler-stub-policy-v0.8.yaml"
FIXTURE_PATH = ROOT / "configs" / "part-b-b2-sampler-stub-fixture-v0.8.yaml"
TRACE_SCHEMA_PATH = (
    ROOT / "schemas" / "part-b-b2-sampler-stub-trace.schema.json"
)

try:
    sampler_api = importlib.import_module(
        "src.executor.part_b_b2_sampler_stub"
    )
except (ImportError, ModuleNotFoundError):
    sampler_api = None


def load_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(
            "missing approved B2 sampler stub artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(
            "missing approved B2 sampler stub artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


class PartBB2SamplerStubRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(
            sampler_api,
            "missing approved B2 sampler stub module: "
            "src.executor.part_b_b2_sampler_stub",
        )
        self.catalog = load_yaml(CATALOG_PATH)
        self.policy = load_yaml(POLICY_PATH)
        self.fixture = load_yaml(FIXTURE_PATH)
        self.trace_schema = load_json(TRACE_SCHEMA_PATH)
        first_case = self.fixture["allowed_cases"][0]
        self.action_id = first_case["action_id"]
        self.world_id = first_case["world_ids"][0]
        self.seed = 20260724
        self.trial_budget = self.policy["trial_budget"]["default"]

    def sample(self, *, seed: int | None = None, trial_budget: int | None = None):
        return sampler_api.sample_fixture(
            catalog=self.catalog,
            policy=self.policy,
            fixture=self.fixture,
            action_id=self.action_id,
            world_id=self.world_id,
            seed=self.seed if seed is None else seed,
            trial_budget=(
                self.trial_budget if trial_budget is None else trial_budget
            ),
        )

    def test_red_08_same_seed_replays_identical_trace(self) -> None:
        """RED-08: identical frozen inputs and seed replay byte-for-value."""
        left = self.sample()
        right = self.sample()
        self.assertEqual(left, right)
        self.assertRegex(left["trace_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            list(Draft202012Validator(self.trace_schema).iter_errors(left)),
            [],
        )

    def test_red_09_seed_commitment_changes_trace_identity(self) -> None:
        """RED-09: a changed seed is visible in both commitment and trace ID."""
        left = self.sample(seed=self.seed)
        right = self.sample(seed=self.seed + 1)
        self.assertNotEqual(left["seed_commitment"], right["seed_commitment"])
        self.assertNotEqual(left["trace_id"], right["trace_id"])
        self.assertRegex(left["seed_commitment"], r"^sha256:[0-9a-f]{64}$")
        self.assertNotIn("seed", left)

    def test_red_10_finite_trial_budget_matches_sequence_counts_and_resources(
        self,
    ) -> None:
        """RED-10: the finite budget is exact across outputs and resources."""
        result = self.sample()
        self.assertEqual(len(result["outcome_sequence"]), self.trial_budget)
        self.assertEqual(
            result["outcome_counts"],
            dict(Counter(result["outcome_sequence"])),
        )
        self.assertEqual(sum(result["outcome_counts"].values()), self.trial_budget)
        self.assertEqual(
            result["resource_trace"],
            {
                "status": "COMPLETED",
                "trials_requested": self.trial_budget,
                "trials_completed": self.trial_budget,
                "random_draw_count": self.trial_budget,
                "failure_kind": None,
            },
        )

    def test_red_11_only_fixture_catalog_action_world_pairs_are_accepted(
        self,
    ) -> None:
        """RED-11: unknown, real-source and out-of-fixture requests fail closed."""
        with self.assertRaises(ValueError):
            sampler_api.sample_fixture(
                catalog=self.catalog,
                policy=self.policy,
                fixture=self.fixture,
                action_id="REAL-SOURCE-ACTION",
                world_id=self.world_id,
                seed=self.seed,
                trial_budget=self.trial_budget,
            )
        with self.assertRaises(ValueError):
            sampler_api.sample_fixture(
                catalog=self.catalog,
                policy=self.policy,
                fixture=self.fixture,
                action_id=self.action_id,
                world_id="OUTSIDE-FIXTURE-WORLD",
                seed=self.seed,
                trial_budget=self.trial_budget,
            )

    def test_red_12_trace_binds_request_generator_and_frozen_artifacts(self) -> None:
        """RED-12: trace identity commits every reproducibility input."""
        result = self.sample()
        self.assertEqual(result["action_id"], self.action_id)
        self.assertEqual(result["world_id"], self.world_id)
        self.assertEqual(result["trial_budget"], self.trial_budget)
        self.assertEqual(result["catalog_hash"], self.fixture["catalog_hash"])
        self.assertEqual(result["policy_hash"], self.policy["hash"])
        self.assertEqual(result["fixture_hash"], self.fixture["hash"])
        self.assertEqual(result["generator"], self.policy["generator"])
        self.assertRegex(result["request_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(result["trace_id"], r"^sha256:[0-9a-f]{64}$")

    def test_red_13_failures_are_explicit_non_samples_and_never_unsat(self) -> None:
        """RED-13: timeout/resource/model failures remain UNKNOWN."""
        expected_status = {
            "TIMEOUT": "UNKNOWN",
            "RESOURCE_EXHAUSTED": "UNKNOWN",
            "MODEL_INVALID": "UNKNOWN",
            "INFEASIBLE": "INFEASIBLE",
        }
        for failure_kind, status in expected_status.items():
            with self.subTest(failure_kind=failure_kind):
                record = sampler_api.failure_record(
                    action_id=self.action_id,
                    world_id=self.world_id,
                    failure_kind=failure_kind,
                )
                self.assertEqual(record["status"], status)
                self.assertFalse(record["sample_emitted"])
                self.assertFalse(record["unsat"])
                self.assertFalse(record["catalog_ceiling_eligible"])

    def test_red_14_stub_output_has_no_evidence_planner_holdout_or_stop_power(
        self,
    ) -> None:
        """RED-14: a reproducible local trace is not evidence or authority."""
        result = self.sample()
        self.assertEqual(result["source_scope"], "FROZEN_B2_FIXTURE_CATALOG_ONLY")
        self.assertTrue(result["simulated"])
        self.assertFalse(result["admitted_case_evidence"])
        self.assertFalse(result["catalog_ceiling_eligible"])
        for forbidden in (
            "certificate",
            "level_certificate",
            "system_status",
            "planner_action",
            "holdout_result",
            "CERTIFIED_STOP",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, result)
                self.assertNotIn(forbidden, result.values())


if __name__ == "__main__":
    unittest.main()
