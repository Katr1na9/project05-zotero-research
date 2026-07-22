"""P9 level-complete certificate issuance owned by the Kernel Checker.

The issuer is intentionally stricter than the generic P0 certificate schema:
this P9 slice signs only exhaustive finite-domain coverage. A candidate-only
Checker result is necessary but never sufficient. This module emits no system
state; CERTIFIED_STOP authority remains in the separate P9 state derivation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
import json
import re

from .finite_domain import CheckerRun, CheckerStatus, QueryStatus
from src.firewall.policy import AdmissionPolicyAuthority


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_RFC3339_UTC = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]+)?Z$"
)
_PROOF_LEVELS = frozenset(
    {"reproducible_run", "solver_proof", "independently_checked"}
)
_SOLVERS = frozenset({"finite_domain_enumerator", "small_csp"})
_CERTIFICATE_FIELDS = frozenset(
    {
        "schema_version",
        "certificate_id",
        "case_id",
        "issued_by",
        "gamma_hash",
        "evidence_hash",
        "admission_policy_hash",
        "admission_policy_approval_hash",
        "formal_ceiling_hash",
        "level",
        "conclusion",
        "certification_scope",
        "candidate_coverage",
        "core_query_results",
        "level_certification",
        "positive_witness",
        "proof_artifact",
        "critical_scope_assumptions",
        "promotion_dependencies",
        "created_at",
        "status",
    }
)
_COVERAGE_FIELDS = frozenset(
    {
        "level",
        "mode",
        "declared_domain_size",
        "checked_count",
        "result_candidates",
        "legal_world_count",
        "legal_worlds_hash",
        "cartesian_assignment_bound",
        "omitted_known_candidates",
        "solver_seed_used",
    }
)
_LEVEL_PROOF_FIELDS = frozenset(
    {
        "all_legal_results_covered",
        "exactly_one_feasible_result",
        "all_critical_queries_known",
    }
)
_PROOF_ARTIFACT_FIELDS = frozenset(
    {"proof_level", "solver", "solver_version", "query_hashes", "artifact_uri"}
)


class LevelCertificateRejected(ValueError):
    """Fail-closed issuance rejection with a stable machine reason code."""

    def __init__(self, reason_code: str, message: str):
        super().__init__(f"{reason_code}: {message}")
        self.reason_code = reason_code


def _reject(reason_code: str, message: str) -> None:
    raise LevelCertificateRejected(reason_code, message)


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
        _reject("P9-CERT-006_INVALID_METADATA", str(exc))
    raise AssertionError("unreachable")


def _identifier(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _canonical_hash(value: object, *, reject_placeholder: bool) -> bool:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        return False
    digest = value.removeprefix("sha256:")
    return not reject_placeholder or len(set(digest)) > 1


def _valid_hash_sequence(
    value: object,
    *,
    reject_placeholder: bool,
    require_nonempty: bool,
) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    items = tuple(value)
    return (
        (bool(items) or not require_nonempty)
        and all(
            _canonical_hash(item, reject_placeholder=reject_placeholder)
            for item in items
        )
        and len(set(items)) == len(items)
    )


def _utc_timestamp(value: object) -> bool:
    if not isinstance(value, str) or _RFC3339_UTC.fullmatch(value) is None:
        return False
    try:
        datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return True


def _string_tuple(
    value: object,
    *,
    field: str,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        _reject("P9-CERT-006_INVALID_METADATA", f"{field} must be a sequence")
    items = tuple(value)
    if require_nonempty and not items:
        _reject("P9-CERT-006_INVALID_METADATA", f"{field} must not be empty")
    if (
        not all(isinstance(item, str) and bool(item) for item in items)
        or len(set(items)) != len(items)
    ):
        _reject(
            "P9-CERT-006_INVALID_METADATA",
            f"{field} must contain unique non-empty strings",
        )
    return items


def _required_mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _reject("P9-CERT-006_INVALID_METADATA", f"{field} must be an object")
    return value


@dataclass(frozen=True)
class IssuedLevelCertificate:
    """Immutable canonical level-complete certificate document."""

    certificate_json: str

    def to_dict(self) -> dict[str, object]:
        return json.loads(self.certificate_json)

    @property
    def certificate_id(self) -> str:
        return self.to_dict()["certificate_id"]

    def binds_checker_run(self, checker_run: CheckerRun) -> bool:
        if not isinstance(checker_run, CheckerRun):
            return False
        try:
            document = self.to_dict()
        except (json.JSONDecodeError, TypeError):
            return False
        if not isinstance(document, dict) or set(document) != _CERTIFICATE_FIELDS:
            return False
        core = document.get("core_query_results")
        level_proof = document.get("level_certification")
        coverage = document.get("candidate_coverage")
        conclusion = document.get("conclusion")
        proof_artifact = document.get("proof_artifact")
        if not all(
            isinstance(value, Mapping)
            for value in (
                core,
                level_proof,
                coverage,
                conclusion,
                proof_artifact,
            )
        ):
            return False
        declared = coverage.get("declared_domain_size")
        query_hashes = proof_artifact.get("query_hashes")
        positive_witness = document.get("positive_witness")
        assumptions = document.get("critical_scope_assumptions")
        promotions = document.get("promotion_dependencies")
        support_witness = checker_run.support.witness
        return (
            document.get("schema_version") == "0.8.0"
            and _identifier(document.get("certificate_id"))
            and _identifier(document.get("case_id"))
            and _canonical_hash(document.get("gamma_hash"), reject_placeholder=True)
            and _canonical_hash(
                document.get("evidence_hash"), reject_placeholder=True
            )
            and _canonical_hash(
                document.get("admission_policy_hash"), reject_placeholder=True
            )
            and _canonical_hash(
                document.get("admission_policy_approval_hash"),
                reject_placeholder=True,
            )
            and _canonical_hash(
                document.get("formal_ceiling_hash"), reject_placeholder=True
            )
            and _identifier(document.get("level"))
            and set(conclusion) == {"entity_id", "entity_type"}
            and _identifier(conclusion.get("entity_id"))
            and _identifier(conclusion.get("entity_type"))
            and checker_run.checker_status is CheckerStatus.CANDIDATE_CERTIFIED
            and checker_run.base.status is QueryStatus.SAT
            and checker_run.support.status is QueryStatus.SAT
            and checker_run.alternative.status is QueryStatus.UNSAT
            and core
            == {"base": "SAT", "support": "SAT", "alternative": "UNSAT"}
            and document.get("issued_by") == "kernel_checker"
            and document.get("certification_scope") == "level_complete"
            and document.get("status") == "valid"
            and coverage.get("mode") == "exhaustive"
            and set(coverage) == _COVERAGE_FIELDS
            and coverage.get("level") == document.get("level")
            and isinstance(declared, int)
            and not isinstance(declared, bool)
            and declared > 0
            and coverage.get("checked_count") == coverage.get("declared_domain_size")
            and self._valid_string_list(
                coverage.get("result_candidates"), require_nonempty=True
            )
            and len(coverage.get("result_candidates")) == declared
            and isinstance(coverage.get("legal_world_count"), int)
            and not isinstance(coverage.get("legal_world_count"), bool)
            and coverage.get("legal_world_count") > 0
            and _canonical_hash(
                coverage.get("legal_worlds_hash"), reject_placeholder=True
            )
            and isinstance(coverage.get("cartesian_assignment_bound"), int)
            and not isinstance(coverage.get("cartesian_assignment_bound"), bool)
            and coverage.get("cartesian_assignment_bound") > 0
            and checker_run.alternative.assignments_examined
            == coverage.get("cartesian_assignment_bound")
            and coverage.get("omitted_known_candidates") == []
            and isinstance(coverage.get("solver_seed_used"), bool)
            and all(
                level_proof.get(field) is True
                for field in (
                    "all_legal_results_covered",
                    "exactly_one_feasible_result",
                    "all_critical_queries_known",
                )
            )
            and set(level_proof) == _LEVEL_PROOF_FIELDS
            and set(proof_artifact) == _PROOF_ARTIFACT_FIELDS
            and proof_artifact.get("proof_level") in _PROOF_LEVELS
            and proof_artifact.get("solver") in _SOLVERS
            and _identifier(proof_artifact.get("solver_version"))
            and _valid_hash_sequence(
                query_hashes,
                reject_placeholder=True,
                require_nonempty=True,
            )
            and (
                proof_artifact.get("artifact_uri") is None
                or _identifier(proof_artifact.get("artifact_uri"))
            )
            and self._valid_string_list(positive_witness, require_nonempty=True)
            and self._valid_string_list(assumptions, require_nonempty=False)
            and self._valid_string_list(promotions, require_nonempty=False)
            and _utc_timestamp(document.get("created_at"))
            and isinstance(support_witness, Mapping)
            and support_witness.get(document.get("level"))
            == conclusion.get("entity_id")
        )

    def binds_artifacts(
        self,
        gamma_hash: object,
        evidence_hash: object,
        admission_policy_hash: object,
        admission_policy_approval_hash: object,
        formal_ceiling_hash: object,
    ) -> bool:
        try:
            document = self.to_dict()
        except (json.JSONDecodeError, TypeError):
            return False
        return (
            isinstance(document, dict)
            and _canonical_hash(gamma_hash, reject_placeholder=True)
            and _canonical_hash(evidence_hash, reject_placeholder=True)
            and _canonical_hash(admission_policy_hash, reject_placeholder=True)
            and _canonical_hash(
                admission_policy_approval_hash, reject_placeholder=True
            )
            and _canonical_hash(formal_ceiling_hash, reject_placeholder=True)
            and document.get("gamma_hash") == gamma_hash
            and document.get("evidence_hash") == evidence_hash
            and document.get("admission_policy_hash")
            == admission_policy_hash
            and document.get("admission_policy_approval_hash")
            == admission_policy_approval_hash
            and document.get("formal_ceiling_hash") == formal_ceiling_hash
        )

    @staticmethod
    def _valid_string_list(value: object, *, require_nonempty: bool) -> bool:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return False
        items = tuple(value)
        return (
            (bool(items) or not require_nonempty)
            and all(isinstance(item, str) and bool(item) for item in items)
            and len(set(items)) == len(items)
        )


class LevelCertificateIssuer:
    """Issue level-complete certificates only from exhaustive Checker proof."""

    def issue(
        self,
        checker_run: CheckerRun,
        *,
        certificate_id: str,
        case_id: str,
        gamma_hash: str,
        evidence_hash: str,
        level: str,
        conclusion: Mapping[str, object],
        candidate_coverage: Mapping[str, object],
        level_certification: Mapping[str, object],
        positive_witness: Sequence[str],
        proof_artifact: Mapping[str, object],
        critical_scope_assumptions: Sequence[str],
        promotion_dependencies: Sequence[str],
        created_at: str,
        requested_issuer: str,
        formal_artifacts_verified: bool,
        admission_policy_authority: AdmissionPolicyAuthority,
        formal_ceiling: object,
    ) -> IssuedLevelCertificate:
        self._validate_checker_run(checker_run, level, conclusion)
        if requested_issuer != "kernel_checker":
            _reject(
                "P9-CERT-002_NON_CHECKER_ISSUER",
                "only kernel_checker may issue a level certificate",
            )

        coverage = self._validate_coverage(candidate_coverage, level)
        level_proof = self._validate_level_proof(level_certification)
        if formal_artifacts_verified is not True or any(
            not _canonical_hash(value, reject_placeholder=True)
            for value in (gamma_hash, evidence_hash)
        ):
            _reject(
                "P9-CERT-005_FORMAL_HASHES_NOT_VERIFIED",
                "formal non-placeholder artifact hashes are required",
            )
        if not isinstance(admission_policy_authority, AdmissionPolicyAuthority):
            _reject(
                "P9-CERT-007_ADMISSION_POLICY_UNVERIFIED",
                "a verified and approved admission policy is required",
            )
        from src.scope.formal_ceiling import FormalCeilingAssessment

        if not isinstance(formal_ceiling, FormalCeilingAssessment):
            _reject(
                "P9-CERT-008_FORMAL_CEILING_UNVERIFIED",
                "certificate requires an exact verified formal ceiling",
            )
        ceiling_report = formal_ceiling.to_dict()
        if not (
            formal_ceiling.verified
            and ceiling_report is not None
            and formal_ceiling.binds(
                gamma_hash=gamma_hash,
                catalog_hash=ceiling_report.get("catalog_hash"),
                target_level=level,
                declared_domain_size=coverage["declared_domain_size"],
                result_candidates=coverage["result_candidates"],
                legal_world_count=coverage["legal_world_count"],
                legal_worlds_hash=coverage["legal_worlds_hash"],
                cartesian_assignment_bound=coverage[
                    "cartesian_assignment_bound"
                ],
            )
            and checker_run.alternative.assignments_examined
            == ceiling_report.get("cartesian_assignment_bound")
        ):
            _reject(
                "P9-CERT-008_FORMAL_CEILING_UNVERIFIED",
                "certificate requires an exact verified formal ceiling",
            )

        if not all(_identifier(value) for value in (certificate_id, case_id, level)):
            _reject(
                "P9-CERT-006_INVALID_METADATA",
                "certificate, case, and level identifiers are required",
            )
        entity = _required_mapping(conclusion, "conclusion")
        if set(entity) != {"entity_id", "entity_type"} or not all(
            _identifier(entity.get(field)) for field in ("entity_id", "entity_type")
        ):
            _reject(
                "P9-CERT-006_INVALID_METADATA",
                "conclusion must be a complete entity reference",
            )
        witnesses = _string_tuple(
            positive_witness,
            field="positive_witness",
            require_nonempty=True,
        )
        assumptions = _string_tuple(
            critical_scope_assumptions,
            field="critical_scope_assumptions",
            require_nonempty=False,
        )
        promotions = _string_tuple(
            promotion_dependencies,
            field="promotion_dependencies",
            require_nonempty=False,
        )
        proof = self._validate_proof_artifact(proof_artifact)
        if not _utc_timestamp(created_at):
            _reject(
                "P9-CERT-006_INVALID_METADATA",
                "created_at must be an RFC3339 UTC timestamp",
            )

        document = {
            "schema_version": "0.8.0",
            "certificate_id": certificate_id,
            "case_id": case_id,
            "issued_by": "kernel_checker",
            "gamma_hash": gamma_hash,
            "evidence_hash": evidence_hash,
            "admission_policy_hash": admission_policy_authority.policy_hash,
            "admission_policy_approval_hash": (
                admission_policy_authority.approval_manifest_hash
            ),
            "formal_ceiling_hash": formal_ceiling.ceiling_hash,
            "level": level,
            "conclusion": {
                "entity_id": entity["entity_id"],
                "entity_type": entity["entity_type"],
            },
            "certification_scope": "level_complete",
            "candidate_coverage": coverage,
            "core_query_results": {
                "base": "SAT",
                "support": "SAT",
                "alternative": "UNSAT",
            },
            "level_certification": level_proof,
            "positive_witness": list(witnesses),
            "proof_artifact": proof,
            "critical_scope_assumptions": list(assumptions),
            "promotion_dependencies": list(promotions),
            "created_at": created_at,
            "status": "valid",
        }
        issued = IssuedLevelCertificate(_canonical_json(document))
        if not issued.binds_checker_run(checker_run):
            _reject(
                "P9-CERT-001_CHECKER_CONDITIONS_NOT_MET",
                "certificate conclusion is not bound to the support witness",
            )
        return issued

    @staticmethod
    def _validate_checker_run(
        checker_run: object,
        level: object,
        conclusion: object,
    ) -> None:
        if not isinstance(checker_run, CheckerRun) or not (
            checker_run.checker_status is CheckerStatus.CANDIDATE_CERTIFIED
            and checker_run.base.status is QueryStatus.SAT
            and checker_run.support.status is QueryStatus.SAT
            and checker_run.alternative.status is QueryStatus.UNSAT
        ):
            _reject(
                "P9-CERT-001_CHECKER_CONDITIONS_NOT_MET",
                "Checker must report SAT/SAT/UNSAT CANDIDATE_CERTIFIED",
            )
        entity = conclusion if isinstance(conclusion, Mapping) else {}
        witness = checker_run.support.witness
        if (
            not _identifier(level)
            or not isinstance(witness, Mapping)
            or witness.get(level) != entity.get("entity_id")
        ):
            _reject(
                "P9-CERT-001_CHECKER_CONDITIONS_NOT_MET",
                "support witness does not bind the requested conclusion",
            )

    @staticmethod
    def _validate_coverage(
        candidate_coverage: object,
        level: str,
    ) -> dict[str, object]:
        coverage = _required_mapping(candidate_coverage, "candidate_coverage")
        if coverage.get("mode") != "exhaustive":
            _reject(
                "P9-CERT-003_NON_EXHAUSTIVE_COVERAGE",
                "P9 signs exhaustive coverage only",
            )
        declared = coverage.get("declared_domain_size")
        checked = coverage.get("checked_count")
        result_candidates = coverage.get("result_candidates")
        legal_world_count = coverage.get("legal_world_count")
        legal_worlds_hash = coverage.get("legal_worlds_hash")
        assignment_bound = coverage.get("cartesian_assignment_bound")
        omitted = coverage.get("omitted_known_candidates")
        if (
            coverage.get("level") != level
            or isinstance(declared, bool)
            or not isinstance(declared, int)
            or declared <= 0
            or isinstance(checked, bool)
            or not isinstance(checked, int)
            or checked != declared
            or not isinstance(result_candidates, Sequence)
            or isinstance(result_candidates, (str, bytes))
            or len(result_candidates) != declared
            or any(
                not isinstance(candidate, str) or not candidate
                for candidate in result_candidates
            )
            or len(set(result_candidates)) != len(result_candidates)
            or isinstance(legal_world_count, bool)
            or not isinstance(legal_world_count, int)
            or legal_world_count <= 0
            or not _canonical_hash(
                legal_worlds_hash, reject_placeholder=True
            )
            or isinstance(assignment_bound, bool)
            or not isinstance(assignment_bound, int)
            or assignment_bound <= 0
            or omitted != []
            or not isinstance(coverage.get("solver_seed_used"), bool)
        ):
            _reject(
                "P9-CERT-003_NON_EXHAUSTIVE_COVERAGE",
                "coverage must check the entire declared domain without omissions",
            )
        return {
            "level": level,
            "mode": "exhaustive",
            "declared_domain_size": declared,
            "checked_count": checked,
            "result_candidates": list(result_candidates),
            "legal_world_count": legal_world_count,
            "legal_worlds_hash": legal_worlds_hash,
            "cartesian_assignment_bound": assignment_bound,
            "omitted_known_candidates": [],
            "solver_seed_used": coverage["solver_seed_used"],
        }

    @staticmethod
    def _validate_level_proof(level_certification: object) -> dict[str, bool]:
        proof = _required_mapping(level_certification, "level_certification")
        required = (
            "all_legal_results_covered",
            "exactly_one_feasible_result",
            "all_critical_queries_known",
        )
        if set(proof) != _LEVEL_PROOF_FIELDS or not all(
            proof.get(field) is True for field in required
        ):
            _reject(
                "P9-CERT-004_LEVEL_PROOF_INCOMPLETE",
                "all three level-complete proof conditions must be true",
            )
        return {field: True for field in required}

    @staticmethod
    def _validate_proof_artifact(proof_artifact: object) -> dict[str, object]:
        proof = _required_mapping(proof_artifact, "proof_artifact")
        query_hashes = proof.get("query_hashes")
        if (
            set(proof) != _PROOF_ARTIFACT_FIELDS
            or proof.get("proof_level") not in _PROOF_LEVELS
            or proof.get("solver") not in _SOLVERS
            or not _identifier(proof.get("solver_version"))
            or not _valid_hash_sequence(
                query_hashes,
                reject_placeholder=True,
                require_nonempty=True,
            )
            or not (
                proof.get("artifact_uri") is None
                or _identifier(proof.get("artifact_uri"))
            )
        ):
            _reject(
                "P9-CERT-006_INVALID_METADATA",
                "proof_artifact is incomplete or contains unverified query hashes",
            )
        return {
            "proof_level": proof["proof_level"],
            "solver": proof["solver"],
            "solver_version": proof["solver_version"],
            "query_hashes": list(query_hashes),
            "artifact_uri": proof["artifact_uri"],
        }
