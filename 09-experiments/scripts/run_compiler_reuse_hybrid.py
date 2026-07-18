#!/usr/bin/env python3
"""Build the development-only REUSE-HYBRID WP3 interface snapshot.

The log/provenance side references the immutable RULE-STRONG development
result.  The CTI side uses the clean-room component adapter and must abstain
because the frozen WP2 requests contain no ``cti_text`` artifact.  This runner
does not execute a third-party component or evaluate C07-C12.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_WP2_ROOT = (
    EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "generated" / "wp2"
)
DEFAULT_PUBLIC_ROOT = DEFAULT_WP2_ROOT / "public"
DEFAULT_RULE_ROOT = DEFAULT_WP2_ROOT / "rule-strong-development"
DEFAULT_CATALOG = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp3"
    / "component-catalog-v0.1.json"
)
DEFAULT_OUTPUT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "generated"
    / "wp3"
    / "reuse-hybrid-development"
)
CONDITION_ID = "REUSE-HYBRID"
RUNNER_VERSION = "project05-mainline-reuse-hybrid-development-v0.1"
EXPECTED_CASES = [
    "C04-compiler-evaluation",
    "C05-compiler-evaluation",
    "C06-compiler-evaluation",
]


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_public_builder_for_reuse_hybrid",
    "build_compiler_public_request.py",
)
ADAPTER = load_sibling(
    "project05_clean_room_adapter_for_reuse_hybrid",
    "adapt_reuse_component_graph.py",
)
RULE = load_sibling(
    "project05_rule_strong_for_reuse_hybrid",
    "run_compiler_rule_strong.py",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl_gz(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite REUSE-HYBRID output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def empty_component_bundle(
    request_id: str, selected_profile: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "output_profile": selected_profile["output_profile"],
        "component_id": selected_profile["component_id"],
        "component_revision": selected_profile["revision"],
        "component_license": selected_profile["license"],
        "component_runtime_executed": False,
        "request_id": request_id,
        "triplets": [],
    }


def validate_frozen_inputs(
    requests: list[dict[str, Any]],
    rule_snapshot: dict[str, Any],
    rule_results: dict[str, Any],
    public_root: Path,
) -> None:
    if rule_snapshot.get("status") != "frozen_before_any_llm_output":
        raise ValueError("RULE-STRONG snapshot is not frozen")
    if rule_snapshot.get("case_ids") != EXPECTED_CASES:
        raise ValueError("RULE-STRONG case set differs from frozen development cases")
    if rule_snapshot.get("test_case_ids_processed") != []:
        raise ValueError("RULE-STRONG snapshot reports test-case processing")
    if rule_results.get("split") != "development":
        raise ValueError("RULE-STRONG results are not development-only")
    if rule_snapshot.get("results_sha256") != BUILDER.sha256_value(rule_results):
        raise ValueError("RULE-STRONG results no longer match the frozen snapshot")
    if sorted(item.get("case_id") for item in requests) != EXPECTED_CASES:
        raise ValueError("public request set differs from C04-C06")
    if any(item.get("split") != "development" for item in requests):
        raise ValueError("non-development public request supplied")
    if any(BUILDER.validate_public_request_integrity(item) for item in requests):
        raise ValueError("public request integrity failure")
    result_ids = {item.get("request_id") for item in rule_results.get("rows", [])}
    request_ids = {item.get("request_id") for item in requests}
    if result_ids != request_ids:
        raise ValueError("RULE-STRONG results and requests do not align")
    rebuilt_requests = RULE.build_development_requests(public_root)
    if rebuilt_requests != requests:
        raise ValueError("saved RULE requests differ from the current public WP2 package")


def build_results(
    requests: list[dict[str, Any]],
    rule_results: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    selected = catalog["selected_adapter_profile"]
    rule_rows = {
        item["request_id"]: item for item in rule_results.get("rows", [])
    }
    rows: list[dict[str, Any]] = []
    for request in sorted(requests, key=lambda item: item["case_id"]):
        bundle = empty_component_bundle(request["request_id"], selected)
        sidecar = ADAPTER.adapt_bundle(request, bundle, catalog)
        if sidecar["status"] != "abstained" or sidecar[
            "abstention_reasons"
        ] != ["no_visible_cti_text_artifact"]:
            raise ValueError("CTI adapter did not fail closed on a no-CTI request")
        rule_row = rule_rows[request["request_id"]]
        decision_counts = rule_row["admission_decision"]["counts"]
        rows.append(
            {
                "case_id": request["case_id"],
                "request_id": request["request_id"],
                "visible_cti_artifact_count": 0,
                "log_provenance_route": {
                    "mode": "frozen_rule_strong_reference",
                    "rule_version": rule_results["rule_version"],
                    "rule_row_sha256": BUILDER.sha256_value(rule_row),
                    "admitted_claim_count": decision_counts["admitted_claims"],
                    "admitted_link_count": decision_counts["admitted_links"],
                },
                "cti_component_route": sidecar,
                "merged_controller_payload_emitted": False,
            }
        )
    return {
        "condition_id": CONDITION_ID,
        "runner_version": RUNNER_VERSION,
        "status": "interface_only_explicit_cti_abstention",
        "split": "development",
        "case_ids": EXPECTED_CASES,
        "test_case_ids_processed": [],
        "rows": rows,
    }


def build_snapshot(
    results: dict[str, Any],
    rule_snapshot: dict[str, Any],
    rule_results: dict[str, Any],
    catalog_path: Path,
    rule_snapshot_path: Path,
) -> dict[str, Any]:
    rows = results["rows"]
    implementation_paths = {
        "adapt_reuse_component_graph.py": SCRIPT_DIR
        / "adapt_reuse_component_graph.py",
        "run_compiler_reuse_hybrid.py": SCRIPT_DIR
        / "run_compiler_reuse_hybrid.py",
        "component-catalog-v0.1.json": catalog_path,
        "normalized_aligned_triplet_bundle.schema.json": catalog_path.parent
        / "contracts"
        / "normalized_aligned_triplet_bundle.schema.json",
        "source_grounded_target_graph_sidecar.schema.json": catalog_path.parent
        / "contracts"
        / "source_grounded_target_graph_sidecar.schema.json",
    }
    return {
        "snapshot_id": "project05-mainline-reuse-hybrid-development-snapshot-v0.1",
        "status": "wp3_adapter_interface_pass_component_performance_not_evaluable",
        "condition_id": CONDITION_ID,
        "split": "development",
        "case_ids": EXPECTED_CASES,
        "test_case_ids_processed": [],
        "case_count": len(rows),
        "rule_admitted_claim_count": sum(
            row["log_provenance_route"]["admitted_claim_count"] for row in rows
        ),
        "rule_admitted_link_count": sum(
            row["log_provenance_route"]["admitted_link_count"] for row in rows
        ),
        "visible_cti_artifact_count": 0,
        "cti_component_request_count": len(rows),
        "cti_component_abstention_count": len(rows),
        "cti_component_accepted_edge_count": 0,
        "cti_component_gate": "not_evaluable_without_frozen_cti_text_artifacts",
        "adapter_unit_gate": "reported_only_by_separate_wp3_test_suite",
        "log_provenance_route": "frozen_rule_strong_reference",
        "rule_snapshot_status": rule_snapshot["status"],
        "rule_snapshot_file_sha256": sha256_file(rule_snapshot_path),
        "rule_results_sha256": BUILDER.sha256_value(rule_results),
        "results_sha256": BUILDER.sha256_value(results),
        "implementation_sha256": {
            name: sha256_file(path) for name, path in implementation_paths.items()
        },
        "private_files_read": False,
        "reference_data_used": False,
        "third_party_code_copied": False,
        "third_party_component_executed": False,
        "model_runtime_used": False,
        "model_or_embedding_downloaded": False,
        "training_used": False,
        "controller_payload_emitted": False,
        "component_performance_claim_authorized": False,
        "llm_performance_claim_authorized": False,
        "end_to_end_gain_claim_authorized": False,
        "wp4_model_gate_authorized": False,
        "next_required_amendment": (
            "freeze source-licensed CTI text artifacts and separately authorize "
            "a component runtime before any real component-performance Gate"
        ),
    }


def run(
    public_root: Path,
    rule_root: Path,
    catalog_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    public_root = ADAPTER.ensure_not_private_path(public_root)
    rule_root = ADAPTER.ensure_not_private_path(rule_root)
    catalog_path = ADAPTER.ensure_not_private_path(catalog_path)
    output_dir = Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing non-empty output directory: {output_dir}")

    requests = read_jsonl_gz(rule_root / "public-requests.jsonl.gz")
    rule_snapshot_path = rule_root / "rule-strong-development-snapshot.json"
    rule_snapshot = load_json(rule_snapshot_path)
    rule_results = load_json(rule_root / "rule-results.json")
    catalog = load_json(catalog_path)
    validate_frozen_inputs(
        requests, rule_snapshot, rule_results, public_root
    )

    results = build_results(requests, rule_results, catalog)
    snapshot = build_snapshot(
        results, rule_snapshot, rule_results, catalog_path, rule_snapshot_path
    )
    write_json_no_overwrite(output_dir / "reuse-hybrid-development-results.json", results)
    write_json_no_overwrite(
        output_dir / "reuse-hybrid-development-snapshot.json", snapshot
    )
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-root", type=Path, default=DEFAULT_PUBLIC_ROOT)
    parser.add_argument("--rule-root", type=Path, default=DEFAULT_RULE_ROOT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    snapshot = run(args.public_root, args.rule_root, args.catalog, args.output_dir)
    print(
        f"Wrote {snapshot['status']} for {snapshot['case_count']} development cases; "
        "no CTI component or model was executed"
    )


if __name__ == "__main__":
    main()
