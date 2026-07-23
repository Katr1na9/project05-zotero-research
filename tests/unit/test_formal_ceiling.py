import copy
import json
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from src.scope.formal_ceiling import CeilingStatus, FormalCeilingVerifier
from tests.integration.supply_chain_kernel_inputs import (
    FIXTURE as SUPPLY_FIXTURE,
    load_supply_chain_kernel_inputs,
)
from tests.integration.twin_kernel_inputs import (
    FIXTURE as TWIN_FIXTURE,
    ROOT,
    load_twin_kernel_inputs,
)


class FormalCeilingTests(unittest.TestCase):
    def test_frozen_ceiling_reports_recompute_byte_for_value(self):
        verifier = FormalCeilingVerifier()
        cases = (
            (
                load_twin_kernel_inputs(),
                "initial_foothold",
                TWIN_FIXTURE / "expected" / "formal_ceiling.json",
            ),
            (
                load_supply_chain_kernel_inputs(),
                "package_origin",
                SUPPLY_FIXTURE / "expected" / "formal_ceiling.json",
            ),
        )
        for inputs, target, frozen_path in cases:
            with self.subTest(target=target):
                recomputed = verifier.assess(
                    inputs.gamma,
                    inputs.compiled,
                    inputs.catalog,
                    requested_target=target,
                )
                frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
                self.assertTrue(recomputed.verified)
                self.assertEqual(frozen, recomputed.to_dict())
                self.assertEqual(frozen["hash"], recomputed.ceiling_hash)

    def test_twin_and_supply_chain_have_exact_but_different_verified_ceilings(self):
        twin = load_twin_kernel_inputs()
        supply = load_supply_chain_kernel_inputs()
        verifier = FormalCeilingVerifier()

        twin_ceiling = verifier.assess(
            twin.gamma,
            twin.compiled,
            twin.catalog,
            requested_target="initial_foothold",
        )
        supply_ceiling = verifier.assess(
            supply.gamma,
            supply.compiled,
            supply.catalog,
            requested_target="package_origin",
        )

        self.assertTrue(twin_ceiling.verified)
        self.assertTrue(supply_ceiling.verified)
        twin_report = twin_ceiling.to_dict()
        supply_report = supply_ceiling.to_dict()
        self.assertEqual(4, twin_report["cartesian_assignment_bound"])
        self.assertEqual(2, twin_report["legal_world_count"])
        self.assertEqual(27, supply_report["cartesian_assignment_bound"])
        self.assertEqual(3, supply_report["legal_world_count"])
        self.assertNotEqual(
            twin_report["compilation_profile"],
            supply_report["compilation_profile"],
        )
        self.assertNotEqual(twin_ceiling.ceiling_hash, supply_ceiling.ceiling_hash)

        schema = json.loads(
            (ROOT / "schemas" / "formal-ceiling.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        for report in (twin_report, supply_report):
            self.assertEqual([], list(validator.iter_errors(report)))

    def test_outside_target_or_action_fails_closed_without_proof_report(self):
        inputs = load_supply_chain_kernel_inputs()
        verifier = FormalCeilingVerifier()

        target = verifier.assess(
            inputs.gamma,
            inputs.compiled,
            inputs.catalog,
            requested_target="actor_identity",
        )
        action = verifier.assess(
            inputs.gamma,
            inputs.compiled,
            inputs.catalog,
            requested_target="package_origin",
            requested_actions=("future_connector",),
        )

        self.assertEqual(CeilingStatus.OUTSIDE_FROZEN_DOMAIN, target.status)
        self.assertEqual(CeilingStatus.OUTSIDE_FROZEN_DOMAIN, action.status)
        self.assertIsNone(target.to_dict())
        self.assertIsNone(action.ceiling_hash)

    def test_resource_exhaustion_is_unknown_never_unsat(self):
        inputs = load_supply_chain_kernel_inputs()
        result = FormalCeilingVerifier().assess(
            inputs.gamma,
            inputs.compiled,
            inputs.catalog,
            requested_target="package_origin",
            max_assignments=26,
        )

        self.assertEqual(CeilingStatus.UNKNOWN_RESOURCE_EXHAUSTED, result.status)
        self.assertEqual(
            "CEILING-003_ENUMERATION_RESOURCE_EXHAUSTED", result.reason_code
        )
        self.assertNotIn("UNSAT", result.status.value)
        self.assertIsNone(result.to_dict())

    def test_tampered_or_stale_artifacts_are_invalid_not_verified(self):
        inputs = load_supply_chain_kernel_inputs()
        tampered_gamma = copy.deepcopy(inputs.gamma)
        tampered_gamma["result_domains"]["package_origin"]["finite_candidates"].append(
            "UNBOUND-D"
        )
        stale_catalog = copy.deepcopy(inputs.catalog)
        stale_catalog["actions"][0]["observation_model"]["noise_model"] = "stochastic"

        for gamma, catalog in (
            (tampered_gamma, inputs.catalog),
            (inputs.gamma, stale_catalog),
        ):
            with self.subTest(gamma_hash=gamma["hash"]):
                result = FormalCeilingVerifier().assess(
                    gamma,
                    inputs.compiled,
                    catalog,
                    requested_target="package_origin",
                )
                self.assertEqual(CeilingStatus.INVALID_ARTIFACT, result.status)
                self.assertFalse(result.verified)


if __name__ == "__main__":
    unittest.main()
