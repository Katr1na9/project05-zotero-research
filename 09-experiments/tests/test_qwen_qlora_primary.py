import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "train_qwen_qlora_primary.py"
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-primary-training-contract-v0.1.json"
)
CONFIG_PATH = MAINLINE_ROOT / "qlora_primary_v0.1" / "training-config-v0.1-local.json"
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.22.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.21.json"
PLAN_PATH = (
    REPO_ROOT
    / "08-writing"
    / "llm-evidence-compiler-primary-training-and-paired-evaluation-plan-v0.1-20260719.md"
)


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


def example(number: int, decision: str, family: str) -> dict:
    pointer = {
        "artifact_id": f"ART-{number}",
        "record_id": f"REC-{number}",
        "record_sha256": f"{number % 16:X}" * 64,
    }
    return {
        "example_id": f"CEDGE-{family}-{decision}-{number:04d}",
        "source_family_id": family,
        "source_modality": "endpoint_event",
        "source_record": {"payload": {"message": f"event {number}"}},
        "candidate": {
            "subject_type": "process",
            "subject_value": "a",
            "predicate": "executed",
            "object_type": "command",
            "object_value": "b",
            "source_pointer": pointer,
        },
        "support_decision": decision,
        "normalized_edge": (
            {"predicate": "executed"} if decision == "supported" else None
        ),
        "pointer": pointer,
    }


class QwenQloraPrimaryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.primary = load_module(SCRIPT_PATH, "train_qwen_qlora_primary")
        cls.contract = load_json(CONTRACT_PATH)
        cls.config = load_json(CONFIG_PATH)
        cls.authority = load_json(AUTHORITY_PATH)

    def test_import_is_lazy_and_never_loads_model_runtime(self):
        for name in ("torch", "transformers", "peft", "bitsandbytes"):
            self.assertNotIn(name, self.primary.__dict__)

    def test_contract_pins_plan_parent_data_runtime_and_config(self):
        self.assertEqual(
            self.contract["parent_authority"]["sha256"],
            sha256(PARENT_AUTHORITY_PATH),
        )
        self.assertEqual(self.contract["approved_plan"]["sha256"], sha256(PLAN_PATH))
        self.assertEqual(
            self.contract["training_config"]["sha256"], sha256(CONFIG_PATH)
        )
        for record in self.contract["frozen_inputs"].values():
            with self.subTest(path=record["path"]):
                self.assertEqual(record["sha256"], sha256(REPO_ROOT / record["path"]))
        self.assertFalse(self.contract["execution_authorized"])

    def test_config_is_the_single_frozen_primary_run(self):
        config = self.config
        self.assertEqual(1200, config["data"]["train_examples"])
        self.assertEqual(300, config["data"]["training_validation_examples"])
        self.assertEqual(4, config["data"]["train_source_families"])
        self.assertEqual(2, config["data"]["training_validation_source_families"])
        self.assertEqual(0.5, config["data"]["supported_fraction"])
        self.assertEqual(3, config["epochs"])
        self.assertEqual(1, config["micro_batch_size"])
        self.assertEqual(16, config["gradient_accumulation_steps"])
        self.assertEqual(225, config["optimizer_steps"])
        self.assertEqual(7, config["scheduler"]["warmup_steps"])
        self.assertEqual(1024, config["sequence_length"])
        self.assertFalse(config["allow_truncation"])
        self.assertEqual(2026071601, config["seed"])
        self.assertTrue(config["output_policy"]["adapter_only"])
        self.assertFalse(config["output_policy"]["allow_merged_model"])
        self.assertFalse(config["output_policy"]["allow_hub_upload"])
        self.assertEqual(
            "family_macro_support_decision_f1",
            config["training_validation"]["primary_metric"],
        )
        self.assertEqual(
            "earlier_epoch", config["training_validation"]["tie_breakers"][-1]
        )

    def test_authority_records_only_tasks_one_and_two(self):
        authority = self.authority
        self.assertEqual(
            "tasks_1_2_implementation_authorized_execution_closed",
            authority["status"],
        )
        self.assertTrue(authority["implementation_gate"]["authorized"])
        self.assertEqual(
            [
                "primary_training_contract_and_config",
                "primary_trainer_skeleton",
                "model_free_negative_tests",
            ],
            authority["implementation_gate"]["authorized_deliverables"],
        )
        for gate in (
            "formal_preflight_authorized",
            "primary_training_authorized",
            "formal_inference_authorized",
            "development_execution_authorized",
            "c07_c12_execution_authorized",
            "m3_integration_authorized",
        ):
            self.assertFalse(authority["next_gate"][gate])

    def test_validate_config_rejects_every_scientific_mutation(self):
        self.primary.validate_primary_config(self.config, self.contract)
        mutations = (
            ("sequence_length", 768),
            ("allow_truncation", True),
            ("epochs", 2),
            ("optimizer_steps", 224),
            ("seed", 3),
            ("learning_rate", 0.0001),
            ("gradient_accumulation_steps", 8),
        )
        for key, value in mutations:
            mutated = copy.deepcopy(self.config)
            mutated[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.primary.validate_primary_config(mutated, self.contract)
        mutated = copy.deepcopy(self.config)
        mutated["lora"]["rank"] = 8
        with self.assertRaises(ValueError):
            self.primary.validate_primary_config(mutated, self.contract)

    def test_schedule_is_exact_and_has_no_partial_accumulation(self):
        schedule = self.primary.build_training_schedule(self.config)
        self.assertEqual(3600, schedule["microbatches"])
        self.assertEqual(225, schedule["optimizer_steps"])
        self.assertEqual(75, schedule["optimizer_steps_per_epoch"])
        self.assertEqual([75, 150, 225], schedule["checkpoint_steps"])
        self.assertEqual(7, schedule["warmup_steps"])
        broken = copy.deepcopy(self.config)
        broken["data"]["train_examples"] = 1201
        with self.assertRaisesRegex(ValueError, "divisible"):
            self.primary.build_training_schedule(broken)

    def test_epoch_order_is_deterministic_complete_and_epoch_specific(self):
        rows = [
            example(index, "supported", "family-a") for index in range(16)
        ]
        first = self.primary.order_epoch_examples(rows, self.config["seed"], 1)
        again = self.primary.order_epoch_examples(
            list(reversed(rows)), self.config["seed"], 1
        )
        second = self.primary.order_epoch_examples(rows, self.config["seed"], 2)
        first_ids = [row["example_id"] for row in first]
        self.assertEqual(first_ids, [row["example_id"] for row in again])
        self.assertEqual(
            sorted(row["example_id"] for row in rows), sorted(first_ids)
        )
        self.assertNotEqual(first_ids, [row["example_id"] for row in second])
        with self.assertRaises(ValueError):
            self.primary.order_epoch_examples(rows + [rows[0]], self.config["seed"], 1)

    def test_dataset_gate_checks_counts_classes_and_family_split(self):
        train_families = ["a", "b", "c", "d"]
        validation_families = ["e", "f"]
        train = []
        validation = []
        number = 0
        for family in train_families:
            for decision in ("supported", "unsupported_by_bound_pointer"):
                for _ in range(150):
                    train.append(example(number, decision, family))
                    number += 1
        for family in validation_families:
            for decision in ("supported", "unsupported_by_bound_pointer"):
                for _ in range(75):
                    validation.append(example(number, decision, family))
                    number += 1
        report = self.primary.validate_primary_datasets(train, validation, self.config)
        self.assertEqual(1200, report["train"]["examples"])
        self.assertEqual(300, report["training_validation"]["examples"])
        self.assertEqual([], report["family_overlap"])
        with self.assertRaisesRegex(ValueError, "overlap"):
            self.primary.validate_primary_datasets(
                train, validation + [example(number, "supported", "a")], self.config
            )

    def test_current_authority_can_never_start_training(self):
        with self.assertRaisesRegex(PermissionError, "primary training is not authorized"):
            self.primary.require_primary_training_authority(
                self.authority, CONTRACT_PATH, CONFIG_PATH
            )
        future = copy.deepcopy(self.authority)
        future["primary_training_gate"] = {
            "authorized": True,
            "contract_sha256": sha256(CONTRACT_PATH),
            "training_config_sha256": sha256(CONFIG_PATH),
            "preflight_required": True,
            "preflight_passed": True,
            "preflight_audit_sha256": "A" * 64,
        }
        future["next_gate"]["primary_training_authorized"] = True
        self.primary.require_primary_training_authority(
            future, CONTRACT_PATH, CONFIG_PATH
        )
        future["primary_training_gate"]["contract_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "contract SHA"):
            self.primary.require_primary_training_authority(
                future, CONTRACT_PATH, CONFIG_PATH
            )

    def test_path_guard_rejects_development_test_m3_and_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            safe = repo / ".local-qwen25-smoke" / "local-output" / "primary-v0.1"
            safe.mkdir(parents=True)
            self.assertEqual(
                safe.resolve(), self.primary.require_primary_path(safe, repo, "safe")
            )
            for component in ("development", "test", "c07", "m3"):
                path = repo / component / "payload"
                path.mkdir(parents=True)
                with self.subTest(component=component), self.assertRaises(ValueError):
                    self.primary.require_primary_path(path, repo, component)
            with self.assertRaisesRegex(ValueError, "escapes"):
                self.primary.require_primary_path(repo.parent / "outside", repo, "escape")

    def test_checkpoint_layout_is_adapter_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "checkpoint-epoch-001"
            adapter = root / "adapter"
            adapter.mkdir(parents=True)
            (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
            (adapter / "adapter_model.safetensors").write_bytes(b"adapter")
            (root / "trainer-state.json").write_text("{}", encoding="utf-8")
            (root / "optimizer.pt").write_bytes(b"optimizer")
            (root / "scheduler.pt").write_bytes(b"scheduler")
            (root / "rng-state.pt").write_bytes(b"rng")
            report = self.primary.validate_primary_checkpoint(root, 1000)
            self.assertEqual(6, len(report))
            (root / "model.safetensors").write_bytes(b"full-model")
            with self.assertRaisesRegex(ValueError, "prohibited"):
                self.primary.validate_primary_checkpoint(root, 1000)

    def test_static_source_forbids_merge_upload_and_adjacent_scopes(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "merge_and_unload",
            "push_to_hub",
            "import run_mvp",
            "run_llm_evidence_compiler_paired",
        ):
            self.assertNotIn(forbidden, source)
        self.assertFalse(
            (EXPERIMENT_ROOT / "scripts" / "run_llm_evidence_compiler_paired.py").exists()
        )

    def test_authority_hash_chain_covers_all_deliverables(self):
        authority = self.authority
        self.assertEqual(
            authority["parent_authority"]["sha256"], sha256(PARENT_AUTHORITY_PATH)
        )
        for group in (
            "authoritative_plan",
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
        ):
            for relative, expected in authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))


if __name__ == "__main__":
    unittest.main()
