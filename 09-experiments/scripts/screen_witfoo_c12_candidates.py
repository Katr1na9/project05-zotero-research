#!/usr/bin/env python3
"""Screen production-SOC metadata under a frozen C12 intake protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, BinaryIO, Iterator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = (
    ROOT
    / "09-experiments"
    / "real_data"
    / "witfoo_precinct6"
    / "c12_intake_lock_v0.1.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def dataset_url(lock: dict[str, Any]) -> str:
    dataset = lock["dataset"]
    return (
        "https://huggingface.co/datasets/"
        f"{dataset['dataset_id']}/resolve/{dataset['revision']}/"
        f"{dataset['attack_reports_path']}"
    )


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            return [part.strip() for part in stripped.split(",") if part.strip()]
        return parsed if isinstance(parsed, list) else [parsed]
    return [value]


def open_source(source: str) -> BinaryIO:
    if not source.casefold().startswith(("http://", "https://")):
        local = Path(source)
        if local.is_file():
            return local.open("rb")
        raise FileNotFoundError(f"C12 screening source does not exist: {local}")
    request = urllib.request.Request(
        source,
        headers={"User-Agent": "Project05-C12-screen/0.2"},
    )
    return urllib.request.urlopen(request, timeout=120)  # noqa: S310


def iter_records(
    source: str, max_records: int | None = None
) -> Iterator[tuple[dict[str, Any], bytes]]:
    with open_source(source) as handle:
        for index, raw_line in enumerate(handle, start=1):
            if max_records is not None and index > max_records:
                break
            if raw_line.strip():
                yield json.loads(raw_line), raw_line


def product_profile(
    labels: list[str], taxonomy: dict[str, dict[str, str]]
) -> dict[str, list[str]]:
    mapped = [taxonomy[label] for label in labels if label in taxonomy]
    return {
        "raw_labels": sorted(set(labels)),
        "families": sorted({item["family"] for item in mapped}),
        "sensor_channels": sorted({item["channel"] for item in mapped}),
        "unmapped_labels": sorted({label for label in labels if label not in taxonomy}),
    }


def candidate_score(
    record: dict[str, Any], profile: dict[str, list[str]], ranking: dict[str, Any]
) -> float:
    channels = len(profile["sensor_channels"])
    families = len(profile["families"])
    nodes = int(record.get("node_count") or 0)
    edges = int(record.get("edge_count") or 0)
    leads = int(record.get("lead_count") or 0)
    stage = str(record.get("lifecycle_stage", "")).casefold()
    score = float(ranking["base_confirmed_malicious"])
    score += min(channels, int(ranking["sensor_channel_cap"])) * float(
        ranking["per_distinct_sensor_channel"]
    )
    score += min(families, int(ranking["product_family_cap"])) * float(
        ranking["per_distinct_product_family"]
    )
    score += min(nodes, int(ranking["node_cap"])) * float(ranking["per_node"])
    score += min(edges, int(ranking["edge_cap"])) * float(ranking["per_edge"])
    score += min(leads, int(ranking["lead_cap"])) * float(ranking["per_lead"])
    score += float(ranking["lifecycle_stage_bonus"].get(stage, 0.0))
    return round(score, 4)


def compact_candidate(
    record: dict[str, Any],
    profile: dict[str, list[str]],
    ranking: dict[str, Any],
    source_record_index: int,
) -> dict[str, Any]:
    incident_id = str(record["incident_id"])
    return {
        "incident_id": incident_id,
        "source_record_index_1based": source_record_index,
        "score": candidate_score(record, profile, ranking),
        "disposition": record.get("disposition"),
        "disposition_category": record.get("disposition_category"),
        "report_source": record.get("report_source"),
        "mo_name": record.get("mo_name"),
        "suspicion_score": record.get("suspicion_score"),
        "lifecycle_stage": record.get("lifecycle_stage"),
        "products_observed": profile["raw_labels"],
        "product_families": profile["families"],
        "sensor_channels": profile["sensor_channels"],
        "attack_tactics": sorted(
            set(map(str, as_list(record.get("attack_tactics"))))
        ),
        "attack_techniques": sorted(
            set(map(str, as_list(record.get("attack_techniques"))))
        ),
        "set_role_names": sorted(
            set(map(str, as_list(record.get("set_role_names"))))
        ),
        "matched_rules": sorted(
            set(map(str, as_list(record.get("matched_rules"))))
        ),
        "lead_count": int(record.get("lead_count") or 0),
        "node_count": int(record.get("node_count") or 0),
        "edge_count": int(record.get("edge_count") or 0),
        "first_observed_at": record.get("first_observed_at"),
        "last_observed_at": record.get("last_observed_at"),
        "graph_path": (
            f"graph/incidents_graphml/{incident_id[0].casefold()}/"
            f"{incident_id}.graphml"
        ),
    }


def screen(
    source: str,
    lock: dict[str, Any],
    lock_sha256: str,
    max_records: int | None = None,
) -> dict[str, Any]:
    inclusion = lock["inclusion"]
    taxonomy = lock["product_taxonomy"]
    allowed_dispositions = {
        str(value).casefold() for value in inclusion["allowed_dispositions"]
    }
    allowed_categories = {
        str(value).casefold()
        for value in inclusion["allowed_disposition_categories"]
    }
    candidates: list[dict[str, Any]] = []
    raw_hash = hashlib.sha256()
    scanned = 0
    product_counts: Counter[str] = Counter()
    unmapped_counts: Counter[str] = Counter()
    rejection_counts = Counter()

    for record, raw_line in iter_records(source, max_records=max_records):
        scanned += 1
        raw_hash.update(raw_line)
        disposition = str(record.get("disposition", "")).casefold()
        category = str(record.get("disposition_category", "")).casefold()
        labels = sorted(
            set(map(str, as_list(record.get("products_observed"))))
        )
        product_counts.update(labels)
        profile = product_profile(labels, taxonomy)
        unmapped_counts.update(profile["unmapped_labels"])

        if disposition not in allowed_dispositions or category not in allowed_categories:
            rejection_counts["not_confirmed_malicious"] += 1
            continue
        if inclusion["require_all_product_labels_mapped"] and profile["unmapped_labels"]:
            rejection_counts["unmapped_product_label"] += 1
            continue
        if len(profile["families"]) < int(
            inclusion["minimum_distinct_product_families"]
        ):
            rejection_counts["insufficient_product_families"] += 1
            continue
        if len(profile["sensor_channels"]) < int(
            inclusion["minimum_distinct_sensor_channels"]
        ):
            rejection_counts["insufficient_sensor_channels"] += 1
            continue
        if int(record.get("node_count") or 0) < int(inclusion["minimum_node_count"]):
            rejection_counts["insufficient_nodes"] += 1
            continue
        if int(record.get("edge_count") or 0) < int(inclusion["minimum_edge_count"]):
            rejection_counts["insufficient_edges"] += 1
            continue
        candidates.append(
            compact_candidate(record, profile, lock["ranking"], scanned)
        )

    candidates.sort(key=lambda item: (-item["score"], item["incident_id"]))
    top_k = int(inclusion["top_k"])
    observed_hash = raw_hash.hexdigest().upper()
    complete = max_records is None
    source_integrity_pass = (
        not complete
        or (
            observed_hash == lock["dataset"]["attack_reports_sha256"]
            and scanned == int(lock["dataset"]["expected_record_count"])
        )
    )
    taxonomy_pass = not unmapped_counts
    selected = candidates[:top_k]
    return {
        "screen_id": "project05-c12-witfoo-operational-screen-v0.1",
        "protocol_lock_sha256": lock_sha256,
        "source": {
            "dataset_id": lock["dataset"]["dataset_id"],
            "revision": lock["dataset"]["revision"],
            "attack_reports_source": source,
            "scanned_raw_sha256": observed_hash,
            "scan_complete": complete,
        },
        "gates": {
            "source_integrity": {
                "pass": source_integrity_pass,
                "expected_records": lock["dataset"]["expected_record_count"],
                "observed_records": scanned,
                "expected_sha256": lock["dataset"]["attack_reports_sha256"],
                "observed_sha256": observed_hash,
            },
            "product_taxonomy": {
                "pass": taxonomy_pass,
                "unmapped_product_labels": dict(sorted(unmapped_counts.items())),
            },
            "event_level_source_review": {
                "pass": False,
                "status": "pending_graph_download_and_recoverability_audit",
            },
        },
        "unit_of_analysis": lock["unit_of_analysis"],
        "screening_rules": inclusion,
        "ranking_rules": lock["ranking"],
        "counts": {
            "records_scanned": scanned,
            "eligible_before_top_k": len(candidates),
            "selected": len(selected),
            "rejections": dict(sorted(rejection_counts.items())),
            "raw_product_labels": dict(sorted(product_counts.items())),
        },
        "candidates": selected,
        "claim_boundary": lock["claim_boundaries"],
        "decision": {
            "status": "metadata_gate_passed_event_gate_pending",
            "paper_result_claim_allowed": False,
            "next_step": "download_and_audit_ranked_graphs_before_freezing_one_C12_engagement",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rank production-SOC incidents under the frozen C12 intake lock."
    )
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--source")
    parser.add_argument("--max-records", type=int)
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "09-experiments"
            / "results"
            / "c12_witfoo_screen_v0.1"
            / "candidate_index.json"
        ),
    )
    args = parser.parse_args()
    lock = load_json(args.lock)
    source = args.source or dataset_url(lock)
    result = screen(source, lock, sha256(args.lock), args.max_records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["counts"], ensure_ascii=False, indent=2))
    print(json.dumps(result["gates"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
