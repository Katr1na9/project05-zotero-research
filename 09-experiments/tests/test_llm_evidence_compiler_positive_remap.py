import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "build_candidate_edge_training.py"
FIELD_MAP_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "field_maps" / "v0.2"
BASELINE_READINESS_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "qwen-candidate-edge-readiness-v0.1.json"
)
REMAP_READINESS_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "qwen-positive-remap-readiness-v0.1.json"
)
HISTORICAL_RECORDS_ROOT = (
    REPO_ROOT
    / ".worktrees"
    / "llm-apt-phase1"
    / "09-experiments"
    / "llm_finetuning_v0.3"
    / "generated"
    / "exclusion-passed-records"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_module():
    spec = importlib.util.spec_from_file_location("candidate_edge_positive_remap", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def source_record(
    family: str,
    message: str,
    *,
    record_id: str = "REC-1",
    document_id: str = "DOC-1",
    artifact_id: str = "ART-1",
    legacy_null: bool = False,
) -> dict:
    return {
        "schema_version": "normalized-jsonl-v1",
        "source_family_id": family,
        "source_type": "endpoint_event",
        "document_id": document_id,
        "artifact_id": artifact_id,
        "record_id": record_id,
        "payload": {"message": message},
        "observation_candidates": [],
        "null_eligible_candidate": legacy_null,
        "provenance": {
            "license_id": "CC-BY-4.0",
            "license_sha256": "A" * 64,
            "source_file_sha256": "B" * 64,
            "source_url": "https://example.invalid/source",
        },
    }


class PositiveRemapAuthorityTests(unittest.TestCase):
    def test_v06_authorizes_only_download_free_positive_remap(self):
        authority = load_json(CONTRACT_ROOT / "authority-lock-v0.6.json")
        remap = authority["positive_remap_amendment"]
        self.assertTrue(remap["authority_granted"])
        self.assertTrue(remap["dependency_free_parser_implementation_allowed"])
        self.assertTrue(remap["read_only_remap_audit_allowed"])
        self.assertFalse(remap["beth_download_allowed"])
        self.assertFalse(remap["formal_candidate_pair_construction_allowed"])
        self.assertFalse(remap["tokenizer_model_training_or_inference_allowed"])
        self.assertTrue(
            {
                "beth_or_other_corpus_download",
                "formal_candidate_pair_construction",
                "tokenizer_download",
                "model_download",
                "formal_training",
                "formal_inference",
                "m3_runtime_integration",
            }
            <= set(authority["not_authorized"])
        )

    def test_v06_hashes_parent_document_and_contract(self):
        authority = load_json(CONTRACT_ROOT / "authority-lock-v0.6.json")
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_documents", "authoritative_contracts"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))


class PositiveRemapParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.maps = cls.module.load_field_maps(
            FIELD_MAP_ROOT / "source-field-maps.json",
            FIELD_MAP_ROOT / "field-map-lock.json",
        )

    def test_execve_parser_preserves_pointer_timestamp_and_quoted_arguments(self):
        source = source_record(
            "ait_cam_lds_manifestations_filtered",
            'type=EXECVE msg=audit(1758532010.089:12238): argc=3 a0="tail" a1="-f" a2="/var/log/audit/audit.log"',
        )
        candidate = self.module.parse_linux_audit_execve_candidate(source)
        self.assertEqual("tail", candidate["subject_value"])
        self.assertEqual("tail -f /var/log/audit/audit.log", candidate["object_value"])
        self.assertEqual("1758532010.089", candidate["event_time"])
        self.assertEqual(
            {"artifact_id": "ART-1", "record_id": "REC-1"},
            candidate["source_pointer"],
        )

    def test_execve_parser_rejects_incomplete_argument_sequence(self):
        source = source_record(
            "ait_cam_lds_manifestations_filtered",
            'type=EXECVE msg=audit(1758532010.089:12238): argc=3 a0="tail" a2="missing-a1"',
        )
        self.assertIsNone(self.module.parse_linux_audit_execve_candidate(source))

    def test_proctitle_parser_decodes_nul_separated_hex(self):
        source = source_record(
            "ait_cam_lds_manifestations_filtered",
            "type=PROCTITLE msg=audit(1758532010.090:12239): "
            "proctitle=707974686F6E007363726970742E7079002D2D666C6167",
        )
        candidate = self.module.parse_linux_audit_proctitle_candidate(source)
        self.assertEqual("python", candidate["subject_value"])
        self.assertEqual("python script.py --flag", candidate["object_value"])
        malformed = source_record(
            "ait_cam_lds_manifestations_filtered",
            "type=PROCTITLE msg=audit(1.000:1): proctitle=NOT_HEX",
        )
        self.assertIsNone(self.module.parse_linux_audit_proctitle_candidate(malformed))

    def test_loghub_oom_parser_uses_only_explicit_line_fields(self):
        source = source_record(
            "logpai_loghub_linux",
            "Nov 21 03:44:47 combo kernel: Out of Memory: Killed process 26555 (httpd).",
            legacy_null=True,
        )
        candidate = self.module.parse_loghub_oom_candidate(source)
        self.assertEqual("kernel@combo", candidate["subject_value"])
        self.assertEqual("terminated", candidate["predicate"])
        self.assertEqual("httpd#pid=26555", candidate["object_value"])
        self.assertEqual(
            {"artifact_id": "ART-1", "record_id": "REC-1"},
            candidate["source_pointer"],
        )
        self.assertTrue(source["null_eligible_candidate"])

    def test_loghub_oom_parser_rejects_nonliteral_near_match(self):
        source = source_record(
            "logpai_loghub_linux",
            "Nov 21 03:44:47 combo app: Out of Memory: Killed process 26555 (httpd).",
            legacy_null=True,
        )
        self.assertIsNone(self.module.parse_loghub_oom_candidate(source))

    def test_v02_maps_recompute_candidate_and_reject_alteration(self):
        source = source_record(
            "logpai_loghub_linux",
            "Nov 21 03:44:47 combo kernel: Out of Memory: Killed process 26555 (httpd).",
            legacy_null=True,
        )
        candidates = self.module.propose_record_candidates(source, self.maps)
        self.assertEqual(1, len(candidates))
        report = self.module.validate_g0_candidate(source, candidates[0], self.maps)
        self.assertTrue(report["eligible"], report["reason_codes"])
        altered = dict(candidates[0])
        altered["object_value"] = "sshd#pid=26555"
        report = self.module.validate_g0_candidate(source, altered, self.maps)
        self.assertFalse(report["eligible"])
        self.assertIn("parser_candidate_mismatch", report["reason_codes"])


class PositiveRemapReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.maps = cls.module.load_field_maps(
            FIELD_MAP_ROOT / "source-field-maps.json",
            FIELD_MAP_ROOT / "field-map-lock.json",
        )

    def assert_expected_readiness(self, report: dict):
        families = {
            row["source_family_id"]: row for row in report["families"]
        }
        cam = families["ait_cam_lds_manifestations_filtered"]
        self.assertEqual(166, cam["new_parser_g0_positive_candidates"])
        self.assertEqual(
            {
                "cam_linux_audit_execve_v1": 59,
                "cam_linux_audit_proctitle_hex_v1": 107,
            },
            cam["parser_template_counts"],
        )
        loghub = families["logpai_loghub_linux"]
        self.assertEqual(193, loghub["new_parser_g0_positive_candidates"])
        self.assertEqual(
            {"loghub_oom_killed_process_v1": 193},
            loghub["parser_template_counts"],
        )
        gate = report["non_token_gate"]
        self.assertEqual(3, len(gate["train_g0_positive_families"]))
        self.assertEqual(2, len(gate["validation_g0_positive_families"]))
        self.assertEqual(
            ["train_g0_positive_families_below_4"], gate["failure_reasons"]
        )
        self.assertFalse(report["formal_data_gate_passed"])
        self.assertEqual(0, report["legacy_packet_null_negative_credit"])
        self.assertFalse(
            report["execution_claims"]["formal_candidate_pairs_constructed"]
        )

    def test_read_only_audit_reproduces_expected_remap_counts(self):
        report = self.module.audit_positive_remap(
            HISTORICAL_RECORDS_ROOT,
            self.maps,
            load_json(BASELINE_READINESS_PATH),
        )
        self.assert_expected_readiness(report)

    def test_frozen_readiness_preserves_the_same_hard_stop(self):
        self.assert_expected_readiness(load_json(REMAP_READINESS_PATH))


if __name__ == "__main__":
    unittest.main()
