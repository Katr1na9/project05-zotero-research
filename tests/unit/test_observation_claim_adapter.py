import copy
import unittest


try:
    from src.ir.observation_claim import (
        ObservationClaimActionBinding,
        ObservationClaimAdapterContext,
        ObservationClaimIRAdapter,
    )
except (ImportError, ModuleNotFoundError):
    ObservationClaimActionBinding = None
    ObservationClaimAdapterContext = None
    ObservationClaimIRAdapter = None


POLICY_HASH = (
    "sha256:0eb3cbb8be3cf51dc9952a447e4d1f90fc89b5dc2c5e2f0edafca32c6805399a"
)
RULE_HASH = "sha256:3b4bb0ed6f9221c5e71bedc50ce508710f693c0e28d84f77af7571ac85f94d3e"


def catalog():
    return {
        "actions": [
            {
                "action_id": "lookup_without_entity_name_in_id",
                "target": {"entity_ids": ["HOST-Z9"], "entity_type": "host"},
                "scope": {
                    "time_window": {
                        "start": "2026-01-01T10:00:00Z",
                        "end": "2026-01-01T10:15:00Z",
                    },
                    "spatial_scope": "tenant:T9/host:HOST-Z9",
                },
                "invocation": {"parameters": {"tenant": "T9"}},
            }
        ]
    }


def observation(**updates):
    row = {
        "observation_id": "OBS-UNIT-001",
        "action_id": "lookup_without_entity_name_in_id",
        "sensor_id": "sensor-Z9",
        "observed_value": "present",
        "used_for_world_elimination": True,
        "completeness_conditions_satisfied": True,
        "observation_kind": "distinguishing_hit",
    }
    row.update(updates)
    return row


def context():
    return ObservationClaimAdapterContext(
        source_id="action_observations.jsonl",
        row_numbers={"OBS-UNIT-001": 7},
        action_bindings={
            "lookup_without_entity_name_in_id": ObservationClaimActionBinding(
                predicate="action_observation",
                source_family="identity",
                source_schema="kernel.action-observation.v0.8",
                admissible_levels=("initial_foothold",),
            )
        },
        certification_basis_rule_id="A-P5-OBSERVATION",
        certification_policy_hash=POLICY_HASH,
        parser_id="p5-observation-adapter",
        parser_version="0.8.0",
        prompt_or_rule_hash=RULE_HASH,
    )


class ObservationClaimIRAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            ObservationClaimIRAdapter,
            "P11 observation-to-Claim-IR adapter is missing",
        )

    def test_catalog_target_not_action_name_binds_subject_time_location_and_pointer(self):
        claim = ObservationClaimIRAdapter().adapt(
            observation(), catalog(), context()
        )

        self.assertEqual(
            {"entity_id": "HOST-Z9", "entity_type": "host"}, claim["subject"]
        )
        self.assertEqual(
            {
                "start": "2026-01-01T10:00:00Z",
                "end": "2026-01-01T10:15:00Z",
                "precision": "bounded",
            },
            claim["time"],
        )
        self.assertEqual(
            {"host": "HOST-Z9", "tenant": "T9", "zone": None},
            claim["location"],
        )
        self.assertEqual("OBS-UNIT-001", claim["pointer"]["record_id"])
        self.assertEqual([7, 7], claim["pointer"]["byte_or_row_range"])
        self.assertEqual("observed", claim["modality"])
        self.assertEqual("candidate", claim["admission_status"])
        self.assertEqual("bound", claim["lifecycle_state"])

    def test_adapter_is_deterministic_and_does_not_mutate_inputs(self):
        row = observation()
        frozen_catalog = catalog()
        original_row = copy.deepcopy(row)
        original_catalog = copy.deepcopy(frozen_catalog)
        adapter = ObservationClaimIRAdapter()

        first = adapter.adapt(row, frozen_catalog, context())
        second = adapter.adapt(row, frozen_catalog, context())

        self.assertEqual(first, second)
        self.assertEqual(original_row, row)
        self.assertEqual(original_catalog, frozen_catalog)

    def test_oracle_hidden_unknown_action_and_missing_pointer_row_fail_closed(self):
        adapter = ObservationClaimIRAdapter()
        oracle = observation(ground_truth="HOST-Z9")
        unknown = observation(action_id="missing-action")
        missing_row_context = ObservationClaimAdapterContext(
            source_id="action_observations.jsonl",
            row_numbers={},
            action_bindings=context().action_bindings,
            certification_basis_rule_id="A-P5-OBSERVATION",
            certification_policy_hash=POLICY_HASH,
            parser_id="p5-observation-adapter",
            parser_version="0.8.0",
            prompt_or_rule_hash=RULE_HASH,
        )

        for row, adapter_context in (
            (oracle, context()),
            (unknown, context()),
            (observation(), missing_row_context),
        ):
            with self.subTest(row=row):
                with self.assertRaises(ValueError):
                    adapter.adapt(row, catalog(), adapter_context)

    def test_batch_rejects_duplicate_observation_ids(self):
        with self.assertRaises(ValueError):
            ObservationClaimIRAdapter().adapt_batch(
                (observation(), observation()), catalog(), context()
            )


if __name__ == "__main__":
    unittest.main()
