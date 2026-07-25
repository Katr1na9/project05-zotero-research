import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
FIELD_MAP_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "field_maps" / "v0.1"
SCHEMA_ROOT = EXPERIMENT_ROOT / "data_schema"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "build_candidate_edge_training.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_module():
    spec = importlib.util.spec_from_file_location("candidate_edge_training", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def record(
    family: str,
    payload: dict,
    candidate: dict | None,
    *,
    record_id: str = "REC-A",
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
        "payload": payload,
        "observation_candidates": [] if candidate is None else [candidate],
        "null_eligible_candidate": legacy_null,
        "provenance": {
            "license_id": "MIT",
            "license_sha256": "A" * 64,
            "source_file_sha256": "B" * 64,
            "source_url": "https://example.invalid/source",
        },
    }


def edge(
    subject_type: str,
    subject_value: str,
    predicate: str,
    object_type: str,
    object_value: str,
    *,
    record_id: str = "REC-A",
    artifact_id: str = "ART-1",
    event_time: str | None = None,
) -> dict:
    output = {
        "subject_type": subject_type,
        "subject_value": subject_value,
        "predicate": predicate,
        "object_type": object_type,
        "object_value": object_value,
        "source_pointer": {
            "artifact_id": artifact_id,
            "record_id": record_id,
        },
    }
    if event_time is not None:
        output["event_time"] = event_time
    return output


def atomic_record() -> dict:
    candidate = edge("process", "powershell.exe", "executed", "command", "powershell.exe -nop")
    return record(
        "redcanary_atomic_red_team",
        {"process_name": "powershell.exe", "command_line": "powershell.exe -nop"},
        candidate,
    )


def socbed_network_record(
    *,
    record_id: str = "REC-A",
    document_id: str = "DOC-1",
    destination: str = "10.0.0.2",
    event_time: str = "2021-01-01T00:00:00Z",
) -> dict:
    candidate = edge(
        "network_address",
        "10.0.0.1",
        "connected_to",
        "network_endpoint",
        f"{destination}:443",
        record_id=record_id,
        event_time=event_time,
    )
    return record(
        "fkie_socbed_acsac2021_winlogbeat",
        {
            "source_address": "10.0.0.1",
            "destination_address": destination,
            "destination_port": "443",
            "timestamp": event_time,
        },
        candidate,
        record_id=record_id,
        document_id=document_id,
    )


def cam_record() -> dict:
    candidate = edge("system", "host", "recorded", "event", "type=EXECVE argc=1")
    return record(
        "ait_cam_lds_manifestations_filtered",
        {"message": "type=EXECVE argc=1"},
        candidate,
    )


def legacy_null_record() -> dict:
    return record(
        "logpai_loghub_linux",
        {"message": "kernel: process exited"},
        None,
        legacy_null=True,
    )


class CandidateTrainingAuthorityTests(unittest.TestCase):
    def test_v05_authorizes_only_dependency_free_candidate_edge_work(self):
        authority = load_json(CONTRACT_ROOT / "authority-lock-v0.5.json")
        amendment = authority["candidate_verification_amendment"]
        self.assertTrue(amendment["authority_granted"])
        self.assertTrue(amendment["dependency_free_implementation_allowed"])
        self.assertFalse(amendment["formal_candidate_pair_construction_allowed"])
        self.assertFalse(amendment["tokenizer_or_model_allowed"])
        self.assertFalse(amendment["training_or_formal_inference_allowed"])
        self.assertTrue(
            {
                "formal_candidate_pair_construction",
                "dependency_install_or_change",
                "tokenizer_download",
                "model_download",
                "formal_training",
                "formal_inference",
                "m3_runtime_integration",
                "run_mvp_modification",
            }
            <= set(authority["not_authorized"])
        )

    def test_v05_hash_chain_preserves_v04_and_approved_contract(self):
        authority = load_json(CONTRACT_ROOT / "authority-lock-v0.5.json")
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for relative, expected in authority["authoritative_documents"].items():
            with self.subTest(path=relative):
                self.assertEqual(expected, sha256(REPO_ROOT / relative))
        for relative, expected in authority["authoritative_contracts"].items():
            with self.subTest(path=relative):
                self.assertEqual(expected, sha256(REPO_ROOT / relative))


class CandidateTrainingSchemaAndG0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.maps = cls.module.load_field_maps(
            FIELD_MAP_ROOT / "source-field-maps.json",
            FIELD_MAP_ROOT / "field-map-lock.json",
        )

    def test_schemas_are_valid_draft_2020_12(self):
        for name in (
            "candidate_edge_training.schema.json",
            "pointer_bounded_negative_proof.schema.json",
        ):
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(load_json(SCHEMA_ROOT / name))

    def test_atomic_executed_candidate_is_g0_supported(self):
        source = atomic_record()
        report = self.module.validate_g0_candidate(
            source, source["observation_candidates"][0], self.maps
        )
        self.assertTrue(report["eligible"])
        self.assertEqual("atomic_process_executed_command_v1", report["template_id"])

    def test_join_host_port_and_explicit_time_are_mechanical(self):
        source = socbed_network_record()
        report = self.module.validate_g0_candidate(
            source, source["observation_candidates"][0], self.maps
        )
        self.assertTrue(report["eligible"])
        self.assertEqual("socbed_network_connected_v1", report["template_id"])

    def test_cam_placeholder_host_is_not_a_g0_positive(self):
        source = cam_record()
        report = self.module.validate_g0_candidate(
            source, source["observation_candidates"][0], self.maps
        )
        self.assertFalse(report["eligible"])
        self.assertIn("explicit_subject_field_missing", report["reason_codes"])

    def test_legacy_null_cannot_be_reinterpreted(self):
        with self.assertRaisesRegex(ValueError, "legacy packet null"):
            self.module.build_supported_example(legacy_null_record(), {}, self.maps)

    def test_pointer_mismatch_and_missing_provenance_fail_closed(self):
        source = atomic_record()
        candidate = dict(source["observation_candidates"][0])
        candidate["source_pointer"] = {"artifact_id": "ART-X", "record_id": "REC-X"}
        report = self.module.validate_g0_candidate(source, candidate, self.maps)
        self.assertFalse(report["eligible"])
        self.assertIn("pointer_mismatch", report["reason_codes"])
        source.pop("provenance")
        report = self.module.validate_g0_candidate(
            source, source["observation_candidates"][0], self.maps
        )
        self.assertFalse(report["eligible"])
        self.assertIn("provenance_missing", report["reason_codes"])

    def test_supported_and_negative_examples_validate_against_schema(self):
        training_schema = load_json(SCHEMA_ROOT / "candidate_edge_training.schema.json")
        proof_schema = load_json(
            SCHEMA_ROOT / "pointer_bounded_negative_proof.schema.json"
        )
        registry = Registry().with_resource(
            proof_schema["$id"], Resource.from_contents(proof_schema)
        )
        validator = Draft202012Validator(training_schema, registry=registry)
        source = socbed_network_record()
        donor = socbed_network_record(record_id="REC-B", destination="10.0.0.3")
        positive = self.module.build_supported_example(
            source, source["observation_candidates"][0], self.maps
        )
        negative = self.module.generate_n1_object_swap(positive, donor, self.maps)
        validator.validate(positive)
        validator.validate(negative)


class CandidateNegativeGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.maps = cls.module.load_field_maps(
            FIELD_MAP_ROOT / "source-field-maps.json",
            FIELD_MAP_ROOT / "field-map-lock.json",
        )

    def _supported(self, source: dict) -> dict:
        return self.module.build_supported_example(
            source, source["observation_candidates"][0], self.maps
        )

    def _validate(self, example: dict, *records: dict) -> dict:
        index = {self.module.record_sha256(row): row for row in records}
        return self.module.validate_negative_example(example, index, self.maps)

    def test_n1_same_type_object_swap_has_revalidatable_proof(self):
        source = socbed_network_record()
        donor = socbed_network_record(record_id="REC-B", destination="10.0.0.3")
        example = self.module.generate_n1_object_swap(
            self._supported(source), donor, self.maps
        )
        report = self._validate(example, source, donor)
        self.assertTrue(report["valid"], report["reason_codes"])
        self.assertEqual("N1", example["negative_proof"]["generator"])
        self.assertEqual("10.0.0.3:443", example["candidate"]["object_value"])

    def test_n2_pointer_swap_is_pointer_bounded_and_revalidated(self):
        source = socbed_network_record()
        bound = socbed_network_record(record_id="REC-B", destination="10.0.0.3")
        example = self.module.generate_n2_pointer_swap(
            self._supported(source), bound, self.maps
        )
        report = self._validate(example, source, bound)
        self.assertTrue(report["valid"], report["reason_codes"])
        self.assertEqual("REC-B", example["candidate"]["source_pointer"]["record_id"])
        self.assertEqual("unsupported_by_bound_pointer", example["support_decision"])
        self.assertFalse(
            example["negative_proof"]["mechanical_checks"]["world_false_claim_made"]
        )

    def test_n3_predicate_incompatibility_comes_from_frozen_map(self):
        source = atomic_record()
        example = self.module.generate_n3_predicate_incompatibility(
            self._supported(source), "connected_to", self.maps
        )
        report = self._validate(example, source)
        self.assertTrue(report["valid"], report["reason_codes"])
        self.assertEqual("N3", example["negative_proof"]["generator"])
        with self.assertRaisesRegex(ValueError, "frozen incompatible"):
            self.module.generate_n3_predicate_incompatibility(
                self._supported(source), "invented_predicate", self.maps
            )

    def test_n4_time_mismatch_requires_explicit_distinct_same_packet_time(self):
        source = socbed_network_record()
        donor = socbed_network_record(
            record_id="REC-B",
            destination="10.0.0.3",
            event_time="2021-01-01T01:00:00Z",
        )
        example = self.module.generate_n4_time_mismatch(
            self._supported(source), donor, self.maps
        )
        report = self._validate(example, source, donor)
        self.assertTrue(report["valid"], report["reason_codes"])
        self.assertEqual("2021-01-01T01:00:00Z", example["candidate"]["event_time"])

    def test_cross_family_and_cross_packet_donors_fail_closed(self):
        source = socbed_network_record()
        with self.assertRaisesRegex(ValueError, "source family"):
            self.module.generate_n1_object_swap(
                self._supported(source), atomic_record(), self.maps
            )
        cross_packet = socbed_network_record(record_id="REC-B", document_id="DOC-X")
        with self.assertRaisesRegex(ValueError, "same packet"):
            self.module.generate_n2_pointer_swap(
                self._supported(source), cross_packet, self.maps
            )

    def test_tampered_world_false_proof_is_rejected(self):
        source = socbed_network_record()
        donor = socbed_network_record(record_id="REC-B", destination="10.0.0.3")
        example = self.module.generate_n1_object_swap(
            self._supported(source), donor, self.maps
        )
        example["negative_proof"]["mechanical_checks"]["world_false_claim_made"] = True
        report = self._validate(example, source, donor)
        self.assertFalse(report["valid"])
        self.assertIn("world_false_claim_forbidden", report["reason_codes"])


class CandidateHistoricalAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_quantity_does_not_override_source_family_gate(self):
        report = self.module.evaluate_non_token_gate(
            train_counts={"train-a": 700},
            validation_counts={"validation-a": 200},
        )
        self.assertEqual("failed_non_token_data_gate", report["status"])
        self.assertIn("train_g0_positive_families_below_4", report["failure_reasons"])
        self.assertIn(
            "validation_g0_positive_families_below_2", report["failure_reasons"]
        )

    def test_non_token_gate_pass_requires_disjoint_four_plus_two_families(self):
        report = self.module.evaluate_non_token_gate(
            train_counts={"a": 150, "b": 150, "c": 150, "d": 150},
            validation_counts={"e": 75, "f": 75},
        )
        self.assertEqual("passed_non_token_gate_token_gate_pending", report["status"])
        self.assertEqual(1200, report["maximum_balanced_train_pairs"])
        self.assertEqual(300, report["maximum_balanced_validation_pairs"])
        overlap = self.module.evaluate_non_token_gate(
            train_counts={"a": 150, "b": 150, "c": 150, "d": 150},
            validation_counts={"a": 75, "f": 75},
        )
        self.assertIn("train_validation_family_overlap", overlap["failure_reasons"])

    def test_frozen_readiness_never_claims_pair_model_or_training_execution(self):
        readiness_path = (
            EXPERIMENT_ROOT
            / "llm_evidence_compiler_mainline"
            / "qwen-candidate-edge-readiness-v0.1.json"
        )
        readiness = load_json(readiness_path)
        self.assertEqual("failed_non_token_data_gate", readiness["status"])
        execution = readiness["execution_claims"]
        self.assertFalse(execution["formal_candidate_pairs_constructed"])
        self.assertFalse(execution["corpus_copied_into_mainline"])
        self.assertFalse(execution["tokenizer_used"])
        self.assertFalse(execution["model_used"])
        self.assertFalse(execution["runtime_modified"])
        self.assertFalse(execution["training_run"])
        self.assertFalse(readiness["formal_data_gate_passed"])


if __name__ == "__main__":
    unittest.main()
