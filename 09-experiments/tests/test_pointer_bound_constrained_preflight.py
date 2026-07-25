import importlib.util
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "09-experiments/scripts/preflight_pointer_bound_constrained_decoder.py"
)
AUTHORITY = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.45.json"
)
LAUNCHER = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/"
    "pointer_bound_atomic_v0.1/"
    "run-constrained-decoder-preflight-4090-v0.1.sh"
)
SCHEMA = (
    ROOT
    / "09-experiments/data_schema/pointer_bound_compiler_output.schema.json"
)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


preflight = load_module(SCRIPT, "project05_test_constrained_preflight")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_preflight_import_is_constraint_and_model_lazy():
    assert "lmformatenforcer" not in sys.modules
    source = SCRIPT.read_text(encoding="utf-8")
    assert "AutoModelForCausalLM" not in source
    assert ".generate(" not in source
    assert "maximum_model_calls" in source


def test_schema_is_valid_and_has_exact_two_pointer_free_branches():
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    assert len(schema["oneOf"]) == 2
    serialized = json.dumps(schema, sort_keys=True)
    assert '"pointer"' not in serialized
    assert '"source_pointer"' not in serialized


def test_path_boundary_rejects_escape(tmp_path):
    inside = tmp_path / "inside"
    inside.mkdir()
    assert preflight.require_within(inside, tmp_path, "fixture") == inside.resolve()
    with pytest.raises(ValueError, match="escapes the authorized server root"):
        preflight.require_within(tmp_path.parent, tmp_path, "escape")


def test_isolated_install_uses_no_shell_and_never_reuses_target(tmp_path, monkeypatch):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text("lm-format-enforcer==0.10.6\n", encoding="utf-8")
    target = tmp_path / "local-runtime/constrained-v0.1"
    observed = {}

    class Completed:
        returncode = 0

    def fake_run(command, **kwargs):
        observed["command"] = command
        observed["kwargs"] = kwargs
        installing = target.with_name(target.name + ".installing")
        package = installing / "lmformatenforcer"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        return Completed()

    monkeypatch.setattr(preflight.subprocess, "run", fake_run)
    result = preflight.install_isolated_dependency(
        requirements,
        target,
        tmp_path,
        maximum_bytes=1000,
    )
    assert result["returncode"] == 0
    assert result["automatic_retry_performed"] is False
    assert target.is_dir()
    assert observed["kwargs"]["check"] is False
    assert observed["kwargs"]["cwd"] == tmp_path
    assert "--target" in observed["command"]
    with pytest.raises(FileExistsError):
        preflight.install_isolated_dependency(
            requirements,
            target,
            tmp_path,
            maximum_bytes=1000,
        )


def test_target_tokenization_prefers_prompt_preserving_combined_encoding():
    class FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            assert add_special_tokens is False
            table = {
                "P": [1],
                "T": [2],
                "PT": [1, 2],
            }
            return table[text]

    prompt, target = preflight.actual_target_ids(FakeTokenizer(), "P", "T")
    assert prompt == [1]
    assert target == [2]


def test_launcher_is_zero_model_call_and_server_root_scoped():
    text = LAUNCHER.read_text(encoding="utf-8")
    root = "/home/myy/project05-qwen25-4090-v0.1"
    assert f'ROOT="{root}"' in text
    assert 'BUNDLE="${ROOT}/bundle-v045"' in text
    assert 'DEPENDENCY_TARGET="${ROOT}/local-runtime/constrained-v0.1"' in text
    assert "CUDA_VISIBLE_DEVICES=\"\"" in text
    assert "run_qwen_pointer_bound_constrained_atomic.py" not in text
    assert "score_qwen_pointer_bound_constrained_atomic.py" not in text
    assert "/home/myy/" in text
    assert "/home/myy/project05-qwen25-4090-v0.1" in text


def test_v045_authority_hashes_artifacts_and_allows_no_model_calls():
    authority = load_json(AUTHORITY)
    gate = authority["compatibility_preflight_gate"]
    assert gate["authorized"] is True
    assert gate["maximum_attempts"] == 1
    assert gate["maximum_model_calls"] == 0
    assert gate["model_loading_authorized"] is False
    assert gate["model_inference_authorized"] is False
    assert gate["training_validation_payload_access_authorized"] is False
    assert gate["automatic_retry_authorized"] is False
    for record in authority["hash_locked_artifacts"].values():
        assert preflight.sha256_file(ROOT / record["path"]) == record["sha256"]


def test_v045_does_not_open_atomic_execution_or_downstream_scope():
    authority = load_json(AUTHORITY)
    assert authority["next_gate"]["model_execution_authorized"] is False
    assert authority["next_gate"]["atomic_panel_execution_authorized"] is False
    forbidden = set(authority["not_authorized"])
    assert {
        "model_loading_or_inference",
        "training_validation_payload_access",
        "development_or_test_access",
        "c07_c12_model_execution",
        "m3_runtime_integration",
        "automatic_retry_or_unconstrained_fallback",
    } <= forbidden
