import copy
import importlib
import unittest


try:
    selection_api = importlib.import_module("src.actions.selection")
except (ImportError, ModuleNotFoundError):
    selection_api = None


def action(
    action_id,
    *,
    dependencies=(),
    elimination_rules=(),
    eligibility="formal",
    feasibility="executable",
    authority="executable",
    noise_model="deterministic",
):
    observation_model = None
    if dependencies or eligibility == "formal":
        observation_model = {
            "noise_model": noise_model,
            "world_dependencies": list(dependencies),
        }
    return {
        "action_id": action_id,
        "authority": {"current_status": authority},
        "invocation": {"parameters": {}},
        "observation_model": observation_model,
        "formal_analysis_eligibility": eligibility,
        "state_effect": {
            "world_elimination_rule_ids": list(elimination_rules),
        },
        "feasibility": {"status": feasibility},
    }


def catalog():
    return {
        "schema_version": "0.8.0",
        "catalog_id": "unit-catalog",
        "catalog_version": "0.8.0",
        "hash": "sha256:" + "1" * 64,
        "actions": [
            action(
                "query_logon_origin_H3",
                dependencies=("authentication_origin:H3",),
                elimination_rules=("origin-mismatch-v1",),
            ),
            action(
                "query_auth_H1_1000_1015",
                dependencies=("credential_activity:H1",),
                elimination_rules=("zero-hit-auth-v1",),
            ),
            action(
                "query_auth_empty_control",
                dependencies=("credential_activity:H1",),
                elimination_rules=(),
            ),
            action(
                "acquire_identity_archive_H3",
                dependencies=("authentication_origin:H3",),
                elimination_rules=("origin-mismatch-v1",),
                feasibility="not_authorized",
                authority="not_authorized",
            ),
            action("analyst_cti_lookup", eligibility="heuristic_only"),
            action(
                "query_irrelevant_network",
                dependencies=("network_link:H1:H3",),
                elimination_rules=("network-mismatch-v1",),
            ),
        ],
    }


def counterexample():
    return {
        "schema_version": "0.8.0",
        "target_level": "initial_foothold",
        "checker_status": "COUNTEREXAMPLE_FOUND",
        "distinguishing_predicates": [
            "authentication_origin:H3",
            "credential_activity:H1",
        ],
    }


class DistinguishingActionSelectorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            selection_api, "P4 distinguishing-action selector API is missing"
        )

    def test_selects_only_formal_deterministic_feasible_distinguishers(self):
        result = selection_api.DistinguishingActionSelector().select(
            counterexample(), catalog()
        )

        self.assertEqual(
            ("query_auth_H1_1000_1015", "query_logon_origin_H3"),
            result.allowed_actions,
        )
        self.assertNotIn("query_auth_empty_control", result.allowed_actions)
        self.assertNotIn("acquire_identity_archive_H3", result.allowed_actions)
        self.assertNotIn("analyst_cti_lookup", result.allowed_actions)
        self.assertEqual(6, result.catalog_actions_examined)

    def test_selection_is_order_independent_and_policy_forbidden_is_explicit(self):
        first_catalog = catalog()
        reversed_catalog = copy.deepcopy(first_catalog)
        reversed_catalog["actions"].reverse()
        selector = selection_api.DistinguishingActionSelector()

        first = selector.select(counterexample(), first_catalog)
        second = selector.select(counterexample(), reversed_catalog)

        self.assertEqual(first, second)
        self.assertEqual(
            (
                "oracle_reveal_true_initial_foothold",
                "use_hidden_recoverable_claim_ids",
            ),
            first.forbidden_actions,
        )
        fields = first.to_outcome_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", fields.values())

    def test_rejects_stochastic_catalog_without_running_observation_model(self):
        invalid = catalog()
        invalid["actions"][0]["observation_model"]["noise_model"] = "stochastic"

        with self.assertRaises(ValueError):
            selection_api.DistinguishingActionSelector().select(
                counterexample(), invalid
            )

    def test_rejects_hidden_or_oracle_catalog_inputs(self):
        invalid = catalog()
        invalid["actions"][0]["invocation"]["parameters"] = {
            "ground_truth": "H1"
        }

        with self.assertRaises(ValueError):
            selection_api.DistinguishingActionSelector().select(
                counterexample(), invalid
            )

    def test_requires_counterexample_and_unique_predicates_and_action_ids(self):
        not_counterexample = counterexample()
        not_counterexample["checker_status"] = "CANDIDATE_CERTIFIED"
        with self.assertRaises(ValueError):
            selection_api.DistinguishingActionSelector().select(
                not_counterexample, catalog()
            )

        duplicate_predicates = counterexample()
        duplicate_predicates["distinguishing_predicates"] = ["p", "p"]
        with self.assertRaises(ValueError):
            selection_api.DistinguishingActionSelector().select(
                duplicate_predicates, catalog()
            )

        duplicate_actions = catalog()
        duplicate_actions["actions"].append(
            copy.deepcopy(duplicate_actions["actions"][0])
        )
        with self.assertRaises(ValueError):
            selection_api.DistinguishingActionSelector().select(
                counterexample(), duplicate_actions
            )


if __name__ == "__main__":
    unittest.main()
