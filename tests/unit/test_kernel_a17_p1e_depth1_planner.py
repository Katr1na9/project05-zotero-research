from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

import yaml

from src.ir.canonical_hash import canonical_value_hash
from src.planner import deterministic_depth1 as planner


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "kernel_a17_p1e_depth1_planner_v0.1.json"
)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finalize_request(request):
    finite = request["finite_domain_binding"]
    finite["current_u_count"] = len(finite["current_u_world_ids"])
    finite["current_u_hash"] = canonical_value_hash(
        finite["current_u_world_ids"]
    )

    counterexample = request["counterexample_binding"]
    counterexample["distinguishing_predicates_hash"] = canonical_value_hash(
        counterexample["distinguishing_predicates"]
    )

    p4 = request["p4_selection_binding"]
    p4["selection_record_hash"] = canonical_value_hash(
        {
            "allowed_actions": p4["allowed_action_ids"],
            "forbidden_actions": p4["forbidden_action_ids"],
            "catalog_actions_examined": 8,
        }
    )
    for partition in request["deterministic_outcome_partitions"]:
        partition["partition_hash"] = planner.canonical_hash_without_field(
            partition, "partition_hash"
        )

    budget = request["resource_budget_declaration"]
    budget["budget_hash"] = planner.canonical_hash_without_field(
        budget, "budget_hash"
    )
    request["request_hash"] = planner.canonical_hash_without_field(
        request, "request_hash"
    )
    return request


def build_request():
    fixture = load_json(FIXTURE_PATH)
    seed = fixture["request_seed"]
    catalog = load_yaml(ROOT / seed["action_catalog_binding"]["catalog_path"])
    actions = {action["action_id"]: action for action in catalog["actions"]}
    counterexample_document = load_json(
        ROOT / fixture["source_pins"]["counterexample_path"]
    )

    checker = deepcopy(seed["checker_seed"])
    checker["checker_run_hash"] = canonical_value_hash(checker)

    counterexample = deepcopy(seed["counterexample_seed"])
    counterexample["counterexample_hash"] = canonical_value_hash(
        counterexample_document
    )
    counterexample["distinguishing_predicates_hash"] = canonical_value_hash(
        counterexample["distinguishing_predicates"]
    )

    p4 = {
        "selection_record_hash": "",
        "allowed_action_ids": deepcopy(
            seed["p4_seed"]["allowed_action_ids"]
        ),
        "forbidden_action_ids": deepcopy(
            seed["p4_seed"]["forbidden_action_ids"]
        ),
    }

    partitions = []
    for partition_seed in seed["partition_seeds"]:
        action = actions[partition_seed["action_id"]]
        model = action["observation_model"]
        partition = {
            "action_id": action["action_id"],
            "observation_model_hash": canonical_value_hash(model),
            "projection_rule_id": model["projection_rule_id"],
            "output_domain": deepcopy(model["output_domain"]),
            "partition_basis": planner.PARTITION_BASIS,
            "world_outcomes": deepcopy(partition_seed["world_outcomes"]),
            "partition_hash": "",
        }
        partitions.append(partition)

    budget = deepcopy(seed["resource_budget_seed"])
    budget["budget_hash"] = ""
    request = {
        "schema_version": planner.REQUEST_SCHEMA_VERSION,
        "request_kind": planner.REQUEST_KIND,
        "planner_mode": planner.PLANNER_MODE,
        "execution_mode": planner.EXECUTION_MODE,
        "case_binding": deepcopy(seed["case_binding"]),
        "finite_domain_binding": deepcopy(seed["finite_domain_binding"]),
        "checker_binding": checker,
        "counterexample_binding": counterexample,
        "action_catalog_binding": deepcopy(
            seed["action_catalog_binding"]
        ),
        "p4_selection_binding": p4,
        "deterministic_outcome_partitions": partitions,
        "resource_budget_declaration": budget,
        "requested_decision_scope": planner.DECISION_SCOPE,
        "request_hash": "",
    }
    return finalize_request(request)


