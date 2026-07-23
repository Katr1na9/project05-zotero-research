"""P5 deterministic, table-driven observation execution.

The executor replays evaluator-frozen observation and resource rows for P4
selected actions. It never invokes an external connector, samples noise,
mutates Claim IR, feeds evidence back to the Checker, plans another action,
promotes authority, or emits a system state. Missing, failed, or infeasible
execution data is reported explicitly without rewriting any Checker result.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass

from src.actions.selection import ActionSelectionResult


class ForbiddenActionError(ValueError):
    """Raised before replay when a policy-forbidden action is requested."""


def _required_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_sequence(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a string sequence")
    frozen = tuple(value)
    if any(not isinstance(item, str) or not item for item in frozen):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(frozen)) != len(frozen):
        raise ValueError(f"{field_name} must not contain duplicates")
    return frozen


def _freeze_rows(
    rows: Sequence[Mapping[str, object]],
    table_name: str,
) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError(f"{table_name} must be a row sequence")
    frozen: list[dict[str, object]] = []
    action_ids: set[str] = set()
    for index, raw_row in enumerate(rows):
        row = _required_mapping(raw_row, f"{table_name}[{index}]")
        action_id = _required_string(
            row.get("action_id"), f"{table_name}[{index}].action_id"
        )
        if action_id in action_ids:
            raise ValueError(
                f"{table_name} contains duplicate action row {action_id!r}"
            )
        action_ids.add(action_id)
        frozen.append(deepcopy(dict(row)))
    return tuple(frozen)


@dataclass(frozen=True)
class FrozenExecutionTables:
    """Evaluator-owned deterministic rows, keyed one-to-one by action ID."""

    observation_rows: Sequence[Mapping[str, object]]
    resource_rows: Sequence[Mapping[str, object]]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observation_rows",
            _freeze_rows(self.observation_rows, "observation_rows"),
        )
        object.__setattr__(
            self,
            "resource_rows",
            _freeze_rows(self.resource_rows, "resource_rows"),
        )


@dataclass(frozen=True)
class ExecutionFailure:
    action_id: str
    status: str
    reason_codes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "status": self.status,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class ExecutionBatchResult:
    observations: tuple[dict[str, object], ...]
    resource_traces: tuple[dict[str, object], ...]
    failures: tuple[ExecutionFailure, ...]

    def to_output_fields(self) -> dict[str, object]:
        """Return executor-owned rows without Checker or system-state fields."""

        return {
            "observations": deepcopy(list(self.observations)),
            "resource_traces": deepcopy(list(self.resource_traces)),
            "failures": [failure.to_dict() for failure in self.failures],
        }


class DeterministicObservationExecutor:
    """Replay selected actions from frozen tables without observation feedback."""

    def execute(
        self,
        selection: ActionSelectionResult,
        action_catalog: Mapping[str, object],
        tables: FrozenExecutionTables,
    ) -> ExecutionBatchResult:
        selected = _string_sequence(
            selection.allowed_actions, "selection.allowed_actions"
        )
        forbidden = frozenset(
            _string_sequence(
                selection.forbidden_actions, "selection.forbidden_actions"
            )
        )
        prohibited_requests = tuple(
            action_id for action_id in selected if action_id in forbidden
        )
        if prohibited_requests:
            raise ForbiddenActionError(
                "policy-forbidden action request(s): "
                + ", ".join(prohibited_requests)
            )

        catalog = _required_mapping(action_catalog, "action_catalog")
        actions = self._catalog_actions(catalog)
        observation_by_action = {
            row["action_id"]: row for row in tables.observation_rows
        }
        resource_by_action = {
            row["action_id"]: row for row in tables.resource_rows
        }

        failures: list[ExecutionFailure] = []
        blocked_actions: set[str] = set()
        for action_id in selected:
            action = actions.get(action_id)
            if action is None:
                failures.append(
                    ExecutionFailure(action_id, "UNKNOWN_CATALOG_ACTION")
                )
                blocked_actions.add(action_id)
                continue

            observation_model = action.get("observation_model")
            if observation_model is None:
                failures.append(
                    ExecutionFailure(action_id, "OBSERVATION_MODEL_MISSING")
                )
                blocked_actions.add(action_id)
                continue
            model = _required_mapping(
                observation_model, f"action {action_id!r}.observation_model"
            )
            if model.get("noise_model") != "deterministic":
                raise ValueError(
                    f"action {action_id!r} is not deterministic and cannot execute"
                )

            authority = _required_mapping(
                action.get("authority"), f"action {action_id!r}.authority"
            )
            feasibility = _required_mapping(
                action.get("feasibility"), f"action {action_id!r}.feasibility"
            )
            authority_status = authority.get("current_status")
            feasibility_status = feasibility.get("status")
            if (
                authority_status != "executable"
                or feasibility_status != "executable"
            ):
                status = (
                    feasibility_status
                    if feasibility_status != "executable"
                    else authority_status
                )
                status = _required_string(status, f"action {action_id!r}.status")
                reason_codes = _string_sequence(
                    feasibility.get("reason_codes", ()),
                    f"action {action_id!r}.reason_codes",
                )
                failures.append(
                    ExecutionFailure(action_id, status, reason_codes)
                )
                blocked_actions.add(action_id)
                continue

            observation = observation_by_action.get(action_id)
            if observation is None:
                failures.append(
                    ExecutionFailure(action_id, "OBSERVATION_ROW_MISSING")
                )
            else:
                output_domain = model.get("output_domain")
                if not isinstance(output_domain, Sequence) or isinstance(
                    output_domain, (str, bytes)
                ):
                    raise ValueError(
                        f"action {action_id!r}.output_domain must be a sequence"
                    )
                if observation.get("observed_value") not in output_domain:
                    raise ValueError(
                        f"action {action_id!r} observed value is outside output_domain"
                    )

            resource = resource_by_action.get(action_id)
            if resource is None:
                failures.append(
                    ExecutionFailure(action_id, "RESOURCE_TRACE_MISSING")
                )
            elif resource.get("status") != "succeeded":
                failures.append(
                    ExecutionFailure(
                        action_id,
                        _required_string(
                            resource.get("status"),
                            f"resource row {action_id!r}.status",
                        ),
                    )
                )

        selected_set = set(selected)
        observations = tuple(
            deepcopy(row)
            for row in tables.observation_rows
            if row["action_id"] in selected_set
            and row["action_id"] not in blocked_actions
        )
        resources = tuple(
            deepcopy(row)
            for row in tables.resource_rows
            if row["action_id"] in selected_set
        )
        return ExecutionBatchResult(
            observations=observations,
            resource_traces=resources,
            failures=tuple(failures),
        )

    @staticmethod
    def _catalog_actions(
        catalog: Mapping[str, object],
    ) -> dict[str, Mapping[str, object]]:
        raw_actions = catalog.get("actions")
        if not isinstance(raw_actions, Sequence) or isinstance(
            raw_actions, (str, bytes)
        ):
            raise ValueError("action_catalog.actions must be an action sequence")
        actions: dict[str, Mapping[str, object]] = {}
        for index, raw_action in enumerate(raw_actions):
            action = _required_mapping(
                raw_action, f"action_catalog.actions[{index}]"
            )
            action_id = _required_string(
                action.get("action_id"),
                f"action_catalog.actions[{index}].action_id",
            )
            if action_id in actions:
                raise ValueError(f"duplicate catalog action ID: {action_id!r}")
            actions[action_id] = action
        return actions
