#!/usr/bin/env python3
"""Build a blind adjudication bundle containing only A/B disagreement items."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[2]
CALIBRATION_PATH = Path(__file__).with_name("analyze_annotation_calibration.py")
TASK_FILES = {
    "claim": "claim_annotations.csv",
    "intent": "intent_annotations.csv",
    "granularity": "granularity_annotations.csv",
}
PUBLIC_FILES = {
    "claim": "claim_items.jsonl",
    "intent": "intent_items.jsonl",
    "granularity": "granularity_items.jsonl",
}


def load_calibration_module() -> Any:
    spec = importlib.util.spec_from_file_location(
        "project05_annotation_calibration_for_bundle",
        CALIBRATION_PATH,
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load calibration module from {CALIBRATION_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CALIBRATION = load_calibration_module()
AGREEMENT = CALIBRATION.AGREEMENT


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def disagreements(annotation_dir: Path, task: str) -> list[str]:
    filename = TASK_FILES[task]
    left = AGREEMENT.read_rows(annotation_dir / "annotator_A" / filename)
    right = AGREEMENT.read_rows(annotation_dir / "annotator_B" / filename)
    if set(left) != set(right):
        raise ValueError(f"{task}: A/B blind IDs differ")
    pending: list[str] = []
    for blind_id in sorted(left):
        if not CALIBRATION.is_reviewed(left[blind_id]) or not CALIBRATION.is_reviewed(
            right[blind_id]
        ):
            raise ValueError(f"{task}: unreviewed A/B item {blind_id}")
        if CALIBRATION.normalized_label(task, left[blind_id]) != CALIBRATION.normalized_label(
            task, right[blind_id]
        ):
            pending.append(blind_id)
    return pending


def read_public(path: Path) -> dict[str, dict[str, Any]]:
    return {
        item["blind_id"]: item
        for item in (
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }


def write_task_files(
    annotation_dir: Path,
    output_dir: Path,
    task: str,
    blind_ids: list[str],
) -> dict[str, Any]:
    public = read_public(annotation_dir / "public" / PUBLIC_FILES[task])
    public_output = output_dir / "public" / PUBLIC_FILES[task]
    public_output.parent.mkdir(parents=True, exist_ok=True)
    public_output.write_text(
        "".join(
            json.dumps(public[blind_id], ensure_ascii=False) + "\n"
            for blind_id in blind_ids
        ),
        encoding="utf-8",
    )

    template_path = annotation_dir / "adjudicator" / TASK_FILES[task]
    with template_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        template = {row["blind_id"]: row for row in reader}
    annotation_output = output_dir / "annotations" / TASK_FILES[task]
    annotation_output.parent.mkdir(parents=True, exist_ok=True)
    with annotation_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for blind_id in blind_ids:
            row = {field: "" for field in fields}
            row["blind_id"] = blind_id
            if blind_id not in template:
                raise ValueError(f"{task}: missing adjudicator template row {blind_id}")
            writer.writerow(row)

    return {
        "item_count": len(blind_ids),
        "blind_ids": blind_ids,
        "public_file": str(public_output.relative_to(output_dir)),
        "public_sha256": sha256(public_output),
        "annotation_file": str(annotation_output.relative_to(output_dir)),
        "annotation_sha256": sha256(annotation_output),
    }


def build_bundle(annotation_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_manifest = {}
    for task in TASK_FILES:
        task_manifest[task] = write_task_files(
            annotation_dir,
            output_dir,
            task,
            disagreements(annotation_dir, task),
        )

    instructions = """# C07-C11 第三人盲裁决说明

状态：仅包含 A/B 首轮分歧项。

1. 只依据 `public/` 中的公开题目填写 `annotations/` 中同名 CSV。
2. 每完成一行，将 `reviewed` 填为 `yes`。
3. 不索取或查看 A/B 标签、管理员 key、recoverable claims、规划结果或论文案例结论。
4. Claim 使用冻结标签 `2_direct`、`1_partial`、`0_unsupported` 或 `U_unassessable`。
5. Intent 允许空集合，多节点以 `|` 分隔，只选择公开候选节点。
6. 本包不含粒度分歧；粒度任务无须填写。
7. 返回 `annotations/claim_annotations.csv` 和 `annotations/intent_annotations.csv`。
"""
    instructions_path = output_dir / "ADJUDICATOR-INSTRUCTIONS.md"
    instructions_path.write_text(instructions, encoding="utf-8")

    manifest = {
        "bundle": "c07_c11_v0.2_adjudication_v0.1",
        "status": "awaiting_third_adjudicator",
        "task_manifest": task_manifest,
        "total_disagreement_items": sum(
            item["item_count"] for item in task_manifest.values()
        ),
        "exclusions": [
            "annotator_A labels",
            "annotator_B labels",
            "admin key",
            "recoverable claim sets",
            "planner outputs",
        ],
        "instructions_sha256": sha256(instructions_path),
    }
    manifest_path = output_dir / "bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    zip_path = output_dir.parent / f"{output_dir.name}.zip"
    with ZipFile(zip_path, "w", ZIP_DEFLATED) as archive:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(output_dir.parent))
    manifest["local_zip"] = {
        "path": str(zip_path),
        "sha256": sha256(zip_path),
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the third-adjudicator bundle.")
    parser.add_argument("annotation_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = build_bundle(args.annotation_dir, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