class KernelA17P1eDepth1PlannerTests(unittest.TestCase):
    def test_select_action_has_exact_request_and_decision_shapes(self):
        fixture = load_json(FIXTURE_PATH)
        request = build_request()
        before = deepcopy(request)

        decision = planner.evaluate_depth1_planner_request(request)

        self.assertEqual(set(request), planner.REQUEST_FIELDS)
        self.assertEqual(len(request), 14)
        self.assertEqual(set(decision), planner.DECISION_FIELDS)
        self.assertEqual(len(decision), 17)
        self.assertEqual(fixture["expected"]["decision"], decision["decision"])
        self.assertEqual(
            fixture["expected"]["selected_action_id"],
            decision["selected_action_id"],
        )
        self.assertEqual(
            fixture["expected"]["tied_action_ids"],
            decision["tie_break"]["tied_action_ids"],
        )
        self.assertEqual(
            fixture["expected"]["tie_break_rule"],
            decision["tie_break"]["rule_id"],
        )
        self.assertEqual(
            decision["record_hash"],
            planner.canonical_hash_without_field(decision, "record_hash"),
        )
        self.assertEqual(
            decision["resource_trace_binding"]["attempt_id"],
            "p1e-attempt:"
            + decision["resource_trace_binding"]["decision_basis_hash"],
        )
        self.assertEqual(before, request)
        self.assertIsNone(decision["probability_model"])
        self.assertIsNone(decision["planning_confidence"])
        self.assertTrue(
            all(
                value is False
                for value in decision["authority_ceiling"].values()
            )
        )

    def test_values_are_exact_rational_and_partition_order_independent(self):
        fixture = load_json(FIXTURE_PATH)
        request = build_request()
        first = planner.evaluate_depth1_planner_request(request)
        rows = {row["action_id"]: row for row in first["action_value_table"]}
        selected = rows[fixture["expected"]["selected_action_id"]]

        self.assertEqual(
            fixture["expected"]["raw_value_numerator"],
            selected["raw_value_numerator"],
        )
        self.assertEqual(
            fixture["expected"]["raw_value_denominator"],
            selected["raw_value_denominator"],
        )
        self.assertEqual(
            fixture["expected"]["reduced_value_numerator"],
            selected["reduced_value_numerator"],
        )
        self.assertEqual(
            fixture["expected"]["reduced_value_denominator"],
            selected["reduced_value_denominator"],
        )
        serialized = json.dumps(first)
        self.assertNotIn('"probability":', serialized)
        self.assertNotIn('"confidence":', serialized)

        reordered = deepcopy(request)
        reordered["deterministic_outcome_partitions"].reverse()
        reordered["request_hash"] = planner.canonical_hash_without_field(
            reordered, "request_hash"
        )
        second = planner.evaluate_depth1_planner_request(reordered)
        self.assertEqual(first["selected_action_id"], second["selected_action_id"])
        self.assertEqual(first["action_value_table"], second["action_value_table"])

    def test_abstain_paths_emit_no_partial_action_or_attempt(self):
        cases = {}

        no_action = build_request()
        predicates = ["unrelated:predicate"]
        no_action["counterexample_binding"][
            "distinguishing_predicates"
        ] = predicates
        no_action["p4_selection_binding"]["allowed_action_ids"] = []
        no_action["deterministic_outcome_partitions"] = []
        cases["no_action"] = (
            finalize_request(no_action),
            planner.ABSTAIN_NO_ACTION,
        )

        no_value = build_request()
        for partition in no_value["deterministic_outcome_partitions"]:
            same_outcome = partition["world_outcomes"][0]["outcome"]
            for row in partition["world_outcomes"]:
                row["outcome"] = same_outcome
        cases["no_value"] = (
            finalize_request(no_value),
            planner.ABSTAIN_NO_VALUE,
        )

        exhausted = build_request()
        budget = exhausted["resource_budget_declaration"]
        for dimension in budget["hard_limits"]:
            budget["hard_limits"][dimension] = 0
            budget["consumed"][dimension] = 0
            budget["remaining"][dimension] = 0
        budget["budget_status"] = "EXHAUSTED"
        cases["budget"] = (
            finalize_request(exhausted),
            planner.ABSTAIN_BUDGET,
        )

        singleton = build_request()
        finite = singleton["finite_domain_binding"]
        finite["current_u_world_ids"] = ["W-SUPPORT-H1"]
        for partition in singleton["deterministic_outcome_partitions"]:
            partition["world_outcomes"] = [
                row
                for row in partition["world_outcomes"]
                if row["world_id"] == "W-SUPPORT-H1"
            ]
        cases["singleton"] = (
            finalize_request(singleton),
            planner.ABSTAIN_SINGLETON,
        )

        for name, (request, expected) in cases.items():
            with self.subTest(name=name):
                decision = planner.evaluate_depth1_planner_request(request)
                self.assertEqual(expected, decision["decision"])
                self.assertIsNone(decision["selected_action_id"])
                self.assertIsNone(decision["resource_trace_binding"])

    def test_fail_closed_matrix_has_no_partial_emission(self):
        cases = []

        extra = build_request()
        extra["unexpected"] = True
        extra["request_hash"] = planner.canonical_hash_without_field(
            extra, "request_hash"
        )
        cases.append(("extra", extra, "P1E-001_CLOSED_WORLD_REQUEST_SHAPE"))

        wrong_scope = build_request()
        wrong_scope["planner_mode"] = "M3-KERNEL-D2"
        wrong_scope["request_hash"] = planner.canonical_hash_without_field(
            wrong_scope, "request_hash"
        )
        cases.append(
            ("wrong_scope", wrong_scope, "P1E-002_SCOPE_OR_MODE_MISMATCH")
        )

        unknown_world = build_request()
        unknown_world["finite_domain_binding"][
            "current_u_world_ids"
        ].append("W-UNKNOWN")
        cases.append(
            (
                "unknown_world",
                finalize_request(unknown_world),
                "P1E-004_FINITE_DOMAIN_BINDING_INVALID",
            )
        )

        checker_status = build_request()
        checker_status["checker_binding"]["checker_status"] = "UNIQUE_CANDIDATE"
        checker_status["checker_binding"]["checker_run_hash"] = (
            planner.canonical_hash_without_field(
                checker_status["checker_binding"], "checker_run_hash"
            )
        )
        checker_status["request_hash"] = planner.canonical_hash_without_field(
            checker_status, "request_hash"
        )
        cases.append(
            (
                "checker_status",
                checker_status,
                "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
            )
        )

        counterexample_target = build_request()
        counterexample_target["counterexample_binding"][
            "target_level"
        ] = "persistence"
        counterexample_target["request_hash"] = (
            planner.canonical_hash_without_field(
                counterexample_target, "request_hash"
            )
        )
        cases.append(
            (
                "counterexample_target",
                counterexample_target,
                "P1E-005_CHECKER_COUNTEREXAMPLE_BINDING_INVALID",
            )
        )

        stale_checker = build_request()
        stale_checker["checker_binding"]["checker_run_hash"] = (
            "sha256:" + "0" * 64
        )
        stale_checker["request_hash"] = planner.canonical_hash_without_field(
            stale_checker, "request_hash"
        )
        cases.append(
            (
                "stale_checker",
                stale_checker,
                "P1E-003_STALE_OR_MISMATCHED_HASH",
            )
        )

        hidden = build_request()
        hidden["actual_world_id"] = "W-SUPPORT-H1"
        hidden["request_hash"] = planner.canonical_hash_without_field(
            hidden, "request_hash"
        )
        cases.append(("hidden", hidden, "P1E-007_HIDDEN_OR_ORACLE_FIELD"))

        stop = build_request()
        stop["requested_system_state"] = "CERTIFIED_STOP"
        stop["request_hash"] = planner.canonical_hash_without_field(
            stop, "request_hash"
        )
        cases.append(
            ("stop", stop, "P1E-013_AUTHORITY_OR_STOP_REQUEST_FORBIDDEN")
        )

        wildcard = build_request()
        wildcard["action_catalog_binding"]["catalog_path"] = "configs/*.yaml"
        wildcard["request_hash"] = planner.canonical_hash_without_field(
            wildcard, "request_hash"
        )
        cases.append(("wildcard", wildcard, "P1E-006_CATALOG_NOT_EXACT"))

        stochastic = build_request()
        stochastic["deterministic_outcome_partitions"][0][
            "partition_basis"
        ] = "STOCHASTIC_MODEL"
        cases.append(
            (
                "stochastic",
                finalize_request(stochastic),
                "P1E-009_STOCHASTIC_OBSERVATION_MODEL",
            )
        )

        missing_partition = build_request()
        missing_partition["deterministic_outcome_partitions"].pop()
        cases.append(
            (
                "missing_partition",
                finalize_request(missing_partition),
                "P1E-010_OUTCOME_PARTITION_INVALID",
            )
        )

        bad_p4 = build_request()
        bad_p4["p4_selection_binding"]["selection_record_hash"] = (
            "sha256:" + "0" * 64
        )
        bad_p4["request_hash"] = planner.canonical_hash_without_field(
            bad_p4, "request_hash"
        )
        cases.append(
            ("bad_p4", bad_p4, "P1E-011_P4_SELECTION_BINDING_INVALID")
        )

        bad_budget = build_request()
        bad_budget["resource_budget_declaration"]["remaining"][
            "wall_seconds"
        ] = 999
        bad_budget["resource_budget_declaration"]["budget_hash"] = (
            planner.canonical_hash_without_field(
                bad_budget["resource_budget_declaration"], "budget_hash"
            )
        )
        bad_budget["request_hash"] = planner.canonical_hash_without_field(
            bad_budget, "request_hash"
        )
        cases.append(
            ("bad_budget", bad_budget, "P1E-012_RESOURCE_BUDGET_INVALID")
        )

        stale_request = build_request()
        stale_request["case_binding"]["case_id"] = "CHANGED"
        cases.append(
            (
                "stale_request",
                stale_request,
                "P1E-003_STALE_OR_MISMATCHED_HASH",
            )
        )

        cases.append(
            (
                "non_mapping",
                ["not", "a", "mapping"],
                "P1E-001_CLOSED_WORLD_REQUEST_SHAPE",
            )
        )

        for name, request, reason_code in cases:
            with self.subTest(name=name):
                decision = planner.evaluate_depth1_planner_request(request)
                self.assertEqual(planner.DENY, decision["decision"])
                self.assertIn(reason_code, decision["reason_codes"])
                self.assertIsNone(decision["selected_action_id"])
                self.assertIsNone(decision["resource_trace_binding"])
                self.assertEqual(17, len(decision))

    def test_missing_observation_model_is_fail_closed(self):
        partition = {
            "action_id": "action_missing_model",
            "observation_model_hash": "sha256:" + "0" * 64,
            "projection_rule_id": "missing",
            "output_domain": ["absent"],
            "partition_basis": planner.PARTITION_BASIS,
            "world_outcomes": [
                {"world_id": "W-A", "outcome": "absent"}
            ],
            "partition_hash": "sha256:" + "0" * 64,
        }
        with self.assertRaises(ValueError) as raised:
            planner._validate_partitions(
                [partition],
                ("action_missing_model",),
                ("W-A",),
                ("credential_activity:H1",),
                {
                    "action_missing_model": {
                        "observation_model": None
                    }
                },
            )
        self.assertEqual(
            "P1E-008_OBSERVATION_MODEL_MISSING", str(raised.exception)
        )

    def test_fixture_pins_and_protected_files_have_zero_drift(self):
        fixture = load_json(FIXTURE_PATH)
        for key in (
            "gamma",
            "action_catalog",
            "historical_resource_trace",
        ):
            path = ROOT / fixture["source_pins"][f"{key}_path"]
            expected = fixture["source_pins"][f"{key}_content_sha256"]
            self.assertEqual(expected, file_sha256(path))

        protected = {
            "src/actions/selection.py": (
                "16f26fa8ca5fa0fe39a9b901b8b13a09"
                "9f5527ed0c21f77718fd57763f847a83"
            ),
            "src/executor/deterministic.py": (
                "4e5ec71edc536bfef70fe19f86a723ac"
                "57b4ab5370bc845fa074ad2d107ba32a"
            ),
            "src/cli/kernel_e2e.py": (
                "8a7807c32d70e98ac5a36bda3a56f227"
                "9ebffbe23e0d2c6a11286bdba9208d60"
            ),
            "src/checker/finite_domain.py": (
                "e52b23538dd99e4a94d26faf865544e0"
                "268d17e13cf8bfbfd34ccb004c004d24"
            ),
            "src/counterexample/artifact.py": (
                "b8195a2043addb7f3e8374a045076319"
                "b77d1cb3225c5036b82dd3dfadb7125e"
            ),
            "configs/action-catalog-kernel-v0.8.yaml": (
                "6442c1099fd0e0a43f081b5e912b516c"
                "8feec3d2dbdd604b9a59020ee43c066b"
            ),
        }
        for path, expected in protected.items():
            with self.subTest(path=path):
                self.assertEqual(expected, file_sha256(ROOT / path))

        self.assertFalse(planner.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(planner.ACTION_EXECUTION_ENABLED)
        self.assertFalse(planner.SYSTEM_STATE_AUTHORITY)
        self.assertFalse(planner.STOP_AUTHORITY)
        self.assertIn("must not be inferred", planner.HARD_BAN)


if __name__ == "__main__":
    unittest.main()
