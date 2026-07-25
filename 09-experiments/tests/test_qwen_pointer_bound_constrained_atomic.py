import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = (
    ROOT / "09-experiments/scripts/run_qwen_pointer_bound_constrained_atomic.py"
)
SCORER_PATH = (
    ROOT / "09-experiments/scripts/score_qwen_pointer_bound_constrained_atomic.py"
)
BINDER_PATH = (
    ROOT / "09-experiments/scripts/bind_pointer_bound_compiler_output.py"
)
SCHEMA_PATH = (
    ROOT / "09-experiments/data_schema/pointer_bound_compiler_output.schema.json"
)
CONFIG_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/pointer_bound_atomic_v0.1/"
    "pointer-bound-atomic-config-v0.1.json"
)
SERIALIZATION_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "pointer-bound-serialization-contract-v0.1.json"
)
CONTRACT_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-pointer-bound-constrained-atomic-contract-v0.1.json"
)
AUTHORITY_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.44.json"
)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = load_module(RUNNER_PATH, "project05_test_pointer_bound_runner")
scorer = load_module(SCORER_PATH, "project05_test_pointer_bound_scorer")
binder = load_module(BINDER_PATH, "project05_test_pointer_binder")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


CONFIG = load_json(CONFIG_PATH)
SERIALIZATION = load_json(SERIALIZATION_PATH)["serialization"]
SCHEMA = load_json(SCHEMA_PATH)


def pointer_for(family, decision, index):
    identity = runner.sha256_text(f"{family}|{decision}|{index}")
    return {
        "artifact_id": f"ART-{identity[:16]}",
        "record_id": f"REC-{identity[16:32]}",
        "record_sha256": identity,
    }


def example_for(family, decision, index):
    pointer = pointer_for(family, decision, index)
    candidate = {
        "subject_type": "process",
        "subject_value": f"proc-{family[-4:]}-{index}.exe",
        "predicate": "wrote",
        "object_type": "file",
        "object_value": f"/tmp/object-{decision[:3]}-{index}.bin",
    }
    return {
        "example_id": f"EX-{family}-{decision}-{index:03d}",
        "split_role": "training-validation",
        "source_family_id": family,
        "source_modality": "local_log",
        "pointer": pointer,
        "source_record": {
            "payload": {
                "process": candidate["subject_value"],
                "operation": "write",
                "path": candidate["object_value"],
            }
        },
        "candidate": candidate,
        "support_decision": decision,
        "normalized_edge": (
            {**candidate, "source_pointer": pointer}
            if decision == "supported"
            else None
        ),
    }


def source_examples():
    return [
        example_for(family, decision, index)
        for family in sorted(CONFIG["panel"]["families"])
        for decision in runner.DECISIONS
        for index in range(75)
    ]


class FakeConstrainedBackend:
    def __init__(self, adapted_mode="gold", general_mode="unsupported"):
        self.adapted_mode = adapted_mode
        self.general_mode = general_mode
        self.calls = []
        self.shared = {
            "base_snapshot_sha256": "A" * 64,
            "tokenizer_snapshot_sha256": "B" * 64,
            "runtime_lock_sha256": "C" * 64,
            "quantization_config_sha256": "D" * 64,
            "serialization_contract_sha256": "E" * 64,
            "model_output_schema_sha256": "F" * 64,
            "pointer_binder_sha256": "1" * 64,
            "scorer_sha256": "2" * 64,
            "constrained_decoder_distribution": "lm-format-enforcer",
            "constrained_decoder_version": "0.10.6",
            "decode_config_sha256": runner.sha256_text(
                runner.canonical_json(CONFIG["decode"])
            ),
            "hardware_id": "fixture-rtx4090",
        }

    def shared_manifest(self):
        return dict(self.shared)

    def generate(self, condition, prompt, example):
        self.calls.append((example["example_id"], condition, prompt))
        mode = self.general_mode if condition == runner.GENERAL else self.adapted_mode
        if mode == "gold":
            output = binder.model_output_from_bound_gold(example)
        elif mode == "supported":
            output = {
                "support_decision": "supported",
                "edge_fields": copy.deepcopy(example["candidate"]),
            }
        else:
            output = {
                "support_decision": "unsupported_by_bound_pointer",
                "edge_fields": None,
            }
        text = runner.canonical_json(output)
        return {
            **self.shared,
            "adapter_state": (
                "off"
                if condition == runner.GENERAL
                else "project05_obs_compiler:on"
            ),
            "same_loaded_base_process": True,
            "schema_constrained": True,
            "raw_output": text,
            "raw_output_sha256": runner.sha256_text(text),
            "eos_terminated": True,
            "input_tokens": 100,
            "generated_tokens": 20,
            "latency_seconds": 0.01,
            "peak_allocated_bytes": 1024,
        }


