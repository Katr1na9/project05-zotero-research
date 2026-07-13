#!/usr/bin/env python3
"""Ingest completed Project05 blind annotations with an auditable repair log."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


TASK_FILES = {
    "claim": "claim_annotations.csv",
    "intent": "intent_annotations.csv",
    "granularity": "granularity_annotations.csv",
}
EXPECTED_FIELDS = {
    "claim": [
        "blind_id",
        "reviewed",
        "support_label",
        "source_pointer_valid",
        "annotator_notes",
    ],
    "intent": [
        "blind_id",
        "reviewed",
        "selected_node_ids_pipe",
        "annotator_notes",
    ],
    "granularity": [
        "blind_id",
        "reviewed",
        "granularity_label",
        "key_missing_evidence",
        "annotator_notes",
    ],
}
REVIEWED_VALUES = {"yes", "y", "true", "1"}
CLAIM_LABELS = {"0_unsupported", "1_partial", "2_direct", "U_unassessable"}
POINTER_LABELS = {"yes", "no", "unassessable"}
GRANULARITY_LABELS = {
    "G0_unknown",
    "G1_technique",
    "G2_tactic_intent",
    "G3_campaign",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def intent_candidates(annotation_dir: Path) -> dict[str, set[str]]:
    path = annotation_dir / "public" / "intent_items.jsonl"
    return {
        item["blind_id"]: {node["node_id"] for node in item["candidate_nodes"]}
        for item in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def read_csv(
    path: Path,
    task: str,
    role: str,
    annotation_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    repairs: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        raw_rows = list(csv.reader(handle))
    if not raw_rows or raw_rows[0] != EXPECTED_FIELDS[task]:
        raise ValueError(
            f"Unexpected fields in {path}: {raw_rows[0] if raw_rows else None!r}"
        )

    rows: list[dict[str, str]] = []
    expected = len(EXPECTED_FIELDS[task])
    candidates = intent_candidates(annotation_dir) if task == "intent" else {}
    for line_number, values in enumerate(raw_rows[1:], start=2):
        original = list(values)
        if len(values) > expected:
            values = [*values[: expected - 1], ",".join(values[expected - 1 :])]
            repairs.append(
                {
                    "role": role,
                    "task": task,
                    "blind_id": values[0],
                    "field": EXPECTED_FIELDS[task][-1],
                    "from": f"{len(original)} CSV fields",
                    "to": f"{expected} CSV fields",
                    "reason": "Unquoted commas were joined back into the final free-text field.",
                }
            )
        elif len(values) < expected:
            if task != "intent" or len(values) != 3:
                raise ValueError(
                    f"Cannot repair field count at {path}:{line_number}: {values!r}"
                )
            blind_id, reviewed, payload = values
            selected = ""
            note = ""
            if reviewed.startswith("yes."):
                selected = reviewed.removeprefix("yes.")
                reviewed = "yes"
                note = payload
            elif reviewed.startswith("yesN"):
                selected = reviewed.removeprefix("yes")
                reviewed = "yes"
                note = payload
            else:
                matches = [
                    node
                    for node in candidates.get(blind_id, set())
                    if payload.startswith(node)
                ]
                if len(matches) != 1:
                    raise ValueError(
                        f"Intent field boundary is not unique at {path}:{line_number}: {values!r}"
                    )
                selected = matches[0]
                note = payload[len(selected) :].lstrip("，,.;； ")
            values = [blind_id, reviewed, selected, note]
            repairs.append(
                {
                    "role": role,
                    "task": task,
                    "blind_id": blind_id,
                    "field": "CSV field boundary",
                    "from": f"{len(original)} CSV fields",
                    "to": f"yes,{selected},<preserved note>",
                    "reason": "The missing delimiter was recovered from a unique frozen candidate-node prefix.",
                }
            )
        rows.append(
            {
                key: (value or "").strip()
                for key, value in zip(EXPECTED_FIELDS[task], values)
            }
        )
    return rows, repairs


def public_ids(annotation_dir: Path, task: str) -> set[str]:
    path = annotation_dir / "public" / f"{task}_items.jsonl"
    return {
        json.loads(line)["blind_id"]
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def normalize_rows(
    role: str,
    task: str,
    rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    repairs: list[dict[str, str]] = []
    for row in rows:
        blind_id = row["blind_id"]
        if task == "claim" and row["support_label"] == "2_directl":
            repairs.append(
                {
                    "role": role,
                    "task": task,
                    "blind_id": blind_id,
                    "field": "support_label",
                    "from": "2_directl",
                    "to": "2_direct",
                    "reason": "Unambiguous one-character suffix typo outside the frozen codebook.",
                }
            )
            row["support_label"] = "2_direct"

        if task == "intent" and row["reviewed"].startswith("yes."):
            original = row["reviewed"]
            selected = original.removeprefix("yes.")
            note = row["selected_node_ids_pipe"]
            row["reviewed"] = "yes"
            row["selected_node_ids_pipe"] = selected
            row["annotator_notes"] = note
            repairs.append(
                {
                    "role": role,
                    "task": task,
                    "blind_id": blind_id,
                    "field": "reviewed/selected_node_ids_pipe/annotator_notes",
                    "from": original,
                    "to": f"yes,{selected}",
                    "reason": "A period replaced the CSV delimiter; the displaced third field is preserved as the note.",
                }
            )
        elif task == "intent" and row["reviewed"].startswith("yesN"):
            original = row["reviewed"]
            selected = original.removeprefix("yes")
            note = row["selected_node_ids_pipe"]
            row["reviewed"] = "yes"
            row["selected_node_ids_pipe"] = selected
            row["annotator_notes"] = note
            repairs.append(
                {
                    "role": role,
                    "task": task,
                    "blind_id": blind_id,
                    "field": "reviewed/selected_node_ids_pipe/annotator_notes",
                    "from": original,
                    "to": f"yes,{selected}",
                    "reason": "A CSV delimiter was omitted; the displaced third field is preserved as the note.",
                }
            )
    return rows, repairs


def validate_rows(annotation_dir: Path, task: str, rows: list[dict[str, str]]) -> None:
    ids = [row["blind_id"] for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != public_ids(annotation_dir, task):
        raise ValueError(f"{task}: blind IDs do not match the frozen public packet")
    incomplete = [
        row["blind_id"]
        for row in rows
        if row["reviewed"].casefold() not in REVIEWED_VALUES
    ]
    if incomplete:
        raise ValueError(f"{task}: unreviewed rows remain: {incomplete}")
    if task == "claim":
        for row in rows:
            if row["support_label"] not in CLAIM_LABELS:
                raise ValueError(f"Invalid claim label: {row}")
            if row["source_pointer_valid"] not in POINTER_LABELS:
                raise ValueError(f"Invalid source-pointer label: {row}")
    elif task == "granularity":
        for row in rows:
            if row["granularity_label"] not in GRANULARITY_LABELS:
                raise ValueError(f"Invalid granularity label: {row}")
    else:
        public_path = annotation_dir / "public" / "intent_items.jsonl"
        candidates = {
            item["blind_id"]: {node["node_id"] for node in item["candidate_nodes"]}
            for item in (
                json.loads(line)
                for line in public_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        }
        for row in rows:
            selected = {
                value.strip()
                for value in row["selected_node_ids_pipe"].split("|")
                if value.strip()
            }
            unknown = selected - candidates[row["blind_id"]]
            if unknown:
                raise ValueError(
                    f"intent: {row['blind_id']} contains unknown nodes: {sorted(unknown)}"
                )


def write_csv(path: Path, task: str, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=EXPECTED_FIELDS[task],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def ingest(
    annotation_dir: Path,
    annotator_a_dir: Path,
    annotator_b_dir: Path,
) -> dict[str, Any]:
    source_dirs = {
        "annotator_A": annotator_a_dir,
        "annotator_B": annotator_b_dir,
    }
    manifest: dict[str, Any] = {
        "round": "c07_c11_v0.2_round1",
        "status": "imported_pending_agreement_and_adjudication",
        "source_files": {},
        "normalizations": [],
        "provenance_flags": [],
    }
    source_hashes: dict[str, dict[str, str]] = {task: {} for task in TASK_FILES}
    for role, source_dir in source_dirs.items():
        manifest["source_files"][role] = {}
        for task, filename in TASK_FILES.items():
            source = source_dir / filename
            source_hash = sha256(source)
            source_hashes[task][role] = source_hash
            rows, structural_repairs = read_csv(
                source,
                task,
                role,
                annotation_dir,
            )
            rows, label_repairs = normalize_rows(role, task, rows)
            validate_rows(annotation_dir, task, rows)
            destination = annotation_dir / role / filename
            write_csv(destination, task, rows)
            manifest["normalizations"].extend(structural_repairs)
            manifest["normalizations"].extend(label_repairs)
            manifest["source_files"][role][filename] = {
                "sha256": source_hash,
                "rows": len(rows),
                "normalized_sha256": sha256(destination),
            }

    for task, hashes in source_hashes.items():
        if hashes["annotator_A"] == hashes["annotator_B"]:
            manifest["provenance_flags"].append(
                {
                    "task": task,
                    "flag": "annotator_source_files_are_byte_identical",
                    "interpretation": (
                        "Agreement can be computed, but independent completion must be "
                        "confirmed before this task is reported as independent double-blind evidence."
                    ),
                }
            )

    output = annotation_dir / "annotation_intake_manifest.json"
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest completed blind annotations.")
    parser.add_argument("annotation_dir", type=Path)
    parser.add_argument("--annotator-a-dir", type=Path, required=True)
    parser.add_argument("--annotator-b-dir", type=Path, required=True)
    args = parser.parse_args()
    result = ingest(
        args.annotation_dir,
        args.annotator_a_dir,
        args.annotator_b_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
