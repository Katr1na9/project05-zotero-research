#!/usr/bin/env python3
"""Build a non-destructive, leakage-controlled Round 2 annotation packet.

The builder imports the existing future-round sanitization path, injects a
prospectively locked mixture of correct and deliberately wrong source
pointers, and gives annotators A/B distinct package metadata and order.  It
never reads or writes human labels and refuses to overwrite a non-empty output
directory.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT_ROOT = ROOT / "09-experiments"
BASE_BUILDER_PATH = Path(__file__).with_name("build_annotation_packets.py")
DEFAULT_CASES_ROOT = EXPERIMENT_ROOT / "real_cases"
DEFAULT_OUTPUT_DIR = EXPERIMENT_ROOT / "annotation" / "c07_c11_round2_v0.1"
PROTOCOL_PATH = (
    EXPERIMENT_ROOT
    / "annotation"
    / "protocols"
    / "c07_c11_round2-codebook-v0.1.md"
)
PREDECESSOR_DIR = EXPERIMENT_ROOT / "annotation" / "c07_c11_v0.2"
PACKET_VERSION = "c07_c11_round2_v0.1"
DESIGN_SEED = 20260714
CREATED_UTC = "2026-07-14T02:00:00Z"
CASE_PREFIXES = ("C07", "C08", "C09", "C10", "C11")
PACKAGE_SPECS = {
    "A": {
        "package_id": "c07_c11_round2_v0.1_A",
        "seed": 20260715,
        "issued_utc": "2026-07-14T02:01:00Z",
    },
    "B": {
        "package_id": "c07_c11_round2_v0.1_B",
        "seed": 20260716,
        "issued_utc": "2026-07-14T02:02:00Z",
    },
}
NEGATIVE_COUNTS_BY_ARTIFACT = {
    "darpa_e5_R04_pidsmaker_event_table": 4,
    "darpa_e5_R05_pidsmaker_event_table": 2,
    "darpa_optc_R06_sysclient0201_ecar_window": 2,
    "darpa_optc_R07_sysclient0351_ecar_window": 2,
    "otrf_apt29_day1_host_events": 4,
}
TASK_FILES = {
    "claim": "claim_items.jsonl",
    "intent": "intent_items.jsonl",
    "granularity": "granularity_items.jsonl",
}
TEMPLATE_SPECS = {
    "claim": (
        "claim_annotations.csv",
        ["reviewed", "support_label", "source_pointer_valid", "annotator_notes"],
    ),
    "intent": (
        "intent_annotations.csv",
        ["reviewed", "selected_node_ids_pipe", "annotator_notes"],
    ),
    "granularity": (
        "granularity_annotations.csv",
        ["reviewed", "granularity_label", "key_missing_evidence", "annotator_notes"],
    ),
}


def _load_base_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_round2_base_builder", BASE_BUILDER_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load annotation builder from {BASE_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load_base_builder()


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def derived_seed(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}|{label}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def stable_blind_id(task: str, admin: dict[str, Any]) -> str:
    if task == "claim":
        identity = {key: admin[key] for key in ("case_id", "claim_id")}
        prefix = "R2-CLM"
    elif task == "intent":
        identity = {key: admin[key] for key in ("case_id", "action_id")}
        prefix = "R2-INT"
    elif task == "granularity":
        identity = {
            key: admin[key]
            for key in ("case_id", "visible_claim_ids", "sampling_condition")
        }
        prefix = "R2-GRN"
    else:
        raise ValueError(f"Unsupported annotation task: {task}")
    payload = f"{PACKET_VERSION}|{task}|{canonical_json(identity)}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()
    return f"{prefix}-{digest[:12]}"


def materialize_records(
    task: str,
    records: list[tuple[dict[str, Any], dict[str, Any]]],
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    public: list[dict[str, Any]] = []
    admin_key: dict[str, dict[str, Any]] = {}
    for item, admin in records:
        blind_id = stable_blind_id(task, admin)
        if blind_id in admin_key:
            raise ValueError(f"Round 2 blind-ID collision: {blind_id}")
        public.append({"blind_id": blind_id, **copy.deepcopy(item)})
        admin_key[blind_id] = copy.deepcopy(admin)
    public.sort(key=lambda row: row["blind_id"])
    return public, admin_key


def inject_pointer_controls(
    records: list[tuple[dict[str, Any], dict[str, Any]]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    prepared = [(copy.deepcopy(item), copy.deepcopy(admin)) for item, admin in records]
    groups: dict[str, list[int]] = {}
    for index, (item, _) in enumerate(prepared):
        pointer = item.get("source_pointer", {})
        artifact_id = str(pointer.get("artifact_id", ""))
        if not artifact_id:
            raise ValueError(f"Claim has no source artifact: {item}")
        groups.setdefault(artifact_id, []).append(index)

    if set(groups) != set(NEGATIVE_COUNTS_BY_ARTIFACT):
        raise ValueError(
            "Round 2 source artifacts differ from the locked design: "
            f"{sorted(groups)}"
        )

    for artifact_id, indices in sorted(groups.items()):
        negative_count = NEGATIVE_COUNTS_BY_ARTIFACT[artifact_id]
        if negative_count < 2 or negative_count > len(indices):
            raise ValueError(f"Invalid negative count for {artifact_id}")
        rng = random.Random(derived_seed(DESIGN_SEED, f"pointer|{artifact_id}"))
        selected = list(indices)
        rng.shuffle(selected)
        selected = selected[:negative_count]
        donors = selected[1:] + selected[:1]

        originals = {
            index: copy.deepcopy(prepared[index][0]["source_pointer"])
            for index in indices
        }
        for index in indices:
            admin = prepared[index][1]
            admin["original_source_pointer"] = originals[index]
            admin["presented_source_pointer"] = originals[index]
            admin["source_pointer_condition"] = "correct"
            admin["pointer_donor_case_id"] = None
            admin["pointer_donor_claim_id"] = None

        for target_index, donor_index in zip(selected, donors):
            target_item, target_admin = prepared[target_index]
            _, donor_admin = prepared[donor_index]
            donor_pointer = originals[donor_index]
            if canonical_json(donor_pointer) == canonical_json(originals[target_index]):
                raise ValueError("Pointer-control rotation produced a fixed point")
            if donor_pointer.get("artifact_id") != artifact_id:
                raise ValueError("Pointer-control donor crossed an artifact boundary")
            target_item["source_pointer"] = copy.deepcopy(donor_pointer)
            target_admin["presented_source_pointer"] = copy.deepcopy(donor_pointer)
            target_admin["source_pointer_condition"] = "deliberately_wrong"
            target_admin["pointer_donor_case_id"] = donor_admin["case_id"]
            target_admin["pointer_donor_claim_id"] = donor_admin["claim_id"]

    presented = [
        canonical_json(item["source_pointer"])
        for item, _ in prepared
    ]
    if len(presented) != len(set(presented)):
        raise ValueError("Presented Round 2 source pointers are not one-to-one")
    return prepared


def package_rows(
    rows: list[dict[str, Any]],
    task: str,
    annotator_code: str,
    spec: dict[str, Any],
) -> list[dict[str, Any]]:
    packaged = [
        {
            "package_id": spec["package_id"],
            "packet_version": PACKET_VERSION,
            "annotator_code": annotator_code,
            "issued_utc": spec["issued_utc"],
            **copy.deepcopy(row),
        }
        for row in rows
    ]
    random.Random(derived_seed(int(spec["seed"]), task)).shuffle(packaged)
    return packaged


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    BASE.write_jsonl(path, rows)


def write_template(
    path: Path,
    ordered_blind_ids: list[str],
    fields: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["blind_id", *fields],
            lineterminator="\n",
        )
        writer.writeheader()
        for blind_id in ordered_blind_ids:
            writer.writerow({"blind_id": blind_id})


def ensure_new_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Round 2 output directory is non-empty; refusing overwrite: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)


def public_source_hashes(case_dirs: list[Path]) -> dict[str, dict[str, str]]:
    return {
        case_dir.name: {
            filename: sha256_file(case_dir / filename)
            for filename in BASE.MVP.CASE_FILENAMES
        }
        for case_dir in case_dirs
    }


def build(
    cases_root: Path = DEFAULT_CASES_ROOT,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    ensure_new_output(output_dir)
    case_dirs = BASE.resolve_cases(cases_root, CASE_PREFIXES)

    claim_records = inject_pointer_controls(
        BASE.claim_records(case_dirs, sanitize=True)
    )
    intent_records = BASE.intent_records(case_dirs)
    granularity_records = BASE.granularity_records(
        case_dirs,
        random.Random(derived_seed(DESIGN_SEED, "granularity_sampling")),
        sanitize=True,
    )
    canonical: dict[str, list[dict[str, Any]]] = {}
    admin_key: dict[str, dict[str, dict[str, Any]]] = {}
    for task, records in (
        ("claim", claim_records),
        ("intent", intent_records),
        ("granularity", granularity_records),
    ):
        canonical[task], admin_key[task] = materialize_records(task, records)

    # This canonical public view is the shared ID namespace used by the
    # agreement analyzer and source-excerpt builder. Annotators receive only
    # their package-specific copy below.
    for task, filename in TASK_FILES.items():
        write_jsonl(output_dir / "public" / filename, canonical[task])
    write_json(output_dir / "admin" / "admin_key.json", admin_key)

    package_manifests: dict[str, Any] = {}
    package_orders: dict[str, dict[str, list[str]]] = {}
    for annotator_code, spec in PACKAGE_SPECS.items():
        annotator_dir = output_dir / f"annotator_{annotator_code}"
        public_hashes: dict[str, str] = {}
        template_hashes: dict[str, str] = {}
        package_orders[annotator_code] = {}
        for task, filename in TASK_FILES.items():
            rows = package_rows(canonical[task], task, annotator_code, spec)
            public_path = annotator_dir / "public" / filename
            write_jsonl(public_path, rows)
            ordered_ids = [row["blind_id"] for row in rows]
            package_orders[annotator_code][task] = ordered_ids
            template_name, fields = TEMPLATE_SPECS[task]
            template_path = annotator_dir / template_name
            write_template(template_path, ordered_ids, fields)
            public_hashes[filename] = sha256_file(public_path)
            template_hashes[template_name] = sha256_file(template_path)

        metadata = {
            "package_id": spec["package_id"],
            "packet_version": PACKET_VERSION,
            "annotator_code": annotator_code,
            "seed": spec["seed"],
            "issued_utc": spec["issued_utc"],
            "public_file_sha256": public_hashes,
            "annotation_template_sha256": template_hashes,
            "human_labels_present": False,
        }
        write_json(annotator_dir / "PACKAGE-METADATA.json", metadata)
        package_manifests[annotator_code] = metadata

    for task in TASK_FILES:
        if set(package_orders["A"][task]) != set(package_orders["B"][task]):
            raise ValueError(f"A/B item sets differ for {task}")
        if package_orders["A"][task] == package_orders["B"][task]:
            raise ValueError(f"A/B randomized order unexpectedly matches for {task}")

    # Adjudication remains blank until A/B are frozen; item IDs are supplied
    # only to keep the analysis interface stable.
    for task, (template_name, fields) in TEMPLATE_SPECS.items():
        write_template(
            output_dir / "adjudicator" / template_name,
            [row["blind_id"] for row in canonical[task]],
            fields,
        )

    pointer_conditions = [
        row["source_pointer_condition"] for row in admin_key["claim"].values()
    ]
    condition_counts = {
        condition: pointer_conditions.count(condition)
        for condition in ("correct", "deliberately_wrong")
    }
    if condition_counts != {"correct": 13, "deliberately_wrong": 14}:
        raise ValueError(f"Unexpected pointer-control balance: {condition_counts}")

    canonical_hashes = {
        filename: sha256_file(output_dir / "public" / filename)
        for filename in TASK_FILES.values()
    }
    predecessor_manifest = PREDECESSOR_DIR / "packet_manifest.json"
    manifest = {
        "packet_version": PACKET_VERSION,
        "status": "prospective_locked_awaiting_two_independent_annotations",
        "created_utc": CREATED_UTC,
        "design_seed": DESIGN_SEED,
        "case_prefixes": list(CASE_PREFIXES),
        "independent_case_count": len(case_dirs),
        "statistical_unit": "case_or_attack_chain",
        "within_case_repeated_measures": [
            "claim_items",
            "action_items",
            "mask_strategy",
            "mask_intensity",
            "seed",
        ],
        "item_counts": {
            task: len(rows) for task, rows in canonical.items()
        },
        "human_labels_present": False,
        "annotation_status": "awaiting_annotations",
        "public_views_sanitized": True,
        "pointer_control": {
            "assignment": "locked_within_artifact_permutation",
            "condition_counts": condition_counts,
            "cross_artifact_swaps": 0,
            "source_excerpts_required_for_presented_pointer": True,
        },
        "intent_rule": (
            "Label only nodes directly targeted by the action request; do not "
            "label upstream, downstream, adjacent, or merely possible-benefit nodes."
        ),
        "protocol": {
            "path": PROTOCOL_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(PROTOCOL_PATH),
        },
        "predecessor": {
            "packet_version": "c07_c11_v0.2",
            "read_only": True,
            "manifest_sha256": sha256_file(predecessor_manifest),
        },
        "canonical_public_file_sha256": canonical_hashes,
        "source_case_file_sha256": public_source_hashes(case_dirs),
        "packages": package_manifests,
        "package_invariants": {
            "same_blind_id_sets": True,
            "different_package_ids": True,
            "different_issued_utc": True,
            "different_randomized_order_for_every_task": True,
            "different_public_file_hashes": True,
        },
        "no_overwrite": True,
    }
    write_json(output_dir / "packet_manifest.json", manifest)
    (output_dir / "README.md").write_text(
        "# C07-C11 annotation Round 2 v0.1\n\n"
        "状态：prospective locked，等待两名真实独立标注者；当前无人工标签。\n\n"
        "- 只向标注者 A 分发 `annotator_A/`，只向 B 分发 `annotator_B/`。\n"
        "- `public/` 是一致性分析和来源摘录构建器使用的共享盲 ID 视图，"
        "不是标注者分发包。\n"
        "- `admin/` 含负例条件与真实映射，受 `.gitignore` 保护，严禁分发。\n"
        "- `adjudicator/` 当前为空；只有 A/B 首轮冻结后才允许生成分歧包。\n"
        "- 前序 `c07_c11_v0.2` 保持只读，Round 2 不覆盖任何旧标签或结果。\n"
        "- Codebook：`../protocols/c07_c11_round2-codebook-v0.1.md`。\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build leakage-controlled C07-C11 annotation Round 2 packets."
    )
    parser.add_argument("--cases-root", type=Path, default=DEFAULT_CASES_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    manifest = build(args.cases_root.resolve(), args.output_dir.resolve())
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
