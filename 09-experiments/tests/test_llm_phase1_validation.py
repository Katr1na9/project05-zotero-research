import importlib.util
import inspect
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = EXPERIMENT_ROOT / "scripts" / "validate_llm_phase1_output.py"
BUILDER_PATH = EXPERIMENT_ROOT / "scripts" / "build_llm_evaluation_packets.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("llm_packet_builder_for_validation", BUILDER_PATH)
validator = load_module("validate_llm_phase1_output", VALIDATOR_PATH)


def fixture_valid_candidate_and_packet():
    payload = {
        "operation": "EVENT_WRITE",
        "process": "PowerShell.EXE",
        "command": "Compress-Archive C:\\Temp\\A.txt C:\\Temp\\A.zip",
    }
    record = builder.make_packet_record(
        "local_log",
        {"artifact_id": "SRC-C07-01", "record_id": "event-public-1"},
        payload,
    )
    packet = {
        "request_id": "REQ-" + "A" * 24,
        "case_id": "C07-evaluation-case",
        "split": "test",
        "packet_role": "positive",
        "support_ceiling": "G2_tactic_intent",
        "records": [record],
    }
    candidate = {
        "candidate_claim_id": builder.derive_candidate_claim_id(
            packet["request_id"], "general_compiler", 0, 0
        ),
        "source_type": "local_log",
        "subject": {"entity_type": "process", "value": "powershell.exe"},
        "predicate": "created",
        "object": {"entity_type": "file", "value": "C:\\Temp\\A.zip"},
        "source_pointer": dict(record["source_pointer"]),
    }
    return candidate, packet


class G0AdmissionTests(unittest.TestCase):
    def test_admission_signature_and_result_do_not_depend_on_private_gold(self):
        self.assertEqual(
            [
                "candidate",
                "packet",
                "condition_id",
                "attempt_index",
                "output_index",
            ],
            list(inspect.signature(validator.validate_candidate).parameters),
        )
        candidate, packet = fixture_valid_candidate_and_packet()
        before = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )
        private_gold = {
            "acceptable_observations": [{"predicate": "contradicts-candidate"}]
        }
        private_gold["acceptable_observations"][0]["predicate"] = "another-change"
        after = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertEqual([], before)
        self.assertEqual(before, after)

    def test_candidate_id_pointer_hash_and_literal_checks_are_g0_only(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        candidate["candidate_claim_id"] = "CC-" + "B" * 24
        candidate["object"]["value"] = "C:\\Absent\\payload.exe"
        packet["records"][0]["record_sha256"] = "0" * 64

        errors = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertEqual(
            [
                "candidate_id_mismatch",
                "literal_entity_not_in_source",
                "record_sha256_mismatch",
            ],
            errors,
        )

    def test_pointer_outside_packet_is_rejected(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        candidate["source_pointer"]["record_id"] = "outside-packet"

        errors = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertIn("pointer_not_in_packet", errors)

    def test_non_object_candidate_is_schema_rejected_without_crashing(self):
        _, packet = fixture_valid_candidate_and_packet()

        errors = validator.validate_candidate(
            [], packet, "general_compiler", 0, 0
        )

        self.assertIn("candidate_schema_invalid", errors)

    def test_admission_returns_machine_gap_codes(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        invalid = json.loads(json.dumps(candidate))
        invalid["candidate_claim_id"] = builder.derive_candidate_claim_id(
            packet["request_id"], "general_compiler", 0, 1
        )
        invalid["object"]["value"] = "not-visible"
        result = {
            "request_id": packet["request_id"],
            "condition_id": "general_compiler",
            "attempt_index": 0,
            "status": "completed",
            "candidate_claims": [candidate, invalid],
            "telemetry": {
                "latency_ms": 0,
                "peak_vram_mb": 0,
                "input_tokens": None,
                "output_tokens": None,
                "error_code": None,
            },
        }

        admission = validator.admit_candidates(result, packet)

        self.assertEqual(1, len(admission["admitted_claims"]))
        self.assertEqual(1, len(admission["rejected"]))
        self.assertEqual(["literal_entity_absent"], admission["explicit_gaps"])

    def test_structured_stage2_input_excludes_raw_rejected_and_private(self):
        payload = validator.build_structured_stage2_input(
            {
                "admitted_claims": [{"candidate_claim_id": "CC-" + "A" * 24}],
                "rejected": [{"raw": "secret"}],
                "explicit_gaps": ["missing_source"],
                "private_gold": {"answer": "secret"},
            },
            "G2_tactic_intent",
        )
        serialized = json.dumps(payload, sort_keys=True)

        self.assertNotIn("source_payload", serialized)
        self.assertNotIn("rejected", serialized)
        self.assertNotIn("private", serialized)
        self.assertEqual(
            {"admitted_claims", "explicit_gaps", "support_ceiling"},
            set(payload),
        )


class ManifestValidationTests(unittest.TestCase):
    def test_manifest_rejects_config_and_input_drift(self):
        config = {"experiment_id": "phase1", "status": "pre_model"}
        input_manifest = {"packet_count": 64, "split": "test"}
        prompt_lock = {
            "contract_sha256": "C" * 64,
            "prompt_sha256": {"compiler": "D" * 64},
        }
        model_lock = {
            "model_role": "general",
            "model_id": "stub",
            "revision": None,
            "weights_sha256": None,
        }
        manifest = {
            "input_manifest_sha256": validator.hash_value(input_manifest),
            "config_sha256": validator.hash_value(config),
            "contract_sha256": "C" * 64,
            "prompt_sha256": {"compiler": "D" * 64},
            "model_lock": model_lock,
        }

        self.assertEqual(
            [],
            validator.validate_run_manifest(
                manifest, config, input_manifest, prompt_lock, model_lock
            ),
        )
        changed = dict(config, status="changed-after-lock")
        self.assertEqual(
            ["config_sha256_mismatch"],
            validator.validate_run_manifest(
                manifest, changed, input_manifest, prompt_lock, model_lock
            ),
        )


if __name__ == "__main__":
    unittest.main()
