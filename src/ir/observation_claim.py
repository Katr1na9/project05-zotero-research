"""P11 deterministic adapter from P5 observations to bound Claim IR.

The adapter binds only evaluator-emitted observations to frozen catalog
metadata and an explicit caller-owned semantic context. It does not inspect
action names, infer hidden facts, admit evidence, promote authority, issue a
certificate, or derive a system state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")
_SOURCE_FAMILIES = frozenset(
    {
        "execution",
        "identity",
        "communication",
        "data_access",
        "control_plane",
        "system_provenance",
        "software_supply_chain",
        "external_intel",
        "human_investigation",
    }
)
_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _required_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    return value


def _string_tuple(
    value: object, field: str, *, require_nonempty: bool = False
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field} must be a string sequence")
    items = tuple(value)
    if require_nonempty and not items:
        raise ValueError(f"{field} must not be empty")
    if any(not isinstance(item, str) or not item for item in items):
        raise ValueError(f"{field} must contain non-empty strings")
    if len(set(items)) != len(items):
        raise ValueError(f"{field} must not contain duplicates")
    return items


def _contains_oracle_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _ORACLE_FIELDS or _contains_oracle_field(nested)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_oracle_field(item) for item in value)
    return False


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(f"observation is not canonical JSON: {exc}") from exc


def _content_hash(value: object) -> str:
    canonical = _canonical_json(value)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ObservationClaimActionBinding:
    """Explicit Claim-IR semantics for one frozen action-catalog entry."""

    predicate: str
    source_family: str
    source_schema: str
    admissible_levels: Sequence[str]

    def __post_init__(self) -> None:
        _required_string(self.predicate, "predicate")
        source_family = _required_string(self.source_family, "source_family")
        if source_family not in _SOURCE_FAMILIES:
            raise ValueError("source_family is outside the Claim IR finite domain")
        _required_string(self.source_schema, "source_schema")
        levels = _string_tuple(
            self.admissible_levels,
            "admissible_levels",
            require_nonempty=True,
        )
        object.__setattr__(self, "admissible_levels", levels)


@dataclass(frozen=True)
class ObservationClaimAdapterContext:
    """Frozen non-oracle metadata required to bind P5 rows into Claim IR."""

    source_id: str
    row_numbers: Mapping[str, int]
    action_bindings: Mapping[str, ObservationClaimActionBinding]
    certification_basis_rule_id: str
    certification_policy_hash: str
    parser_id: str
    parser_version: str
    prompt_or_rule_hash: str
    claim_id_prefix: str = "P11"

    def __post_init__(self) -> None:
        for field in (
            "source_id",
            "certification_basis_rule_id",
            "parser_id",
            "parser_version",
            "claim_id_prefix",
        ):
            _required_string(getattr(self, field), field)
        if _IDENTIFIER.fullmatch(self.claim_id_prefix) is None:
            raise ValueError("claim_id_prefix must be a Claim IR identifier")
        for field in ("certification_policy_hash", "prompt_or_rule_hash"):
            value = getattr(self, field)
            if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
                raise ValueError(f"{field} must be a canonical SHA-256")

        rows = _required_mapping(self.row_numbers, "row_numbers")
        frozen_rows: dict[str, int] = {}
        for observation_id, row_number in rows.items():
            if (
                not isinstance(observation_id, str)
                or not observation_id
                or isinstance(row_number, bool)
                or not isinstance(row_number, int)
                or row_number < 0
            ):
                raise ValueError("row_numbers must map observation IDs to rows >= 0")
            frozen_rows[observation_id] = row_number

        bindings = _required_mapping(self.action_bindings, "action_bindings")
        frozen_bindings: dict[str, ObservationClaimActionBinding] = {}
        for action_id, binding in bindings.items():
            if not isinstance(action_id, str) or not action_id:
                raise ValueError("action_bindings keys must be action IDs")
            if not isinstance(binding, ObservationClaimActionBinding):
                raise ValueError(
                    "action_bindings values must be ObservationClaimActionBinding"
                )
            frozen_bindings[action_id] = binding
        if not frozen_bindings:
            raise ValueError("action_bindings must not be empty")

        object.__setattr__(self, "row_numbers", MappingProxyType(frozen_rows))
        object.__setattr__(
            self, "action_bindings", MappingProxyType(frozen_bindings)
        )


class ObservationClaimIRAdapter:
    """Bind deterministic P5 observations without interpreting action names."""

    def adapt(
        self,
        observation: Mapping[str, object],
        action_catalog: Mapping[str, object],
        context: ObservationClaimAdapterContext,
    ) -> dict[str, object]:
        row = _required_mapping(observation, "observation")
        if not isinstance(context, ObservationClaimAdapterContext):
            raise ValueError("context must be an ObservationClaimAdapterContext")
        if _contains_oracle_field(row):
            raise ValueError("observation contains a forbidden oracle/hidden field")

        observation_id = _required_string(
            row.get("observation_id"), "observation.observation_id"
        )
        action_id = _required_string(row.get("action_id"), "observation.action_id")
        if _IDENTIFIER.fullmatch(observation_id) is None:
            raise ValueError("observation_id cannot form a Claim IR identifier")
        row_number = context.row_numbers.get(observation_id)
        if row_number is None:
            raise ValueError("observation has no explicit pointer row binding")
        binding = context.action_bindings.get(action_id)
        if binding is None:
            raise ValueError("action has no explicit Claim IR semantic binding")

        action = self._catalog_actions(action_catalog).get(action_id)
        if action is None:
            raise ValueError("observation action is absent from the frozen catalog")
        if _contains_oracle_field(action):
            raise ValueError("catalog action contains a forbidden oracle/hidden field")

        subject = self._subject(action, action_id)
        time = self._time(action, action_id)
        location = self._location(action, subject, action_id)
        observed_value = row.get("observed_value")
        if observed_value is None or not isinstance(
            observed_value, (str, int, float, bool)
        ):
            raise ValueError("observation.observed_value must be a JSON scalar")
        levels = list(binding.admissible_levels)
        claim = {
            "schema_version": "0.8.0",
            "claim_id": f"{context.claim_id_prefix}-{observation_id}",
            "subject": subject,
            "predicate": binding.predicate,
            "object": {
                "entity_id": None,
                "literal": observed_value,
                "entity_type": None,
            },
            "time": time,
            "location": location,
            "polarity": "positive",
            "modality": "observed",
            "truth_status": "supported",
            "epistemic_role": "case_evidence",
            "certification_authority": {
                "allowed": True,
                "levels": levels,
                "basis_rule_id": context.certification_basis_rule_id,
                "policy_hash": context.certification_policy_hash,
            },
            "source_family": binding.source_family,
            "source_schema": binding.source_schema,
            "pointer": {
                "source_id": context.source_id,
                "record_id": observation_id,
                "byte_or_row_range": [row_number, row_number],
                "content_hash": _content_hash(row),
            },
            "compiler": {
                "parser_id": context.parser_id,
                "parser_version": context.parser_version,
                "model_id": None,
                "prompt_or_rule_hash": context.prompt_or_rule_hash,
            },
            "binding_status": "bound",
            "admission_status": "candidate",
            "promotion_status": "none",
            "promotion_event_id": None,
            "admissible_levels": levels,
            "support_claim_ids": [],
            "contradict_claim_ids": [],
            "rule_trace": [context.certification_basis_rule_id],
            "confidence": {"extraction": 1.0, "source": 1.0, "model": None},
            "lifecycle_state": "bound",
        }
        if _contains_oracle_field(claim):
            raise AssertionError("adapter emitted an oracle/hidden field")
        return claim

    def adapt_batch(
        self,
        observations: Sequence[Mapping[str, object]],
        action_catalog: Mapping[str, object],
        context: ObservationClaimAdapterContext,
    ) -> tuple[dict[str, object], ...]:
        if not isinstance(observations, Sequence) or isinstance(
            observations, (str, bytes)
        ):
            raise ValueError("observations must be a row sequence")
        claims: list[dict[str, object]] = []
        seen: set[str] = set()
        for row in observations:
            observation = _required_mapping(row, "observation")
            observation_id = _required_string(
                observation.get("observation_id"), "observation.observation_id"
            )
            if observation_id in seen:
                raise ValueError("observations contain duplicate observation IDs")
            seen.add(observation_id)
            claims.append(self.adapt(observation, action_catalog, context))
        return tuple(claims)

    @staticmethod
    def _catalog_actions(
        action_catalog: Mapping[str, object],
    ) -> dict[str, Mapping[str, object]]:
        catalog = _required_mapping(action_catalog, "action_catalog")
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
                raise ValueError("action_catalog contains duplicate action IDs")
            actions[action_id] = action
        return actions

    @staticmethod
    def _subject(
        action: Mapping[str, object], action_id: str
    ) -> dict[str, str]:
        target = _required_mapping(
            action.get("target"), f"action {action_id!r}.target"
        )
        entity_ids = _string_tuple(
            target.get("entity_ids"),
            f"action {action_id!r}.target.entity_ids",
            require_nonempty=True,
        )
        if len(entity_ids) != 1:
            raise ValueError("observation Claim IR requires exactly one target entity")
        entity_type = _required_string(
            target.get("entity_type"), f"action {action_id!r}.target.entity_type"
        )
        return {"entity_id": entity_ids[0], "entity_type": entity_type}

    @staticmethod
    def _time(action: Mapping[str, object], action_id: str) -> dict[str, object]:
        scope = _required_mapping(
            action.get("scope"), f"action {action_id!r}.scope"
        )
        window = _required_mapping(
            scope.get("time_window"), f"action {action_id!r}.scope.time_window"
        )
        start = _required_string(
            window.get("start"), f"action {action_id!r}.scope.time_window.start"
        )
        end = _required_string(
            window.get("end"), f"action {action_id!r}.scope.time_window.end"
        )
        return {"start": start, "end": end, "precision": "bounded"}

    @staticmethod
    def _location(
        action: Mapping[str, object],
        subject: Mapping[str, str],
        action_id: str,
    ) -> dict[str, str | None]:
        invocation = _required_mapping(
            action.get("invocation"), f"action {action_id!r}.invocation"
        )
        parameters = _required_mapping(
            invocation.get("parameters"),
            f"action {action_id!r}.invocation.parameters",
        )

        def optional_string(name: str) -> str | None:
            value = parameters.get(name)
            if value is None:
                return None
            return _required_string(value, f"action {action_id!r}.parameters.{name}")

        return {
            "host": (
                subject["entity_id"] if subject["entity_type"] == "host" else None
            ),
            "tenant": optional_string("tenant"),
            "zone": optional_string("zone"),
        }
