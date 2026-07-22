"""P7 No-Evidence-Laundering admission Firewall for ``E_case``.

The Firewall evaluates a fully bound candidate claim together with its P5
observation context. It returns an immutable allow/deny decision and never
mutates the claim, changes modality, writes admission state, promotes
authority, issues a certificate, or emits a system state/STOP decision.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re

from .policy import AdmissionPolicyAuthority


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)
@dataclass(frozen=True)
class AdmissionDecision:
    claim_id: str
    allowed: bool
    reason_codes: tuple[str, ...]
    resulting_admission_status: str
    preserved_modality: str | None
    policy_hash: str | None
    approval_manifest_hash: str | None

    def to_outcome_fields(self) -> dict[str, object]:
        """Return Firewall-owned decision fields without certificate or STOP."""

        return {
            "claim_id": self.claim_id,
            "allowed": self.allowed,
            "reason_codes": list(self.reason_codes),
            "resulting_admission_status": self.resulting_admission_status,
            "preserved_modality": self.preserved_modality,
            "policy_hash": self.policy_hash,
            "approval_manifest_hash": self.approval_manifest_hash,
        }


class ECaseAdmissionFirewall:
    """Fail-closed admission gate for observation-bound case evidence."""

    def __init__(
        self,
        policy_authority: AdmissionPolicyAuthority | None = None,
    ) -> None:
        if policy_authority is not None and not isinstance(
            policy_authority, AdmissionPolicyAuthority
        ):
            raise ValueError("policy_authority must be AdmissionPolicyAuthority")
        self._policy_authority = policy_authority

    def evaluate(
        self,
        candidate_claim: Mapping[str, object],
        observation: Mapping[str, object] | None,
    ) -> AdmissionDecision:
        if not isinstance(candidate_claim, Mapping):
            raise ValueError("candidate_claim must be an object")
        claim = candidate_claim
        claim_id = self._string_or_placeholder(claim.get("claim_id"), "<unknown>")
        modality = claim.get("modality")
        preserved_modality = modality if isinstance(modality, str) else None
        reasons: list[str] = []

        if self._contains_oracle_field(claim):
            reasons.append("FW-001_ORACLE_OR_HIDDEN_FIELD")
        if modality != "observed":
            reasons.append("FW-002_MODALITY_NOT_OBSERVED")
        if claim.get("truth_status") != "supported":
            reasons.append("FW-003_TRUTH_STATUS_NOT_SUPPORTED")
        if claim.get("epistemic_role") != "case_evidence":
            reasons.append("FW-004_ROLE_NOT_CASE_EVIDENCE")
        authority_shape_valid = self._authority_shape_is_valid(claim)
        if not authority_shape_valid:
            reasons.append("FW-005_CERTIFICATION_AUTHORITY_INVALID")
        if self._policy_authority is None:
            reasons.append("FW-018_POLICY_AUTHORITY_UNVERIFIED")
        elif authority_shape_valid and not self._authority_matches_policy(claim):
            reasons.append("FW-019_POLICY_BINDING_MISMATCH")

        pointer = claim.get("pointer")
        pointer_complete = self._pointer_is_complete(pointer)
        if not pointer_complete:
            reasons.append("FW-006_POINTER_INCOMPLETE")

        if claim.get("binding_status") != "bound":
            reasons.append("FW-008_BINDING_NOT_BOUND")
        if (
            claim.get("promotion_status") != "none"
            or claim.get("promotion_event_id") is not None
        ):
            reasons.append("FW-009_PROMOTION_OUT_OF_SCOPE")
        if (
            claim.get("admission_status") != "candidate"
            or claim.get("lifecycle_state") not in {"generated", "bound"}
        ):
            reasons.append("FW-013_NON_CANDIDATE_STATE")

        if observation is None:
            reasons.append("FW-016_OBSERVATION_CONTEXT_REQUIRED")
        elif not isinstance(observation, Mapping):
            raise ValueError("observation must be an object or None")
        else:
            observation_id = observation.get("observation_id")
            if (
                pointer_complete
                and isinstance(pointer, Mapping)
                and pointer.get("record_id") != observation_id
            ):
                reasons.append("FW-007_POINTER_OBSERVATION_MISMATCH")

            observation_kind = observation.get("observation_kind")
            if observation_kind == "heuristic_only":
                reasons.append("FW-010_HEURISTIC_OBSERVATION")
            elif observation_kind == "true_empty_control":
                reasons.append("FW-011_CONTROL_OBSERVATION")
            elif (
                self._policy_authority is None
                or observation_kind
                not in self._policy_authority.admissible_observation_kinds
            ):
                reasons.append("FW-017_OBSERVATION_KIND_UNSUPPORTED")

            if observation.get("completeness_conditions_satisfied") is not True:
                reasons.append("FW-012_COMPLETENESS_NOT_SATISFIED")
            if observation.get("used_for_world_elimination") is not True:
                reasons.append("FW-014_OBSERVATION_NOT_ELIMINATION_ELIGIBLE")

            claim_object = claim.get("object")
            claim_literal = (
                claim_object.get("literal")
                if isinstance(claim_object, Mapping)
                else None
            )
            if claim_literal != observation.get("observed_value"):
                reasons.append("FW-015_OBSERVATION_VALUE_MISMATCH")

        allowed = not reasons
        return AdmissionDecision(
            claim_id=claim_id,
            allowed=allowed,
            reason_codes=("FW-000_ADMITTED",) if allowed else tuple(reasons),
            resulting_admission_status="admitted" if allowed else "rejected",
            preserved_modality=preserved_modality,
            policy_hash=(
                self._policy_authority.policy_hash
                if self._policy_authority is not None
                else None
            ),
            approval_manifest_hash=(
                self._policy_authority.approval_manifest_hash
                if self._policy_authority is not None
                else None
            ),
        )

    @staticmethod
    def _authority_shape_is_valid(claim: Mapping[str, object]) -> bool:
        authority = claim.get("certification_authority")
        if not isinstance(authority, Mapping) or authority.get("allowed") is not True:
            return False
        levels = authority.get("levels")
        if not ECaseAdmissionFirewall._unique_nonempty_strings(levels, nonempty=True):
            return False
        if not isinstance(authority.get("basis_rule_id"), str) or not authority.get(
            "basis_rule_id"
        ):
            return False
        policy_hash = authority.get("policy_hash")
        if not isinstance(policy_hash, str) or _SHA256.fullmatch(policy_hash) is None:
            return False
        admissible_levels = claim.get("admissible_levels")
        if not ECaseAdmissionFirewall._unique_nonempty_strings(
            admissible_levels, nonempty=True
        ):
            return False
        return set(levels).issubset(admissible_levels)

    def _authority_matches_policy(self, claim: Mapping[str, object]) -> bool:
        if self._policy_authority is None:
            return False
        authority = claim.get("certification_authority")
        if not isinstance(authority, Mapping):
            return False
        rule_id = authority.get("basis_rule_id")
        source_family = claim.get("source_family")
        levels = authority.get("levels")
        if (
            authority.get("policy_hash") != self._policy_authority.policy_hash
            or not isinstance(rule_id, str)
            or not isinstance(source_family, str)
            or not isinstance(levels, Sequence)
            or isinstance(levels, (str, bytes))
        ):
            return False
        return self._policy_authority.authorizes(
            rule_id=rule_id,
            source_family=source_family,
            levels=levels,
        )

    @staticmethod
    def _pointer_is_complete(pointer: object) -> bool:
        if not isinstance(pointer, Mapping):
            return False
        if not isinstance(pointer.get("source_id"), str) or not pointer.get(
            "source_id"
        ):
            return False
        if not isinstance(pointer.get("record_id"), str) or not pointer.get(
            "record_id"
        ):
            return False
        content_hash = pointer.get("content_hash")
        if not isinstance(content_hash, str) or _SHA256.fullmatch(content_hash) is None:
            return False
        row_range = pointer.get("byte_or_row_range")
        if (
            not isinstance(row_range, Sequence)
            or isinstance(row_range, (str, bytes))
            or len(row_range) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) for value in row_range)
            or any(value < 0 for value in row_range)
            or row_range[0] > row_range[1]
        ):
            return False
        return True

    @staticmethod
    def _unique_nonempty_strings(value: object, *, nonempty: bool) -> bool:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return False
        frozen = tuple(value)
        if nonempty and not frozen:
            return False
        return (
            all(isinstance(item, str) and bool(item) for item in frozen)
            and len(set(frozen)) == len(frozen)
        )

    @classmethod
    def _contains_oracle_field(cls, value: object) -> bool:
        if isinstance(value, Mapping):
            return any(
                key in _ORACLE_FIELDS or cls._contains_oracle_field(nested)
                for key, nested in value.items()
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return any(cls._contains_oracle_field(item) for item in value)
        return False

    @staticmethod
    def _string_or_placeholder(value: object, placeholder: str) -> str:
        return value if isinstance(value, str) and value else placeholder
