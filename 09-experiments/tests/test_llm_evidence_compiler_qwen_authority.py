import hashlib
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
READINESS_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "qwen-data-reuse-readiness-v0.2.json"
)
NULL_SOURCE_GATE_PATH = CONTRACT_ROOT / "train-null-source-literature-gate-v0.1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class QwenPairedRouteAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = json.loads(
            (CONTRACT_ROOT / "authority-lock-v0.3.json").read_text(encoding="utf-8")
        )

    def test_general_and_adapted_use_the_same_frozen_base(self):
        contract = self.lock["model_contract"]
        self.assertEqual("Qwen/Qwen2.5-7B-Instruct", contract["base_model_id"])
        self.assertEqual(
            "a09a35458c702b33eeacc393d103063234e8bc28",
            contract["base_revision"],
        )
        self.assertFalse(contract["general_condition"]["adapter_enabled"])
        self.assertTrue(contract["adapted_condition"]["adapter_enabled"])
        self.assertEqual("adapter_state", contract["only_intended_model_difference"])

    def test_base_is_frozen_and_adapter_is_small_and_adapter_only(self):
        contract = self.lock["model_contract"]
        adapted = contract["adapted_condition"]
        self.assertFalse(contract["general_condition"]["base_trainable"])
        self.assertFalse(adapted["base_trainable"])
        self.assertLessEqual(adapted["maximum_trainable_parameter_fraction"], 0.01)
        self.assertTrue(adapted["save_adapter_only"])
        self.assertTrue(adapted["merged_full_model_forbidden"])
        self.assertEqual("project05_obs_compiler", adapted["adapter_key"])

    def test_all_predeclared_comparison_conditions_are_retained(self):
        self.assertEqual(
            {
                "RULE-STRONG",
                "QWEN-GENERAL",
                "QWEN-ADAPTED",
                "REUSE-HYBRID",
                "GENERAL-CONSTRAINED",
                "GENERAL-DIRECT",
            },
            set(self.lock["required_conditions"]),
        )

    def test_design_approval_does_not_authorize_execution(self):
        forbidden = set(self.lock["not_authorized"])
        self.assertTrue(
            {
                "dependency_install_or_change",
                "tokenizer_download",
                "model_download",
                "smoke_training",
                "formal_training",
                "formal_inference",
                "c07_c12_model_execution",
                "m3_runtime_integration",
                "run_mvp_modification",
                "frozen_case_overwrite",
                "frozen_result_overwrite",
            }
            <= forbidden
        )
        self.assertFalse(self.lock["controller_eligible"])

    def test_referenced_authority_documents_match_frozen_hashes(self):
        frozen = {
            **self.lock["authoritative_documents"],
            **self.lock["authoritative_contracts"],
        }
        for relative, expected in frozen.items():
            with self.subTest(path=relative):
                self.assertNotEqual("PENDING_AFTER_FILE_CREATION", expected)
                self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_parent_and_superseded_document_hashes_are_preserved(self):
        parent = self.lock["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        old = self.lock["model_selection_supersession"]
        self.assertTrue(old["historical_record_preserved"])
        self.assertEqual(
            old["superseded_document_sha256"],
            sha256(REPO_ROOT / old["superseded_document"]),
        )

    def test_repeats_are_not_promoted_to_independent_cases(self):
        unit = self.lock["statistical_unit"]
        self.assertEqual("case_or_attack_chain", unit["independent"])
        self.assertEqual(6, unit["test_case_count"])
        self.assertFalse(unit["generation_repeats_are_independent"])

    def test_fairness_contract_allows_only_adapter_state_to_differ(self):
        fairness = json.loads(
            (CONTRACT_ROOT / "qwen-paired-fairness-contract-v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            "adapter_state",
            fairness["comparison"]["only_allowed_model_difference"],
        )
        self.assertTrue(fairness["run_design"]["same_loaded_base_required"])
        self.assertFalse(
            fairness["run_design"]["generation_repeats_are_independent_samples"]
        )
        self.assertTrue(
            fairness["test_blindness"][
                "checkpoint_selected_on_training_validation_only"
            ]
        )
        self.assertFalse(fairness["test_blindness"]["test_output_may_change_gate"])
        self.assertFalse(fairness["execution_authorized"])

    def test_fairness_manifest_requires_all_confounders_to_match(self):
        fairness = json.loads(
            (CONTRACT_ROOT / "qwen-paired-fairness-contract-v0.1.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(
            {
                "base_snapshot_sha256",
                "tokenizer_snapshot_sha256",
                "runtime_lock_sha256",
                "quantization_config_sha256",
                "prompt_sha256",
                "schema_sha256",
                "public_packet_sha256",
                "decode_config_sha256",
                "hardware_id",
                "admission_contract_sha256",
                "scorer_contract_sha256",
            }
            <= set(fairness["must_match_manifest_fields"])
        )

    def test_data_reaudit_fails_closed_on_train_null_shortage(self):
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        train = readiness["historical_candidate_counts_after_exclusion"]["train"]
        arithmetic = readiness["train_null_arithmetic"]
        self.assertEqual(
            train["total"], train["observation"] + train["eligible_null"]
        )
        self.assertEqual(480, arithmetic["minimum_train_null_for_1200_packet_formal_set"])
        self.assertEqual(478, arithmetic["current_minimum_deficit"])
        self.assertEqual(0, arithmetic["cisa_kev_eligible_train_null"])
        self.assertEqual("fail", readiness["formal_gate_evaluation"]["overall"])
        self.assertEqual(
            "rejected_for_formal_train_null_after_literature_audit",
            readiness["v3_bn_01"]["current_disposition"],
        )
        self.assertFalse(readiness["v3_bn_01"]["user_review_required"])
        self.assertFalse(readiness["v3_bn_01"]["formal_training_use_authorized"])

    def test_kev_license_permission_is_not_promoted_to_label_validity(self):
        gate = json.loads(NULL_SOURCE_GATE_PATH.read_text(encoding="utf-8"))
        self.assertTrue(gate["license_assessment"]["training_processing_permitted"])
        self.assertFalse(gate["scientific_assessment"]["unit_match"])
        formal = gate["formal_training_decision"]
        self.assertFalse(formal["eligible_as_train_null"])
        self.assertFalse(formal["eligible_as_train_hard_negative"])
        self.assertEqual(0, formal["formal_train_null_gate_credit"])
        self.assertFalse(formal["single_author_feasibility_review_required"])

    def test_kev_is_diagnostic_only_and_cannot_select_a_checkpoint(self):
        gate = json.loads(NULL_SOURCE_GATE_PATH.read_text(encoding="utf-8"))
        diagnostic = gate["diagnostic_only_decision"]
        self.assertTrue(diagnostic["eligible"])
        self.assertEqual(
            "non_entailing_contract_negative", diagnostic["required_label"]
        )
        self.assertFalse(diagnostic["may_enter_qlora_training"])
        self.assertFalse(diagnostic["may_count_toward_data_gate"])
        self.assertFalse(diagnostic["may_select_checkpoint"])

    def test_external_evidence_gate_precedes_any_row_level_review(self):
        truth = self.lock["data_truth_contract"]
        self.assertTrue(truth["external_evidence_before_row_review"])
        self.assertFalse(truth["single_author_kev_review_required"])
        self.assertFalse(truth["cisa_kev_formal_train_null_eligible"])
        self.assertEqual(478, truth["current_minimum_deficit"])

    def test_data_reaudit_does_not_claim_model_or_tokenizer_execution(self):
        readiness = json.loads(READINESS_PATH.read_text(encoding="utf-8"))
        self.assertFalse(readiness["corpus_copied_into_mainline"])
        self.assertFalse(readiness["new_corpus_downloaded"])
        self.assertFalse(readiness["tokenizer_used"])
        self.assertFalse(readiness["model_runtime_used"])


if __name__ == "__main__":
    unittest.main()