def selected_panel():
    return runner.select_atomic_panel(source_examples(), CONFIG)


def run_and_score(backend):
    panel = selected_panel()
    rows, summary = runner.run_panel(panel, CONFIG, SERIALIZATION, backend)
    sanitized = scorer.make_sanitized_rows(rows, panel)
    return summary, sanitized, scorer.score_paired_rows(sanitized, CONFIG)


def test_json_schema_accepts_only_pointer_free_supported_or_unsupported_branch():
    Draft202012Validator.check_schema(SCHEMA)
    validator = Draft202012Validator(SCHEMA)
    supported = {
        "support_decision": "supported",
        "edge_fields": {
            "subject_type": "process",
            "subject_value": "a.exe",
            "predicate": "wrote",
            "object_type": "file",
            "object_value": "/tmp/a",
        },
    }
    unsupported = {
        "support_decision": "unsupported_by_bound_pointer",
        "edge_fields": None,
    }
    assert list(validator.iter_errors(supported)) == []
    assert list(validator.iter_errors(unsupported)) == []
    leaked = copy.deepcopy(supported)
    leaked["pointer"] = pointer_for("x", "supported", 1)
    assert list(validator.iter_errors(leaked))
    mismatch = copy.deepcopy(unsupported)
    mismatch["edge_fields"] = supported["edge_fields"]
    assert list(validator.iter_errors(mismatch))


def test_pointer_binding_is_programmatic_deep_copied_and_hash_identical():
    example = example_for("logpai_loghub_linux", "supported", 1)
    model_output = binder.model_output_from_bound_gold(example)
    assert "pointer" not in model_output
    assert "source_pointer" not in model_output["edge_fields"]
    bound = binder.bind_pointer(model_output, example["pointer"])
    assert bound["pointer"] == example["pointer"]
    assert bound["normalized_edge"]["source_pointer"] == example["pointer"]
    assert binder.canonical_sha256(bound["pointer"]) == binder.canonical_sha256(
        bound["normalized_edge"]["source_pointer"]
    )
    example["pointer"]["record_id"] = "MUTATED"
    assert bound["pointer"]["record_id"] != "MUTATED"


def test_binder_rejects_pointer_emission_coercion_and_decision_edge_mismatch():
    pointer = pointer_for("x", "supported", 1)
    with pytest.raises(binder.PointerBindingError):
        binder.bind_pointer(
            {
                "support_decision": "supported",
                "edge_fields": {"pointer": pointer},
            },
            pointer,
        )
    with pytest.raises(binder.PointerBindingError):
        binder.bind_pointer(
            {
                "support_decision": "unsupported_by_bound_pointer",
                "edge_fields": {},
            },
            pointer,
        )
    malformed = copy.deepcopy(pointer)
    malformed["record_sha256"] = 7
    with pytest.raises(binder.PointerBindingError):
        binder.bind_pointer(
            {
                "support_decision": "unsupported_by_bound_pointer",
                "edge_fields": None,
            },
            malformed,
        )


def test_import_and_validate_only_are_model_and_constraint_library_lazy():
    assert "torch" not in runner.__dict__
    assert "lmformatenforcer" not in sys.modules
    runner.validate_config(CONFIG)


def test_new_atomic_panel_is_balanced_deterministic_and_uses_new_seed():
    examples = source_examples()
    first = runner.select_atomic_panel(examples, CONFIG)
    second = runner.select_atomic_panel(list(reversed(examples)), CONFIG)
    assert [row["example_id"] for row in first] == [
        row["example_id"] for row in second
    ]
    assert len(first) == len({row["example_id"] for row in first}) == 16
    assert Counter(
        (row["source_family_id"], row["support_decision"]) for row in first
    ) == {
        ("logpai_loghub_linux", "supported"): 4,
        ("logpai_loghub_linux", "unsupported_by_bound_pointer"): 4,
        ("zeek_non_pcap_test_logs", "supported"): 4,
        ("zeek_non_pcap_test_logs", "unsupported_by_bound_pointer"): 4,
    }
    legacy = runner.LEGACY.select_atomic_panel(
        examples,
        load_json(
            ROOT
            / "09-experiments/llm_evidence_compiler_mainline/"
            "paired_evaluation_v0.1/paired-evaluation-config-v0.1.json"
        ),
    )
    assert {row["example_id"] for row in first} != {
        row["example_id"] for row in legacy
    }


