import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "preflight_qwen_qlora_memory_stress.py"
CONTRACT_PATH = (
    MAINLINE_ROOT / "contracts" / "qwen25-memory-stress-preflight-contract-v0.1.json"
)
AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.27.json"
PARENT_AUTHORITY_PATH = MAINLINE_ROOT / "contracts" / "authority-lock-v0.26.json"
LAUNCHER_PATH = (
    MAINLINE_ROOT / "qlora_primary_v0.1" / "run-memory-stress-preflight-v0.1.ps1"
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


class MemoryStressPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT_PATH, "qwen_memory_stress")
        cls.contract = load_json(CONTRACT_PATH)
        cls.authority = load_json(AUTHORITY_PATH)

    def test_import_is_lazy_and_has_no_model_runtime(self):
        for name in ("torch", "transformers", "peft", "bitsandbytes"):
            self.assertNotIn(name, self.module.__dict__)

    def test_contract_hashes_parent_amendment_and_all_inputs(self):
        for group in ("parent_authority", "approved_amendment"):
            record = self.contract[group]
            self.assertEqual(record["sha256"], sha256(REPO_ROOT / record["path"]))
        for group in ("frozen_inputs", "local_inputs"):
            for record in self.contract[group].values():
                with self.subTest(group=group, path=record["path"]):
                    self.assertEqual(record["sha256"], sha256(REPO_ROOT / record["path"]))

    def test_longest_selection_is_length_descending_and_hash_tied(self):
        rows = [("b", 10), ("a", 10), ("c", 9), ("d", 8)]
        ranked = self.module.rank_stress_candidates(rows, 3)
        self.assertEqual([10, 10, 9], [length for _, length in ranked])
        expected_tie = sorted(("a", "b"), key=self.module.sha256_text)
        self.assertEqual(expected_tie, [identity for identity, _ in ranked[:2]])
        with self.assertRaises(ValueError):
            self.module.rank_stress_candidates(rows + [("a", 7)], 3)

    def test_frozen_envelope_is_the_global_longest_sixteen(self):
        selection = self.contract["selection"]
        lengths = selection["expected_lengths_descending"]
        self.assertEqual(16, len(lengths))
        self.assertEqual(sorted(lengths, reverse=True), lengths)
        self.assertEqual(982, min(lengths))
        self.assertEqual(1021, max(lengths))
        self.assertEqual(15999, sum(lengths))
        ranked = [(f"id-{index}", length) for index, length in enumerate(lengths)]
        report = self.module.validate_stress_selection(ranked, self.contract)
        self.assertEqual(15999, report["total_tokens"])
        self.assertFalse(report["raw_example_ids_recorded"])

    def test_stabilization_does_not_change_scientific_configuration(self):
        stable = self.contract["stabilization"]
        self.assertEqual(
            "max_split_size_mb:128,garbage_collection_threshold:0.8",
            stable["pytorch_cuda_alloc_conf"],
        )
        self.assertTrue(stable["python_gc_after_each_microbatch"])
        self.assertTrue(stable["cuda_empty_cache_after_each_microbatch"])
        self.assertFalse(stable["reset_peak_stats_inside_microbatch_loop"])
        self.assertFalse(stable["formal_training_order_change_allowed"])
        self.assertEqual(11274289152, self.contract["memory_gate"]["peak_reserved_limit_bytes"])

    def test_authority_opens_only_one_stress_preflight(self):
        gate = self.authority["memory_stress_gate"]
        self.assertTrue(gate["authorized"])
        self.assertEqual(1, gate["maximum_executions"])
        self.assertEqual(gate["contract_sha256"], sha256(CONTRACT_PATH))
        for key, value in self.authority["next_gate"].items():
            if key != "status":
                self.assertFalse(value, key)

    def test_authority_hash_chain_covers_every_deliverable(self):
        parent = self.authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in (
            "authoritative_contracts",
            "authoritative_implementation",
            "authoritative_tests",
            "authoritative_documentation",
        ):
            for relative, expected in self.authority[group].items():
                with self.subTest(group=group, path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_output_path_is_exact_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory) / "repo"
            run = repo / ".local-qwen25-smoke"
            run.mkdir(parents=True)
            contract = {"execution_boundary": dict(self.contract["execution_boundary"])}
            old_root = self.module.REPO_ROOT
            try:
                self.module.REPO_ROOT = repo
                output = self.module.exact_output_path(contract, run)
                self.assertEqual(
                    (run / "local-output" / "memory-stress-preflight-v0.1.json").resolve(),
                    output,
                )
                output.parent.mkdir(parents=True)
                output.write_text("{}", encoding="utf-8")
                with self.assertRaises(FileExistsError):
                    self.module.exact_output_path(contract, run)
            finally:
                self.module.REPO_ROOT = old_root

    def test_launcher_is_offline_and_pins_allocator(self):
        source = LAUNCHER_PATH.read_text(encoding="utf-8")
        self.assertIn('$env:HF_HUB_OFFLINE = "1"', source)
        self.assertIn('$env:TRANSFORMERS_OFFLINE = "1"', source)
        self.assertIn(
            '$env:PYTORCH_CUDA_ALLOC_CONF = "max_split_size_mb:128,garbage_collection_threshold:0.8"',
            source,
        )
        for forbidden in ("pip install", "Remove-Item", "snapshot_download"):
            self.assertNotIn(forbidden, source)

    def test_static_script_performs_no_generation_or_persistence(self):
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        for forbidden in (
            ".generate(",
            "save_pretrained",
            "torch.save",
            "merge_and_unload",
            "push_to_hub",
            "snapshot_download",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("gc.collect()", source)
        self.assertIn("torch.cuda.empty_cache()", source)
        self.assertIn("torch.cuda.max_memory_reserved(0)", source)


if __name__ == "__main__":
    unittest.main()
