import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = EXPERIMENT_ROOT / "scripts" / "validate_llm_phase1_output.py"
BUILDER_PATH = EXPERIMENT_ROOT / "scripts" / "build_llm_evaluation_packets.py"
RUNNER_PATH = EXPERIMENT_ROOT / "scripts" / "run_llm_phase1.py"
CONFIG = EXPERIMENT_ROOT / "llm_compiler_v0.2" / "experiment_config.json"
CONTRACT = (
    EXPERIMENT_ROOT / "governance" / "contracts" / "llm-compiler-contract-v0.2.json"
)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_module("llm_packet_builder_for_validation", BUILDER_PATH)
validator = load_module("validate_llm_phase1_output", VALIDATOR_PATH)
runner = load_module("run_llm_phase1", RUNNER_PATH)


def fixture_valid_candidate_and_packet():
    payload = {
        "operation": "EVENT_WRITE",
        "process": "PowerShell.EXE",
        "command": "Compress-Archive C:\\Temp\\A.txt C:\\Temp\\A.zip",
    }
    record = builder.make_packet_record(
        "local_log",
        {"artifact_id": "SRC-C07-01", "record_id": "event-public-1"},
        payload,
    )
    packet = {
        "request_id": "REQ-" + "A" * 24,
        "case_id": "C07-evaluation-case",
        "split": "test",
        "packet_role": "positive",
        "support_ceiling": "G2_tactic_intent",
        "records": [record],
    }
    candidate = {
        "candidate_claim_id": builder.derive_candidate_claim_id(
            packet["request_id"], "general_compiler", 0, 0
        ),
        "source_type": "local_log",
        "subject": {"entity_type": "process", "value": "powershell.exe"},
        "predicate": "created",
        "object": {"entity_type": "file", "value": "C:\\Temp\\A.zip"},
        "source_pointer": dict(record["source_pointer"]),
    }
    return candidate, packet


