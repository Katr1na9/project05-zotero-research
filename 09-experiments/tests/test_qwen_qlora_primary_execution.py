import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "execute_qwen_qlora_primary.py"
LAUNCHER_PATH = (
    MAINLINE_ROOT / "qlora_primary_v0.1" / "run-local-primary-v0.1.ps1"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.25.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.24.json"
CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-training-contract-v0.1.json"
)
CONFIG_PATH = MAINLINE_ROOT / "qlora_primary_v0.1" / "training-config-v0.1-local.json"


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


class PrimaryExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT_PATH, "execute_qwen_qlora_primary")
        cls.authority = load_json(AUTHORITY_PATH)
        cls.contract = load_json(CONTRACT_PATH)
        cls.config = load_json(CONFIG_PATH)

    def test_import_is_lazy_and_does_not_load_model_runtime(self):
        for name in ("torch", "transformers", "peft", "bitsandbytes"):
            self.assertNotIn(name, self.module.__dict__)

    def test_task4_authority_opens_exactly_one_primary_run(self):
        gate = self.authority["primary_training_gate"]
        self.assertTrue(gate["authorized"])
        self.assertEqual(1, gate["maximum_executions"])
        self.assertFalse(gate["resume_authorized"])
        self.assertEqual(gate["contract_sha256"], sha256(CONTRACT_PATH))
        self.assertEqual(gate["training_config_sha256"], sha256(CONFIG_PATH))
        self.assertTrue(self.authority["next_gate"]["primary_training_authorized"])
        for closed in (
            "checkpoint_selection_authorized",
            "paired_runner_authorized",
            "formal_inference_authorized",
            "development_execution_authorized",
            "c07_c12_execution_authorized",
            "m3_integration_authorized",
        ):
            self.assertFalse(self.authority["next_gate"][closed])

    def test_authority_hash_chain_covers_every_task4_deliverable(self):
        parent = self.authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in (
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
            "authoritative_results",
        ):
            for relative, expected in self.authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_output_root_is_exact_and_refuses_a_second_run(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            run = repo / ".local-qwen25-smoke"
            run.mkdir(parents=True)
            contract = {
                "execution_boundary": {
                    "run_directory_name": ".local-qwen25-smoke",
                    "primary_output_subdirectory": "local-output/primary-v0.1",
                }
            }
            output = self.module.expected_output_root(run, contract, repo)
            self.assertEqual((run / "local-output" / "primary-v0.1").resolve(), output)
            wrong = dict(contract)
            wrong["execution_boundary"] = dict(contract["execution_boundary"])
            wrong["execution_boundary"]["primary_output_subdirectory"] = "other"
            with self.assertRaises(ValueError):
                self.module.expected_output_root(run, wrong, repo)

    def test_progress_writer_rejects_payload_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progress.jsonl"
            self.module.append_progress(
                path,
                {
                    "event": "optimizer_step_completed",
                    "epoch": 1,
                    "optimizer_step": 1,
                    "optimizer_steps_total": 225,
                    "elapsed_seconds": 3.0,
                },
            )
            self.assertEqual(1, len(path.read_text(encoding="utf-8").splitlines()))
            with self.assertRaises(ValueError):
                self.module.append_progress(path, {"event": "bad", "payload": {}})

    def test_completion_gate_requires_exact_3_epoch_225_step_run(self):
        valid = {
            "completed_epochs": 3,
            "optimizer_steps": 225,
            "microbatches": 3600,
            "checkpoint_epochs": [1, 2, 3],
            "losses_finite": True,
            "gradient_norms_finite": True,
        }
        self.module.validate_completed_training(valid, self.config)
        for field, value in (
            ("completed_epochs", 2),
            ("optimizer_steps", 224),
            ("microbatches", 3599),
            ("checkpoint_epochs", [1, 2]),
            ("losses_finite", False),
        ):
            broken = dict(valid)
            broken[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.validate_completed_training(broken, self.config)

    def test_launcher_reuses_offline_runtime_and_has_no_install_or_delete(self):
        launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
        self.assertIn("local-runtime\\venv\\Scripts\\python.exe", launcher)
        self.assertIn('$env:HF_HUB_OFFLINE = "1"', launcher)
        self.assertIn('$env:TRANSFORMERS_OFFLINE = "1"', launcher)
        self.assertIn("authority-lock-v0.25.json", launcher)
        for forbidden in ("pip install", "snapshot_download", "Remove-Item", "rm -"):
            self.assertNotIn(forbidden, launcher)

    def test_static_execution_has_no_generation_merge_upload_or_adjacent_scope(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            ".generate(",
            "merge_and_unload",
            "push_to_hub",
            "snapshot_download",
            "run_llm_evidence_compiler_paired",
            "import run_mvp",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("local_files_only=True", source)
        self.assertIn("model.save_pretrained(adapter_dir", source)

    def test_failure_and_success_outputs_keep_downstream_gates_closed(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("automatic_restart_authorized\": False", source)
        self.assertIn("checkpoint_selection_authorized\": False", source)
        self.assertIn("model_generation_calls\": 0", source)
        self.assertIn("merged_model_saved\": False", source)


if __name__ == "__main__":
    unittest.main()
