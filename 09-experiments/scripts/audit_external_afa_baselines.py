#!/usr/bin/env python3
"""Audit pinned external AFA sources and Project05 action-family coverage."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCK = (
    ROOT
    / "09-experiments"
    / "external_baselines"
    / "external_baseline_lock_v0.1.json"
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def git_head(path: Path) -> str | None:
    if not (path / ".git").is_dir():
        return None
    completed = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def discover_actions(case_root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    for case_dir in sorted(case_root.iterdir()):
        if not case_dir.is_dir() or not case_dir.name.startswith(
            ("C07-", "C08-", "C09-", "C10-", "C11-", "C12-")
        ):
            continue
        for action in load_json(case_dir / "acquisition_actions.json"):
            counts[action["action_type"]] += 1
    return counts


def audit(lock_path: Path, clone_root: Path | None) -> dict[str, Any]:
    lock = load_json(lock_path)
    action_counts = discover_actions(
        ROOT / "09-experiments" / "real_cases"
    )
    family_mapping = lock["winregrl_action_family_mapping"]
    unmapped = sorted(set(action_counts) - set(family_mapping))

    source_checks: list[dict[str, Any]] = []
    for baseline in lock["baselines"]:
        check: dict[str, Any] = {
            "baseline_id": baseline["baseline_id"],
            "expected_commit": baseline["repository_commit"],
            "local_checkout_present": False,
            "commit_matches": None,
            "archive_matches": None,
        }
        local_directory = baseline.get("local_directory")
        if clone_root is not None and local_directory:
            checkout = clone_root / local_directory
            actual_head = git_head(checkout)
            check["local_checkout_present"] = actual_head is not None
            check["actual_commit"] = actual_head
            check["commit_matches"] = actual_head == baseline["repository_commit"]
            archive_path = baseline.get("archive_path")
            if archive_path and (checkout / archive_path).is_file():
                actual_hash = sha256(checkout / archive_path)
                check["actual_archive_sha256"] = actual_hash
                check["archive_matches"] = actual_hash == baseline["archive_sha256"]
        source_checks.append(check)

    checked_sources = [
        item for item in source_checks if item["local_checkout_present"]
    ]
    # A source-verification gate must not pass vacuously when nothing was checked
    # (e.g. --clone-root omitted): verifying zero sources is not a pass.
    sources_pass = bool(checked_sources) and all(
        item["commit_matches"] is True
        and item["archive_matches"] is not False
        for item in checked_sources
    )
    return {
        "audit_id": "project05-external-afa-source-and-interface-audit-v0.1",
        "lock_file": lock_path.relative_to(ROOT).as_posix(),
        "source_checks": source_checks,
        "source_gate": {
            "checked_source_count": len(checked_sources),
            "pass": sources_pass,
        },
        "project05_action_inventory": dict(sorted(action_counts.items())),
        "winregrl_action_family_mapping": {
            action_type: family_mapping.get(action_type)
            for action_type in sorted(action_counts)
        },
        "action_family_gate": {
            "mapped_action_type_count": len(action_counts) - len(unmapped),
            "total_action_type_count": len(action_counts),
            "unmapped_action_types": unmapped,
            "pass": not unmapped,
        },
        "comparability_decision": lock["decision"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit pinned external AFA sources and action mappings."
    )
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--clone-root",
        type=Path,
        help="Optional parent containing pinned external repository checkouts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            ROOT
            / "09-experiments"
            / "results"
            / "external_afa_baseline_audit_v0.1"
            / "audit.json"
        ),
    )
    args = parser.parse_args()
    result = audit(args.lock, args.clone_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
