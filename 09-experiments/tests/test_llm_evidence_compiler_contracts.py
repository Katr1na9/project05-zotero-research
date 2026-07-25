import hashlib
import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"


def load_script(name: str):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_script("build_compiler_public_request")
stub = load_script("run_compiler_mainline_stub")


def fixture_request():
    record = builder.build_record(
        "REC-0000000000000001",
        {"operation": "EVENT_EXECUTE", "process": "cmd.exe", "command": "whoami"},
        scope={"host_id": "host-a"},
    )
    artifact = builder.build_artifact(
        "ART-0000000000000001", "local_log", [record], scope={"host_id": "host-a"}
    )
    target = builder.build_target_node(
        "NODE-0000000000000001",
        "A process executes a command",
        allowed_claim_types=["process_execution"],
        allowed_predicates=["executed"],
    )
    return builder.build_public_request(
        case_id="C01-compiler-unit",
        split="unit",
        step_index=0,
        visible_artifacts=[artifact],
        target_nodes=[target],
        predicate_allowlist={"local_log": ["executed"]},
    )


class ContractAndStubTests(unittest.TestCase):
    def test_all_new_contract_schemas_are_valid_draft_2020_12(self):
        expected = {
            "compiler_public_request.schema.json",
            "candidate_claim_envelope.schema.json",
            "entity_binding.schema.json",
            "claim_node_link.schema.json",
            "compiler_decision.schema.json",
            "compiler_run_manifest.schema.json",
        }
        found = {path.name for path in CONTRACT_ROOT.glob("*.schema.json")}
        self.assertEqual(expected, found)
        for path in sorted(CONTRACT_ROOT.glob("*.schema.json")):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(
                    json.loads(path.read_text(encoding="utf-8"))
                )

    def test_public_request_validates_against_contract(self):
        request = fixture_request()
        schema = json.loads(
            (CONTRACT_ROOT / "compiler_public_request.schema.json").read_text(
                encoding="utf-8"
            )
        )
        Draft202012Validator(schema).validate(request)

    def test_stub_abstains_and_loads_no_model_runtime(self):
        request = fixture_request()
        before = set(sys.modules)

        decision, manifest = stub.run_stub(request)

        loaded = set(sys.modules) - before
        self.assertEqual("abstain", decision["status"])
        self.assertEqual("deterministic_stub_v0.1", manifest["backend_id"])
        self.assertFalse(manifest["model_runtime_loaded"])
        self.assertFalse(manifest["private_reference_accessed"])
        self.assertFalse({"torch", "transformers", "bitsandbytes"} & loaded)
        self.assertEqual(
            ["request_sha256", "candidate_payload_sha256", "admission_sha256"],
            list(manifest["stage_hash_chain"]),
        )
        self.assertTrue(all(manifest["stage_hash_chain"].values()))

    def test_authority_lock_keeps_legacy_files_byte_identical(self):
        lock = json.loads(
            (CONTRACT_ROOT / "authority-lock-v0.1.json").read_text(encoding="utf-8")
        )
        for relative, expected_hash in lock["legacy_inheritance_lock"].items():
            with self.subTest(path=relative):
                actual = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest().upper()
                self.assertEqual(expected_hash, actual)

    def test_authority_lock_forbids_model_and_frozen_mutations(self):
        lock = json.loads(
            (CONTRACT_ROOT / "authority-lock-v0.1.json").read_text(encoding="utf-8")
        )
        forbidden = set(lock["not_authorized"])
        self.assertTrue(
            {
                "dependency_install",
                "model_download",
                "training",
                "formal_inference",
                "run_mvp_modification",
                "frozen_case_overwrite",
                "frozen_result_overwrite",
            }
            <= forbidden
        )


if __name__ == "__main__":
    unittest.main()