class G0AdmissionTests(unittest.TestCase):
    def test_admission_signature_and_result_do_not_depend_on_private_gold(self):
        self.assertEqual(
            [
                "candidate",
                "packet",
                "condition_id",
                "attempt_index",
                "output_index",
            ],
            list(inspect.signature(validator.validate_candidate).parameters),
        )
        candidate, packet = fixture_valid_candidate_and_packet()
        before = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )
        private_gold = {
            "acceptable_observations": [{"predicate": "contradicts-candidate"}]
        }
        private_gold["acceptable_observations"][0]["predicate"] = "another-change"
        after = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertEqual([], before)
        self.assertEqual(before, after)

    def test_candidate_id_pointer_hash_and_literal_checks_are_g0_only(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        candidate["candidate_claim_id"] = "CC-" + "B" * 24
        candidate["object"]["value"] = "C:\\Absent\\payload.exe"
        packet["records"][0]["record_sha256"] = "0" * 64

        errors = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertEqual(
            [
                "candidate_id_mismatch",
                "literal_entity_not_in_source",
                "record_sha256_mismatch",
            ],
            errors,
        )

    def test_pointer_outside_packet_is_rejected(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        candidate["source_pointer"]["record_id"] = "outside-packet"

        errors = validator.validate_candidate(
            candidate, packet, "general_compiler", 0, 0
        )

        self.assertIn("pointer_not_in_packet", errors)

    def test_non_object_candidate_is_schema_rejected_without_crashing(self):
        _, packet = fixture_valid_candidate_and_packet()

        errors = validator.validate_candidate(
            [], packet, "general_compiler", 0, 0
        )

        self.assertIn("candidate_schema_invalid", errors)

    def test_admission_returns_machine_gap_codes(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        invalid = json.loads(json.dumps(candidate))
        invalid["candidate_claim_id"] = builder.derive_candidate_claim_id(
            packet["request_id"], "general_compiler", 0, 1
        )
        invalid["object"]["value"] = "not-visible"
        result = {
            "request_id": packet["request_id"],
            "condition_id": "general_compiler",
            "attempt_index": 0,
            "status": "completed",
            "candidate_claims": [candidate, invalid],
            "telemetry": {
                "latency_ms": 0,
                "peak_vram_mb": 0,
                "input_tokens": None,
                "output_tokens": None,
                "error_code": None,
            },
        }

        admission = validator.admit_candidates(result, packet)

        self.assertEqual(1, len(admission["admitted_claims"]))
        self.assertEqual(1, len(admission["rejected"]))
        self.assertEqual(["literal_entity_absent"], admission["explicit_gaps"])

    def test_structured_stage2_input_excludes_raw_rejected_and_private(self):
        payload = validator.build_structured_stage2_input(
            {
                "admitted_claims": [{"candidate_claim_id": "CC-" + "A" * 24}],
                "rejected": [{"raw": "secret"}],
                "explicit_gaps": ["missing_source"],
                "private_gold": {"answer": "secret"},
            },
            "G2_tactic_intent",
        )
        serialized = json.dumps(payload, sort_keys=True)

        self.assertNotIn("source_payload", serialized)
        self.assertNotIn("rejected", serialized)
        self.assertNotIn("private", serialized)
        self.assertEqual(
            {"admitted_claims", "explicit_gaps", "support_ceiling"},
            set(payload),
        )


class ManifestValidationTests(unittest.TestCase):
    def test_manifest_rejects_config_and_input_drift(self):
        config = {"experiment_id": "phase1", "status": "pre_model"}
        input_manifest = {"packet_count": 64, "split": "test"}
        prompt_lock = {
            "contract_sha256": "C" * 64,
            "prompt_sha256": {"compiler": "D" * 64},
        }
        model_lock = {
            "model_role": "general",
            "model_id": "stub",
            "revision": None,
            "weights_sha256": None,
        }
        manifest = {
            "input_manifest_sha256": validator.hash_value(input_manifest),
            "config_sha256": validator.hash_value(config),
            "contract_sha256": "C" * 64,
            "prompt_sha256": {"compiler": "D" * 64},
            "model_lock": model_lock,
        }

        self.assertEqual(
            [],
            validator.validate_run_manifest(
                manifest, config, input_manifest, prompt_lock, model_lock
            ),
        )
        changed = dict(config, status="changed-after-lock")
        self.assertEqual(
            ["config_sha256_mismatch"],
            validator.validate_run_manifest(
                manifest, changed, input_manifest, prompt_lock, model_lock
            ),
        )


class RuleBaselineTests(unittest.TestCase):
    def fixture_development_manifest_and_results(self):
        manifest = {
            "split": "development",
            "packet_count": 52,
            "positive_count": 26,
            "null_count": 26,
            "input_manifest_sha256": "A" * 64,
            "null_construction_audit": {
                "status": "frozen",
                "audit_sha256": "B" * 64,
            },
        }
        rows = []
        for index in range(26):
            rows.append(
                {
                    "request_id": f"REQ-{index:024X}",
                    "case_id": "C04-evaluation-case",
                    "packet_role": "positive",
                    "schema_valid": True,
                    "project_gold_packet_agreement": 1.0,
                    "result": {"status": "completed", "candidate_claims": [{}]},
                }
            )
        for index in range(26, 52):
            rows.append(
                {
                    "request_id": f"REQ-{index:024X}",
                    "case_id": "C04-evaluation-case",
                    "packet_role": "null",
                    "schema_valid": True,
                    "project_gold_packet_agreement": 1.0,
                    "result": {"status": "abstain", "candidate_claims": []},
                }
            )
        return manifest, rows

    def test_rule_snapshot_is_required_before_any_llm_backend(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "rule baseline snapshot"):
                runner.preflight_llm_backend(
                    Path(temp) / "missing.json", CONFIG, CONTRACT
                )

    def test_rule_or_config_drift_after_snapshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest, rows = self.fixture_development_manifest_and_results()
            snapshot = root / "rule-baseline-development.json"
            runner.freeze_rule_snapshot(
                CONFIG,
                CONTRACT,
                manifest,
                rows,
                snapshot,
            )
            changed = json.loads(CONFIG.read_text(encoding="utf-8"))
            changed["rule_baseline"]["operation_map"]["EVENT_READ"] = (
                "changed_after_freeze"
            )
            changed_path = root / "changed.json"
            changed_path.write_text(json.dumps(changed), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "snapshot hash mismatch"):
                runner.require_rule_snapshot_unchanged(
                    snapshot, changed_path, CONTRACT
                )

    def test_rule_compiler_emits_only_g0_valid_literal_observation(self):
        payload = {
            "operation": "EVENT_WRITE",
            "process": "powershell.exe",
            "path": "C:\\Temp\\A.zip",
        }
        record = builder.make_packet_record(
            "local_log",
            {"artifact_id": "SRC-C07-01", "record_id": "event-1"},
            payload,
        )
        packet = {
            "request_id": "REQ-" + "A" * 24,
            "case_id": "C07-evaluation-case",
            "split": "test",
            "packet_role": "positive",
            "support_ceiling": "G2_tactic_intent",
            "records": [record],
        }

        result = runner.rule_compile(packet)

        self.assertEqual("completed", result["status"])
        self.assertEqual(1, len(result["candidate_claims"]))
        self.assertEqual("wrote", result["candidate_claims"][0]["predicate"])
        self.assertEqual(
            [],
            validator.validate_candidate(
                result["candidate_claims"][0],
                packet,
                "rule_compiler",
                0,
                0,
            ),
        )

    def test_rule_compiler_abstains_when_operation_is_unmapped(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        del candidate
        packet["records"][0]["source_payload"] = {
            "operation": "UNMAPPED_EVENT",
            "process": "powershell.exe",
            "path": "C:\\Temp\\A.zip",
        }
        packet["records"][0]["record_sha256"] = builder.sha256_bytes(
            builder.canonical_json(packet["records"][0]["source_payload"])
        )

        result = runner.rule_compile(packet)

        self.assertEqual("abstain", result["status"])
        self.assertEqual([], result["candidate_claims"])


class StubAndHashChainTests(unittest.TestCase):
    def test_direct_and_structured_share_model_and_generation_config(self):
        config = json.loads(CONFIG.read_text(encoding="utf-8"))

        self.assertEqual(
            config["conditions"]["general_direct"]["model_role"],
            config["conditions"]["general_structured"]["model_role"],
        )
        self.assertEqual(
            config["conditions"]["general_direct"]["generation"],
            config["conditions"]["general_structured"]["generation"],
        )

    def test_structured_repeat_hash_binds_both_stages(self):
        _, packet = fixture_valid_candidate_and_packet()
        result, manifest = runner.run_structured(
            packet,
            runner.StubBackend(),
            attempt_index=3,
        )

        self.assertEqual("general_structured", result["condition_id"])
        self.assertEqual(
            [
                "stage1_prompt_sha256",
                "stage1_raw_sha256",
                "admission_sha256",
                "stage2_input_sha256",
                "stage2_prompt_sha256",
                "stage2_raw_sha256",
                "final_result_sha256",
            ],
            list(manifest["stage_hash_chain"]),
        )
        self.assertTrue(runner.hash_chain_complete(manifest))

    def test_stub_backend_does_not_import_model_packages(self):
        _, packet = fixture_valid_candidate_and_packet()
        before = set(sys.modules)

        runner.run_compiler(
            packet,
            "general_compiler",
            runner.StubBackend(),
            attempt_index=0,
        )

        loaded = set(sys.modules) - before
        self.assertFalse({"torch", "transformers", "bitsandbytes"} & loaded)

    def test_invalid_stub_json_is_preserved_as_invalid_first_pass(self):
        _, packet = fixture_valid_candidate_and_packet()

        result, manifest = runner.run_compiler(
            packet,
            "general_compiler",
            runner.StubBackend(responses=["not-json"]),
            attempt_index=0,
        )

        self.assertEqual("invalid", result["status"])
        self.assertEqual("json_parse_error", result["telemetry"]["error_code"])
        self.assertEqual(runner.sha256_value(result), manifest["result_sha256"])

    def test_stub_compiler_exercises_admitted_and_rejected_candidates(self):
        candidate, packet = fixture_valid_candidate_and_packet()
        rejected = json.loads(json.dumps(candidate))
        rejected["candidate_claim_id"] = builder.derive_candidate_claim_id(
            packet["request_id"], "general_compiler", 0, 1
        )
        rejected["object"]["value"] = "not-visible"

        result, _ = runner.run_compiler(
            packet,
            "general_compiler",
            runner.StubBackend(
                responses=[
                    {
                        "status": "completed",
                        "candidate_claims": [candidate, rejected],
                    }
                ]
            ),
            attempt_index=0,
        )
        admission = validator.admit_candidates(result, packet)

        self.assertEqual(1, len(admission["admitted_claims"]))
        self.assertEqual(1, len(admission["rejected"]))

    def test_direct_stub_returns_a_complete_abstaining_conclusion(self):
        _, packet = fixture_valid_candidate_and_packet()

        result, manifest = runner.run_direct(
            packet,
            runner.StubBackend(),
            attempt_index=0,
        )

        self.assertEqual("general_direct", result["condition_id"])
        self.assertEqual("abstain", result["status"])
        self.assertTrue(result["abstain"])
        self.assertEqual([], result["observation_claims"])
        self.assertEqual(runner.sha256_value(result), manifest["result_sha256"])

    def test_run_condition_dispatches_all_stub_modes(self):
        _, packet = fixture_valid_candidate_and_packet()
        config = json.loads(CONFIG.read_text(encoding="utf-8"))

        for condition_id in (
            "general_compiler",
            "security_compiler",
            "general_structured",
            "general_direct",
        ):
            with self.subTest(condition=condition_id):
                result, manifest = runner.run_condition(
                    config,
                    packet,
                    condition_id,
                    runner.StubBackend(),
                    attempt_index=2,
                )
                self.assertEqual(condition_id, result["condition_id"])
                self.assertEqual(condition_id, manifest["condition_id"])

    def test_prompt_lock_hashes_all_prompts_contract_config_and_schemas(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = runner.freeze_prompt_config_lock(Path(temp) / "lock.json")

        self.assertEqual(4, len(lock["prompt_sha256"]))
        self.assertEqual(4, len(lock["schema_sha256"]))
        self.assertRegex(lock["config_file_sha256"], r"^[A-F0-9]{64}$")
        self.assertRegex(lock["contract_sha256"], r"^[A-F0-9]{64}$")

    def test_repeat_panel_and_call_arithmetic_are_exact(self):
        rows = []
        counter = 0
        for case in ("C07", "C08", "C09", "C10", "C11", "C12"):
            for role in ("positive", "null"):
                for _ in range(2):
                    rows.append(
                        {
                            "request_id": f"REQ-{counter:024X}",
                            "case_id": f"{case}-evaluation-case",
                            "packet_role": role,
                        }
                    )
                    counter += 1

        panel = runner.select_repeat_panel(rows, seed=2026071504)
        budget = runner.calculate_call_budget(
            json.loads(CONFIG.read_text(encoding="utf-8"))
        )

        self.assertEqual(12, len(panel))
        for case in ("C07", "C08", "C09", "C10", "C11", "C12"):
            selected = [row for row in panel if row["case_id"].startswith(case)]
            self.assertEqual({"positive", "null"}, {row["packet_role"] for row in selected})
        self.assertEqual(
            {"first_pass": 256, "repeat_diagnostic": 192, "maximum": 448},
            budget,
        )


class PreModelReadinessTests(unittest.TestCase):
    def test_model_output_scan_is_evidence_based(self):
        with tempfile.TemporaryDirectory() as temp:
            generated = Path(temp)
            self.assertEqual([], runner.find_model_output_files(generated))

            output = generated / "runs" / "phase1-test" / "raw.json"
            output.parent.mkdir(parents=True)
            output.write_text("{}", encoding="utf-8")

            self.assertEqual(
                ["runs/phase1-test/raw.json"],
                runner.find_model_output_files(generated),
            )

    def test_public_private_scan_detects_private_identifier_collision(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle_dir = Path(temp) / "bundle"
            candidate, packet = fixture_valid_candidate_and_packet()
            observation = {
                key: value
                for key, value in candidate.items()
                if key != "candidate_claim_id"
            }
            observation["canonical_claim_id"] = "C07-EC-001"
            public, private = builder.build_packet_pair(
                case_id="C07-test-case",
                split="test",
                packet_role="positive",
                support_ceiling="G2_tactic_intent",
                records=packet["records"],
                acceptable_observations=[observation],
            )
            builder.write_bundle(
                bundle_dir,
                public_rows=[public],
                private_rows=[private],
                public_catalog={"catalog_version": "test-v1", "artifacts": []},
                metadata={"split": "test", "status": "draft"},
            )
            self.assertEqual([], runner.scan_packet_bundle(bundle_dir))

            private_rows = builder.read_jsonl_gz(
                bundle_dir / "private" / "observation_gold.jsonl.gz"
            )
            private_id = private_rows[0]["acceptable_observations"][0][
                "gold_claim_id"
            ]
            (bundle_dir / "public" / "public_cti_catalog.json").write_text(
                json.dumps({"leak": private_id}),
                encoding="utf-8",
            )

            self.assertEqual(
                ["private_identifier_in_public_bytes"],
                runner.scan_packet_bundle(bundle_dir),
            )

    def test_prompt_config_lock_revalidates_and_detects_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            lock_path = Path(temp) / "prompt-config-lock.json"
            runner.freeze_prompt_config_lock(lock_path)
            self.assertEqual([], runner.validate_prompt_config_lock(lock_path))

            changed = json.loads(lock_path.read_text(encoding="utf-8"))
            prompt_name = sorted(changed["prompt_sha256"])[0]
            changed["prompt_sha256"][prompt_name] = "0" * 64
            builder.write_json(lock_path, changed)

            self.assertIn(
                "prompt_hash_mismatch",
                runner.validate_prompt_config_lock(lock_path),
            )

    def test_pending_human_audit_and_rule_snapshot_block_authorization(self):
        checks = {
            name: {"status": "passed"}
            for name in runner.REQUIRED_READINESS_CHECKS
        }
        checks["null_construction_audit"] = {
            "status": "pending_human",
        }
        checks["rule_baseline_snapshot"] = {"status": "missing"}

        report = runner.assemble_pre_model_readiness(checks)

        self.assertEqual("blocked_pending_human_gates", report["status"])
        self.assertFalse(report["ready_to_request_model_authorization"])
        self.assertEqual(
            ["null_construction_audit", "rule_baseline_snapshot"],
            report["blockers"],
        )


if __name__ == "__main__":
    unittest.main()
