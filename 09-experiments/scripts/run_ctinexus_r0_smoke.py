#!/usr/bin/env python3
"""Run a no-input, no-provider, network-guarded CTINexus Gate R0 smoke."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_R0_ROOT = (
    EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "wp5" / "r0"
)
SENSITIVE_ENV_MARKERS = (
    "OPENAI",
    "GEMINI",
    "GOOGLE_API",
    "AWS_",
    "BEDROCK",
    "OLLAMA",
    "CUSTOM_BASE",
    "CUSTOM_API",
    "API_KEY",
)
EXPECTED_NON_BOOTSTRAP_PACKAGES = {
    "ctinexus==0.2.1",
    "python-dotenv==1.2.1",
}
FORBIDDEN_IMPORTED_MODULE_PREFIXES = (
    "gradio",
    "hydra",
    "litellm",
    "networkx",
    "nltk",
    "numpy",
    "omegaconf",
    "pandas",
    "pyvis",
    "scipy",
    "sklearn",
    "trafilatura",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text_no_overwrite(path: Path, value: str) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite R0 smoke artifact: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8", newline="\n")


def write_json_no_overwrite(path: Path, value: Any) -> None:
    write_text_no_overwrite(
        path,
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )


def sanitized_environment(source: dict[str, str], sandbox: Path) -> dict[str, str]:
    output = {
        key: value
        for key, value in source.items()
        if not any(marker in key.upper() for marker in SENSITIVE_ENV_MARKERS)
    }
    output.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHON_DOTENV_DISABLED": "1",
            "HOME": str(Path(sandbox).resolve()),
            "USERPROFILE": str(Path(sandbox).resolve()),
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
        }
    )
    return output


def import_child_source() -> str:
    forbidden = repr(FORBIDDEN_IMPORTED_MODULE_PREFIXES)
    return f'''import json, os, socket, sys, urllib.request
from pathlib import Path

network_attempts = []
data_accesses = []

def audit_hook(event, args):
    if event == "open" and args:
        path = str(args[0]).replace("\\\\", "/").casefold()
        if "/ctinexus/data/" in path:
            data_accesses.append(path)

sys.addaudithook(audit_hook)

def blocked_connect(*args, **kwargs):
    network_attempts.append(repr(args[1:] if len(args) > 1 else args))
    raise RuntimeError("R0 network guard blocked a connection")

socket.socket.connect = blocked_connect
socket.create_connection = blocked_connect
urllib.request.urlopen = blocked_connect

assert not (Path.cwd() / ".env").exists()
import ctinexus
from ctinexus import app
from ctinexus.utils import model_utils

api_keys_available = model_utils.check_api_key()
help_text = app.create_argument_parser().format_help()
forbidden = {forbidden}
forbidden_loaded = sorted(
    name for name in sys.modules
    if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
)
result = {{
    "ctinexus_version": ctinexus.__version__,
    "ctinexus_file": ctinexus.__file__,
    "clean_working_directory": not (Path.cwd() / ".env").exists(),
    "provider_credentials_detected": bool(api_keys_available),
    "registered_provider_count": len(model_utils.MODELS),
    "help_contains_component_name": "CTINexus" in help_text,
    "help_sha256": __import__("hashlib").sha256(help_text.encode()).hexdigest().upper(),
    "network_attempts": network_attempts,
    "bundled_data_accesses": sorted(set(data_accesses)),
    "forbidden_full_runtime_modules_loaded": forbidden_loaded,
    "pipeline_runtime_executed": False,
    "model_or_embedding_loaded": False,
}}
print(json.dumps(result, sort_keys=True))
'''


def cli_help_child_source() -> str:
    return '''import json, socket, sys, urllib.request
network_attempts = []
def blocked_connect(*args, **kwargs):
    network_attempts.append(repr(args[1:] if len(args) > 1 else args))
    raise RuntimeError("R0 network guard blocked a connection")
socket.socket.connect = blocked_connect
socket.create_connection = blocked_connect
urllib.request.urlopen = blocked_connect
sys.argv = ["ctinexus", "--help"]
from ctinexus.app import main
code = 0
try:
    main()
except SystemExit as exc:
    code = int(exc.code or 0)
print(json.dumps({"system_exit_code": code, "network_attempts": network_attempts}, sort_keys=True))
raise SystemExit(code)
'''


def run_child(python: Path, source: str, sandbox: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(python), "-I", "-c", source],
        cwd=sandbox,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )


def parse_last_json_line(text: str) -> dict[str, Any]:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("child output contains no JSON object")


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in Path(path).rglob("*") if item.is_file())


def run_smoke(r0_root: Path) -> tuple[dict[str, Any], str, str]:
    root = Path(r0_root)
    authority = load_json(root / "r0-authority.json")
    static_audit = load_json(root / "wheel-static-audit.json")
    if authority.get("status") != "user_authorized_minimal_import_smoke_only":
        raise ValueError("R0 authority is not active")
    if static_audit.get("status") != "ready_for_minimal_no_model_import_smoke":
        raise ValueError("wheel static audit is not ready")
    python = root / "venv" / "Scripts" / "python.exe"
    if not python.is_file():
        raise FileNotFoundError(f"R0 venv Python missing: {python}")
    sandbox = root / "sandbox"
    sandbox.mkdir(parents=True, exist_ok=True)
    if any(sandbox.iterdir()):
        raise ValueError("R0 clean sandbox is not empty")
    env = sanitized_environment(dict(os.environ), sandbox)
    import_run = run_child(python, import_child_source(), sandbox, env)
    cli_run = run_child(python, cli_help_child_source(), sandbox, env)
    freeze_run = subprocess.run(
        [str(python), "-I", "-m", "pip", "freeze", "--all"],
        cwd=sandbox,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )
    list_run = subprocess.run(
        [str(python), "-I", "-m", "pip", "list", "--format=json"],
        cwd=sandbox,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )
    check_run = subprocess.run(
        [str(python), "-I", "-m", "pip", "check"],
        cwd=sandbox,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
    )
    errors: list[str] = []
    if import_run.returncode != 0:
        errors.append("import_child_failed")
        import_result: dict[str, Any] = {}
    else:
        import_result = parse_last_json_line(import_run.stdout)
    if cli_run.returncode != 0:
        errors.append("cli_help_child_failed")
        cli_result: dict[str, Any] = {}
    else:
        cli_result = parse_last_json_line(cli_run.stdout)
    if freeze_run.returncode != 0:
        errors.append("pip_freeze_failed")
    if list_run.returncode != 0:
        errors.append("pip_list_failed")

    if import_result.get("ctinexus_version") != "0.2.1":
        errors.append("imported_ctinexus_version_mismatch")
    if import_result.get("provider_credentials_detected") is not False:
        errors.append("provider_credentials_detected")
    if import_result.get("registered_provider_count") != 0:
        errors.append("provider_registry_not_empty")
    if import_result.get("network_attempts") != []:
        errors.append("network_attempt_during_import")
    if import_result.get("bundled_data_accesses") != []:
        errors.append("bundled_data_access_during_import")
    if import_result.get("forbidden_full_runtime_modules_loaded") != []:
        errors.append("full_runtime_module_loaded")
    if import_result.get("pipeline_runtime_executed") is not False:
        errors.append("pipeline_runtime_executed")
    if import_result.get("model_or_embedding_loaded") is not False:
        errors.append("model_or_embedding_loaded")
    if cli_result.get("system_exit_code") != 0:
        errors.append("cli_help_nonzero_exit")
    if cli_result.get("network_attempts") != []:
        errors.append("network_attempt_during_cli_help")

    try:
        installed_rows = json.loads(list_run.stdout) if list_run.returncode == 0 else []
    except json.JSONDecodeError:
        installed_rows = []
        errors.append("pip_list_json_invalid")
    installed = {
        f"{str(row.get('name', '')).casefold().replace('_', '-')}=={row.get('version')}"
        for row in installed_rows
        if isinstance(row, dict) and row.get("name") and row.get("version")
    }
    non_bootstrap = {
        line for line in installed if not line.startswith(("pip==", "setuptools=="))
    }
    if non_bootstrap != EXPECTED_NON_BOOTSTRAP_PACKAGES:
        errors.append("minimal_environment_package_set_mismatch")
    env_bytes = directory_bytes(root / "venv")
    if env_bytes > 250 * 1024 * 1024:
        errors.append("minimal_environment_exceeds_250mb")

    # pip check must report the deliberately absent full-runtime dependencies.
    if check_run.returncode == 0:
        errors.append("pip_check_unexpectedly_reports_full_dependency_closure")
    if "requires" not in check_run.stdout.casefold():
        errors.append("pip_check_missing_dependency_diagnostics_absent")

    report = {
        "schema_version": "project05-ctinexus-r0-import-smoke-v0.1",
        "status": "passed_minimal_import_only_full_runtime_not_ready" if not errors else "failed_closed",
        "errors": sorted(set(errors)),
        "component": {
            "id": "ctinexus",
            "version": import_result.get("ctinexus_version"),
            "wheel_sha256": static_audit.get("wheel", {}).get("sha256"),
        },
        "isolation": {
            "python_isolated_flag": True,
            "python_no_user_site": True,
            "dotenv_disabled": True,
            "clean_working_directory": import_result.get("clean_working_directory"),
            "provider_environment_variables_removed": True,
            "network_guard_enabled": True,
            "network_attempts": import_result.get("network_attempts", [])
            + cli_result.get("network_attempts", []),
        },
        "smoke": {
            "import_return_code": import_run.returncode,
            "cli_help_return_code": cli_run.returncode,
            "help_contains_component_name": import_result.get("help_contains_component_name"),
            "help_sha256": import_result.get("help_sha256"),
            "bundled_data_accesses": import_result.get("bundled_data_accesses", []),
            "full_runtime_modules_loaded": import_result.get(
                "forbidden_full_runtime_modules_loaded", []
            ),
            "provider_credentials_detected": import_result.get(
                "provider_credentials_detected"
            ),
            "pipeline_runtime_executed": False,
            "model_or_embedding_loaded": False,
            "cti_input_supplied": False,
        },
        "environment": {
            "venv_bytes": env_bytes,
            "venv_megabytes": round(env_bytes / (1024 * 1024), 3),
            "installed_packages": sorted(installed),
            "pip_freeze_lines": sorted(
                line.strip() for line in freeze_run.stdout.splitlines() if line.strip()
            ),
            "expected_non_bootstrap_packages": sorted(EXPECTED_NON_BOOTSTRAP_PACKAGES),
            "pip_check_return_code": check_run.returncode,
            "dependency_closure_complete": False,
            "full_runtime_ready": False,
        },
        "bundled_data_authorized_as_input": False,
        "authorization": {
            "component_pipeline_runtime": False,
            "model_or_embedding": False,
            "external_api": False,
            "training": False,
            "formal_inference": False,
            "C07_C12_execution": False,
            "controller_integration": False,
        },
        "next_gate": "review full-runtime dependency blocker and separately freeze local model plus embedding configuration",
        "diagnostics": {
            "import_stderr_sha256": sha256_bytes(import_run.stderr.encode("utf-8")),
            "cli_stderr_sha256": sha256_bytes(cli_run.stderr.encode("utf-8")),
            "pip_check_sha256": sha256_bytes(check_run.stdout.encode("utf-8")),
        },
    }
    return report, freeze_run.stdout, check_run.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r0-root", type=Path, default=DEFAULT_R0_ROOT)
    parser.add_argument("--run-id", default="v0.1.1")
    args = parser.parse_args()
    report, freeze_text, check_text = run_smoke(args.r0_root)
    write_json_no_overwrite(
        args.r0_root / f"r0-import-smoke-{args.run_id}.json", report
    )
    write_text_no_overwrite(
        args.r0_root / f"minimal-environment-lock-{args.run_id}.txt", freeze_text
    )
    write_text_no_overwrite(
        args.r0_root / f"minimal-pip-check-{args.run_id}.txt", check_text
    )
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    if report["status"] == "failed_closed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
