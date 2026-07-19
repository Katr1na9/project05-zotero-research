import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
PREPARE_PATH = EXPERIMENT_ROOT / "scripts" / "prepare_qwen_qlora_smoke.py"
TRAIN_PATH = EXPERIMENT_ROOT / "scripts" / "train_qwen_qlora_smoke.py"
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
CONTRACT_PATH = MAINLINE_ROOT / "contracts" / "qwen25-qlora-smoke-contract-v0.1.json"
CONFIG_PATH = MAINLINE_ROOT / "qlora_smoke_v0.1" / "training-config-v0.1.json"
REQUIREMENTS_PATH = (
    MAINLINE_ROOT / "qlora_smoke_v0.1" / "requirements-linux-cu121-v0.1.txt"
)
LOCAL_CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-qlora-local-smoke-contract-v0.2.json"
)
LOCAL_CONFIG_PATH = (
    MAINLINE_ROOT / "qlora_smoke_v0.2" / "training-config-v0.2-local.json"
)
LOCAL_REQUIREMENTS_PATH = (
    MAINLINE_ROOT / "qlora_smoke_v0.2" / "requirements-windows-cu121-v0.2.txt"
)
LOCAL_LAUNCHER_PATH = (
    MAINLINE_ROOT / "qlora_smoke_v0.2" / "run-local-smoke-v0.2.ps1"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.19.json"


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


class FakeTokenizer:
    def encode(self, text, add_special_tokens=False):
        if add_special_tokens:
            raise AssertionError("special tokens must remain disabled")
        return [ord(character) for character in text]


class QwenQloraSmokeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepare = load_module(PREPARE_PATH, "prepare_qwen_smoke")
        cls.train = load_module(TRAIN_PATH, "train_qwen_smoke")
        cls.contract = load_json(CONTRACT_PATH)
        cls.config = load_json(CONFIG_PATH)
        cls.local_contract = load_json(LOCAL_CONTRACT_PATH)
        cls.local_config = load_json(LOCAL_CONFIG_PATH)

    def test_import_is_lazy_and_does_not_require_model_runtime(self):
        for module in (self.prepare, self.train):
            self.assertNotIn("torch", module.__dict__)
            self.assertNotIn("transformers", module.__dict__)
            self.assertNotIn("peft", module.__dict__)
            self.assertNotIn("bitsandbytes", module.__dict__)

    def test_contract_pins_server_home_config_and_runtime(self):
        boundary = self.contract["server_execution_boundary"]
        self.assertEqual("/home/myy", boundary["allowed_home"])
        self.assertEqual("project05-qwen25-smoke-v0.1", boundary["run_directory_name"])
        self.assertEqual([], boundary["explicit_read_list_outside_allowed_home"])
        self.assertEqual([], boundary["explicit_write_list_outside_allowed_home"])
        self.assertEqual(
            self.contract["training_config"]["sha256"], sha256(CONFIG_PATH)
        )
        self.assertEqual(
            self.contract["runtime_requirements"]["sha256"],
            sha256(REQUIREMENTS_PATH),
        )
        self.assertTrue(
            self.contract["execution_host_amendment"][
                "user_authorized_transfer_to_rtx4090_server"
            ]
        )

    def test_fixed_revision_model_allowlist_and_weight_total(self):
        model = self.contract["model"]
        self.assertEqual("Qwen/Qwen2.5-7B-Instruct", model["repository_id"])
        self.assertRegex(model["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(14, len(model["files"]))
        self.assertEqual(model["repository_bytes"], sum(row["bytes"] for row in model["files"]))
        weights = [row for row in model["files"] if "lfs_sha256" in row]
        self.assertEqual(4, len(weights))
        self.assertEqual(model["weight_bytes"], sum(row["bytes"] for row in weights))
        self.assertTrue(all(len(row["lfs_sha256"]) == 64 for row in weights))

    def test_smoke_configuration_is_bounded_and_adapter_only(self):
        config = self.config
        self.assertEqual(20, config["smoke_packet_limit"])
        self.assertEqual(10, config["smoke_supported"])
        self.assertEqual(10, config["smoke_pointer_unsupported"])
        self.assertEqual(16, config["gradient_accumulation_steps"])
        self.assertEqual(1, config["optimizer_steps"])
        self.assertEqual(1024, config["sequence_length"])
        self.assertFalse(config["allow_truncation"])
        self.assertTrue(config["output_policy"]["adapter_only"])
        self.assertFalse(config["output_policy"]["allow_merged_model"])
        self.assertEqual(22.0, config["hardware"]["maximum_operational_peak_vram_gib"])

    def test_requirements_match_every_frozen_runtime_pin(self):
        content = REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
        observed = {
            line.split("==", 1)[0]: line.split("==", 1)[1]
            for line in content
            if line and not line.startswith("--")
        }
        expected = {
            key: value
            for key, value in self.contract["runtime_packages"].items()
            if key != "python"
        }
        self.assertEqual(expected, observed)

    def test_local_route_abandons_server_and_pins_repository_boundary(self):
        disposition = self.local_contract["server_route_disposition"]
        self.assertEqual("abandoned_by_user", disposition["status"])
        self.assertFalse(disposition["further_server_connection_authorized"])
        self.assertFalse(disposition["server_training_authorized"])
        boundary = self.local_contract["execution_boundary"]
        self.assertEqual("repository_relative_local_windows", boundary["mode"])
        self.assertEqual(".local-qwen25-smoke", boundary["run_directory_name"])
        self.assertEqual(
            self.local_contract["training_config"]["sha256"],
            sha256(LOCAL_CONFIG_PATH),
        )
        self.assertEqual(
            self.local_contract["runtime_requirements"]["sha256"],
            sha256(LOCAL_REQUIREMENTS_PATH),
        )

    def test_local_boundary_accepts_only_exact_repository_child(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            expected = repo / ".local-qwen25-smoke"
            allowed, observed = self.prepare.validate_execution_boundary(
                self.local_contract, expected, repo
            )
            self.assertEqual(repo.resolve(), allowed)
            self.assertEqual(expected.resolve(), observed)
            with self.assertRaisesRegex(ValueError, "repository-relative"):
                self.prepare.validate_execution_boundary(
                    self.local_contract, repo / "another-root", repo
                )

    def test_local_config_restores_blocking_2080ti_memory_gate(self):
        hardware = self.local_config["hardware"]
        self.assertEqual("NVIDIA GeForce RTX 2080 Ti", hardware["execution_target"])
        self.assertEqual(10.5, hardware["maximum_operational_peak_vram_gib"])
        self.assertTrue(hardware["local_memory_gate_is_blocking"])
        self.assertEqual("float16", self.local_config["quantization"]["compute_dtype"])
        self.assertFalse(self.local_config["allow_truncation"])

    def test_local_launcher_confines_all_caches_and_contains_no_delete(self):
        launcher = LOCAL_LAUNCHER_PATH.read_text(encoding="utf-8")
        for name in (
            "PIP_CACHE_DIR",
            "HF_HOME",
            "HF_HUB_CACHE",
            "TRANSFORMERS_CACHE",
            "XDG_CACHE_HOME",
            "PYTHONPYCACHEPREFIX",
        ):
            self.assertIn(name, launcher)
        self.assertNotIn("Remove-Item", launcher)
        self.assertNotIn("rm -", launcher)

    def test_path_guard_rejects_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            root.mkdir()
            inside = root / "child"
            inside.mkdir()
            self.assertEqual(inside.resolve(), self.prepare.require_within(inside, root, "inside"))
            with self.assertRaisesRegex(ValueError, "escapes"):
                self.prepare.require_within(root.parent / "outside", root, "outside")

    def example(self, number: int, decision: str):
        pointer = {
            "artifact_id": f"ART-{number}",
            "record_id": f"REC-{number}",
            "record_sha256": "A" * 64,
        }
        return {
            "example_id": f"CEDGE-{decision}-{number:03d}",
            "source_modality": "endpoint_event",
            "source_record": {"payload": {"message": f"process {number}"}},
            "candidate": {
                "subject_type": "process",
                "subject_value": "a",
                "predicate": "executed",
                "object_type": "command",
                "object_value": "b",
                "source_pointer": pointer,
            },
            "support_decision": decision,
            "normalized_edge": None if decision != "supported" else {"predicate": "executed"},
            "pointer": pointer,
        }

    def test_selection_is_deterministic_balanced_and_uses_sixteen_microbatches(self):
        examples = []
        for decision in ("supported", "unsupported_by_bound_pointer"):
            examples.extend(self.example(index, decision) for index in range(20))
        first = self.train.select_smoke_examples(examples, 2026071601)
        second = self.train.select_smoke_examples(list(reversed(examples)), 2026071601)
        self.assertEqual(
            [row["example_id"] for row in first["selected"]],
            [row["example_id"] for row in second["selected"]],
        )
        self.assertEqual(
            {"supported": 10, "unsupported_by_bound_pointer": 10},
            first["selected_counts"],
        )
        self.assertEqual(
            {"supported": 8, "unsupported_by_bound_pointer": 8},
            first["training_counts"],
        )
        self.assertEqual(16, len(first["training"]))

    def test_assistant_only_mask_leaves_prompt_unsupervised_without_truncation(self):
        serialization = load_json(
            REPO_ROOT
            / self.contract["data_inputs"]["serialization_contract_path"]
        )["serialization"]
        example = self.example(1, "supported")
        prompt, target = self.train.render_training_parts(example, serialization)
        encoded = self.train.encode_assistant_only(
            example, serialization, FakeTokenizer(), len(prompt) + len(target)
        )
        self.assertEqual([-100] * len(prompt), encoded["labels"][: len(prompt)])
        self.assertEqual(
            [ord(character) for character in target], encoded["labels"][len(prompt) :]
        )
        with self.assertRaisesRegex(ValueError, "no-truncation"):
            self.train.encode_assistant_only(
                example, serialization, FakeTokenizer(), len(prompt) + len(target) - 1
            )

    def test_adapter_validator_accepts_only_adapter_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "adapter_config.json").write_text("{}", encoding="utf-8")
            (root / "adapter_model.safetensors").write_bytes(b"adapter")
            files = self.train.validate_adapter_directory(root, 1000)
            self.assertEqual(2, len(files))
            (root / "model.safetensors").write_bytes(b"full-model")
            with self.assertRaisesRegex(ValueError, "prohibited"):
                self.train.validate_adapter_directory(root, 1000)

    def test_static_scope_excludes_primary_training_and_merge(self):
        contract = self.contract
        self.assertIn("primary_or_multi_epoch_training", contract["not_authorized"])
        self.assertIn("merged_model_save", contract["not_authorized"])
        source = TRAIN_PATH.read_text(encoding="utf-8")
        self.assertNotIn("merge_and_unload", source)
        self.assertNotIn("push_to_hub", source)
        self.assertNotIn("import run_mvp", source)

    def test_server_launcher_keeps_pip_cache_inside_run_root(self):
        launcher = (
            MAINLINE_ROOT
            / "qlora_smoke_v0.1"
            / "run-server-smoke-v0.1.sh"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'export PIP_CACHE_DIR="${RUN_ROOT}/local-cache/pip"', launcher
        )
        self.assertNotIn("rm -", launcher)

    def test_authority_hash_chain_and_closed_primary_gate(self):
        authority = load_json(AUTHORITY_PATH)
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in (
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
        ):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))
        self.assertTrue(authority["smoke_gate"]["user_authorized"])
        self.assertFalse(authority["next_gate"]["primary_training_authorized"])
        self.assertEqual("abandoned_by_user", authority["server_route"]["status"])
        self.assertFalse(authority["server_route"]["further_connection_authorized"])


if __name__ == "__main__":
    unittest.main()
