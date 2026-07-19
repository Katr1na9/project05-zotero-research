import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
RESULT_PATH = MAINLINE_ROOT / "results" / "qwen25-primary-preflight-result-v0.1.json"
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.24.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.23.json"
PREFLIGHT_CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-preflight-contract-v0.1.json"
)
PRIMARY_CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-training-contract-v0.1.json"
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PrimaryPreflightResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = load_json(RESULT_PATH)
        cls.authority = load_json(AUTHORITY_PATH)

    def test_result_is_a_passed_zero_step_preflight(self):
        self.assertEqual("passed_zero_step_primary_preflight", self.result["status"])
        proof = self.result["zero_step_proof"]
        for field in (
            "model_forward_calls",
            "generation_calls",
            "loss_calls",
            "backward_calls",
            "optimizer_objects_created",
            "optimizer_steps",
            "scheduler_objects_created",
            "adapter_or_checkpoint_files_written",
        ):
            with self.subTest(field=field):
                self.assertEqual(0, proof[field])
        self.assertFalse(proof["network_or_download_used"])

    def test_result_hashes_the_exact_execution_authority_and_contracts(self):
        lock = self.result["contract_lock"]
        self.assertEqual(lock["authority_sha256"], sha256(PARENT_AUTHORITY_PATH))
        self.assertEqual(
            lock["preflight_contract_sha256"], sha256(PREFLIGHT_CONTRACT_PATH)
        )
        self.assertEqual(
            lock["primary_training_contract_sha256"], sha256(PRIMARY_CONTRACT_PATH)
        )
        self.assertEqual(
            lock["training_config_sha256"],
            sha256(
                MAINLINE_ROOT
                / "qlora_primary_v0.1"
                / "training-config-v0.1-local.json"
            ),
        )

    def test_data_gate_is_balanced_and_family_disjoint(self):
        gate = self.result["data_gate"]
        self.assertEqual(1200, gate["train"]["examples"])
        self.assertEqual(300, gate["training_validation"]["examples"])
        self.assertEqual(
            {"supported": 600, "unsupported_by_bound_pointer": 600},
            gate["train"]["decisions"],
        )
        self.assertEqual(
            {"supported": 150, "unsupported_by_bound_pointer": 150},
            gate["training_validation"]["decisions"],
        )
        self.assertEqual(set(), set(gate["train"]["families"]) & set(gate["training_validation"]["families"]))
        self.assertEqual([], gate["family_overlap"])

    def test_lora_parameter_and_module_gates_pass(self):
        inventory = self.result["lora_inventory"]
        self.assertTrue(inventory["adapter_attached_in_memory_only"])
        self.assertFalse(inventory["adapter_saved"])
        self.assertTrue(inventory["all_target_families_present"])
        self.assertEqual(196, inventory["total_matches"])
        self.assertEqual(set(inventory["target_modules"]), set(inventory["counts"]))
        self.assertTrue(all(value == 28 for value in inventory["counts"].values()))
        self.assertGreater(inventory["trainable_ratio"], 0)
        self.assertLess(
            inventory["trainable_ratio"], inventory["maximum_trainable_ratio"]
        )
        self.assertTrue(inventory["passed"])

    def test_capacity_gates_pass_without_being_claimed_as_training(self):
        self.assertLessEqual(
            self.result["memory_gate"]["peak_reserved_bytes"],
            self.result["memory_gate"]["peak_limit_bytes"],
        )
        self.assertEqual(
            2097152, self.result["memory_gate"]["post_cleanup_reserved_bytes"]
        )
        projection = self.result["wall_time_projection"]
        self.assertLessEqual(
            projection["conservative_total_hours"], projection["maximum_hours"]
        )
        self.assertEqual(
            "capacity_projection_not_a_training_result", projection["interpretation"]
        )
        resources = self.result["resource_gate"]
        self.assertLessEqual(
            resources["projected_total_bytes"], resources["maximum_total_bytes"]
        )

    def test_result_is_sanitized_and_scope_closed(self):
        def collect_keys(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    yield key
                    yield from collect_keys(child)
            elif isinstance(value, list):
                for child in value:
                    yield from collect_keys(child)

        keys = set(collect_keys(self.result))
        for forbidden in (
            "payload",
            "raw_text",
            "model_output",
            "example_ids",
            "example_id",
            "case_id",
            "claim_id",
            "sample_id",
        ):
            self.assertNotIn(forbidden, keys)
        scope = self.result["privacy_and_scope"]
        self.assertTrue(all(value is False for value in scope.values()))
        self.assertFalse(self.result["next_gate"]["primary_training_authorized"])
        self.assertFalse(self.result["next_gate"]["formal_inference_authorized"])
        self.assertFalse(self.result["next_gate"]["m3_integration_authorized"])

    def test_result_authority_hash_chain_and_deliverables(self):
        parent = self.authority["parent_authority"]
        self.assertEqual(parent["path"], str(PARENT_AUTHORITY_PATH.relative_to(REPO_ROOT)).replace("\\", "/"))
        self.assertEqual(parent["sha256"], sha256(PARENT_AUTHORITY_PATH))
        for group in (
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
            "authoritative_results",
            "authoritative_documentation",
        ):
            for relative, expected in self.authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_result_authority_keeps_task4_and_downstream_gates_closed(self):
        self.assertEqual(
            "task3_preflight_passed_task4_primary_training_closed",
            self.authority["status"],
        )
        self.assertTrue(self.authority["preflight_result_gate"]["execution_passed"])
        self.assertEqual(0, self.authority["preflight_result_gate"]["optimizer_steps"])
        self.assertFalse(self.authority["next_gate"]["primary_training_authorized"])
        self.assertFalse(self.authority["next_gate"]["formal_inference_authorized"])
        self.assertFalse(self.authority["next_gate"]["c07_c12_execution_authorized"])
        self.assertFalse(self.authority["next_gate"]["m3_integration_authorized"])


if __name__ == "__main__":
    unittest.main()
