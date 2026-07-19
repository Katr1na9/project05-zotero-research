import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
RESULT_PATH = (
    MAINLINE_ROOT
    / "results"
    / "qwen25-memory-stress-preflight-failure-result-v0.1.json"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.28.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.27.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class MemoryStressResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(RESULT_PATH)
        cls.authority = load_json(AUTHORITY_PATH)

    def test_result_records_completed_stress_but_failed_memory_gate(self):
        self.assertEqual(
            "failed_memory_stress_preflight_peak_reserved_no_artifact",
            self.result["status"],
        )
        attempt = self.result["attempt"]
        self.assertEqual(1, attempt["execution_count"])
        self.assertEqual(16, attempt["microbatches_completed"])
        self.assertEqual(1, attempt["optimizer_steps_completed"])
        self.assertEqual(0, attempt["checkpoint_count"])
        self.assertFalse(attempt["adapter_saved"])
        self.assertEqual(0, attempt["model_generation_calls"])

    def test_numerical_gate_passes_but_reserved_memory_gate_fails(self):
        self.assertTrue(self.result["numerical_gate"]["passed"])
        self.assertTrue(self.result["numerical_gate"]["losses_finite"])
        gate = self.result["memory_gate"]
        self.assertFalse(gate["cuda_oom"])
        self.assertEqual(11274289152, gate["frozen_peak_reserved_limit_bytes"])
        self.assertEqual(13788774400, gate["peak_reserved_bytes"])
        self.assertGreater(
            gate["peak_reserved_bytes"], gate["frozen_peak_reserved_limit_bytes"]
        )
        self.assertEqual(
            gate["peak_reserved_bytes"] - gate["frozen_peak_reserved_limit_bytes"],
            gate["excess_reserved_bytes"],
        )
        self.assertFalse(gate["passed"])

    def test_longest_selection_envelope_is_frozen_without_raw_content(self):
        selection = self.result["selection_envelope"]
        self.assertEqual(16, len(selection["lengths_descending"]))
        self.assertEqual(15999, selection["total_tokens"])
        self.assertEqual(982, selection["minimum_tokens"])
        self.assertEqual(1021, selection["maximum_tokens"])
        self.assertFalse(selection["raw_identifiers_recorded"])
        self.assertFalse(selection["raw_content_recorded"])

    def test_local_audit_and_execution_authority_are_hash_locked(self):
        record = self.result["source_audit"]
        path = REPO_ROOT / record["local_gitignored_path"]
        self.assertEqual(record["bytes"], path.stat().st_size)
        self.assertEqual(record["sha256"], sha256(path))
        self.assertFalse(record["committed"])
        self.assertEqual(
            self.result["contract_lock"]["execution_authority_sha256"],
            sha256(PARENT_AUTHORITY_PATH),
        )

    def test_result_is_sanitized_and_scope_preserved(self):
        scope = self.result["privacy_and_scope"]
        self.assertTrue(all(value is False for value in scope.values()))
        keys = set()

        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    keys.add(key)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(self.result)
        for forbidden in ("payload", "example_id", "case_id", "model_output"):
            self.assertNotIn(forbidden, keys)

    def test_result_and_authority_close_every_downstream_gate(self):
        for container in (self.result["next_gate"], self.authority["next_gate"]):
            for key, value in container.items():
                if key != "status":
                    self.assertFalse(value, key)
        self.assertFalse(self.authority["memory_stress_result_gate"]["attempt_passed"])
        self.assertTrue(self.authority["memory_stress_result_gate"]["attempt_completed"])

    def test_result_authority_hash_chain_and_deliverables(self):
        parent = self.authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in (
            "authoritative_tests",
            "authoritative_results",
            "authoritative_documentation",
        ):
            for relative, expected in self.authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))


if __name__ == "__main__":
    unittest.main()
