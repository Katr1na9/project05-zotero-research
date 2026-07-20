import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-general-adapted-paired-contract-v0.1.json"
)
CONFIG = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/"
    "paired_evaluation_v0.1/paired-evaluation-config-v0.1.json"
)
IMPLEMENTATION_AUTHORITY = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.41.json"
)
EXECUTION_AUTHORITY = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.42.json"
)
RUNNER = ROOT / "09-experiments/scripts/run_qwen_general_adapted_paired.py"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "project05_paired_execution_authority_test",
        RUNNER,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_v042_authorizes_exactly_one_atomic_paired_execution():
    runner = load_runner()
    verified = runner.validate_implementation_bundle(
        CONTRACT,
        CONFIG,
        IMPLEMENTATION_AUTHORITY,
    )
    authority = runner.validate_execution_authority(
        EXECUTION_AUTHORITY,
        verified,
    )
    gate = authority["paired_execution_gate"]
    assert gate["authorized"] is True
    assert gate["maximum_executions"] == 1
    assert gate["split"] == "training-validation"
    assert gate["examples"] == 16
    assert gate["model_calls"] == 32
    assert gate["automatic_retry_authorized"] is False


def test_execution_authority_binds_all_new_artifacts_and_keeps_scope_closed():
    authority = load_json(EXECUTION_AUTHORITY)
    for record in authority["hash_locked_artifacts"].values():
        path = ROOT / record["path"]
        assert path.is_file()
        assert sha(path) == record["sha256"]
    gate = authority["paired_execution_gate"]
    assert gate["train_access_authorized"] is False
    assert gate["development_or_test_access_authorized"] is False
    assert gate["c07_c12_execution_authorized"] is False
    assert gate["m3_integration_authorized"] is False
    assert gate["raw_generation_download_authorized"] is False


def test_launcher_is_single_pass_and_confined_to_authorized_root():
    authority = load_json(EXECUTION_AUTHORITY)
    launcher = ROOT / authority["hash_locked_artifacts"]["launcher"]["path"]
    text = launcher.read_text(encoding="utf-8")
    assert text.count("run_qwen_general_adapted_paired.py") == 1
    assert text.count("score_qwen_general_adapted_paired.py") == 1
    assert "/home/myy/project05-qwen25-4090-v0.1" in text
    assert 'CUDA_VISIBLE_DEVICES="2"' in text
    assert "GPU-b0302acd-64e2-8218-7b5c-07a152007357" in text
    for forbidden in (
        "C07",
        "C08",
        "C09",
        "C10",
        "C11",
        "C12",
        "development",
        "run_mvp.py",
    ):
        assert forbidden not in text
