#!/usr/bin/env python3
"""Validate the metadata-only CTI text source gate for the mainline compiler.

The validator never fetches source text.  It checks source decisions, publisher-
blocked roles, license evidence, concurrency boundaries and legacy hashes.  A
passing source gate authorizes only bounded retrieval and a later payload scan;
it never authorizes a component, model, training, formal inference or C07-C12.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_ROOT.parent
DEFAULT_CATALOG = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "cti-text-source-catalog-v0.1.json"
)
REQUIRED_ROLES = frozenset({"unit", "development", "component_validation"})
APPROVED_DECISIONS = frozenset({"approve", "conditional_approve"})
ELIGIBLE_SCREENING = "eligible_pending_user_review"
VERIFIED_LICENSE_STATES = frozenset(
    {
        "verified_repository_authored_content",
        "verified_repository_license",
        "verified_original_government_work_per_document",
    }
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite CTI source-gate output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_catalog(
    catalog: dict[str, Any], *, repo_root: Path | None = REPO_ROOT
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    candidates = catalog.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
        errors.append("candidates_not_array")
    source_ids = [item.get("source_id") for item in candidates if isinstance(item, dict)]
    duplicate_ids = sorted(
        str(key) for key, count in Counter(source_ids).items() if count > 1
    )
    if duplicate_ids:
        errors.append("duplicate_source_ids:" + ",".join(duplicate_ids))

    eligible = [
        item
        for item in candidates
        if isinstance(item, dict)
        and item.get("screening_status") == ELIGIBLE_SCREENING
    ]
    pending = [
        item["source_id"] for item in eligible if item.get("user_decision") == "pending"
    ]
    activated: list[dict[str, Any]] = []
    for item in candidates:
        if not isinstance(item, dict):
            errors.append("candidate_not_object")
            continue
        decision = item.get("user_decision")
        authorized = item.get("retrieval_authorized")
        if decision in APPROVED_DECISIONS:
            if item.get("screening_status") != ELIGIBLE_SCREENING:
                errors.append(f"ineligible_source_activated:{item.get('source_id')}")
            if authorized is not True:
                errors.append(f"approved_without_retrieval_authority:{item.get('source_id')}")
            if item.get("controller_eligible") is not False:
                errors.append(f"controller_eligibility_not_false:{item.get('source_id')}")
            activated.append(item)
        elif authorized is True:
            errors.append(f"retrieval_authorized_without_approval:{item.get('source_id')}")

    role_to_families: dict[str, set[str]] = defaultdict(set)
    family_to_roles: dict[str, set[str]] = defaultdict(set)
    for item in activated:
        role = item.get("split_role")
        family = item.get("publisher_family")
        if role not in REQUIRED_ROLES:
            errors.append(f"activated_source_has_invalid_role:{item.get('source_id')}")
        if not isinstance(family, str) or not family:
            errors.append(f"activated_source_missing_publisher_family:{item.get('source_id')}")
        else:
            role_to_families[str(role)].add(family)
            family_to_roles[family].add(str(role))
        license_status = (item.get("license") or {}).get("verification_status")
        if role != "component_validation" and license_status not in VERIFIED_LICENSE_STATES:
            errors.append(f"unverified_license:{item.get('source_id')}")
        if role == "component_validation" and item.get("content_class") != (
            "natural_public_security_advisory"
        ):
            errors.append(
                f"validation_source_not_natural_report:{item.get('source_id')}"
            )
        if not item.get("repository") or not item.get("revision"):
            errors.append(f"unfrozen_source_identity:{item.get('source_id')}")

    crossing_families = sorted(
        family for family, roles in family_to_roles.items() if len(roles) > 1
    )
    if crossing_families:
        errors.append("publisher_family_crosses_roles:" + ",".join(crossing_families))

    source_gate_complete = not pending and bool(activated)
    if source_gate_complete:
        missing_roles = sorted(REQUIRED_ROLES.difference(role_to_families))
        if missing_roles:
            errors.append("missing_required_roles:" + ",".join(missing_roles))
        distinct_families = set(family_to_roles)
        minimum = int(
            catalog.get("source_gate_policy", {}).get(
                "minimum_distinct_publisher_families", 3
            )
        )
        if len(distinct_families) < minimum:
            errors.append("insufficient_distinct_publisher_families")

    legacy_hashes: dict[str, str] = {}
    if repo_root is not None:
        root = Path(repo_root)
        for relative, expected in catalog.get("legacy_inheritance_lock", {}).items():
            path = root / relative
            if not path.is_file():
                errors.append(f"legacy_lock_file_missing:{relative}")
                continue
            actual = sha256_file(path)
            legacy_hashes[relative] = actual
            if actual != expected:
                errors.append(f"legacy_lock_hash_mismatch:{relative}")

    forbidden_flags = {
        "raw_cti_text_present": False,
        "corpus_downloaded": False,
        "component_runtime_authorized": False,
        "model_or_embedding_authorized": False,
        "training_authorized": False,
        "formal_inference_authorized": False,
        "controller_integration_authorized": False,
    }
    for key, expected in forbidden_flags.items():
        if catalog.get(key) is not expected:
            errors.append(f"unauthorized_catalog_flag:{key}")
    if catalog.get("concurrency_boundary", {}).get("parallel_work_allowed") is not True:
        errors.append("parallel_work_boundary_missing")
    if catalog.get("concurrency_boundary", {}).get("integration_rule") != (
        "LLM sidecars remain controller_eligible=false until both the compiler contract "
        "and the selected M3 controller interface are independently frozen"
    ):
        errors.append("integration_rule_changed")

    if errors:
        status = "failed_closed"
    elif pending:
        status = "pending_user_source_review"
    elif source_gate_complete:
        status = "ready_for_bounded_retrieval_and_payload_scan"
    else:
        status = "smoke_only_no_activated_sources"
        warnings.append("no_source_activated")

    return {
        "report_id": "project05-mainline-compiler-cti-source-gate-validation-v0.1",
        "catalog_id": catalog.get("catalog_id"),
        "status": status,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "counts": {
            "candidate_sources": len(candidates),
            "eligible_sources": len(eligible),
            "pending_user_decisions": len(pending),
            "activated_sources": len(activated),
            "activated_publisher_families": len(family_to_roles),
        },
        "pending_source_ids": sorted(pending),
        "activated_source_ids": sorted(
            item.get("source_id") for item in activated if item.get("source_id")
        ),
        "role_to_publisher_families": {
            role: sorted(families) for role, families in sorted(role_to_families.items())
        },
        "legacy_hashes": legacy_hashes,
        "authorization": {
            "bounded_retrieval": status == "ready_for_bounded_retrieval_and_payload_scan",
            "payload_normalization": False,
            "component_runtime": False,
            "model_or_embedding": False,
            "training": False,
            "formal_inference": False,
            "C07_C12_execution": False,
            "controller_integration": False,
        },
        "next_gate": (
            "user source decisions" if pending else "bounded retrieval plus per-document "
            "license/origin verification and protected-family payload exclusion scan"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_catalog(load_json(args.catalog), repo_root=args.repo_root)
    if args.output:
        write_json_no_overwrite(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["status"] == "failed_closed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
