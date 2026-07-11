#!/usr/bin/env python3
"""Build deterministic blind annotation packets for Project05 C07-C10."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MVP_PATH = Path(__file__).with_name("run_mvp.py")
CASE_PREFIXES = ("C07", "C08", "C09", "C10")


def _load_mvp() -> Any:
    spec = importlib.util.spec_from_file_location("project05_annotation_mvp", MVP_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load simulator from {MVP_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MVP = _load_mvp()


def resolve_cases(cases_root: Path) -> list[Path]:
    cases: list[Path] = []
    for prefix in CASE_PREFIXES:
        matches = sorted(
            path
            for path in cases_root.glob(f"{prefix}*")
            if path.is_dir()
            and all((path / filename).is_file() for filename in MVP.CASE_FILENAMES)
        )
        if len(matches) != 1:
            raise FileNotFoundError(
                f"Expected one complete {prefix} case under {cases_root}; found {matches}"
            )
        cases.append(matches[0])
    return cases


def compact_claim(claim: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_type": claim.get("source_type", ""),
        "claim_type": claim.get("claim_type", ""),
        "subject": claim.get("subject", {}),
        "predicate": claim.get("predicate", ""),
        "object": claim.get("object", {}),
        "mapped_tactic": claim.get("mapped_tactic", []),
        "mapped_technique": claim.get("mapped_technique", []),
        "notes": claim.get("notes", ""),
        "source_pointer": claim.get("source_pointer", {}),
    }


def public_nodes(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node["node_id"],
            "stage": node.get("stage", ""),
            "critical": bool(node.get("critical", False)),
        }
        for node in config.get("cti_nodes", [])
    ]


def public_edges(config: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "source": edge.get("source", ""),
            "target": edge.get("target", ""),
        }
        for edge in config.get("cti_edges", [])
    ]


def shuffled_blind_items(
    task: str,
    records: list[tuple[dict[str, Any], dict[str, Any]]],
    rng: random.Random,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    rng.shuffle(records)
    prefix = {"claim": "CLM", "intent": "INT", "granularity": "GRN"}[task]
    public: list[dict[str, Any]] = []
    key: dict[str, dict[str, Any]] = {}
    for index, (item, admin) in enumerate(records, start=1):
        blind_id = f"{prefix}-{index:03d}"
        public.append({"blind_id": blind_id, **item})
        key[blind_id] = admin
    return public, key


def claim_records(case_dirs: list[Path]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    records = []
    for case_dir in case_dirs:
        for claim in MVP.load_json(case_dir / "evidence_claims.json"):
            records.append(
                (
                    {"task": "claim_support", **compact_claim(claim)},
                    {
                        "case_id": claim["case_id"],
                        "claim_id": claim["claim_id"],
                    },
                )
            )
    return records


def intent_records(case_dirs: list[Path]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    records = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        for action in MVP.load_json(case_dir / "acquisition_actions.json"):
            if MVP.is_stop_action(action):
                continue
            records.append(
                (
                    {
                        "task": "public_intent",
                        "action_type": action.get("action_type", ""),
                        "acquisition_channel": MVP.acquisition_channel(action),
                        "target": action.get("target", {}),
                        "natural_language_request": action.get(
                            "natural_language_request", ""
                        ),
                        "candidate_nodes": public_nodes(config),
                        "cti_edges": public_edges(config),
                    },
                    {
                        "case_id": config["case_id"],
                        "action_id": action["action_id"],
                        "intended_cti_node_ids": action.get(
                            "intended_cti_node_ids", []
                        ),
                        "recoverable_claim_ids": action.get(
                            "recoverable_claim_ids", []
                        ),
                    },
                )
            )
    return records


def sampled_visible_sets(
    config: dict[str, Any],
    claims: list[dict[str, Any]],
    rng: random.Random,
    maximum: int = 12,
) -> list[tuple[frozenset[str], str, tuple[str, float, int]]]:
    all_ids = {claim["claim_id"] for claim in claims}
    unique: dict[frozenset[str], tuple[str, float, int]] = {}
    for strategy, intensity, seed in MVP.experiment_conditions(config):
        hidden = MVP.build_hidden_claims(config, claims, strategy, seed, intensity)
        visible = frozenset(all_ids - hidden)
        unique.setdefault(visible, (strategy, intensity, seed))

    strata: dict[str, list[tuple[frozenset[str], str, tuple[str, float, int]]]] = {}
    for visible, condition in unique.items():
        granularity = MVP.supportable_granularity(config, set(visible))
        strata.setdefault(granularity, []).append((visible, granularity, condition))
    for rows in strata.values():
        rng.shuffle(rows)

    selected: list[tuple[frozenset[str], str, tuple[str, float, int]]] = []
    labels = sorted(strata, key=lambda label: MVP.granularity_index(config, label))
    while len(selected) < maximum and any(strata[label] for label in labels):
        for label in labels:
            if strata[label] and len(selected) < maximum:
                selected.append(strata[label].pop())
    return selected


def granularity_records(
    case_dirs: list[Path], rng: random.Random
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    records = []
    for case_dir in case_dirs:
        config = MVP.load_json(case_dir / "case_config.json")
        claims = MVP.load_json(case_dir / "evidence_claims.json")
        claim_map = {claim["claim_id"]: claim for claim in claims}
        for visible, granularity, condition in sampled_visible_sets(
            config, claims, rng
        ):
            records.append(
                (
                    {
                        "task": "granularity_judgment",
                        "visible_claims": [
                            compact_claim(claim_map[claim_id])
                            for claim_id in sorted(visible)
                        ],
                        "cti_nodes": public_nodes(config),
                        "cti_edges": public_edges(config),
                        "allowed_labels": [
                            "G0_unknown",
                            "G1_technique",
                            "G2_tactic_intent",
                            "G3_campaign",
                        ],
                    },
                    {
                        "case_id": config["case_id"],
                        "visible_claim_ids": sorted(visible),
                        "computed_granularity": granularity,
                        "sampling_condition": {
                            "mask_strategy": condition[0],
                            "mask_intensity": condition[1],
                            "seed": condition[2],
                        },
                    },
                )
            )
    return records


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_template(path: Path, blind_ids: list[str], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["blind_id", *fields])
        writer.writeheader()
        for blind_id in blind_ids:
            writer.writerow({"blind_id": blind_id})


def build_packets(cases_root: Path, output_dir: Path, seed: int = 20260711) -> dict[str, Any]:
    case_dirs = resolve_cases(cases_root)
    rng = random.Random(seed)
    claim_items, claim_key = shuffled_blind_items(
        "claim", claim_records(case_dirs), rng
    )
    intent_items, intent_key = shuffled_blind_items(
        "intent", intent_records(case_dirs), rng
    )
    granularity_items, granularity_key = shuffled_blind_items(
        "granularity", granularity_records(case_dirs, rng), rng
    )

    public_dir = output_dir / "public"
    write_jsonl(public_dir / "claim_items.jsonl", claim_items)
    write_jsonl(public_dir / "intent_items.jsonl", intent_items)
    write_jsonl(public_dir / "granularity_items.jsonl", granularity_items)

    templates = {
        "claim_annotations.csv": (
            claim_items,
            ["reviewed", "support_label", "source_pointer_valid", "annotator_notes"],
        ),
        "intent_annotations.csv": (
            intent_items,
            ["reviewed", "selected_node_ids_pipe", "annotator_notes"],
        ),
        "granularity_annotations.csv": (
            granularity_items,
            ["reviewed", "granularity_label", "key_missing_evidence", "annotator_notes"],
        ),
    }
    for annotator in ("annotator_A", "annotator_B"):
        for filename, (items, fields) in templates.items():
            write_template(
                output_dir / annotator / filename,
                [item["blind_id"] for item in items],
                fields,
            )

    admin_key = {
        "claim": claim_key,
        "intent": intent_key,
        "granularity": granularity_key,
    }
    MVP.write_json(output_dir / "admin" / "admin_key.json", admin_key)
    summary = {
        "seed": seed,
        "independent_case_count": len(case_dirs),
        "claim_item_count": len(claim_items),
        "intent_item_count": len(intent_items),
        "granularity_item_count": len(granularity_items),
        "human_labels_present": False,
    }
    MVP.write_json(output_dir / "packet_manifest.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build blind C07-C10 annotation packets.")
    parser.add_argument(
        "--cases-root",
        type=Path,
        default=ROOT / "09-experiments" / "real_cases",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "09-experiments" / "annotation" / "c07_c10_v0.1",
    )
    parser.add_argument("--seed", type=int, default=20260711)
    args = parser.parse_args()
    summary = build_packets(args.cases_root, args.output_dir, args.seed)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