def test_prompt_contains_bound_pointer_but_excludes_gold_and_output_pointer_request():
    example = selected_panel()[0]
    prompt = runner.render_prompt(example, SERIALIZATION)
    assert '"bound_pointer"' in prompt
    assert '"support_decision"' not in prompt.split("<|im_start|>user\n", 1)[1]
    assert '"normalized_edge"' not in prompt.split("<|im_start|>user\n", 1)[1]
    assert "Never emit, copy, alter, or invent an evidence pointer" in prompt


def test_same_prompt_constrained_schema_and_process_are_shared_between_conditions():
    summary, sanitized, report = run_and_score(FakeConstrainedBackend())
    assert summary["examples"] == 16
    assert summary["calls"] == 32
    assert summary["first_condition_counts"] == {
        runner.ADAPTED: 8,
        runner.GENERAL: 8,
    }
    assert len(sanitized) == 32
    assert report["technical_gate"]["passed"] is True
    assert all(row["schema_constrained"] for row in sanitized)
    assert all("raw_output" not in row for row in sanitized)


def test_positive_generation_gate_passes_only_for_real_supported_path():
    _, _, report = run_and_score(FakeConstrainedBackend())
    general = report["positive_generation_gate"]["conditions"][runner.GENERAL]
    adapted = report["positive_generation_gate"]["conditions"][runner.ADAPTED]
    assert general["passed"] is False
    assert general["checks"]["supported_f1_nonzero_overall"] is False
    assert adapted["passed"] is True
    assert report["positive_generation_gate"]["passed_any_condition"] is True
    assert (
        report["next_disposition"]["s0_s3_data_design_may_be_considered"]
        is True
    )
    assert report["next_disposition"]["new_qlora_training_authorized"] is False
    assert report["next_disposition"]["formal_test_authorized"] is False


def test_all_unsupported_collapse_fails_even_if_macro_metric_is_present():
    _, _, report = run_and_score(
        FakeConstrainedBackend(adapted_mode="unsupported")
    )
    gate = report["positive_generation_gate"]["conditions"][runner.ADAPTED]
    assert gate["passed"] is False
    assert gate["macro_f1_may_override"] is False
    assert gate["checks"]["supported_schema_valid_overall"] is False
    assert gate["checks"]["supported_f1_nonzero_each_family"] is False
    assert report["positive_generation_gate"]["passed_any_condition"] is False
    assert (
        report["next_disposition"]["fallback_if_all_conditions_fail"]
        == "retain_rule_strong_and_reuse_hybrid"
    )


def test_checkpoint_eligibility_precedes_ranking_and_rejects_refusal_champion():
    _, _, report = run_and_score(FakeConstrainedBackend())
    eligible_metrics = report["conditions"][runner.ADAPTED]
    refusal_metrics = copy.deepcopy(report["conditions"][runner.GENERAL])
    refusal_metrics["family_macro_support_decision_f1"] = 0.99
    reports = [
        {"epoch": 1, "metrics": refusal_metrics},
        {"epoch": 2, "metrics": eligible_metrics},
    ]
    assert scorer.checkpoint_is_eligible(refusal_metrics, CONFIG) is False
    assert scorer.choose_checkpoint(reports, CONFIG)["epoch"] == 2
    with pytest.raises(scorer.NoEligibleCheckpointError):
        scorer.choose_checkpoint([reports[0]], CONFIG)


def test_v044_bundle_is_hash_locked_and_execution_remains_closed():
    verified = runner.validate_implementation_bundle(
        CONTRACT_PATH,
        CONFIG_PATH,
        AUTHORITY_PATH,
    )
    gate = verified["authority"]["implementation_gate"]
    assert gate["model_free_implementation_authorized"] is True
    assert gate["dependency_install_authorized"] is False
    assert gate["model_execution_authorized"] is False
    assert gate["development_or_test_access_authorized"] is False
    assert verified["contract"]["parent_negative_result_authority"]["path"].endswith(
        "authority-lock-v0.43.json"
    )


def test_implementation_authority_cannot_be_reused_as_execution_authority():
    verified = {
        "contract": load_json(CONTRACT_PATH),
        "config": CONFIG,
        "contract_path": CONTRACT_PATH,
        "config_path": CONFIG_PATH,
    }
    with pytest.raises(PermissionError, match="new explicit pointer-bound execution"):
        runner.validate_execution_authority(AUTHORITY_PATH, verified)
