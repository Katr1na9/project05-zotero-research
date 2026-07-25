#!/usr/bin/env python3
"""Independently validate the WP4 bounded CTI retrieval and exclusion output."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_ROOT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "generated"
    / "retrieval-v0.1"
)
EXPECTED_SOURCE_ROLES = {
    "ctid_blueprints_intrusion_sample": "unit",
    "mitre_attack_software_procedure_text": "development",
    "tram_cisa_first_party_advisory_subset": "component_validation",
}
FORBIDDEN_AUTHORIZATIONS = frozenset(
    {
        "component_runtime",
        "model_or_embedding",
        "training",
        "formal_inference",
        "C07_C12_execution",
        "controller_integration",
    }
)


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


RETRIEVAL = load_sibling(
    "project05_wp4_retrieval_for_independent_validation",
    "retrieve_compiler_cti_sources.py",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite retrieval readiness: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_loaded(
    manifest: dict[str, Any],
    origin_audit: list[dict[str, Any]],
    exclusion_audit: dict[str, Any],
    records: list[dict[str, Any]],
    lock_provenance: dict[str, Any],
    *,
    copied_lock_sha256: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if manifest.get("status") != "passed":
        errors.append("retrieval_manifest_not_passed")
    if manifest.get("raw_upstream_corpora_retained") is not False:
        errors.append("raw_upstream_corpora_retained")
    if manifest.get("blockers") != []:
        errors.append("retrieval_manifest_has_blockers")
    authorization = manifest.get("authorization", {})
    for key in FORBIDDEN_AUTHORIZATIONS:
        if authorization.get(key) is not False:
            errors.append(f"unauthorized_runtime_flag:{key}")

    if exclusion_audit.get("status") != "passed_clean":
        errors.append("payload_exclusion_not_clean")
    for key in (
        "excluded_record_count",
        "normalized_exact_match_count",
        "near_duplicate_match_count",
        "forbidden_literal_match_count",
        "forbidden_field_match_count",
    ):
        if exclusion_audit.get(key) != 0:
            errors.append(f"payload_exclusion_nonzero:{key}")
    if exclusion_audit.get("matches") != []:
        errors.append("payload_exclusion_matches_not_empty")
    threshold = float(exclusion_audit.get("threshold", 0))
    maximum = float(exclusion_audit.get("maximum_jaccard", 1))
    if threshold != 0.85:
        errors.append("payload_exclusion_threshold_changed")
    if maximum >= threshold:
        errors.append("payload_exclusion_maximum_reaches_threshold")
    if exclusion_audit.get("contains_raw_protected_payload") is not False:
        errors.append("audit_contains_raw_protected_payload")

    if lock_provenance.get("contains_raw_test_payload") is not False:
        errors.append("lock_contains_raw_test_payload")
    if lock_provenance.get("contains_raw_private_gold") is not False:
        errors.append("lock_contains_raw_private_gold")
    if lock_provenance.get("copied_file_sha256") != copied_lock_sha256:
        errors.append("copied_exclusion_lock_hash_mismatch")
    if lock_provenance.get("source_file_sha256") != copied_lock_sha256:
        errors.append("source_and_copied_exclusion_lock_hash_differ")

    if len(origin_audit) != 7:
        errors.append("cisa_origin_audit_document_count_not_seven")
    verified_origins = 0
    for index, row in enumerate(origin_audit):
        if row.get("status") != "verified_first_party_government_origin":
            errors.append(f"cisa_origin_not_verified:{index}")
            continue
        verified_origins += 1
        if row.get("reason_codes") != []:
            errors.append(f"cisa_origin_has_reason_codes:{index}")
        if row.get("third_party_embedded_media_copied") is not False:
            errors.append(f"cisa_third_party_media_copied:{index}")
        if not RETRIEVAL.government_host(str(row.get("original_url") or "")):
            errors.append(f"cisa_original_url_not_government:{index}")
        final_url = (row.get("origin_retrieval") or {}).get("final_url", "")
        if not RETRIEVAL.government_host(str(final_url)):
            errors.append(f"cisa_final_url_not_government:{index}")
        if (row.get("origin_retrieval") or {}).get("http_status") != 200:
            errors.append(f"cisa_origin_http_not_200:{index}")

    source_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    document_units: dict[str, set[str]] = {}
    record_ids: set[str] = set()
    for index, record in enumerate(records):
        source_id = record.get("source_id")
        expected_role = EXPECTED_SOURCE_ROLES.get(source_id)
        if expected_role is None:
            errors.append(f"unexpected_admitted_source:{index}")
            continue
        if record.get("split_role") != expected_role:
            errors.append(f"admitted_record_role_mismatch:{index}")
        if record.get("controller_eligible") is not False:
            errors.append(f"admitted_record_controller_eligible:{index}")
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"admitted_record_missing_id:{index}")
        elif record_id in record_ids:
            errors.append(f"duplicate_admitted_record_id:{record_id}")
        else:
            record_ids.add(record_id)
        if RETRIEVAL.forbidden_field_paths(record.get("payload")):
            errors.append(f"admitted_record_forbidden_field:{index}")
        source_counts[str(record.get("source_family_id"))] += 1
        role_counts[expected_role] += 1
        document_units.setdefault(str(record.get("source_family_id")), set()).add(
            str(record.get("document_unit_id"))
        )

    manifest_counts = manifest.get("admitted_record_counts", {})
    if dict(sorted(source_counts.items())) != manifest_counts:
        errors.append("admitted_record_counts_mismatch")
    if len(records) != exclusion_audit.get("admitted_record_count"):
        errors.append("admitted_count_differs_from_exclusion_audit")
    if verified_origins != manifest.get("verified_cisa_document_count"):
        errors.append("verified_cisa_count_mismatch")
    if manifest.get("rejected_cisa_document_count") != 0:
        errors.append("rejected_cisa_document_count_nonzero")

    if source_counts.get("ctid_blueprints", 0) < 1:
        errors.append("no_ctid_unit_record")
    if source_counts.get("mitre_attack", 0) < 1:
        errors.append("no_mitre_development_record")
    if source_counts.get("cisa_first_party_advisories", 0) != 7:
        errors.append("cisa_validation_record_count_not_seven")
    if len(document_units.get("cisa_first_party_advisories", set())) != 7:
        errors.append("cisa_document_units_not_seven")
    if len(document_units.get("mitre_attack", set())) == 1:
        warnings.append("mitre_records_share_one_upstream_document_unit")

    status = "passed_s2_s3_ready_for_runtime_gate_review" if not errors else "failed_closed"
    return {
        "schema_version": "project05-mainline-compiler-cti-s2-s3-readiness-v0.1",
        "status": status,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "counts": {
            "admitted_records": len(records),
            "verified_cisa_documents": verified_origins,
            "source_family_records": dict(sorted(source_counts.items())),
            "split_role_records": dict(sorted(role_counts.items())),
            "source_family_document_units": {
                key: len(value) for key, value in sorted(document_units.items())
            },
        },
        "exclusion": {
            "threshold": threshold,
            "maximum_jaccard": maximum,
            "exact_matches": exclusion_audit.get("normalized_exact_match_count"),
            "near_matches": exclusion_audit.get("near_duplicate_match_count"),
            "forbidden_literal_matches": exclusion_audit.get(
                "forbidden_literal_match_count"
            ),
            "forbidden_field_matches": exclusion_audit.get(
                "forbidden_field_match_count"
            ),
        },
        "authorization": {
            "component_runtime": False,
            "model_or_embedding": False,
            "training": False,
            "formal_inference": False,
            "C07_C12_execution": False,
            "controller_integration": False,
        },
        "next_gate": "separate component runtime authorization and frozen component-bench plan",
    }


def validate_root(root: Path) -> dict[str, Any]:
    root = Path(root)
    required = {
        "retrieval-manifest.json": root / "retrieval-manifest.json",
        "source-origin-audit.json": root / "source-origin-audit.json",
        "payload-exclusion-audit.json": root / "payload-exclusion-audit.json",
        "admitted-records.jsonl": root / "admitted-records.jsonl",
        "protected-signature-lock-v0.1.json": root
        / "protected-signature-lock-v0.1.json",
        "protected-signature-lock-provenance.json": root
        / "protected-signature-lock-provenance.json",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        return {
            "schema_version": "project05-mainline-compiler-cti-s2-s3-readiness-v0.1",
            "status": "failed_closed",
            "errors": ["missing_artifacts:" + ",".join(sorted(missing))],
            "warnings": [],
            "authorization": {key: False for key in FORBIDDEN_AUTHORIZATIONS},
        }
    report = validate_loaded(
        load_json(required["retrieval-manifest.json"]),
        load_json(required["source-origin-audit.json"]),
        load_json(required["payload-exclusion-audit.json"]),
        load_jsonl(required["admitted-records.jsonl"]),
        load_json(required["protected-signature-lock-provenance.json"]),
        copied_lock_sha256=sha256_file(
            required["protected-signature-lock-v0.1.json"]
        ),
    )
    report["artifact_sha256"] = {
        name: sha256_file(path) for name, path in sorted(required.items())
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_root(args.root)
    if args.output:
        write_json_no_overwrite(args.output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    if report["status"] == "failed_closed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
