import copy
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = (
    ROOT / "09-experiments/scripts/run_qwen_general_adapted_paired.py"
)
SCORER_PATH = (
    ROOT / "09-experiments/scripts/score_qwen_general_adapted_paired.py"
)
CONFIG_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/"
    "paired_evaluation_v0.1/paired-evaluation-config-v0.1.json"
)
CONTRACT_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "qwen25-general-adapted-paired-contract-v0.1.json"
)
AUTHORITY_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "authority-lock-v0.41.json"
)
SERIALIZATION_PATH = (
    ROOT
    / "09-experiments/llm_evidence_compiler_mainline/contracts/"
    "token-length-gate-contract-v0.2.json"
)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = load_module(RUNNER_PATH, "project05_test_paired_runner")
scorer = load_module(SCORER_PATH, "project05_test_paired_scorer")


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


CONFIG = load_json(CONFIG_PATH)
SERIALIZATION = load_json(SERIALIZATION_PATH)["serialization"]


def pointer_for(family, decision, index):
    identity = runner.sha256_text(f"{family}|{decision}|{index}")
    return {
        "artifact_id": f"ART-{identity[:16]}",
        "record_id": f"REC-{identity[16:32]}",
        "record_sha256": identity,
    }


def example_for(family, decision, index):
    pointer = pointer_for(family, decision, index)
    subject = f"proc-{family[-4:]}-{index}.exe"
    object_value = f"/tmp/object-{decision[:3]}-{index}.bin"
    candidate = {
        "subject_type": "process",
        "subject_value": subject,
        "predicate": "wrote",
        "object_type": "file",
        "object_value": object_value,
    }
    edge = (
        {
            **candidate,
            "source_pointer": pointer,
        }
        if decision == "supported"
        else None
    )
    return {
        "example_id": f"EX-{family}-{decision}-{index:03d}",
        "split_role": "training-validation",
        "source_family_id": family,
        "source_modality": "local_log",
        "pointer": pointer,
        "source_record": {
            "payload": {
                "process": subject,
                "operation": "write",
                "path": object_value,
            }
        },
        "candidate": candidate,
        "support_decision": decision,
        "normalized_edge": edge,
    }


def source_examples():
    output = []
    for family in sorted(CONFIG["panel"]["families"]):
        for decision in runner.DECISIONS:
            output.extend(example_for(family, decision, i) for i in range(75))
    return output


def prediction_for(example, use_gold):
    if use_gold:
        decision = example["support_decision"]
        edge = example["normalized_edge"]
    else:
        decision = "unsupported_by_bound_pointer"
        edge = None
    return {
        "support_decision": decision,
        "normalized_edge": edge,
        "pointer": example["pointer"],
    }


