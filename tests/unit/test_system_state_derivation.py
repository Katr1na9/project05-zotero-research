import importlib
import json
import unittest

from src.actions.selection import ActionSelectionResult
from src.checker.finite_domain import CheckerRun, CheckerStatus, QueryResult, QueryStatus
from src.executor.deterministic import ExecutionBatchResult, ExecutionFailure
from tests.unit.test_level_certificate_issuer import (
    candidate_certified_run,
    counterexample_run,
    issue_valid_certificate,
)


try:
    state_api = importlib.import_module("src.scope.system_state")
    certificate_api = importlib.import_module("src.checker.level_certificate")
except (ImportError, ModuleNotFoundError):
    state_api = None
    certificate_api = None


def checker_run(status):
    if status is CheckerStatus.SCOPE_MISMATCH_SUSPECTED:
        return CheckerRun(
            QueryResult(QueryStatus.UNSAT),
            QueryResult.not_run(),
            QueryResult.not_run(),
            status,
        )
    if status is CheckerStatus.UNKNOWN:
        return CheckerRun(
            QueryResult(QueryStatus.TIMEOUT),
            QueryResult.not_run(),
            QueryResult.not_run(),
            status,
        )
    if status is CheckerStatus.REJECT_CANDIDATE:
        return CheckerRun(
            QueryResult(QueryStatus.SAT),
            QueryResult(QueryStatus.UNSAT),
            QueryResult.not_run(),
            status,
        )
    raise ValueError(status)


def selection(allowed=(), forbidden=()):
    return ActionSelectionResult(tuple(allowed), tuple(forbidden), 2)


class SystemStateDerivationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(state_api, "P9 system state API is missing")
        self.deriver = state_api.SystemStateDeriver()

    def test_scope_mismatch_and_unknown_precede_any_stop_claim(self):
        certificate = issue_valid_certificate()

        mismatch = self.deriver.derive(
            checker_run(CheckerStatus.SCOPE_MISMATCH_SUSPECTED),
            level_certificate=certificate,
        )
        unknown = self.deriver.derive(
            checker_run(CheckerStatus.UNKNOWN), level_certificate=certificate
        )

        self.assertEqual("SCOPE_MISMATCH_SUSPECTED", mismatch.system_status.value)
        self.assertEqual("UNKNOWN", unknown.system_status.value)

    def test_only_bound_level_certificate_can_emit_certified_stop(self):
        candidate_only = self.deriver.derive(candidate_certified_run())
        certificate = issue_valid_certificate()
        document = certificate.to_dict()
        stopped = self.deriver.derive(
            candidate_certified_run(),
            level_certificate=certificate,
            active_gamma_hash=document["gamma_hash"],
            active_evidence_hash=document["evidence_hash"],
            active_admission_policy_hash=document["admission_policy_hash"],
            active_admission_policy_approval_hash=document[
                "admission_policy_approval_hash"
            ],
            active_formal_ceiling_hash=document["formal_ceiling_hash"],
        )

        self.assertEqual("CONTINUE", candidate_only.system_status.value)
        self.assertTrue(candidate_only.conditional)
        self.assertIsNone(candidate_only.certificate_id)
        self.assertEqual("CERTIFIED_STOP", stopped.system_status.value)
        self.assertFalse(stopped.conditional)
        self.assertEqual("CERT-LEVEL-001", stopped.certificate_id)

        stale = self.deriver.derive(
            candidate_certified_run(),
            level_certificate=certificate,
            active_gamma_hash=document["gamma_hash"],
            active_evidence_hash="sha256:" + "a0" * 32,
            active_admission_policy_hash=document["admission_policy_hash"],
            active_admission_policy_approval_hash=document[
                "admission_policy_approval_hash"
            ],
            active_formal_ceiling_hash=document["formal_ceiling_hash"],
        )
        self.assertEqual("CONTINUE", stale.system_status.value)

    def test_forged_candidate_or_non_checker_certificate_cannot_stop(self):
        valid = issue_valid_certificate().to_dict()
        for field, value in (
            ("certification_scope", "candidate_level"),
            ("issued_by", "m3star"),
        ):
            with self.subTest(field=field):
                forged = dict(valid)
                forged[field] = value
                wrapped = certificate_api.IssuedLevelCertificate(
                    json.dumps(forged, sort_keys=True, separators=(",", ":"))
                )
                decision = self.deriver.derive(
                    candidate_certified_run(),
                    level_certificate=wrapped,
                    active_gamma_hash=valid["gamma_hash"],
                    active_evidence_hash=valid["evidence_hash"],
                    active_admission_policy_hash=valid[
                        "admission_policy_hash"
                    ],
                    active_admission_policy_approval_hash=valid[
                        "admission_policy_approval_hash"
                    ],
                    active_formal_ceiling_hash=valid["formal_ceiling_hash"],
                )
                self.assertEqual("CONTINUE", decision.system_status.value)

    def test_counterexample_with_formal_feasible_action_continues(self):
        decision = self.deriver.derive(
            counterexample_run(),
            action_selection=selection(
                allowed=("query_logon_origin_H3",),
                forbidden=("oracle_reveal",),
            ),
        )

        self.assertEqual("CONTINUE", decision.system_status.value)
        self.assertEqual("P9-STATE-004_FORMAL_ACTION_FEASIBLE", decision.reason_code)

    def test_failed_selected_actions_are_distinguishable_but_infeasible(self):
        selected = selection(allowed=("query_logon_origin_H3",))
        execution = ExecutionBatchResult(
            observations=(),
            resource_traces=(),
            failures=(
                ExecutionFailure(
                    "query_logon_origin_H3",
                    "permission_denied",
                    ("AUTHORITY_MISSING",),
                ),
            ),
        )

        decision = self.deriver.derive(
            counterexample_run(),
            action_selection=selected,
            execution_result=execution,
        )

        self.assertEqual(
            "DISTINGUISHABLE_BUT_INFEASIBLE", decision.system_status.value
        )

    def test_infeasible_equivalent_and_unknown_action_routes_are_distinct(self):
        infeasible = self.deriver.derive(
            counterexample_run(),
            action_selection=selection(forbidden=("formal_but_forbidden",)),
            formal_distinguishing_infeasible=True,
        )
        equivalent = self.deriver.derive(
            counterexample_run(),
            action_selection=selection(),
            catalog_observation_equivalent=True,
        )
        unknown = self.deriver.derive(
            counterexample_run(), action_selection=selection()
        )

        self.assertEqual(
            "DISTINGUISHABLE_BUT_INFEASIBLE", infeasible.system_status.value
        )
        self.assertEqual("UNRESOLVABLE_UNDER_CATALOG", equivalent.system_status.value)
        self.assertEqual(
            "NO_KNOWN_DISTINGUISHING_ACTION", unknown.system_status.value
        )

        oracle_only = self.deriver.derive(
            counterexample_run(),
            action_selection=selection(
                forbidden=("oracle_reveal_true_initial_foothold",)
            ),
        )
        self.assertEqual(
            "NO_KNOWN_DISTINGUISHING_ACTION", oracle_only.system_status.value
        )

    def test_budget_and_rejected_candidate_have_unique_main_state(self):
        exhausted = self.deriver.derive(
            checker_run(CheckerStatus.REJECT_CANDIDATE), budget_exhausted=True
        )
        ongoing = self.deriver.derive(
            checker_run(CheckerStatus.REJECT_CANDIDATE), budget_exhausted=False
        )

        self.assertEqual("BUDGET_EXHAUSTED", exhausted.system_status.value)
        self.assertEqual("CONTINUE", ongoing.system_status.value)
        self.assertNotEqual(exhausted.system_status, ongoing.system_status)

    def test_main_state_order_matches_frozen_p0_contract(self):
        self.assertEqual(
            (
                "SCOPE_MISMATCH_SUSPECTED",
                "UNKNOWN",
                "CERTIFIED_STOP",
                "CONTINUE",
                "DISTINGUISHABLE_BUT_INFEASIBLE",
                "UNRESOLVABLE_UNDER_CATALOG",
                "NO_KNOWN_DISTINGUISHING_ACTION",
                "BUDGET_EXHAUSTED",
            ),
            state_api.MAIN_STATE_ORDER,
        )


if __name__ == "__main__":
    unittest.main()
