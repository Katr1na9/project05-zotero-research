"""P4 deterministic selection of catalog-declared distinguishing actions.

Selection is metadata-only: the selector intersects frozen observation-model
``world_dependencies`` with counterexample ``distinguishing_predicates`` and
requires a declared world-elimination rule plus current executability. It does
not invoke an executor or observation model, feed observations back, plan,
promote authority, or emit a system state.

The Kernel negative-action contract also names two policy-prohibited
pseudo-actions that cannot be valid action-catalog entries. They are derived
deterministically from the target level and the hidden/oracle-field
prohibition, rather than being silently treated as ordinary absent catalog
actions.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_FORBIDDEN_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)
_AUTHORITY_STATUSES = frozenset(
    {"executable", "not_authorized", "temporarily_unavailable"}
)
_FEASIBILITY_STATUSES = frozenset(
    {
        "executable",
        "not_authorized",
        "temporarily_unavailable",
        "retention_expired",
        "sensor_unavailable",
    }
)


def _required_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _string_sequence(
    value: object,
    field_name: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a string sequence")
    frozen = tuple(value)
    if nonempty and not frozen:
        raise ValueError(f"{field_name} must not be empty")
    if any(not isinstance(item, str) or not item for item in frozen):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(frozen)) != len(frozen):
        raise ValueError(f"{field_name} must not contain duplicates")
    return frozen


def _reject_oracle_fields(value: object, path: str = "catalog") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if key in _FORBIDDEN_ORACLE_FIELDS:
                raise ValueError(f"forbidden oracle field at {path}.{key}")
            _reject_oracle_fields(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, nested in enumerate(value):
            _reject_oracle_fields(nested, f"{path}[{index}]")


@dataclass(frozen=True)
class ActionSelectionResult:
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    catalog_actions_examined: int

    def to_outcome_fields(self) -> dict[str, list[str]]:
        """Return selection-owned fields without system state or STOP power."""

        return {
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
        }


class DistinguishingActionSelector:
    """Select catalog actions by frozen formal metadata in action-ID order."""

    def select(
        self,
        counterexample_artifact: Mapping[str, object],
        action_catalog: Mapping[str, object],
    ) -> ActionSelectionResult:
        artifact = _required_mapping(counterexample_artifact, "counterexample")
        if artifact.get("checker_status") != "COUNTEREXAMPLE_FOUND":
            raise ValueError("action selection requires COUNTEREXAMPLE_FOUND")

        target_level = _required_string(
            artifact.get("target_level"), "counterexample.target_level"
        )
        if _IDENTIFIER.fullmatch(target_level) is None:
            raise ValueError("counterexample.target_level is not a valid identifier")
        predicates = frozenset(
            _string_sequence(
                artifact.get("distinguishing_predicates"),
                "counterexample.distinguishing_predicates",
                nonempty=True,
            )
        )

        catalog = _required_mapping(action_catalog, "action_catalog")
        _reject_oracle_fields(catalog)
        raw_actions = catalog.get("actions")
        if not isinstance(raw_actions, Sequence) or isinstance(
            raw_actions, (str, bytes)
        ):
            raise ValueError("action_catalog.actions must be an action sequence")
        if not raw_actions:
            raise ValueError("action_catalog.actions must not be empty")

        actions_by_id: dict[str, Mapping[str, object]] = {}
        for index, raw_action in enumerate(raw_actions):
            action = _required_mapping(
                raw_action, f"action_catalog.actions[{index}]"
            )
            action_id = _required_string(
                action.get("action_id"),
                f"action_catalog.actions[{index}].action_id",
            )
            if _IDENTIFIER.fullmatch(action_id) is None:
                raise ValueError(f"invalid action ID: {action_id!r}")
            if action_id in actions_by_id:
                raise ValueError(f"duplicate action ID: {action_id!r}")
            actions_by_id[action_id] = action

        forbidden = (
            f"oracle_reveal_true_{target_level}",
            "use_hidden_recoverable_claim_ids",
        )
        allowed: list[str] = []
        for action_id in sorted(actions_by_id):
            action = actions_by_id[action_id]
            if action_id in forbidden:
                continue
            if self._is_selectable(action, predicates, action_id):
                allowed.append(action_id)

        return ActionSelectionResult(
            allowed_actions=tuple(allowed),
            forbidden_actions=forbidden,
            catalog_actions_examined=len(actions_by_id),
        )

    @staticmethod
    def _is_selectable(
        action: Mapping[str, object],
        predicates: frozenset[str],
        action_id: str,
    ) -> bool:
        eligibility = action.get("formal_analysis_eligibility")
        if eligibility not in {"formal", "heuristic_only"}:
            raise ValueError(
                f"action {action_id!r} lacks explicit formal/heuristic eligibility"
            )

        authority = _required_mapping(
            action.get("authority"), f"action {action_id!r}.authority"
        )
        authority_status = authority.get("current_status")
        if authority_status not in _AUTHORITY_STATUSES:
            raise ValueError(f"action {action_id!r} has invalid authority status")

        feasibility = _required_mapping(
            action.get("feasibility"), f"action {action_id!r}.feasibility"
        )
        feasibility_status = feasibility.get("status")
        if feasibility_status not in _FEASIBILITY_STATUSES:
            raise ValueError(f"action {action_id!r} has invalid feasibility status")

        state_effect = _required_mapping(
            action.get("state_effect"), f"action {action_id!r}.state_effect"
        )
        elimination_rules = _string_sequence(
            state_effect.get("world_elimination_rule_ids"),
            f"action {action_id!r}.world_elimination_rule_ids",
        )

        observation_model = action.get("observation_model")
        if observation_model is None:
            return False
        observation = _required_mapping(
            observation_model, f"action {action_id!r}.observation_model"
        )
        if observation.get("noise_model") != "deterministic":
            raise ValueError(
                f"action {action_id!r} has a non-deterministic observation model"
            )
        dependencies = frozenset(
            _string_sequence(
                observation.get("world_dependencies"),
                f"action {action_id!r}.world_dependencies",
            )
        )

        if eligibility != "formal":
            return False
        if not predicates.intersection(dependencies):
            return False
        if not elimination_rules:
            return False
        return (
            authority_status == "executable"
            and feasibility_status == "executable"
        )
