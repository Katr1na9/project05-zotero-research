import copy
import importlib
import unittest


try:
    recert_api = importlib.import_module("src.scope.recertify")
except (ImportError, ModuleNotFoundError):
    recert_api = None


def artifact(*, include_absence_semantics=True):
    return {
        "schema_version": "0.8.0",
        "target_level": "initial_foothold",
        "candidate_q": {"entity_id": "H1", "entity_type": "host"},
        "checker_status": "COUNTEREXAMPLE_FOUND",
        "support_world": {
            "world_id": "W-SUPPORT-H1",
            "target_result": {"entity_id": "H1", "entity_type": "host"},
            "predicates": [
                "credential_activity:H1",
                "authentication_origin:H3=H1",
                "compromised:H3",
            ],
        },
        "alternative_world": {
            "world_id": "W-ALTERNATIVE-H3",
            "target_result": {"entity_id": "H3", "entity_type": "host"},
            "predicates": [
                "external_credential_login:H3",
                "authentication_origin:H3=EXTERNAL",
                "compromised:H3",
            ],
        },
        "shared_predicates": ["compromised:H3"],
        "critical_absence_semantics": (
            ["auth-H1:bounded_completeness"]
            if include_absence_semantics
            else []
        ),
    }


def catalog():
    return {
        "actions": [
            {
                "action_id": "query_logon_origin_H3",
                "observation_model": {
                    "noise_model": "deterministic",
                    "output_domain": ["H1", "EXTERNAL", "absent"],
                    "absence_semantics_ref": "logon-origin-H3",
                    "world_dependencies": ["authentication_origin:H3"],
                },
                "formal_analysis_eligibility": "formal",
                "state_effect": {
                    "world_elimination_rule_ids": ["origin-mismatch-v1"]
                },
            },
            {
                "action_id": "query_auth_H1_1000_1015",
                "observation_model": {
                    "noise_model": "deterministic",
                    "output_domain": ["present", "absent"],
                    "absence_semantics_ref": "auth-H1",
                    "world_dependencies": ["credential_activity:H1"],
                },
                "formal_analysis_eligibility": "formal",
                "state_effect": {
                    "world_elimination_rule_ids": ["zero-hit-auth-v1"]
                },
            },
            {
                "action_id": "query_auth_empty_control",
                "observation_model": {
                    "noise_model": "deterministic",
                    "output_domain": ["present", "absent"],
                    "absence_semantics_ref": "auth-empty-control",
                    "world_dependencies": ["credential_activity:H1"],
                },
                "formal_analysis_eligibility": "formal",
                "state_effect": {"world_elimination_rule_ids": []},
            },
            {
                "action_id": "analyst_cti_lookup",
                "observation_model": None,
                "formal_analysis_eligibility": "heuristic_only",
                "state_effect": {"world_elimination_rule_ids": []},
            },
        ]
    }


def observation(action_id, value, *, used=True, complete=True, kind="hit"):
    return {
        "observation_id": f"OBS-{action_id}",
        "action_id": action_id,
        "sensor_id": action_id,
        "observed_value": value,
        "used_for_world_elimination": used,
        "completeness_conditions_satisfied": complete,
        "observation_kind": kind,
    }


class WorldEliminationRecertificationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            recert_api, "P6 world-elimination/recertification API is missing"
        )

    def test_positive_origin_eliminates_alternative_and_candidate_certifies(self):
        result = recert_api.RecertificationOrchestrator().recertify(
            artifact(),
            [observation("query_logon_origin_H3", "H1")],
            catalog(),
        )

        self.assertEqual(("W-SUPPORT-H1",), result.surviving_world_ids)
        self.assertEqual(("W-ALTERNATIVE-H3",), result.eliminated_world_ids)
        self.assertEqual("CANDIDATE_CERTIFIED", result.checker_run.checker_status.value)
        self.assertEqual("SAT", result.checker_run.base.status.value)
        self.assertEqual("SAT", result.checker_run.support.status.value)
        self.assertEqual("UNSAT", result.checker_run.alternative.status.value)
        self.assertIsNone(result.mindiff_result)
        fields = result.to_outcome_fields()
        self.assertNotIn("system_status", fields)
        self.assertNotIn("CERTIFIED_STOP", fields.values())
        self.assertNotIn("certification_scope", fields)

    def test_bounded_complete_zero_hit_rejects_candidate(self):
        result = recert_api.RecertificationOrchestrator().recertify(
            artifact(),
            [
                observation(
                    "query_auth_H1_1000_1015",
                    "absent",
                    kind="bounded_complete_zero_hit",
                )
            ],
            catalog(),
        )

        self.assertEqual(("W-ALTERNATIVE-H3",), result.surviving_world_ids)
        self.assertEqual("REJECT_CANDIDATE", result.checker_run.checker_status.value)

    def test_conflicting_eligible_observations_exhaust_scope_not_stop(self):
        result = recert_api.RecertificationOrchestrator().recertify(
            artifact(),
            [
                observation("query_logon_origin_H3", "H1"),
                observation("query_auth_H1_1000_1015", "absent"),
            ],
            catalog(),
        )

        self.assertEqual((), result.surviving_world_ids)
        self.assertEqual(
            "SCOPE_MISMATCH_SUSPECTED", result.checker_run.checker_status.value
        )
        self.assertEqual("UNSAT", result.checker_run.base.status.value)
        self.assertIsNone(result.mindiff_result)

    def test_control_heuristic_and_incomplete_observations_are_ignored(self):
        result = recert_api.RecertificationOrchestrator().recertify(
            artifact(),
            [
                observation("query_auth_empty_control", "absent", used=False),
                observation("analyst_cti_lookup", "report_found", used=False),
                observation(
                    "query_auth_H1_1000_1015", "absent", complete=False
                ),
            ],
            catalog(),
        )

        self.assertEqual((), result.applied_observation_ids)
        self.assertEqual(3, len(result.ignored_observations))
        self.assertEqual("COUNTEREXAMPLE_FOUND", result.checker_run.checker_status.value)
        self.assertIsNotNone(result.mindiff_result)
        self.assertEqual((), result.mindiff_result.distinguishing_predicates)
        self.assertEqual(
            ("initial_foothold",), result.mindiff_result.unprojected_variables
        )

    def test_zero_hit_without_frozen_absence_semantics_is_ignored(self):
        result = recert_api.RecertificationOrchestrator().recertify(
            artifact(include_absence_semantics=False),
            [observation("query_auth_H1_1000_1015", "absent")],
            catalog(),
        )

        self.assertEqual((), result.applied_observation_ids)
        self.assertEqual(
            "ABSENCE_SEMANTICS_UNVERIFIED",
            result.ignored_observations[0].reason,
        )
        self.assertEqual("COUNTEREXAMPLE_FOUND", result.checker_run.checker_status.value)

    def test_stochastic_model_is_rejected_without_elimination(self):
        invalid_catalog = copy.deepcopy(catalog())
        invalid_catalog["actions"][0]["observation_model"]["noise_model"] = (
            "stochastic"
        )

        with self.assertRaises(ValueError):
            recert_api.RecertificationOrchestrator().recertify(
                artifact(),
                [observation("query_logon_origin_H3", "H1")],
                invalid_catalog,
            )


if __name__ == "__main__":
    unittest.main()
