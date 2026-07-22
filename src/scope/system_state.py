"""P9 pure system-state derivation for the finite Kernel.

The deriver maps already-computed Checker, recertification, selection, and
execution results to exactly one frozen main state. It performs no planning,
action execution, world elimination, certificate issuance, or orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.actions.selection import ActionSelectionResult
from src.checker.finite_domain import CheckerRun, CheckerStatus
from src.checker.level_certificate import IssuedLevelCertificate
from src.executor.deterministic import ExecutionBatchResult

from .recertify import RecertificationResult


class SystemStatus(str, Enum):
    SCOPE_MISMATCH_SUSPECTED = "SCOPE_MISMATCH_SUSPECTED"
    UNKNOWN = "UNKNOWN"
    CERTIFIED_STOP = "CERTIFIED_STOP"
    CONTINUE = "CONTINUE"
    DISTINGUISHABLE_BUT_INFEASIBLE = "DISTINGUISHABLE_BUT_INFEASIBLE"
    UNRESOLVABLE_UNDER_CATALOG = "UNRESOLVABLE_UNDER_CATALOG"
    NO_KNOWN_DISTINGUISHING_ACTION = "NO_KNOWN_DISTINGUISHING_ACTION"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


MAIN_STATE_ORDER = tuple(status.value for status in SystemStatus)


@dataclass(frozen=True)
class SystemStateDecision:
    system_status: SystemStatus
    reason_code: str
    conditional: bool
    effective_checker_status: str
    recertification_used: bool
    certificate_id: str | None = None

    def to_outcome_fields(self) -> dict[str, object]:
        return {
            "system_status": self.system_status.value,
            "reason_code": self.reason_code,
            "conditional": self.conditional,
            "effective_checker_status": self.effective_checker_status,
            "recertification_used": self.recertification_used,
            "certificate_id": self.certificate_id,
        }


class SystemStateDeriver:
    """Apply the frozen P0 precedence to existing typed component results."""

    def derive(
        self,
        checker_run: CheckerRun,
        *,
        recertification_result: RecertificationResult | None = None,
        action_selection: ActionSelectionResult | None = None,
        execution_result: ExecutionBatchResult | None = None,
        catalog_observation_equivalent: bool = False,
        formal_distinguishing_infeasible: bool = False,
        budget_exhausted: bool = False,
        level_certificate: IssuedLevelCertificate | None = None,
        active_gamma_hash: str | None = None,
        active_evidence_hash: str | None = None,
    ) -> SystemStateDecision:
        if not isinstance(checker_run, CheckerRun):
            raise ValueError("checker_run must be a CheckerRun")
        if recertification_result is not None and not isinstance(
            recertification_result, RecertificationResult
        ):
            raise ValueError("recertification_result has the wrong type")
        if action_selection is not None and not isinstance(
            action_selection, ActionSelectionResult
        ):
            raise ValueError("action_selection has the wrong type")
        if execution_result is not None and not isinstance(
            execution_result, ExecutionBatchResult
        ):
            raise ValueError("execution_result has the wrong type")
        if execution_result is not None and action_selection is None:
            raise ValueError("execution_result requires action_selection")
        if not isinstance(catalog_observation_equivalent, bool):
            raise ValueError("catalog_observation_equivalent must be boolean")
        if not isinstance(formal_distinguishing_infeasible, bool):
            raise ValueError("formal_distinguishing_infeasible must be boolean")
        if not isinstance(budget_exhausted, bool):
            raise ValueError("budget_exhausted must be boolean")

        effective_run = (
            recertification_result.checker_run
            if recertification_result is not None
            else checker_run
        )
        recertification_used = recertification_result is not None
        status = effective_run.checker_status

        if status is CheckerStatus.SCOPE_MISMATCH_SUSPECTED:
            return self._decision(
                SystemStatus.SCOPE_MISMATCH_SUSPECTED,
                "P9-STATE-001_SCOPE_MISMATCH",
                status,
                recertification_used,
            )
        if status is CheckerStatus.UNKNOWN:
            return self._decision(
                SystemStatus.UNKNOWN,
                "P9-STATE-002_CHECKER_UNKNOWN",
                status,
                recertification_used,
            )

        if (
            isinstance(level_certificate, IssuedLevelCertificate)
            and level_certificate.binds_checker_run(effective_run)
            and level_certificate.binds_artifacts(
                active_gamma_hash, active_evidence_hash
            )
        ):
            return self._decision(
                SystemStatus.CERTIFIED_STOP,
                "P9-STATE-003_LEVEL_COMPLETE_CERTIFICATE",
                status,
                recertification_used,
                conditional=False,
                certificate_id=level_certificate.certificate_id,
            )

        if status is CheckerStatus.COUNTEREXAMPLE_FOUND:
            return self._counterexample_state(
                status=status,
                recertification_used=recertification_used,
                action_selection=action_selection,
                execution_result=execution_result,
                catalog_observation_equivalent=catalog_observation_equivalent,
                formal_distinguishing_infeasible=formal_distinguishing_infeasible,
            )

        if budget_exhausted:
            return self._decision(
                SystemStatus.BUDGET_EXHAUSTED,
                "P9-STATE-008_BUDGET_EXHAUSTED",
                status,
                recertification_used,
            )

        if status is CheckerStatus.CANDIDATE_CERTIFIED:
            return self._decision(
                SystemStatus.CONTINUE,
                "P9-STATE-009_CANDIDATE_ONLY_NOT_LEVEL_COMPLETE",
                status,
                recertification_used,
            )
        if status is CheckerStatus.REJECT_CANDIDATE:
            return self._decision(
                SystemStatus.CONTINUE,
                "P9-STATE-010_REJECTED_CANDIDATE_CONTINUE_SCAN",
                status,
                recertification_used,
            )
        raise ValueError(f"unhandled Checker status: {status.value}")

    def _counterexample_state(
        self,
        *,
        status: CheckerStatus,
        recertification_used: bool,
        action_selection: ActionSelectionResult | None,
        execution_result: ExecutionBatchResult | None,
        catalog_observation_equivalent: bool,
        formal_distinguishing_infeasible: bool,
    ) -> SystemStateDecision:
        allowed = action_selection.allowed_actions if action_selection else ()
        forbidden = action_selection.forbidden_actions if action_selection else ()
        if set(allowed).intersection(forbidden):
            raise ValueError("allowed and forbidden action sets must be disjoint")

        if allowed:
            if execution_result is None:
                return self._decision(
                    SystemStatus.CONTINUE,
                    "P9-STATE-004_FORMAL_ACTION_FEASIBLE",
                    status,
                    recertification_used,
                )
            observed_action_ids = {
                row.get("action_id")
                for row in execution_result.observations
                if isinstance(row, dict)
            }
            if set(allowed).intersection(observed_action_ids):
                return self._decision(
                    SystemStatus.CONTINUE,
                    "P9-STATE-004_FORMAL_ACTION_FEASIBLE",
                    status,
                    recertification_used,
                )
            failed_action_ids = {
                failure.action_id for failure in execution_result.failures
            }
            if set(allowed).issubset(failed_action_ids):
                return self._decision(
                    SystemStatus.DISTINGUISHABLE_BUT_INFEASIBLE,
                    "P9-STATE-005_SELECTED_ACTIONS_INFEASIBLE",
                    status,
                    recertification_used,
                )
            return self._decision(
                SystemStatus.CONTINUE,
                "P9-STATE-004_FORMAL_ACTION_FEASIBLE",
                status,
                recertification_used,
            )

        if formal_distinguishing_infeasible:
            return self._decision(
                SystemStatus.DISTINGUISHABLE_BUT_INFEASIBLE,
                "P9-STATE-005_FORMAL_ACTION_INFEASIBLE",
                status,
                recertification_used,
            )
        if catalog_observation_equivalent:
            return self._decision(
                SystemStatus.UNRESOLVABLE_UNDER_CATALOG,
                "P9-STATE-006_FORMAL_CATALOG_EQUIVALENCE",
                status,
                recertification_used,
            )
        return self._decision(
            SystemStatus.NO_KNOWN_DISTINGUISHING_ACTION,
            "P9-STATE-007_NO_FORMAL_DISTINGUISHER",
            status,
            recertification_used,
        )

    @staticmethod
    def _decision(
        system_status: SystemStatus,
        reason_code: str,
        checker_status: CheckerStatus,
        recertification_used: bool,
        *,
        conditional: bool = True,
        certificate_id: str | None = None,
    ) -> SystemStateDecision:
        return SystemStateDecision(
            system_status=system_status,
            reason_code=reason_code,
            conditional=conditional,
            effective_checker_status=checker_status.value,
            recertification_used=recertification_used,
            certificate_id=certificate_id,
        )