class FakeBackend:
    def __init__(self, adapted_uses_gold=True, invalid_condition=None):
        self.adapted_uses_gold = adapted_uses_gold
        self.invalid_condition = invalid_condition
        self.calls = []
        self.shared = {
            "base_snapshot_sha256": "A" * 64,
            "tokenizer_snapshot_sha256": "B" * 64,
            "runtime_lock_sha256": "C" * 64,
            "quantization_config_sha256": "D" * 64,
            "serialization_contract_sha256": "E" * 64,
            "atomic_admission_sha256": "F" * 64,
            "scorer_sha256": "1" * 64,
            "max_context_tokens": 1024,
            "decode_config_sha256": runner.sha256_text(
                runner.canonical_json(CONFIG["decode"])
            ),
            "hardware_id": "fixture-rtx4090",
        }

    def shared_manifest(self):
        return dict(self.shared)

    def generate(self, condition, prompt, example):
        self.calls.append((example["example_id"], condition, prompt))
        if condition == self.invalid_condition:
            text = "not-json"
        else:
            use_gold = condition == runner.ADAPTED and self.adapted_uses_gold
            text = runner.canonical_json(prediction_for(example, use_gold))
        return {
            **self.shared,
            "adapter_state": (
                "off"
                if condition == runner.GENERAL
                else "project05_obs_compiler:on"
            ),
            "same_loaded_base_process": True,
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


def test_import_and_validate_only_path_remain_model_lazy():
    assert "torch" not in runner.__dict__
    assert "transformers" not in runner.__dict__
    runner.validate_config(CONFIG)


def test_atomic_panel_is_deterministic_balanced_and_without_replacement():
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


def test_condition_order_is_exactly_balanced_in_every_block():
    panel = selected_panel()
    orders = runner.build_condition_orders(panel, CONFIG)
    for family in CONFIG["panel"]["families"]:
        for decision in runner.DECISIONS:
            subset = [
                orders[row["example_id"]][0]
                for row in panel
                if row["source_family_id"] == family
                and row["support_decision"] == decision
            ]
            assert Counter(subset) == {
                runner.GENERAL: 2,
                runner.ADAPTED: 2,
            }


def test_prompt_excludes_gold_and_governance_fields():
    example = selected_panel()[0]
    prompt = runner.render_prompt(example, SERIALIZATION)
    assert '"support_decision"' not in prompt
    assert '"normalized_edge"' not in prompt
    for field in SERIALIZATION["forbidden_message_fields"]:
        assert f'"{field}"' not in prompt


def test_private_scoring_mutation_does_not_change_public_input_hash():
    example = selected_panel()[0]
    mutated = copy.deepcopy(example)
    mutated["support_decision"] = "unsupported_by_bound_pointer"
    mutated["normalized_edge"] = None
    mutated["private_reference_only"] = "changed"
    assert runner.public_input_sha256(example) == runner.public_input_sha256(
        mutated
    )


def test_runner_pairs_same_prompt_and_only_toggles_adapter_state():
    panel = selected_panel()
    backend = FakeBackend()
    rows, audit = runner.run_panel(panel, CONFIG, SERIALIZATION, backend)
    assert audit["examples"] == 16
    assert audit["calls"] == 32
    assert audit["first_condition_counts"] == {
        runner.ADAPTED: 8,
        runner.GENERAL: 8,
    }
    paired = scorer.pair_generation_rows(rows)
    for pair in paired.values():
        scorer.assert_fair_pair(pair)
        assert (
            pair[runner.GENERAL]["prompt_sha256"]
            == pair[runner.ADAPTED]["prompt_sha256"]
        )
        assert (
            pair[runner.GENERAL]["public_input_sha256"]
            == pair[runner.ADAPTED]["public_input_sha256"]
        )


def test_scorer_keeps_raw_generation_out_and_passes_clear_adapted_gain():
    panel = selected_panel()
    rows, _ = runner.run_panel(
        panel,
        CONFIG,
        SERIALIZATION,
        FakeBackend(adapted_uses_gold=True),
    )
    sanitized = scorer.make_sanitized_rows(rows, panel)
    assert len(sanitized) == 32
    assert all("raw_output" not in row for row in sanitized)
    assert all(row["raw_generation_included"] is False for row in sanitized)
    report = scorer.score_paired_rows(sanitized, CONFIG)
    assert report["technical_gate"]["passed"] is True
    assert report["adapter_diagnostic_gate"]["passed"] is True
    assert (
        report["conditions"][runner.GENERAL]["overall_supported_class_f1"]
        == 0.0
    )
    assert (
        report["conditions"][runner.ADAPTED]["overall_supported_class_f1"]
        == 1.0
    )
    assert (
        report["adapter_diagnostic_gate"]["may_select_adapter_for_mainline"]
        is False
    )


def test_supported_class_collapse_is_an_explicit_negative_diagnostic():
    panel = selected_panel()
    rows, _ = runner.run_panel(
        panel,
        CONFIG,
        SERIALIZATION,
        FakeBackend(adapted_uses_gold=False),
    )
    report = scorer.score_paired_rows(
        scorer.make_sanitized_rows(rows, panel),
        CONFIG,
    )
    assert report["technical_gate"]["passed"] is True
    assert report["adapter_diagnostic_gate"]["passed"] is False
    checks = report["adapter_diagnostic_gate"]["checks"]
    assert checks["adapted_supported_f1_nonzero_overall"] is False
    assert checks["adapted_supported_f1_nonzero_each_family"] is False
    assert report["scientific_scope"]["paper_positive_claim_authorized"] is False


def test_invalid_first_pass_is_scored_as_invalid_without_repair():
    panel = selected_panel()
    rows, _ = runner.run_panel(
        panel,
        CONFIG,
        SERIALIZATION,
        FakeBackend(invalid_condition=runner.ADAPTED),
    )
    sanitized = scorer.make_sanitized_rows(rows, panel)
    adapted = [row for row in sanitized if row["condition"] == runner.ADAPTED]
    assert all(row["predicted_decision"] == "invalid" for row in adapted)
    assert all(row["failure_reason"] == "invalid_json" for row in adapted)


def test_forbidden_between_condition_difference_fails_closed():
    panel = selected_panel()
    rows, _ = runner.run_panel(
        panel,
        CONFIG,
        SERIALIZATION,
        FakeBackend(),
    )
    paired = scorer.pair_generation_rows(rows)
    pair = copy.deepcopy(next(iter(paired.values())))
    pair[runner.ADAPTED]["hardware_id"] = "different-gpu"
    with pytest.raises(ValueError, match="forbidden between-condition difference"):
        scorer.assert_fair_pair(pair)


def test_v041_bundle_is_hash_locked_and_model_execution_remains_closed():
    verified = runner.validate_implementation_bundle(
        CONTRACT_PATH,
        CONFIG_PATH,
        AUTHORITY_PATH,
    )
    gate = verified["authority"]["paired_gate"]
    assert gate["implementation_authorized"] is True
    assert gate["model_execution_authorized"] is False
    assert gate["development_or_test_access_authorized"] is False
    assert gate["c07_c12_execution_authorized"] is False
    assert gate["m3_integration_authorized"] is False
    assert verified["contract"]["selected_adapter"]["epoch"] == 2
    assert (
        verified["contract"]["selected_adapter"]["adapter_sha256"]
        == "D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11"
    )


def test_current_implementation_authority_cannot_be_used_as_execution_authority():
    verified = {
        "contract": load_json(CONTRACT_PATH),
        "config": CONFIG,
        "contract_path": CONTRACT_PATH,
        "config_path": CONFIG_PATH,
    }
    with pytest.raises(PermissionError, match="explicit paired execution"):
        runner.validate_execution_authority(AUTHORITY_PATH, verified)
