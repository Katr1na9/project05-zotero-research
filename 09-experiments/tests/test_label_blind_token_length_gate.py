import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "audit_label_blind_pair_tokens.py"
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
CONTRACT_ROOT = MAINLINE_ROOT / "contracts"
CONTRACT_PATH = CONTRACT_ROOT / "token-length-gate-contract-v0.1.json"
AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.13.json"
RESULT_AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.14.json"
V02_CONTRACT_PATH = CONTRACT_ROOT / "token-length-gate-contract-v0.2.json"
V016_AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.16.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class TokenLengthAuthorityTests(unittest.TestCase):
    def test_v013_hash_chain_and_model_hard_stops(self):
        authority = load_json(AUTHORITY_PATH)
        self.assertTrue(authority["tokenizer_gate"]["authority_granted"])
        self.assertFalse(authority["tokenizer_gate"]["truncation_allowed"])
        prohibited = set(authority["not_authorized"])
        self.assertIn("model_weight_download", prohibited)
        self.assertIn("transformers_install", prohibited)
        self.assertIn("formal_training", prohibited)
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_documents", "authoritative_contracts"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_contract_pins_tokenizer_only_and_exact_gate(self):
        contract = load_json(CONTRACT_PATH)
        tokenizer = contract["tokenizer"]
        self.assertEqual("Qwen/Qwen2.5-7B-Instruct", tokenizer["repository_id"])
        self.assertEqual(
            "a09a35458c702b33eeacc393d103063234e8bc28",
            tokenizer["revision"],
        )
        self.assertEqual(4, len(tokenizer["allowlisted_files"]))
        self.assertFalse(tokenizer["transformers_allowed"])
        self.assertFalse(tokenizer["model_files_allowed"])
        self.assertEqual(1500, contract["gate"]["exact_total_examples"])
        self.assertEqual(1024, contract["gate"]["maximum_p95_tokens"])
        self.assertEqual(1024, contract["gate"]["maximum_example_tokens"])
        self.assertFalse(contract["gate"]["example_exclusion_allowed"])
        self.assertFalse(contract["gate"]["truncation_allowed"])

    def test_v014_records_failed_gate_without_opening_model_gate(self):
        authority = load_json(RESULT_AUTHORITY_PATH)
        result = authority["tokenizer_gate_result"]
        self.assertFalse(result["passed"])
        self.assertEqual(1131, result["overall_p95"])
        self.assertEqual(2094, result["overall_max"])
        self.assertEqual(173, result["over_1024"])
        self.assertEqual(0, result["examples_truncated"])
        self.assertTrue(result["byte_identical_reproduction"])
        self.assertFalse(result["formal_data_gate_passed"])
        self.assertIn("model_weight_download", authority["not_authorized"])
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_contracts", "authoritative_evidence"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_v02_contract_matches_selection_serialization(self):
        contract = load_json(V02_CONTRACT_PATH)
        selection_path = REPO_ROOT / contract["inputs"]["selection_contract_path"]
        selection = load_json(selection_path)
        self.assertEqual(selection["serialization"], contract["serialization"])
        self.assertEqual(1024, contract["gate"]["maximum_example_tokens"])
        self.assertFalse(contract["gate"]["truncation_allowed"])
        self.assertEqual(
            contract["inputs"]["selection_contract_sha256"],
            sha256(selection_path),
        )

    def test_v016_passes_exact_token_gate_but_keeps_training_closed(self):
        authority = load_json(V016_AUTHORITY_PATH)
        result = authority["tokenizer_gate_result"]
        self.assertTrue(result["passed"])
        self.assertEqual(881, result["overall_p95"])
        self.assertEqual(1021, result["overall_max"])
        self.assertEqual(0, result["over_1024"])
        self.assertEqual(0, result["examples_truncated"])
        self.assertTrue(result["byte_identical_reproduction"])
        self.assertFalse(authority["next_gate"]["model_and_training_gate_open"])


class TokenLengthImplementationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT_PATH, "label_blind_token_gate")
        cls.contract = load_json(CONTRACT_PATH)

    def example(self):
        return {
            "example_id": "CEDGE-TEST",
            "split_role": "train",
            "packet_key": "family::document",
            "field_map_id": "map-v1",
            "reason_code": "pointer_swap",
            "negative_proof": {"generator": "N2"},
            "source_family_id": "example_family",
            "source_modality": "endpoint_event",
            "source_record": {
                "artifact_id": "ART-1",
                "document_id": "DOC-1",
                "record_id": "REC-1",
                "record_sha256": "A" * 64,
                "payload": {"message": "process started"},
                "provenance": {"license_id": "MIT"},
            },
            "candidate": {
                "subject_type": "process",
                "subject_value": "a",
                "predicate": "executed",
                "object_type": "command",
                "object_value": "b",
                "source_pointer": {"artifact_id": "ART-1", "record_id": "REC-2"},
            },
            "support_decision": "unsupported_by_bound_pointer",
            "normalized_edge": None,
            "pointer": {
                "artifact_id": "ART-1",
                "record_id": "REC-1",
                "record_sha256": "A" * 64,
            },
        }

    def test_serialization_excludes_generator_and_governance_fields(self):
        serialization = self.contract["serialization"]
        messages = self.module.build_messages(self.example(), serialization)
        rendered = self.module.render_messages(messages, serialization)
        self.assertEqual(["system", "user", "assistant"], [m["role"] for m in messages])
        for forbidden in serialization["forbidden_message_fields"]:
            self.assertNotIn(f'"{forbidden}"', rendered)
        self.assertNotIn("N2", rendered)
        self.assertIn("unsupported_by_bound_pointer", rendered)
        self.assertTrue(rendered.endswith("<|im_end|>\n"))

    def test_canonical_user_and_assistant_shapes_are_frozen(self):
        messages = self.module.build_messages(
            self.example(), self.contract["serialization"]
        )
        user = json.loads(messages[1]["content"])
        assistant = json.loads(messages[2]["content"])
        self.assertEqual(
            {"source_family_id", "source_modality", "source_record", "candidate"},
            set(user),
        )
        self.assertEqual(
            {"support_decision", "normalized_edge", "pointer"}, set(assistant)
        )

    def test_v02_compact_serialization_keeps_payload_candidate_and_bound_pointer(self):
        serialization = {
            **self.contract["serialization"],
            "serialization_id": "test-v0.2",
            "user_field_sources": {
                "source_modality": "source_modality",
                "bound_pointer": "pointer",
                "payload": "source_record.payload",
                "candidate": "candidate",
            },
        }
        serialization.pop("user_fields")
        messages = self.module.build_messages(self.example(), serialization)
        user = json.loads(messages[1]["content"])
        self.assertEqual(
            {"source_modality", "bound_pointer", "payload", "candidate"},
            set(user),
        )
        self.assertEqual({"message": "process started"}, user["payload"])
        self.assertEqual(self.example()["pointer"], user["bound_pointer"])
        self.assertNotIn("provenance", user)
        self.assertNotIn("source_family_id", user)

    def test_nearest_rank_percentiles_and_distribution(self):
        values = list(range(1, 101))
        self.assertEqual(50, self.module.nearest_rank(values, 0.50))
        self.assertEqual(95, self.module.nearest_rank(values, 0.95))
        report = self.module.distribution([10, 20, 30, 2000], 1024)
        self.assertEqual(20, report["p50"])
        self.assertEqual(2000, report["p95"])
        self.assertEqual(1, report["over_limit"])

    def test_lock_refuses_extra_snapshot_file(self):
        contract = json.loads(json.dumps(self.contract))
        contract["inputs"] = {}
        self.module.validate_contract_inputs = lambda _: None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            snapshot = root / "snapshot"
            snapshot.mkdir()
            for name in contract["tokenizer"]["allowlisted_files"]:
                content = "{}"
                if name == "tokenizer_config.json":
                    content = json.dumps(
                        {
                            "chat_template": (
                                "{% for message in messages %}<|im_start|>"
                                "{{ message['role'] }}<|im_end|>{% endfor %}"
                            )
                        }
                    )
                (snapshot / name).write_text(content, encoding="utf-8")
            (snapshot / "config.json").write_text("{}", encoding="utf-8")
            wheel = root / "tokenizers.whl"
            wheel.write_bytes(b"wheel")
            with self.assertRaisesRegex(ValueError, "allowlist"):
                self.module.build_tokenizer_lock(
                    contract, CONTRACT_PATH, snapshot, wheel
                )


if __name__ == "__main__":
    unittest.main()
