"""Non-Bypass entry for one separately authorized LO2v2 bounded audit.

This file is inert unless executed explicitly. It never offers plan mode and
does not alter or bypass any host execution policy. A committed attempt-3
authority must pin this exact file before it can hand off to the pinned audit
script in the same CPython process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import runpy
import sys
from pathlib import Path
from typing import Sequence


TARGET_ID = "lo2v2_index_json"
EXTERNAL_SUPERVISOR_SECONDS = 300

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_SCRIPT = REPO_ROOT / "datasets/llm/audit_lo2v2_index_v0_1.py"
AUDIT_CONTRACT = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-json-reader-privacy-notice-schema-"
    "manifest-lineage-label-v1-v2-pointer-audit-contract-v0.1-20260723.json"
)
READER_AMENDMENT = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-json-reader-tool-amendment-"
    "v0.1-20260723.json"
)
ATTEMPT_1_FAILURE = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-attempt-1-launcher-"
    "failure-result-v0.1-20260723.json"
)
ATTEMPT_2_FAILURE = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-attempt-2-launcher-"
    "failure-result-v0.1-20260723.json"
)
AUTHORITY = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-execute-attempt-3-"
    "authority-v0.1-20260723.json"
)
RESULT_JSON = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-result-v0.1-20260723.json"
)
RESULT_MARKDOWN = REPO_ROOT / (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-lo2v2-index-bounded-audit-result-v0.1-20260723.md"
)

EXPECTED_HASHES = {
    "audit_script": (
        "170a2d115e35c080ca3c64d4d01356a0046db5603d86f42d3b04335b288a8c85"
    ),
    "audit_contract": (
        "055afec2d650a29f007f9ec6d20f61f3609e2992aa4b55bbf1c8f6672dc0ef26"
    ),
    "reader_amendment": (
        "725baaf4580fb11496d73a4b9b4ce6b35d414928a85dfb8f87841a5249ea76f8"
    ),
    "attempt_1_failure": (
        "11e6cfc1c9fb61164c2650e96cf43efbe6892c0e6d2b7771da5805b55d61ea5c"
    ),
    "attempt_2_failure": (
        "0347800539dc3ec4617d95af958f48351360f19ff9c6f18eaf7ebdddb29601bf"
    ),
}


class EntryBlocked(RuntimeError):
    """Fail-closed non-Bypass entry guard."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_file(path: Path) -> None:
    if not path.is_file():
        raise EntryBlocked("required_file_missing")


def _verify_entry_contract(target_id: str, supervisor_seconds: int) -> None:
    if target_id != TARGET_ID:
        raise EntryBlocked("target_id_mismatch")
    if supervisor_seconds != EXTERNAL_SUPERVISOR_SECONDS:
        raise EntryBlocked("external_supervisor_seconds_mismatch")

    required = {
        "audit_script": AUDIT_SCRIPT,
        "audit_contract": AUDIT_CONTRACT,
        "reader_amendment": READER_AMENDMENT,
        "attempt_1_failure": ATTEMPT_1_FAILURE,
        "attempt_2_failure": ATTEMPT_2_FAILURE,
    }
    for path in (*required.values(), AUTHORITY):
        _require_file(path)

    if RESULT_JSON.exists() or RESULT_MARKDOWN.exists():
        raise EntryBlocked("result_already_exists_execute_once_gate")

    for key, path in required.items():
        if _sha256(path) != EXPECTED_HASHES[key]:
            raise EntryBlocked("pinned_artifact_hash_mismatch")

    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if authority.get("status") != "authorized_once":
        raise EntryBlocked("execution_authority_status_invalid")
    if authority.get("target_id") != TARGET_ID:
        raise EntryBlocked("execution_authority_target_mismatch")
    if authority.get("attempt_number") != 3:
        raise EntryBlocked("execution_authority_attempt_number_mismatch")
    if authority.get("execution_count_authorized") != 1:
        raise EntryBlocked("execution_authority_count_mismatch")
    if authority.get("non_bypass_entry_sha256") != _sha256(Path(__file__)):
        raise EntryBlocked("non_bypass_entry_hash_mismatch")
    if authority.get("audit_script_sha256") != EXPECTED_HASHES["audit_script"]:
        raise EntryBlocked("execution_authority_audit_script_hash_mismatch")
    if authority.get("audit_contract_sha256") != EXPECTED_HASHES["audit_contract"]:
        raise EntryBlocked("execution_authority_audit_contract_hash_mismatch")
    if authority.get("automatic_retry_authorized") is not False:
        raise EntryBlocked("automatic_retry_boundary_missing")
    if authority.get("resume_authorized") is not False:
        raise EntryBlocked("resume_boundary_missing")
    if authority.get("execution_policy_bypass_authorized") is not False:
        raise EntryBlocked("execution_policy_bypass_boundary_missing")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-id", choices=(TARGET_ID,), required=True)
    parser.add_argument(
        "--external-supervisor-seconds",
        type=int,
        choices=(EXTERNAL_SUPERVISOR_SECONDS,),
        required=True,
    )
    args = parser.parse_args(argv)

    try:
        _verify_entry_contract(
            args.target_id,
            args.external_supervisor_seconds,
        )
    except (EntryBlocked, OSError, ValueError, json.JSONDecodeError) as error:
        reason = str(error) if isinstance(error, EntryBlocked) else "entry_failure"
        print(
            json.dumps({"status": "blocked", "reason_code": reason}),
            file=sys.stderr,
        )
        return 2

    os.chdir(REPO_ROOT)
    sys.argv = [
        str(AUDIT_SCRIPT),
        "--mode",
        "execute",
        "--authority-json",
        str(AUTHORITY),
    ]
    runpy.run_path(str(AUDIT_SCRIPT), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
