import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
RESULT_PATH = (
    MAINLINE_ROOT / "results" / "qwen25-primary-training-failure-result-v0.1.json"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.26.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.25.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PrimaryFailureResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(RESULT_PATH)
        cls.authority = load_json(AUTHORITY_PATH)

    def test_result_records_a_capacity_failure_not_training_success(self):
        self.assertEqual(
            "failed_primary_capacity_gate_no_checkpoint", self.result["status"]
        )
        attempt = self.result["attempt"]
        self.assertEqual(1, attempt["execution_count"])
        self.assertEqual(48, attempt["microbatches_completed"])
        self.assertEqual(3, attempt["optimizer_steps_completed"])
        self.assertEqual(0, attempt["completed_epochs"])
        self.assertEqual(0, attempt["checkpoint_count"])
        self.assertFalse(attempt["adapter_saved"])
        self.assertFalse(attempt["final_training_audit_written"])

    def test_failure_is_exactly_the_frozen_memory_gate(self):
        gate = self.result["failure_gate"]
        self.assertEqual(
            "operational peak GPU memory exceeds the frozen limit",
            gate["failure_message"],
        )
        self.assertEqual(11274289152, gate["frozen_peak_reserved_vram_limit_bytes"])
        self.assertLess(
            gate["last_accepted_recorded_peak_reserved_vram_bytes"],
            gate["frozen_peak_reserved_vram_limit_bytes"],
        )
        self.assertFalse(gate["exceeding_peak_reserved_vram_bytes_recorded"])
        self.assertFalse(gate["passed"])

    def test_source_audits_and_execution_authority_are_hash_locked(self):
        self.assertEqual(
            self.result["contract_lock"]["execution_authority_sha256"],
            sha256(PARENT_AUTHORITY_PATH),
        )
        for record in self.result["source_audits"].values():
            path = REPO_ROOT / record["local_gitignored_path"]
            self.assertEqual(record["bytes"], path.stat().st_size)
            self.assertEqual(record["sha256"], sha256(path))
            self.assertFalse(record["committed"])

    def test_no_checkpoint_selection_or_downstream_gate_is_open(self):
        for key, value in self.result["next_gate"].items():
            if key != "status":
                self.assertFalse(value, key)
        self.assertEqual(
            "hard_stop_for_new_memory_amendment_and_explicit_retry_authorization",
            self.result["next_gate"]["status"],
        )

    def test_result_is_sanitized_and_scope_preserved(self):
        scope = self.result["privacy_and_scope"]
        self.assertTrue(all(value is False or value == 0 for value in scope.values()))
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

    def test_result_authority_closes_consumed_training_authority(self):
        self.assertEqual(
            "task4_failed_memory_gate_all_execution_closed",
            self.authority["status"],
        )
        self.assertTrue(self.authority["failure_result_gate"]["attempt_completed"])
        self.assertFalse(self.authority["failure_result_gate"]["attempt_passed"])
        for key, value in self.authority["next_gate"].items():
            if key != "status":
                self.assertFalse(value, key)

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
