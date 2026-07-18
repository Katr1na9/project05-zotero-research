#!/usr/bin/env python3
"""Independently validate the CTINexus Gate R0 minimal import smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_ROOT = (
    EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "wp5" / "r0"
)
EXPECTED_COMPONENT_SHA256 = "EE45EEF7D719B5EDA187455DDC9262967A36A1595785F190E9062080D4A1C003"
EXPECTED_DOTENV_SHA256 = "B81EE9561E9CA4004139C6CBBA3A238C32B03E4894671E181B671E8CB8425D61"
EXPECTED_MINIMAL_PACKAGES = {
    "ctinexus==0.2.1",
    "python-dotenv==1.2.1",
}
EXPECTED_MISSING_RUNTIME_DEPENDENCIES = {
    "gradio",
    "hydra-core",
    "jinja2",
    "litellm",
    "networkx",
    "nltk",
    "omegaconf",
    "pandas",
    "pyvis",
    "scikit-learn",
    "scipy",
    "tld",
    "trafilatura",
}
FORBIDDEN_AUTHORITY_FLAGS = (
    "full_dependency_install_authorized",
    "component_pipeline_runtime_authorized",
    "model_or_embedding_download_authorized",
    "external_api_authorized",
    "training_authorized",
    "formal_inference_authorized",
    "C07_C12_execution_authorized",
    "controller_integration_authorized",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite CTINexus R0 readiness: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_missing_dependencies(text: str) -> set[str]:
    return {
        match.group(1).casefold()
        for match in re.finditer(
            r"^ctinexus\s+\S+\s+requires\s+([^,]+),\s+which is not installed\.$",
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
    }


def validate_loaded(
    authority: dict[str, Any],
    static_audit: dict[str, Any],
    smoke: dict[str, Any],
    lock: dict[str, Any],
    resolution: dict[str, Any],
    pip_check_text: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if authority.get("status") != "user_authorized_minimal_import_smoke_only":
        errors.append("r0_authority_status_invalid")
    for key in FORBIDDEN_AUTHORITY_FLAGS:
        if authority.get(key) is not False:
            errors.append(f"unauthorized_authority_flag:{key}")
    if authority.get("bundled_component_demo_or_annotation_data_authorized_as_input") is not False:
        errors.append("bundled_component_data_authorized_as_input")
    if (authority.get("component") or {}).get("wheel_sha256") != EXPECTED_COMPONENT_SHA256:
        errors.append("authority_component_wheel_hash_mismatch")
    if (authority.get("minimum_import_dependency") or {}).get("wheel_sha256") != EXPECTED_DOTENV_SHA256:
        errors.append("authority_dotenv_wheel_hash_mismatch")

    if static_audit.get("status") != "ready_for_minimal_no_model_import_smoke":
        errors.append("static_wheel_audit_not_ready")
    if static_audit.get("errors") != []:
        errors.append("static_wheel_audit_has_errors")
    if (static_audit.get("wheel") or {}).get("sha256") != EXPECTED_COMPONENT_SHA256:
        errors.append("static_wheel_hash_mismatch")
    if (static_audit.get("wheel") or {}).get("native_binary_count") != 0:
        errors.append("wheel_contains_native_binary")
    if (static_audit.get("wheel") or {}).get("unsafe_path_count") != 0:
        errors.append("wheel_contains_unsafe_path")
    quarantine = static_audit.get("bundled_data_quarantine") or {}
    if quarantine.get("annotation_file_count", 0) <= 0 or quarantine.get("demo_file_count", 0) <= 0:
        errors.append("bundled_data_inventory_missing")
    if quarantine.get("bundled_data_authorized_as_project05_input") is not False:
        errors.append("bundled_data_quarantine_not_enforced")
    if quarantine.get("bundled_data_access_authorized_during_smoke") is not False:
        errors.append("bundled_data_smoke_access_authorized")

    if smoke.get("status") != "passed_minimal_import_only_full_runtime_not_ready":
        errors.append("minimal_import_smoke_not_passed")
    if smoke.get("errors") != []:
        errors.append("minimal_import_smoke_has_errors")
    if (smoke.get("component") or {}).get("wheel_sha256") != EXPECTED_COMPONENT_SHA256:
        errors.append("smoke_component_wheel_hash_mismatch")
    isolation = smoke.get("isolation") or {}
    for key in (
        "python_isolated_flag",
        "python_no_user_site",
        "dotenv_disabled",
        "clean_working_directory",
        "provider_environment_variables_removed",
        "network_guard_enabled",
    ):
        if isolation.get(key) is not True:
            errors.append(f"smoke_isolation_not_true:{key}")
    if isolation.get("network_attempts") != []:
        errors.append("network_attempt_observed")
    smoke_body = smoke.get("smoke") or {}
    if smoke_body.get("bundled_data_accesses") != []:
        errors.append("bundled_data_access_observed")
    if smoke_body.get("full_runtime_modules_loaded") != []:
        errors.append("full_runtime_module_loaded")
    for key in (
        "provider_credentials_detected",
        "pipeline_runtime_executed",
        "model_or_embedding_loaded",
        "cti_input_supplied",
    ):
        if smoke_body.get(key) is not False:
            errors.append(f"smoke_forbidden_state:{key}")
    if smoke_body.get("import_return_code") != 0 or smoke_body.get("cli_help_return_code") != 0:
        errors.append("import_or_cli_help_nonzero")

    environment = smoke.get("environment") or {}
    installed = set(environment.get("installed_packages") or [])
    non_bootstrap = {
        item for item in installed if not item.startswith(("pip==", "setuptools=="))
    }
    if non_bootstrap != EXPECTED_MINIMAL_PACKAGES:
        errors.append("minimal_installed_package_set_mismatch")
    if environment.get("dependency_closure_complete") is not False:
        errors.append("dependency_closure_incorrectly_complete")
    if environment.get("full_runtime_ready") is not False:
        errors.append("full_runtime_incorrectly_ready")
    if float(environment.get("venv_megabytes", 9999)) > 250:
        errors.append("minimal_environment_exceeds_250mb")

    locked = {
        f"{row.get('name')}=={row.get('version')}"
        for row in lock.get("packages", [])
        if isinstance(row, dict)
    }
    if locked != EXPECTED_MINIMAL_PACKAGES:
        errors.append("minimal_lock_package_set_mismatch")
    lock_hashes = {row.get("name"): row.get("sha256") for row in lock.get("packages", [])}
    if lock_hashes.get("ctinexus") != EXPECTED_COMPONENT_SHA256:
        errors.append("minimal_lock_component_hash_mismatch")
    if lock_hashes.get("python-dotenv") != EXPECTED_DOTENV_SHA256:
        errors.append("minimal_lock_dotenv_hash_mismatch")
    if lock.get("full_dependency_closure_complete") is not False:
        errors.append("minimal_lock_claims_full_closure")

    if resolution.get("status") != "failed_closed_before_project_environment_install":
        errors.append("full_dependency_resolution_status_not_failed_closed")
    if resolution.get("project_r0_venv_modified_by_failed_resolution") is not False:
        errors.append("failed_resolution_modified_project_venv")
    if resolution.get("ctinexus_full_dependency_closure_installed") is not False:
        errors.append("full_dependency_closure_installed")
    if resolution.get("model_or_embedding_downloaded") is not False:
        errors.append("model_or_embedding_downloaded")
    cleanup = (resolution.get("temporary_external_cache_side_effect") or {}).get(
        "cleanup_status"
    )
    if cleanup != "deleted_after_exact_path_verification":
        errors.append("temporary_rust_cache_not_cleaned")

    missing_dependencies = parse_missing_dependencies(pip_check_text)
    if missing_dependencies != EXPECTED_MISSING_RUNTIME_DEPENDENCIES:
        errors.append("pip_check_missing_dependency_set_mismatch")
    if missing_dependencies:
        warnings.append("full_runtime_dependency_closure_intentionally_missing")
    if quarantine.get("annotation_file_count", 0) or quarantine.get("demo_file_count", 0):
        warnings.append("bundled_component_examples_present_but_quarantined")
    warnings.append("full_dependency_resolution_blocked_by_litellm_windows_sdist_rust_path")

    status = "passed_r0_minimal_import_full_runtime_blocked" if not errors else "failed_closed"
    return {
        "schema_version": "project05-ctinexus-r0-readiness-v0.1",
        "status": status,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "component": {
            "id": "ctinexus",
            "version": "0.2.1",
            "wheel_sha256": EXPECTED_COMPONENT_SHA256,
            "minimal_import_passed": status != "failed_closed",
            "full_runtime_ready": False,
        },
        "environment": {
            "python": lock.get("python"),
            "minimal_packages": sorted(EXPECTED_MINIMAL_PACKAGES),
            "venv_megabytes": environment.get("venv_megabytes"),
            "missing_runtime_dependencies": sorted(missing_dependencies),
            "dependency_closure_complete": False,
        },
        "isolation": {
            "network_attempts": isolation.get("network_attempts"),
            "provider_credentials_detected": smoke_body.get(
                "provider_credentials_detected"
            ),
            "bundled_data_accesses": smoke_body.get("bundled_data_accesses"),
            "full_runtime_modules_loaded": smoke_body.get(
                "full_runtime_modules_loaded"
            ),
            "pipeline_runtime_executed": False,
            "model_or_embedding_loaded": False,
        },
        "bundled_data_quarantine": quarantine,
        "authorization": {
            "full_dependency_install": False,
            "component_pipeline_runtime": False,
            "model_or_embedding": False,
            "external_api": False,
            "training": False,
            "formal_inference": False,
            "C07_C12_execution": False,
            "controller_integration": False,
        },
        "next_gate": "freeze a Windows-compatible full-runtime dependency strategy and local model plus embedding configuration",
    }


def validate_root(root: Path) -> dict[str, Any]:
    root = Path(root)
    required = {
        "r0-authority.json": root / "r0-authority.json",
        "wheel-static-audit.json": root / "wheel-static-audit.json",
        "r0-import-smoke-v0.1.1.json": root / "r0-import-smoke-v0.1.1.json",
        "minimal-environment-lock-v0.1.1.json": root
        / "minimal-environment-lock-v0.1.1.json",
        "r0-dependency-resolution-observation.json": root
        / "r0-dependency-resolution-observation.json",
        "minimal-pip-check-v0.1.1.txt": root / "minimal-pip-check-v0.1.1.txt",
    }
    missing = [name for name, path in required.items() if not path.is_file()]
    if missing:
        return {
            "schema_version": "project05-ctinexus-r0-readiness-v0.1",
            "status": "failed_closed",
            "errors": ["missing_artifacts:" + ",".join(sorted(missing))],
            "warnings": [],
        }
    report = validate_loaded(
        load_json(required["r0-authority.json"]),
        load_json(required["wheel-static-audit.json"]),
        load_json(required["r0-import-smoke-v0.1.1.json"]),
        load_json(required["minimal-environment-lock-v0.1.1.json"]),
        load_json(required["r0-dependency-resolution-observation.json"]),
        required["minimal-pip-check-v0.1.1.txt"].read_text(encoding="utf-8"),
    )
    report["artifact_sha256"] = {
        name: sha256_file(path) for name, path in sorted(required.items())
    }
    failed_smoke = root / "r0-import-smoke.json"
    report["prior_fail_closed_smoke_preserved"] = failed_smoke.is_file()
    if failed_smoke.is_file():
        report["prior_fail_closed_smoke_sha256"] = sha256_file(failed_smoke)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_root(args.root)
    if args.output:
        write_json_no_overwrite(args.output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    if report["status"] == "failed_closed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
