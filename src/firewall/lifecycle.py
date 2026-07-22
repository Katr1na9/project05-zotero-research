"""P8 audited Claim IR admission, promotion, and revocation transitions.

This module applies an already-issued P7 Firewall decision and records every
successful lifecycle change in a deterministic append-only hash chain. It has
no certificate issuance, level-complete certification, checker orchestration,
planner, system-state, or STOP authority.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import re

from .admission import AdmissionDecision


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_RFC3339_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?Z$"
)
_GENESIS_HASH = "sha256:" + "0" * 64
_OPERATIONS = frozenset({"ADMIT", "PROMOTE", "REVOKE"})
_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)


class LifecycleTransitionRejected(ValueError):
    """Fail-closed transition rejection with a stable machine reason code."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code


def _reject(reason_code: str, message: str) -> None:
    raise LifecycleTransitionRejected(reason_code, message)


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
        _reject("P8-013_CLAIM_NOT_CANONICAL_JSON", str(exc))
    raise AssertionError("unreachable")


def _json_copy(value: object) -> object:
    return json.loads(_canonical_json(value))


def _sha256(canonical_text: str) -> str:
    return "sha256:" + hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _validate_timestamp(timestamp: object) -> bool:
    if not isinstance(timestamp, str) or _RFC3339_UTC.fullmatch(timestamp) is None:
        return False
    try:
        datetime.fromisoformat(timestamp.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def _unique_nonempty_strings(value: object, *, require_nonempty: bool) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    items = tuple(value)
    if require_nonempty and not items:
        return False
    return (
        all(isinstance(item, str) and bool(item) for item in items)
        and len(set(items)) == len(items)
    )


def _contains_oracle_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _ORACLE_FIELDS or _contains_oracle_field(nested)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_oracle_field(item) for item in value)
    return False


