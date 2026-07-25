import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
MAINLINE_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline"
CONTRACT_ROOT = MAINLINE_ROOT / "contracts"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class CandidateVerificationDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gate = load_json(CONTRACT_ROOT / "train-null-source-literature-gate-v0.2.json")
        cls.draft = load_json(
            CONTRACT_ROOT / "candidate-edge-verification-contract-draft-v0.1.json"
        )
        cls.readiness = load_json(MAINLINE_ROOT / "qwen-data-reuse-readiness-v0.3.json")
        cls.authority = load_json(CONTRACT_ROOT / "authority-lock-v0.4.json")

    def test_review_counts_and_hashes_are_frozen(self):
        evidence = self.gate["evidence_authority"]
        self.assertEqual(16, evidence["parallel_search_files"])
        self.assertEqual(180, evidence["search_results_total"])
        self.assertEqual(150, evidence["search_urls_unique"])
        self.assertEqual(26, evidence["targeted_extract_files"])
        for path_key, hash_key in (
            ("review_path", "review_sha256"),
            ("paper_evidence_matrix_path", "paper_evidence_matrix_sha256"),
            ("candidate_source_matrix_path", "candidate_source_matrix_sha256"),
            ("citation_report_path", "citation_report_sha256"),
        ):
            with self.subTest(path=evidence[path_key]):
                self.assertEqual(evidence[hash_key], sha256(REPO_ROOT / evidence[path_key]))
        self.assertEqual(32, evidence["verified_doi_occurrences"])
        self.assertEqual(0, evidence["failed_doi_occurrences"])

    def test_no_external_candidate_is_promoted_to_packet_null(self):
        current = self.gate["current_packet_null_contract"]
        self.assertEqual(480, current["formal_train_null_minimum"])
        self.assertEqual(2, current["currently_eligible_train_null"])
        self.assertEqual(478, current["current_minimum_deficit"])
        self.assertEqual(0, current["external_candidate_credit"])
        self.assertFalse(
            self.gate["candidate_dispositions"][
                "formal_external_packet_null_source_found"
            ]
        )

    def test_benign_and_missing_annotations_are_not_null_truth(self):
        assessment = self.gate["structural_assessment"]
        self.assertFalse(
            assessment[
                "benign_or_normal_attack_label_implies_empty_observation_packet"
            ]
        )
        self.assertFalse(
            assessment[
                "security_ie_no_trigger_or_no_relation_implies_empty_project05_packet"
            ]
        )
        self.assertFalse(
            assessment["missing_annotation_or_knowledge_base_relation_is_reliable_negative"]
        )
        self.assertFalse(
            assessment["continue_searching_benign_logs_as_default_packet_null_route"]
        )

    def test_candidate_verification_contract_is_draft_and_non_authorizing(self):
        self.assertFalse(self.draft["authority"])
        self.assertEqual(
            "draft_non_authorizing_pending_user_review", self.draft["status"]
        )
        self.assertFalse(self.draft["negative_semantics"]["world_false_claim"])
        self.assertFalse(self.draft["negative_semantics"]["benign_or_normal_claim"])
        self.assertFalse(self.draft["negative_semantics"]["whole_packet_empty_claim"])
        self.assertEqual(
            {
                "same_type_object_swap_within_packet",
                "pointer_swap_within_packet",
                "frozen_predicate_field_incompatibility",
                "explicit_timestamp_mismatch",
            },
            set(self.draft["proposed_negative_generators"]),
        )

    def test_draft_gate_prevents_source_modality_shortcuts(self):
        gate = self.draft["proposed_data_gate"]
        self.assertEqual(1200, gate["minimum_train_candidate_pairs"])
        self.assertEqual(300, gate["minimum_training_validation_candidate_pairs"])
        self.assertGreaterEqual(gate["minimum_negative_generator_families"], 3)
        self.assertLessEqual(gate["maximum_single_negative_generator_fraction"], 0.5)
        self.assertGreaterEqual(gate["minimum_same_packet_negative_fraction"], 0.75)
        self.assertEqual(1.0, gate["source_modality_match_fraction"])
        self.assertEqual(1.0, gate["proof_validator_pass_fraction"])
        self.assertFalse(gate["truncation_allowed"])

    def test_readiness_remains_failed_under_current_authority(self):
        current = self.readiness["current_formal_packet_gate"]
        self.assertEqual("fail", current["status"])
        self.assertEqual(478, current["current_minimum_deficit"])
        proposed = self.readiness["candidate_verification_draft"]
        self.assertEqual("recommended_not_authorized", proposed["status"])
        self.assertFalse(proposed["g0_positive_count_measured"])
        self.assertFalse(proposed["formal_data_gate_passed"])
        self.assertFalse(proposed["old_packet_null_rows_reinterpreted"])
        self.assertEqual("fail", self.readiness["current_gate_evaluation"]["overall"])

    def test_research_did_not_claim_corpus_model_or_runtime_execution(self):
        self.assertFalse(self.readiness["corpus_copied_into_mainline"])
        self.assertFalse(self.readiness["new_corpus_downloaded"])
        self.assertFalse(self.readiness["tokenizer_used"])
        self.assertFalse(self.readiness["model_runtime_used"])

    def test_latest_authority_preserves_qwen_pair_and_forbids_execution(self):
        model = self.authority["model_contract"]
        self.assertEqual("Qwen/Qwen2.5-7B-Instruct", model["base_model_id"])
        self.assertEqual("adapter_state", model["only_intended_model_difference"])
        amendment = self.authority["candidate_verification_amendment"]
        self.assertFalse(amendment["authority_granted"])
        self.assertFalse(amendment["formal_candidate_pair_construction_allowed"])
        self.assertFalse(amendment["old_packet_null_reinterpretation_allowed"])
        forbidden = set(self.authority["not_authorized"])
        self.assertTrue(
            {
                "candidate_pair_construction",
                "dependency_install_or_change",
                "tokenizer_download",
                "model_download",
                "smoke_training",
                "formal_training",
                "formal_inference",
                "run_mvp_modification",
            }
            <= forbidden
        )
        self.assertFalse(self.authority["controller_eligible"])

    def test_latest_authority_hashes_all_referenced_files(self):
        frozen = {
            **self.authority["authoritative_documents"],
            **self.authority["authoritative_contracts"],
            **self.authority["non_authorizing_drafts"],
        }
        for relative, expected in frozen.items():
            with self.subTest(path=relative):
                self.assertEqual(expected, sha256(REPO_ROOT / relative))
        parent = self.authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))


if __name__ == "__main__":
    unittest.main()
