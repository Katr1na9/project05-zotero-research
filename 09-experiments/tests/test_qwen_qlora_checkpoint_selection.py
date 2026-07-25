import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "09-experiments/scripts/select_qwen_qlora_checkpoint_4090.py"
CONFIG = ROOT / "09-experiments/llm_evidence_compiler_mainline/checkpoint_selection_v0.1/selection-config-v0.1.json"
CONTRACT = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-checkpoint-selection-contract-v0.1.json"
AUTHORITY = ROOT / "09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.39.json"
LAUNCHER = ROOT / "09-experiments/llm_evidence_compiler_mainline/checkpoint_selection_v0.1/run-checkpoint-selection-detached-v0.1.sh"
PAIR_ROOT = ROOT / "09-experiments/llm_evidence_compiler_mainline/candidate_pairs_v0.2/local-data"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_selector():
    spec = importlib.util.spec_from_file_location("project05_checkpoint_selector_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def supported_prediction():
    pointer = {"artifact_id": "a", "record_id": "r", "record_sha256": "0" * 64}
    return {
        "support_decision": "supported",
        "normalized_edge": {
            "subject_type": "process",
            "subject_value": "cmd.exe",
            "predicate": "connects_to",
            "object_type": "ip",
            "object_value": "192.0.2.1",
            "source_pointer": pointer,
        },
        "pointer": pointer,
    }


def test_strict_json_schema_accepts_exact_supported_and_unsupported_only():
    module = load_selector()
    supported = supported_prediction()
    assert module.strict_prediction(json.dumps(supported), True) == (supported, None)
    unsupported = {
        "support_decision": "unsupported_by_bound_pointer",
        "normalized_edge": None,
        "pointer": supported["pointer"],
    }
    assert module.strict_prediction(json.dumps(unsupported), True) == (unsupported, None)
    assert module.strict_prediction(json.dumps(supported), False) == (None, "missing_eos_or_max_tokens")
    assert module.strict_prediction("```json\n{}\n```", True) == (None, "invalid_json")
    with_extra = {**supported, "explanation": "repair me"}
    assert module.strict_prediction(json.dumps(with_extra), True) == (None, "invalid_top_level_schema")
    unsupported["normalized_edge"] = supported["normalized_edge"]
    assert module.strict_prediction(json.dumps(unsupported), True) == (None, "unsupported_edge_must_be_null")


def test_family_and_class_macro_f1_counts_invalid_as_error():
    module = load_selector()
    rows = [
        {"source_family_id": "a", "gold_decision": "supported", "predicted_decision": "supported"},
        {"source_family_id": "a", "gold_decision": "unsupported_by_bound_pointer", "predicted_decision": "invalid"},
        {"source_family_id": "b", "gold_decision": "supported", "predicted_decision": "unsupported_by_bound_pointer"},
        {"source_family_id": "b", "gold_decision": "unsupported_by_bound_pointer", "predicted_decision": "unsupported_by_bound_pointer"},
    ]
    for row in rows:
        row.update(
            canonical_json_exact=False,
            normalized_edge_exact=False,
            pointer_exact=False,
            json_valid=False,
            schema_valid=False,
            eos_terminated=False,
            assistant_token_nll=1.0,
            assistant_target_tokens=1,
        )
    report = module.score_rows(rows)
    assert report["families"]["a"]["macro_support_decision_f1"] == pytest.approx(0.5)
    assert report["families"]["b"]["macro_support_decision_f1"] == pytest.approx(1 / 3)
    assert report["family_macro_support_decision_f1"] == pytest.approx(5 / 12)


def test_assistant_token_nll_is_token_weighted_not_example_weighted():
    module = load_selector()
    rows = []
    for nll, tokens in ((1.0, 1), (3.0, 3)):
        rows.append({
            "source_family_id": "a",
            "gold_decision": "supported",
            "predicted_decision": "supported",
            "canonical_json_exact": True,
            "normalized_edge_exact": True,
            "pointer_exact": True,
            "json_valid": True,
            "schema_valid": True,
            "eos_terminated": True,
            "assistant_token_nll": nll,
            "assistant_target_tokens": tokens,
        })
    report = module.score_rows(rows)
    assert report["assistant_token_nll"] == pytest.approx(2.5)
    assert report["assistant_target_tokens"] == 4


def selection_report(epoch, primary=0.5, canonical=0.5, edge=0.5, pointer=0.5, nll=1.0):
    return {
        "epoch": epoch,
        "metrics": {
            "family_macro_support_decision_f1": primary,
            "canonical_json_exact_match_rate": canonical,
            "normalized_edge_exact_match_rate": edge,
            "pointer_exact_match_rate": pointer,
            "assistant_token_nll": nll,
        },
    }


@pytest.mark.parametrize(
    "replacement",
    [
        {"primary": 0.6},
        {"canonical": 0.6},
        {"edge": 0.6},
        {"pointer": 0.6},
        {"nll": 0.9},
    ],
)
def test_selection_tie_breakers_are_lexicographic_and_frozen(replacement):
    module = load_selector()
    reports = [selection_report(1), selection_report(2, **replacement), selection_report(3)]
    assert module.choose_checkpoint(reports)["epoch"] == 2


def test_exact_tie_selects_earlier_epoch():
    module = load_selector()
    reports = [selection_report(epoch) for epoch in (1, 2, 3)]
    assert module.choose_checkpoint(reports)["epoch"] == 1


def test_config_and_payload_boundary_are_training_validation_only():
    module = load_selector()
    config = load_json(CONFIG)
    module.validate_config(config)
    verified = {
        "run_root": ROOT,
        "config": config,
        "contract": {
            "pair_payloads": {
                "training_validation": {
                    "file": "training-validation.jsonl.gz",
                    "sha256": config["data"]["sha256"],
                }
            }
        },
    }
    rows, report = module.load_validation(verified, PAIR_ROOT)
    assert len(rows) == report["examples"] == 300
    assert {row["split_role"] for row in rows} == {"training-validation"}
    altered = json.loads(json.dumps(config))
    altered["data"]["split"] = "development"
    with pytest.raises(ValueError, match="data boundary"):
        module.validate_config(altered)
    with pytest.raises(ValueError, match="pair root differs"):
        module.load_validation(verified, ROOT / "development")


def build_fake_checkpoint_inventory(module, root):
    reports = []
    config = {"checkpoints": []}
    names = [
        "adapter/README.md",
        "adapter/adapter_config.json",
        "adapter/adapter_model.safetensors",
        "optimizer.pt",
        "rng-state.pt",
        "scheduler.pt",
        "trainer-state.json",
    ]
    for epoch in (1, 2, 3):
        epoch_root = root / f"checkpoint-epoch-{epoch:03d}"
        files = []
        for name in names:
            path = epoch_root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(f"{epoch}:{name}".encode())
            files.append({"path": name, "bytes": path.stat().st_size, "sha256": sha(path)})
        adapter_sha = next(row["sha256"] for row in files if row["path"] == "adapter/adapter_model.safetensors")
        reports.append({
            "epoch": epoch,
            "optimizer_step": epoch * 75,
            "root": epoch_root.name,
            "adapter_only": True,
            "merged_model_saved": False,
            "files": files,
        })
        config["checkpoints"].append({"epoch": epoch, "optimizer_step": epoch * 75, "adapter_sha256": adapter_sha})
    formal = {"status": "passed_single_4090_adamw_primary_adapter_training", "checkpoints": reports}
    return formal, config


def test_full_checkpoint_inventory_is_verified_before_adapter_use(tmp_path):
    module = load_selector()
    formal, config = build_fake_checkpoint_inventory(module, tmp_path)
    adapters = module.verify_checkpoint_inventory(tmp_path, formal, config)
    assert sorted(adapters) == [1, 2, 3]
    (tmp_path / "checkpoint-epoch-002/trainer-state.json").write_text("mutated", encoding="utf-8")
    with pytest.raises(ValueError, match="byte-size mismatch|SHA-256 mismatch"):
        module.verify_checkpoint_inventory(tmp_path, formal, config)


def test_launcher_is_detached_scoped_and_uses_real_worker_pid():
    text = LAUNCHER.read_text(encoding="utf-8")
    assert 'readonly ALLOWED_HOME="/home/myy"' in text
    assert "/usr/bin/nohup /usr/bin/setsid" in text
    assert 'detached_worker_pid=$$' in text
    assert 'CUDA_VISIBLE_DEVICES="${physical_gpu_uuid}"' in text
    assert "pip install" not in text


def test_contract_authority_hash_chain_and_downstream_gates():
    contract, authority = load_json(CONTRACT), load_json(AUTHORITY)
    gate = authority["checkpoint_selection_gate"]
    assert gate["contract_sha256"] == sha(CONTRACT)
    assert gate["selection_config_sha256"] == sha(CONFIG)
    assert gate["maximum_executions"] == 1
    assert gate["authorized"] is True
    assert gate["paired_evaluation_authorized"] is False
    assert gate["development_or_test_access_authorized"] is False
    assert gate["m3_integration_authorized"] is False
    for record in contract["implementation"].values():
        assert sha(ROOT / record["path"]) == record["sha256"]
    assert contract["formal_training_result"]["sha256"] == sha(ROOT / contract["formal_training_result"]["path"])
    assert authority["next_gate"]["paired_general_vs_adapted_evaluation_authorized"] is False
    assert authority["next_gate"]["development_or_test_access_authorized"] is False
    assert authority["next_gate"]["m3_integration_authorized"] is False


def test_success_audit_is_written_after_completion_progress_hash_is_frozen():
    source = SCRIPT.read_text(encoding="utf-8")
    completion = source.index('append_jsonl(progress_path, {"event": "checkpoint_selection_completed"')
    audit_write = source.index("CORE.write_json_no_overwrite(output_root / AUDIT_NAME, result)")
    assert completion < audit_write
    assert '"progress": {"file": PROGRESS_NAME, "sha256": CORE.sha256_file(progress_path)}' in source
