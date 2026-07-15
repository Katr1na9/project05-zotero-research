#!/usr/bin/env python3
"""Build answer-key-separated LLM evidence-claim pilot samples."""

from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable


def load_script(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


pg = load_script("compile_pgdump_motifs")
ecar = load_script("compile_ecar_motifs")


def make_sample(
    claim: dict[str, Any],
    source_modality: str,
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    context_required = (
        claim.get("claim_type") == "benign_maintenance"
        or "stage:benign_context" in claim.get("tags", [])
    )
    pointer = claim["source_pointer"]
    return {
        "sample_id": claim["claim_id"],
        "evaluation_role": (
            "context_required_control" if context_required else "primary_atomic"
        ),
        "model_input": {
            "sample_id": claim["claim_id"],
            "case_id": claim["case_id"],
            "source_modality": source_modality,
            "source_pointer": {
                "artifact_id": pointer["artifact_id"],
                "record_id": pointer["record_id"],
            },
            "source_payload": source_payload,
        },
        "gold_claim": claim,
    }


def load_claims(case_dir: Path) -> list[dict[str, Any]]:
    return json.loads((case_dir / "evidence_claims.json").read_text(encoding="utf-8"))


def pg_samples(
    case_dir: Path,
    events_path: Path,
    nodes_path: Path,
) -> list[dict[str, Any]]:
    claims = load_claims(case_dir)
    by_record = {claim["source_pointer"]["record_id"]: claim for claim in claims}
    nodes = pg.build_node_lookup(nodes_path)
    samples: list[dict[str, Any]] = []
    for event in pg.load_event_rows(events_path):
        claim = by_record.get(event["event_uuid"])
        if claim is None:
            continue
        payload = {
            "event_uuid": event["event_uuid"],
            "timestamp_nanos": event["timestamp_nanos"],
            "operation": event["operation"],
            "src_node": event["src_node"],
            "dst_node": event["dst_node"],
            "resolved_context": pg.event_context(event, nodes),
        }
        samples.append(make_sample(claim, "provenance_edge", payload))
        if len(samples) == len(claims):
            break
    require_all_records(samples, claims, case_dir.name)
    return samples


def ecar_samples(
    case_dir: Path,
    events_path: Path,
) -> list[dict[str, Any]]:
    claims = load_claims(case_dir)
    by_record = {claim["source_pointer"]["record_id"]: claim for claim in claims}
    samples: list[dict[str, Any]] = []
    for event in ecar.load_jsonl(events_path):
        event_id = str(event.get("id") or "")
        claim = by_record.get(event_id)
        if claim is None:
            continue
        samples.append(
            make_sample(claim, "ecar_event", ecar.event_context(event))
        )
        if len(samples) == len(claims):
            break
    require_all_records(samples, claims, case_dir.name)
    return samples


def require_all_records(
    samples: list[dict[str, Any]],
    claims: list[dict[str, Any]],
    case_name: str,
) -> None:
    found = {sample["sample_id"] for sample in samples}
    expected = {claim["claim_id"] for claim in claims}
    missing = sorted(expected - found)
    if missing:
        raise ValueError(f"{case_name}: representative records not found: {missing}")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".gz":
        payload = "".join(
            json.dumps(row, ensure_ascii=False) + "\n" for row in rows
        ).encode("utf-8")
        # mtime=0 keeps the gzip bytes reproducible across runs.
        path.write_bytes(gzip.compress(payload, mtime=0))
        return
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = args.experiment_root
    cases = root / "real_cases"
    data = root / "real_data"
    samples = []
    samples.extend(
        pg_samples(
            cases / "C07-darpa-e5-theia-0515",
            data / "darpa_tc_e5" / "extracted" / "R04_event_table.tsv",
            data / "darpa_tc_e5" / "extracted" / "R04_nodes.jsonl",
        )
    )
    samples.extend(
        pg_samples(
            cases / "C08-darpa-e5-clearscope-0515",
            data / "darpa_tc_e5" / "extracted" / "R05_event_table.tsv",
            data / "darpa_tc_e5" / "extracted" / "R05_nodes.jsonl",
        )
    )
    samples.extend(
        ecar_samples(
            cases / "C09-darpa-optc-sysclient0201-0923",
            data / "darpa_optc" / "extracted" / "R06_sysclient0201_window.jsonl",
        )
    )
    samples.sort(key=lambda sample: sample["sample_id"])
    write_jsonl(args.output, samples)
    primary = sum(sample["evaluation_role"] == "primary_atomic" for sample in samples)
    controls = len(samples) - primary
    print(f"Wrote {len(samples)} pilot samples ({primary} primary, {controls} controls)")


if __name__ == "__main__":
    main()