def _promotion_pointer_is_resolvable(pointer: object) -> bool:
    if not isinstance(pointer, Mapping):
        return False
    source_id = pointer.get("source_id")
    record_id = pointer.get("record_id")
    content_hash = pointer.get("content_hash")
    return (
        _valid_identifier(source_id)
        and (
            _valid_identifier(record_id)
            or (
                isinstance(content_hash, str)
                and _SHA256.fullmatch(content_hash) is not None
            )
        )
    )


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit event with canonical before/after snapshots."""

    sequence: int
    event_id: str
    claim_id: str
    operation: str
    rule_id: str
    timestamp: str
    previous_hash: str
    before_json: str
    after_json: str
    event_hash: str

    @property
    def before(self) -> dict[str, object]:
        return json.loads(self.before_json)

    @property
    def after(self) -> dict[str, object]:
        return json.loads(self.after_json)

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema_version": "0.8.0",
            "sequence": self.sequence,
            "event_id": self.event_id,
            "claim_id": self.claim_id,
            "operation": self.operation,
            "rule_id": self.rule_id,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "before": self.before,
            "after": self.after,
        }

    def recompute_hash(self) -> str:
        return _sha256(_canonical_json(self._hash_payload()))

    def to_dict(self) -> dict[str, object]:
        payload = self._hash_payload()
        payload["event_hash"] = self.event_hash
        return payload


class AppendOnlyAuditLedger:
    """In-memory append-only tuple ledger with deterministic hash chaining."""

    def __init__(self) -> None:
        self._events: tuple[AuditEvent, ...] = ()

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return self._events

    def append_transition(
        self,
        *,
        event_id: str,
        operation: str,
        rule_id: str,
        timestamp: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
    ) -> AuditEvent:
        if any(event.event_id == event_id for event in self._events):
            _reject("P8-005_DUPLICATE_EVENT_ID", "event_id already exists")
        if (
            not _valid_identifier(event_id)
            or operation not in _OPERATIONS
            or not _valid_identifier(rule_id)
            or not _validate_timestamp(timestamp)
        ):
            _reject("P8-004_EVENT_METADATA_INVALID", "invalid audit event metadata")

        before_json = _canonical_json(before)
        after_json = _canonical_json(after)
        before_snapshot = json.loads(before_json)
        after_snapshot = json.loads(after_json)
        claim_id = before_snapshot.get("claim_id")
        if (
            not _valid_identifier(claim_id)
            or after_snapshot.get("claim_id") != claim_id
        ):
            _reject(
                "P8-002_CLAIM_DECISION_MISMATCH",
                "before/after claim identifiers must match",
            )

        sequence = len(self._events) + 1
        previous_hash = self._events[-1].event_hash if self._events else _GENESIS_HASH
        event_without_hash = AuditEvent(
            sequence=sequence,
            event_id=event_id,
            claim_id=claim_id,
            operation=operation,
            rule_id=rule_id,
            timestamp=timestamp,
            previous_hash=previous_hash,
            before_json=before_json,
            after_json=after_json,
            event_hash="",
        )
        event = AuditEvent(
            sequence=sequence,
            event_id=event_id,
            claim_id=claim_id,
            operation=operation,
            rule_id=rule_id,
            timestamp=timestamp,
            previous_hash=previous_hash,
            before_json=before_json,
            after_json=after_json,
            event_hash=event_without_hash.recompute_hash(),
        )
        self._events = (*self._events, event)
        return event

    def verify_integrity(self) -> bool:
        previous_hash = _GENESIS_HASH
        seen_event_ids: set[str] = set()
        for expected_sequence, event in enumerate(self._events, start=1):
            if (
                event.sequence != expected_sequence
                or event.event_id in seen_event_ids
                or event.previous_hash != previous_hash
                or event.operation not in _OPERATIONS
                or event.event_hash != event.recompute_hash()
                or event.before.get("claim_id") != event.claim_id
                or event.after.get("claim_id") != event.claim_id
            ):
                return False
            seen_event_ids.add(event.event_id)
            previous_hash = event.event_hash
        return True


@dataclass(frozen=True)
class LifecycleTransition:
    operation: str
    claim_json: str
    audit_event: AuditEvent
    recertification_required: bool

    @property
    def claim(self) -> dict[str, object]:
        return json.loads(self.claim_json)

    def to_outcome_fields(self) -> dict[str, object]:
        """Return P8-owned fields without certificate, system state, or STOP."""

        return {
            "operation": self.operation,
            "claim": self.claim,
            "audit_event": self.audit_event.to_dict(),
            "recertification_required": self.recertification_required,
        }


class ClaimLifecycleManager:
    """Apply P8 lifecycle transitions and append one audit event atomically."""

    def __init__(
        self,
        *,
        ledger: AppendOnlyAuditLedger,
        promotion_policy: Mapping[str, object],
        promotion_policy_hash: str,
    ) -> None:
        if not isinstance(ledger, AppendOnlyAuditLedger):
            raise ValueError("ledger must be an AppendOnlyAuditLedger")
        if not isinstance(promotion_policy, Mapping):
            raise ValueError("promotion_policy must be an object")
        version = promotion_policy.get("version")
        rules = promotion_policy.get("rules")
        if not _valid_identifier(version) or not _unique_nonempty_strings(
            rules, require_nonempty=False
        ):
            raise ValueError("promotion_policy must contain version and unique rules")
        if (
            not isinstance(promotion_policy_hash, str)
            or _SHA256.fullmatch(promotion_policy_hash) is None
        ):
            raise ValueError("promotion_policy_hash must be a canonical SHA-256")
        self._ledger = ledger
        self._promotion_policy_version = version
        self._promotion_rules = frozenset(rules)
        self._promotion_policy_hash = promotion_policy_hash

    @property
    def ledger(self) -> AppendOnlyAuditLedger:
        return self._ledger

    @property
    def promotion_policy_version(self) -> str:
        return self._promotion_policy_version

    def admit(
        self,
        candidate_claim: Mapping[str, object],
        firewall_decision: AdmissionDecision,
        *,
        event_id: str,
        rule_id: str,
        timestamp: str,
    ) -> LifecycleTransition:
        before = self._claim_snapshot(candidate_claim)
        if not isinstance(firewall_decision, AdmissionDecision):
            _reject(
                "P8-002_CLAIM_DECISION_MISMATCH",
                "admission requires a P7 AdmissionDecision",
            )
        if firewall_decision.allowed is not True:
            _reject("P8-001_FIREWALL_DENIED", "P7 Firewall denied admission")
        if (
            firewall_decision.claim_id != before.get("claim_id")
            or firewall_decision.reason_codes != ("FW-000_ADMITTED",)
            or firewall_decision.resulting_admission_status != "admitted"
            or firewall_decision.preserved_modality != before.get("modality")
        ):
            _reject(
                "P8-002_CLAIM_DECISION_MISMATCH",
                "Firewall decision does not bind this claim",
            )
        if (
            before.get("admission_status") != "candidate"
            or before.get("lifecycle_state") not in {"generated", "bound"}
            or before.get("promotion_status") != "none"
            or before.get("promotion_event_id") is not None
        ):
            _reject(
                "P8-003_INVALID_ADMISSION_STATE",
                "claim is not an unpromoted candidate",
            )

        after = self._claim_snapshot(before)
        after["admission_status"] = "admitted"
        after["lifecycle_state"] = "admitted"
        return self._commit(
            operation="ADMIT",
            before=before,
            after=after,
            event_id=event_id,
            rule_id=rule_id,
            timestamp=timestamp,
            recertification_required=False,
        )

    def promote(
        self,
        admitted_claim: Mapping[str, object],
        *,
        event_id: str,
        rule_id: str,
        timestamp: str,
        target_levels: Sequence[str],
        requested_modality: str | None = None,
    ) -> LifecycleTransition:
        before = self._claim_snapshot(admitted_claim)
        if (
            before.get("admission_status") != "admitted"
            or before.get("lifecycle_state") != "admitted"
            or before.get("promotion_status") not in {"none", "eligible"}
            or before.get("promotion_event_id") is not None
        ):
            _reject(
                "P8-007_PROMOTION_STATE_INVALID",
                "only an admitted, not-yet-promoted claim may be promoted",
            )
        if _contains_oracle_field(before):
            _reject(
                "P8-012_ORACLE_OR_HIDDEN_FIELD",
                "oracle or hidden fields cannot enter promotion",
            )
        modality = before.get("modality")
        if requested_modality is not None and requested_modality != modality:
            _reject(
                "P8-008_MODALITY_CHANGE_FORBIDDEN",
                "Promote must preserve modality",
            )
        if rule_id not in self._promotion_rules:
            _reject(
                "P8-006_PROMOTION_RULE_NOT_REGISTERED",
                "promotion rule is not frozen in the policy",
            )
        if not _promotion_pointer_is_resolvable(before.get("pointer")):
            _reject(
                "P8-009_PROMOTION_POINTER_UNRESOLVABLE",
                "promoted claims require a resolvable pointer",
            )
        if not _unique_nonempty_strings(target_levels, require_nonempty=True):
            _reject(
                "P8-010_PROMOTION_LEVEL_INVALID",
                "promotion target levels must be unique and non-empty",
            )
        admissible_levels = before.get("admissible_levels")
        if not _unique_nonempty_strings(admissible_levels, require_nonempty=True):
            _reject(
                "P8-010_PROMOTION_LEVEL_INVALID",
                "claim has no admissible promotion levels",
            )
        target_level_set = set(target_levels)
        if not target_level_set.issubset(admissible_levels):
            _reject(
                "P8-010_PROMOTION_LEVEL_INVALID",
                "promotion exceeds claim admissible levels",
            )

        authority = before.get("certification_authority")
        existing_levels: tuple[str, ...] = ()
        if isinstance(authority, Mapping) and authority.get("allowed") is True:
            levels = authority.get("levels")
            if not _unique_nonempty_strings(levels, require_nonempty=True):
                _reject(
                    "P8-011_CERTIFICATION_AUTHORITY_INVALID",
                    "existing authority is malformed",
                )
            existing_levels = tuple(levels)
        promoted_levels = tuple(
            sorted(set(existing_levels).union(target_level_set))
        )
        if not set(promoted_levels).issubset(admissible_levels):
            _reject(
                "P8-010_PROMOTION_LEVEL_INVALID",
                "combined authority exceeds claim admissible levels",
            )

        after = self._claim_snapshot(before)
        after["epistemic_role"] = "case_evidence"
        after["certification_authority"] = {
            "allowed": True,
            "levels": list(promoted_levels),
            "basis_rule_id": rule_id,
            "policy_hash": self._promotion_policy_hash,
        }
        after["promotion_status"] = "promoted"
        after["promotion_event_id"] = event_id
        after["lifecycle_state"] = "promoted"
        rule_trace = after.get("rule_trace")
        if not isinstance(rule_trace, list):
            _reject("P8-013_CLAIM_NOT_CANONICAL_JSON", "rule_trace must be a list")
        if rule_id not in rule_trace:
            rule_trace.append(rule_id)
        if after.get("modality") != modality:
            _reject(
                "P8-008_MODALITY_CHANGE_FORBIDDEN",
                "internal promotion changed modality",
            )
        return self._commit(
            operation="PROMOTE",
            before=before,
            after=after,
            event_id=event_id,
            rule_id=rule_id,
            timestamp=timestamp,
            recertification_required=False,
        )

    def revoke(
        self,
        active_claim: Mapping[str, object],
        *,
        event_id: str,
        rule_id: str,
        timestamp: str,
    ) -> LifecycleTransition:
        before = self._claim_snapshot(active_claim)
        if (
            before.get("admission_status") != "admitted"
            or before.get("lifecycle_state") not in {"admitted", "promoted"}
            or before.get("promotion_status") not in {"none", "eligible", "promoted"}
        ):
            _reject(
                "P8-014_REVOCATION_STATE_INVALID",
                "only an active admitted or promoted claim may be revoked",
            )
        modality = before.get("modality")
        after = self._claim_snapshot(before)
        after["admission_status"] = "rejected"
        after["promotion_status"] = "revoked"
        after["lifecycle_state"] = "revoked"
        after["certification_authority"] = {
            "allowed": False,
            "levels": [],
            "basis_rule_id": None,
            "policy_hash": None,
        }
        rule_trace = after.get("rule_trace")
        if not isinstance(rule_trace, list):
            _reject("P8-013_CLAIM_NOT_CANONICAL_JSON", "rule_trace must be a list")
        if rule_id not in rule_trace:
            rule_trace.append(rule_id)
        if after.get("modality") != modality:
            _reject(
                "P8-008_MODALITY_CHANGE_FORBIDDEN",
                "internal revocation changed modality",
            )
        return self._commit(
            operation="REVOKE",
            before=before,
            after=after,
            event_id=event_id,
            rule_id=rule_id,
            timestamp=timestamp,
            recertification_required=True,
        )

    @staticmethod
    def _claim_snapshot(claim: object) -> dict[str, object]:
        if not isinstance(claim, Mapping):
            _reject("P8-013_CLAIM_NOT_CANONICAL_JSON", "claim must be an object")
        snapshot = _json_copy(claim)
        if not isinstance(snapshot, dict) or not _valid_identifier(
            snapshot.get("claim_id")
        ):
            _reject(
                "P8-013_CLAIM_NOT_CANONICAL_JSON",
                "claim_id must be a non-empty string",
            )
        return snapshot

    def _commit(
        self,
        *,
        operation: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
        event_id: str,
        rule_id: str,
        timestamp: str,
        recertification_required: bool,
    ) -> LifecycleTransition:
        event = self._ledger.append_transition(
            event_id=event_id,
            operation=operation,
            rule_id=rule_id,
            timestamp=timestamp,
            before=before,
            after=after,
        )
        return LifecycleTransition(
            operation=operation,
            claim_json=_canonical_json(after),
            audit_event=event,
            recertification_required=recertification_required,
        )
