"""Verified admission-policy authority for the Kernel v0.8 Firewall.

Policy semantics and human approval are deliberately separate artifacts.  A
policy becomes runtime authority only when both canonical hashes replay, the
approval manifest says APPROVED, and the active Gamma reference binds the
same artifact, approval manifest, and rule subset.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

from src.ir.canonical_hash import SHA256_PATTERN, has_valid_document_hash


_ORACLE_FIELDS = frozenset(
    {
        "ground_truth",
        "recoverable_claim_ids",
        "oracle_effects",
        "hidden_claim_ids",
        "true_outcome",
    }
)


class AdmissionPolicyRejected(ValueError):
    """Fail-closed policy verification error with a stable reason code."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code


def _reject(reason_code: str, message: str) -> None:
    raise AdmissionPolicyRejected(reason_code, message)


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _reject("AP-006_ARTIFACT_INVALID", f"{field} must be an object")
    return value


def _identifier(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        _reject("AP-006_ARTIFACT_INVALID", f"{field} must be non-empty")
    return value


def _string_tuple(
    value: object,
    field: str,
    *,
    nonempty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _reject("AP-006_ARTIFACT_INVALID", f"{field} must be a string sequence")
    frozen = tuple(value)
    if nonempty and not frozen:
        _reject("AP-006_ARTIFACT_INVALID", f"{field} must not be empty")
    if (
        any(not isinstance(item, str) or not item for item in frozen)
        or len(set(frozen)) != len(frozen)
    ):
        _reject(
            "AP-006_ARTIFACT_INVALID",
            f"{field} must contain unique non-empty strings",
        )
    return frozen


def _contains_oracle_field(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _ORACLE_FIELDS or _contains_oracle_field(nested)
            for key, nested in value.items()
        )
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_oracle_field(item) for item in value)
    return False


@dataclass(frozen=True)
class AdmissionRule:
    rule_id: str
    source_families: frozenset[str]
    admissible_levels: frozenset[str]


@dataclass(frozen=True)
class AdmissionPolicyAuthority:
    """Content-verified, human-approved, Gamma-bound admission authority."""

    policy_id: str
    policy_version: str
    policy_hash: str
    approval_manifest_id: str
    approval_manifest_hash: str
    active_rule_ids: frozenset[str]
    admissible_observation_kinds: frozenset[str]
    rules: Mapping[str, AdmissionRule]

    @classmethod
    def from_documents(
        cls,
        policy_document: Mapping[str, object],
        approval_manifest: Mapping[str, object],
        gamma_reference: Mapping[str, object],
    ) -> "AdmissionPolicyAuthority":
        policy = _mapping(policy_document, "policy_document")
        manifest = _mapping(approval_manifest, "approval_manifest")
        gamma_ref = _mapping(gamma_reference, "gamma_reference")
        if _contains_oracle_field(policy) or _contains_oracle_field(manifest):
            _reject("AP-007_ORACLE_FIELD_FORBIDDEN", "policy authority is non-oracle")

        if not has_valid_document_hash(policy):
            _reject("AP-001_POLICY_HASH_MISMATCH", "policy hash does not replay")
        if not has_valid_document_hash(manifest):
            _reject(
                "AP-002_APPROVAL_HASH_MISMATCH",
                "approval-manifest hash does not replay",
            )
        if policy.get("schema_version") != "0.8.0":
            _reject("AP-006_ARTIFACT_INVALID", "policy schema_version must be 0.8.0")
        if manifest.get("schema_version") != "0.8.0":
            _reject(
                "AP-006_ARTIFACT_INVALID",
                "approval schema_version must be 0.8.0",
            )
        if policy.get("default_decision") != "deny":
            _reject("AP-006_ARTIFACT_INVALID", "policy must default deny")
        if manifest.get("decision") != "APPROVED":
            _reject("AP-003_POLICY_NOT_APPROVED", "policy approval is not APPROVED")

        policy_id = _identifier(policy.get("policy_id"), "policy_id")
        policy_version = _identifier(policy.get("policy_version"), "policy_version")
        policy_hash = _identifier(policy.get("hash"), "policy.hash")
        manifest_id = _identifier(manifest.get("manifest_id"), "manifest_id")
        manifest_hash = _identifier(manifest.get("hash"), "manifest.hash")
        if any(
            SHA256_PATTERN.fullmatch(value) is None
            for value in (policy_hash, manifest_hash)
        ):
            _reject("AP-006_ARTIFACT_INVALID", "authority hashes are malformed")
        if (
            manifest.get("policy_id") != policy_id
            or manifest.get("policy_version") != policy_version
            or manifest.get("policy_hash") != policy_hash
        ):
            _reject(
                "AP-004_APPROVAL_POLICY_MISMATCH",
                "approval manifest does not bind the policy",
            )
        for field in ("approved_by", "approved_at", "authority_source"):
            _identifier(manifest.get(field), f"approval_manifest.{field}")

        requirements = _mapping(
            policy.get("admission_requirements"), "admission_requirements"
        )
        required_constants = {
            "modality": "observed",
            "truth_status": "supported",
            "epistemic_role": "case_evidence",
            "binding_status": "bound",
            "admission_status": "candidate",
            "promotion_status": "none",
            "lifecycle_states": ["bound", "generated"],
            "authority_allowed": True,
            "pointer_complete": True,
            "pointer_matches_observation": True,
            "literal_matches_observation": True,
            "completeness_conditions_satisfied": True,
            "used_for_world_elimination": True,
            "oracle_hidden_fields_forbidden": True,
        }
        for field, expected in required_constants.items():
            if requirements.get(field) != expected:
                _reject(
                    "AP-006_ARTIFACT_INVALID",
                    f"admission_requirements.{field} violates v0.8",
                )
        observation_kinds = frozenset(
            _string_tuple(
                requirements.get("observation_kinds"),
                "admission_requirements.observation_kinds",
            )
        )
        if observation_kinds != frozenset(
            {"distinguishing_hit", "bounded_complete_zero_hit"}
        ):
            _reject(
                "AP-006_ARTIFACT_INVALID",
                "admission observation kinds must match deterministic v0.8",
            )

        raw_rules = policy.get("rules")
        if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, (str, bytes)):
            _reject("AP-006_ARTIFACT_INVALID", "rules must be a sequence")
        rules: dict[str, AdmissionRule] = {}
        for index, raw_rule in enumerate(raw_rules):
            rule = _mapping(raw_rule, f"rules[{index}]")
            rule_id = _identifier(rule.get("rule_id"), f"rules[{index}].rule_id")
            if rule_id in rules:
                _reject("AP-006_ARTIFACT_INVALID", f"duplicate rule {rule_id}")
            if rule.get("decision") != "allow_when_all_requirements_hold":
                _reject("AP-006_ARTIFACT_INVALID", f"rule {rule_id} has invalid effect")
            rules[rule_id] = AdmissionRule(
                rule_id=rule_id,
                source_families=frozenset(
                    _string_tuple(
                        rule.get("source_families"),
                        f"rules[{index}].source_families",
                    )
                ),
                admissible_levels=frozenset(
                    _string_tuple(
                        rule.get("admissible_levels"),
                        f"rules[{index}].admissible_levels",
                    )
                ),
            )

        gamma_policy_id = gamma_ref.get("policy_id")
        gamma_version = gamma_ref.get("version")
        gamma_policy_hash = gamma_ref.get("policy_hash")
        gamma_manifest_id = gamma_ref.get("approval_manifest_id")
        gamma_manifest_hash = gamma_ref.get("approval_manifest_hash")
        if (
            gamma_policy_id != policy_id
            or gamma_version != policy_version
            or gamma_policy_hash != policy_hash
            or gamma_manifest_id != manifest_id
            or gamma_manifest_hash != manifest_hash
        ):
            _reject("AP-005_GAMMA_BINDING_MISMATCH", "Gamma policy binding differs")
        active_rules = frozenset(
            _string_tuple(gamma_ref.get("rules"), "gamma_reference.rules")
        )
        if not active_rules.issubset(rules):
            _reject("AP-005_GAMMA_BINDING_MISMATCH", "Gamma activates unknown rules")

        return cls(
            policy_id=policy_id,
            policy_version=policy_version,
            policy_hash=policy_hash,
            approval_manifest_id=manifest_id,
            approval_manifest_hash=manifest_hash,
            active_rule_ids=active_rules,
            admissible_observation_kinds=observation_kinds,
            rules=MappingProxyType(rules),
        )

    def authorizes(
        self,
        *,
        rule_id: str,
        source_family: str,
        levels: Sequence[str],
    ) -> bool:
        """Return whether an active rule covers the source and every level."""

        rule = self.rules.get(rule_id)
        return (
            rule_id in self.active_rule_ids
            and rule is not None
            and source_family in rule.source_families
            and bool(levels)
            and set(levels).issubset(rule.admissible_levels)
        )
