#!/usr/bin/env python3
"""Run the dependency-free mainline evidence-compiler stub.

The stub exercises request, candidate, admission, decision, and manifest
contracts without importing or simulating a language model.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
BACKEND_ID = "deterministic_stub_v0.1"


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_compiler_public_builder_for_stub",
    "build_compiler_public_request.py",
)
ADMISSION = load_sibling(
    "project05_compiler_admission_for_stub",
    "validate_compiler_admission.py",
)


def contract_hashes() -> dict[str, str]:
    return {
        path.name: BUILDER.sha256_file(path)
        for path in sorted(CONTRACT_ROOT.glob("*.schema.json"))
    }


def default_candidate_bundle(request: dict[str, Any], run_id: str) -> dict[str, Any]:
    return {
        "compiler_run_id": run_id,
        "request_id": request["request_id"],
        "status": "abstain",
        "candidate_claims": [],
        "abstention_reasons": ["stub_no_supported_observation"],
    }


def normalize_response(
    request: dict[str, Any],
    run_id: str,
    response: dict[str, Any] | None,
) -> dict[str, Any]:
    if response is None:
        return default_candidate_bundle(request, run_id)
    if not isinstance(response, dict):
        raise ValueError("stub response must be a JSON object")
    output = copy.deepcopy(response)
    output.setdefault("compiler_run_id", run_id)
    output.setdefault("request_id", request["request_id"])
    output.setdefault("status", "completed")
    output.setdefault("candidate_claims", [])
    output.setdefault("abstention_reasons", [])
    BUILDER.assert_public_boundary(output)
    return output


def run_stub(
    request: dict[str, Any],
    response: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    BUILDER.assert_public_boundary(request)
    run_id = BUILDER.derive_scoped_id(
        "RUN", request["request_id"], "stub", BACKEND_ID
    )
    candidate_bundle = normalize_response(request, run_id, response)
    decision = ADMISSION.admit_candidates(request, candidate_bundle)
    manifest = {
        "manifest_version": "0.1.0",
        "request_id": request["request_id"],
        "compiler_run_id": run_id,
        "condition_id": "stub",
        "backend_id": BACKEND_ID,
        "status": decision["status"],
        "stage_hash_chain": {
            "request_sha256": BUILDER.sha256_value(request),
            "candidate_payload_sha256": BUILDER.sha256_value(candidate_bundle),
            "admission_sha256": BUILDER.sha256_value(decision),
        },
        "contract_sha256": contract_hashes(),
        "model_runtime_loaded": False,
        "private_reference_accessed": False,
        "telemetry": {
            "latency_ms": 0.0,
            "input_tokens": None,
            "output_tokens": None,
            "peak_vram_mb": 0.0,
        },
    }
    manifest_schema = json.loads(
        (CONTRACT_ROOT / "compiler_run_manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(
        manifest_schema,
        format_checker=FormatChecker(),
    ).validate(manifest)
    return decision, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--response", type=Path)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    response = (
        json.loads(args.response.read_text(encoding="utf-8"))
        if args.response is not None
        else None
    )
    output_dir = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"refusing non-empty output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    decision, manifest = run_stub(request, response)
    run_id = manifest["compiler_run_id"]
    candidate_bundle = normalize_response(request, run_id, response)
    BUILDER.write_json_no_overwrite(output_dir / "candidate_bundle.json", candidate_bundle)
    BUILDER.write_json_no_overwrite(output_dir / "admission_decision.json", decision)
    BUILDER.write_json_no_overwrite(output_dir / "run_manifest.json", manifest)
    print(f"Stub {run_id}: {decision['status']}")


if __name__ == "__main__":
    main()
