import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "preflight_qwen_qlora_primary.py"
CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-preflight-contract-v0.1.json"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.23.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.22.json"
PRIMARY_CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-training-contract-v0.1.json"
)
CONFIG_PATH = MAINLINE_ROOT / "qlora_primary_v0.1" / "training-config-v0.1-local.json"
LAUNCHER_PATH = MAINLINE_ROOT / "qlora_primary_v0.1" / "run-local-preflight-v0.1.ps1"


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


class PrimaryPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT_PATH, "preflight_qwen_qlora_primary")
        cls.contract = load_json(CONTRACT_PATH)
        cls.authority = load_json(AUTHORITY_PATH)
        cls.config = load_json(CONFIG_PATH)

    def test_import_is_lazy_and_has_no_model_runtime(self):
        for name in ("torch", "transformers", "peft", "bitsandbytes"):
            self.assertNotIn(name, self.module.__dict__)

    def test_contract_hashes_parent_primary_config_and_smoke_evidence(self):
        self.assertEqual(
            self.contract["parent_authority"]["sha256"],
            sha256(PARENT_AUTHORITY_PATH),
        )
        self.assertEqual(
            self.contract["primary_training_contract"]["sha256"],
            sha256(PRIMARY_CONTRACT_PATH),
        )
        self.assertEqual(
            self.contract["training_config"]["sha256"], sha256(CONFIG_PATH)
        )
        for record in self.contract["tracked_inputs"].values():
            with self.subTest(path=record["path"]):
                self.assertEqual(record["sha256"], sha256(REPO_ROOT / record["path"]))

    def test_authority_opens_only_preflight(self):
        gate = self.authority["preflight_gate"]
        self.assertTrue(gate["authorized"])
        self.assertEqual(gate["contract_sha256"], sha256(CONTRACT_PATH))
        self.assertFalse(self.authority["next_gate"]["primary_training_authorized"])
        self.assertFalse(self.authority["next_gate"]["formal_inference_authorized"])
        self.assertFalse(self.authority["next_gate"]["c07_c12_execution_authorized"])
        self.assertFalse(self.authority["next_gate"]["m3_integration_authorized"])

    def test_authority_hashes_every_preflight_deliverable(self):
        self.assertEqual(
            self.authority["parent_authority"]["sha256"],
            sha256(PARENT_AUTHORITY_PATH),
        )
        for group in (
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
        ):
            for relative, expected in self.authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_authority_guard_rejects_closed_or_wrong_contract(self):
        self.module.require_preflight_authority(
            self.authority, CONTRACT_PATH, PRIMARY_CONTRACT_PATH, CONFIG_PATH
        )
        closed = copy.deepcopy(self.authority)
        closed["preflight_gate"]["authorized"] = False
        with self.assertRaises(PermissionError):
            self.module.require_preflight_authority(
                closed, CONTRACT_PATH, PRIMARY_CONTRACT_PATH, CONFIG_PATH
            )
        wrong = copy.deepcopy(self.authority)
        wrong["preflight_gate"]["contract_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "contract SHA"):
            self.module.require_preflight_authority(
                wrong, CONTRACT_PATH, PRIMARY_CONTRACT_PATH, CONFIG_PATH
            )

    def test_projection_is_conservative_and_below_frozen_limit(self):
        projection = self.module.project_primary_wall_time(
            smoke_step_seconds=82.78099999999904,
            optimizer_steps=225,
            multiplier=2.0,
            validation_and_io_hours=6.0,
            maximum_hours=24.0,
        )
        self.assertAlmostEqual(5.1738125, projection["linear_training_hours"], places=5)
        self.assertAlmostEqual(16.347625, projection["conservative_total_hours"], places=5)
        self.assertTrue(projection["passed"])
        failed = self.module.project_primary_wall_time(200, 225, 2, 6, 24)
        self.assertFalse(failed["passed"])

    def test_module_inventory_requires_every_frozen_target(self):
        names = []
        for layer in range(2):
            names.extend(
                f"model.layers.{layer}.{target}"
                for target in self.config["lora"]["target_modules"]
            )
        report = self.module.summarize_target_module_inventory(
            names, self.config["lora"]["target_modules"]
        )
        self.assertEqual(14, report["total_matches"])
        self.assertTrue(all(value == 2 for value in report["counts"].values()))
        with self.assertRaisesRegex(ValueError, "missing"):
            self.module.summarize_target_module_inventory(
                [name for name in names if not name.endswith("down_proj")],
                self.config["lora"]["target_modules"],
            )

    def test_parameter_gate_is_strictly_below_one_percent(self):
        report = self.module.validate_trainable_ratio(
            trainable=40370176,
            total=4393342464,
            maximum_ratio=0.01,
        )
        self.assertLess(report["ratio"], 0.01)
        with self.assertRaisesRegex(ValueError, "ratio"):
            self.module.validate_trainable_ratio(10, 1000, 0.01)
        with self.assertRaises(ValueError):
            self.module.validate_trainable_ratio(0, 1000, 0.01)

    def test_sanitized_dataset_report_has_counts_not_payload(self):
        report = {
            "train": {
                "examples": 1200,
                "decisions": {
                    "supported": 600,
                    "unsupported_by_bound_pointer": 600,
                },
                "families": {"a": 300, "b": 300, "c": 300, "d": 300},
            },
            "training_validation": {
                "examples": 300,
                "decisions": {
                    "supported": 150,
                    "unsupported_by_bound_pointer": 150,
                },
                "families": {"e": 150, "f": 150},
            },
            "family_overlap": [],
            "example_id_overlap": [],
        }
        sanitized = self.module.sanitize_dataset_report(report)
        text = json.dumps(sanitized, sort_keys=True)
        self.assertNotIn("payload", text)
        self.assertNotIn("example_id", text)
        self.assertEqual(1200, sanitized["train"]["examples"])

    def test_output_path_is_exact_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            run_root = repo / ".local-qwen25-smoke"
            run_root.mkdir()
            output = run_root / "local-output" / "primary-preflight-v0.1.json"
            observed = self.module.validate_output_path(output, run_root)
            self.assertEqual(output.resolve(), observed)
            output.parent.mkdir(parents=True)
            output.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                self.module.validate_output_path(output, run_root)
            with self.assertRaises(ValueError):
                self.module.validate_output_path(repo / "outside.json", run_root)

    def test_launcher_reuses_runtime_and_contains_no_install_or_delete(self):
        launcher = LAUNCHER_PATH.read_text(encoding="utf-8")
        self.assertIn("local-runtime\\venv\\Scripts\\python.exe", launcher)
        self.assertIn("local-cache", launcher)
        for forbidden in ("pip install", "huggingface-cli", "Remove-Item", "rm -"):
            self.assertNotIn(forbidden, launcher)

    def test_static_script_has_no_training_inference_or_persistence_call(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            ".backward(",
            ".generate(",
            ".step(",
            "PagedAdam",
            "save_pretrained",
            "torch.save",
            "snapshot_download",
        ):
            self.assertNotIn(forbidden, source)

    def test_current_primary_trainer_stays_execution_closed(self):
        primary = load_json(PRIMARY_CONTRACT_PATH)
        self.assertFalse(primary["execution_authorized"])
        self.assertNotIn("primary_training_gate", self.authority)


if __name__ == "__main__":
    unittest.main()
