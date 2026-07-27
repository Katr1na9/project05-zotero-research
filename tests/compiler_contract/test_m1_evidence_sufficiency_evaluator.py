import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_evidence_sufficiency_evaluator as evaluator  # noqa: E402


EXAMPLE_ROOT = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "fixtures"
    / "evidence-sufficiency-checker-non-null-red-v0.1"
)
EXAMPLES = {
    "conditional": EXAMPLE_ROOT / "conditional-sufficient-record.json",
    "missing": EXAMPLE_ROOT / "missing-modalities-fail-record.json",
    "cti_laundering": EXAMPLE_ROOT / "cti-laundering-deny-record.json",
}
PROTECTED_PINS = {
    evaluator.A2_RED_ACCEPTANCE_PATH: evaluator.A2_RED_ACCEPTANCE_SHA256,
    evaluator.RED_DESIGN_PATH: evaluator.RED_DESIGN_SHA256,
    evaluator.RED_REVIEW_PACKET_PATH: evaluator.RED_REVIEW_PACKET_SHA256,
    evaluator.RED_CONTRACT_TEST_PATH: evaluator.RED_CONTRACT_TEST_SHA256,
    **{
        evaluator.RED_EXAMPLE_PATHS[name]: evaluator.RED_EXAMPLE_SHA256S[name]
        for name in ("conditional", "missing", "cti_laundering")
    },
    evaluator.PATH_A1_ACCEPTANCE_PATH: evaluator.PATH_A1_ACCEPTANCE_SHA256,
    evaluator.READONLY_E2E_ACCEPTANCE_PATH: (
        evaluator.READONLY_E2E_ACCEPTANCE_SHA256
    ),
    evaluator.SCHEMA_GREEN_ACCEPTANCE_PATH: (
        evaluator.SCHEMA_GREEN_ACCEPTANCE_SHA256
    ),
    evaluator.GREEN_2_ACCEPTANCE_PATH: evaluator.GREEN_2_ACCEPTANCE_SHA256,
    evaluator.EXTERNAL_EVIDENCE_SCHEMA_PATH: (
        evaluator.EXTERNAL_EVIDENCE_SCHEMA_SHA256
    ),
    evaluator.KERNEL_ADDITIVE_SCHEMA_PATH: (
        evaluator.KERNEL_ADDITIVE_SCHEMA_SHA256
    ),
    evaluator.CONSUMER_CONTRACT_PATH: evaluator.CONSUMER_CONTRACT_SHA256,
    evaluator.LEGACY_EXTERNAL_SCHEMA_PATH: (
        evaluator.LEGACY_EXTERNAL_SCHEMA_SHA256
    ),
    evaluator.LEGACY_KERNEL_SCHEMA_PATH: evaluator.LEGACY_KERNEL_SCHEMA_SHA256,
    evaluator.LEGACY_CONSUMER_CONTRACT_PATH: (
        evaluator.LEGACY_CONSUMER_CONTRACT_SHA256
    ),
    evaluator.GREEN_2_MAPPER_PATH: evaluator.GREEN_2_MAPPER_SHA256,
    evaluator.SYSTEM_LOG_ADAPTER_PATH: evaluator.SYSTEM_LOG_ADAPTER_SHA256,
    evaluator.PROVENANCE_ADAPTER_PATH: evaluator.PROVENANCE_ADAPTER_SHA256,
    evaluator.CTI_ADAPTER_PATH: evaluator.CTI_ADAPTER_SHA256,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority_for(accepted, rejected=()):
    normalized_accepted = evaluator._normalize_accepted_bindings(
        accepted,
        REPO_ROOT,
    )
    normalized_rejected = evaluator._normalize_rejected_candidates(rejected)
    return {
        "status": evaluator.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(evaluator._EXPECTED_SCOPE),
        "pinned_hashes": {
            "a2_red_acceptance_sha256": evaluator.A2_RED_ACCEPTANCE_SHA256,
            "red_design_sha256": evaluator.RED_DESIGN_SHA256,
            "conditional_example_sha256": evaluator.RED_EXAMPLE_SHA256S[
                "conditional"
            ],
            "missing_example_sha256": evaluator.RED_EXAMPLE_SHA256S["missing"],
            "cti_laundering_example_sha256": evaluator.RED_EXAMPLE_SHA256S[
                "cti_laundering"
            ],
            "external_evidence_schema_sha256": (
                evaluator.EXTERNAL_EVIDENCE_SCHEMA_SHA256
            ),
            "kernel_additive_schema_sha256": (
                evaluator.KERNEL_ADDITIVE_SCHEMA_SHA256
            ),
            "consumer_v0_2_sha256": evaluator.CONSUMER_CONTRACT_SHA256,
            "legacy_external_schema_sha256": (
                evaluator.LEGACY_EXTERNAL_SCHEMA_SHA256
            ),
            "legacy_kernel_schema_sha256": (
                evaluator.LEGACY_KERNEL_SCHEMA_SHA256
            ),
            "legacy_consumer_contract_sha256": (
                evaluator.LEGACY_CONSUMER_CONTRACT_SHA256
            ),
            "green_2_mapper_sha256": evaluator.GREEN_2_MAPPER_SHA256,
            "system_log_adapter_sha256": evaluator.SYSTEM_LOG_ADAPTER_SHA256,
            "provenance_graph_adapter_sha256": (
                evaluator.PROVENANCE_ADAPTER_SHA256
            ),
            "cti_report_adapter_sha256": evaluator.CTI_ADAPTER_SHA256,
            "evaluator_implementation_sha256": file_sha256(
                REPO_ROOT / evaluator.EVALUATOR_IMPLEMENTATION_PATH
            ),
        },
        "pinned_input": {
            "accepted_package_bindings_sha256": (
                evaluator.canonical_json_sha256(normalized_accepted)
            ),
            "rejected_candidates_sha256": evaluator.canonical_json_sha256(
                normalized_rejected
            ),
        },
        "output_policy": copy.deepcopy(evaluator._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(evaluator._EXPECTED_STILL_BLOCKED),
    }


class M1EvidenceSufficiencyEvaluatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = evaluator.package_binding_catalog(REPO_ROOT)
        cls.examples = {
            name: load_json(path) for name, path in EXAMPLES.items()
        }

    def test_evaluator_reverifies_red_and_protected_pins(self):
        evaluator.verify_evaluator_pins(REPO_ROOT)
        actual = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, actual)
        self.assertEqual(21, len(PROTECTED_PINS))

    def test_missing_or_elevated_test_authority_fails_closed(self):
        with self.assertRaises(
            evaluator.M1EvidenceSufficiencyEvaluatorError
        ) as context:
            evaluator.evaluate_evidence_sufficiency_for_readonly_review(
                self.catalog,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("missing_authority", context.exception.code)

        authority = authority_for(self.catalog)
        authority["output_policy"]["kernel_write"] = True
        with self.assertRaises(
            evaluator.M1EvidenceSufficiencyEvaluatorError
        ) as context:
            evaluator.evaluate_evidence_sufficiency_for_readonly_review(
                self.catalog,
                repo_root=REPO_ROOT,
                authority=authority,
            )
        self.assertEqual("authority_output", context.exception.code)

    def test_complete_six_package_scope_reproduces_conditional_red_record(self):
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            list(reversed(self.catalog)),
            repo_root=REPO_ROOT,
            authority=authority_for(self.catalog),
        )
        self.assertEqual(self.examples["conditional"], record)
        self.assertEqual(
            "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertTrue(record["checker_decision"]["checker_decision_non_null"])
        self.assertEqual(
            "ACCEPT_CONDITIONAL_FOR_READONLY_REVIEW_ONLY",
            record["checker_decision"]["decision"],
        )
        self._assert_field_set_pins_and_no_elevation(record)

    def test_missing_modalities_reproduces_fail_red_record_despite_structural_pass(self):
        accepted = [
            entry
            for entry in self.catalog
            if entry["source_class"] == "system_log_public_projection"
        ]
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            accepted,
            repo_root=REPO_ROOT,
            authority=authority_for(accepted),
        )
        self.assertEqual(self.examples["missing"], record)
        self.assertEqual(
            "PASS_FOR_ACCEPTED_PACKAGES_ONLY",
            record["input_binding"]["schema_validity_layer"],
        )
        self.assertEqual(
            "PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY",
            record["input_binding"]["consumer_structural_layer"],
        )
        self.assertEqual(
            "FAIL_INSUFFICIENT_EVIDENCE",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertEqual("REJECT_FAIL_CLOSED", record["checker_decision"]["decision"])
        self._assert_field_set_pins_and_no_elevation(record)

    def test_cti_observed_reproduces_red_laundering_deny(self):
        rejected = [
            {
                "source_class": "cti_report_public_projection",
                "candidate_projection_sha256": (
                    "2869145b445195c780164fa9bce8721fa"
                    "909ca68a9f4e41c4c85a1933c43d860"
                ),
                "epistemic_modality": "observed",
            }
        ]
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            [],
            repo_root=REPO_ROOT,
            authority=authority_for([], rejected),
            rejected_candidates=rejected,
        )
        self.assertEqual(self.examples["cti_laundering"], record)
        self.assertEqual(
            "DENY_INVALID_OR_LAUNDERED_INPUT",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertFalse(
            record["input_binding"]["rejected_candidates"][0][
                "package_emitted"
            ]
        )
        self._assert_field_set_pins_and_no_elevation(record)

    def test_cti_derived_is_denied_without_package(self):
        rejected = [
            {
                "source_class": "cti_report_public_projection",
                "candidate_projection_sha256": "1" * 64,
                "epistemic_modality": "derived",
            }
        ]
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            [],
            repo_root=REPO_ROOT,
            authority=authority_for([], rejected),
            rejected_candidates=rejected,
        )
        self.assertEqual(
            "DENY_INVALID_OR_LAUNDERED_INPUT",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertEqual(
            ["CTI_DERIVED_LAUNDERING"],
            record["evidence_sufficiency_decision"]["fail_closed_reasons"],
        )
        self.assertEqual([], record["input_binding"]["accepted_packages"])
        self._assert_field_set_pins_and_no_elevation(record)

    def test_unknown_modality_abstains_without_package_or_partial_emission(self):
        rejected = [
            {
                "source_class": "system_log_public_projection",
                "candidate_projection_sha256": "0" * 64,
                "epistemic_modality": "unknown",
            }
        ]
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            [],
            repo_root=REPO_ROOT,
            authority=authority_for([], rejected),
            rejected_candidates=rejected,
        )
        self.assertEqual(
            "ABSTAIN_UNRESOLVED_EVIDENCE",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertEqual("ABSTAIN_FAIL_CLOSED", record["checker_decision"]["decision"])
        self.assertEqual([], record["input_binding"]["accepted_packages"])
        self.assertEqual([], record["evidence_sufficiency_decision"]["pinned_package_sha256s"])
        self.assertFalse(
            record["input_binding"]["rejected_candidates"][0][
                "package_emitted"
            ]
        )
        self._assert_field_set_pins_and_no_elevation(record)

    def test_structural_pass_never_silently_promotes_partial_scope(self):
        accepted = [self.catalog[0]]
        record = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            accepted,
            repo_root=REPO_ROOT,
            authority=authority_for(accepted),
        )
        self.assertEqual(
            "PASS_FOR_ACCEPTED_PACKAGES_ONLY",
            record["input_binding"]["schema_validity_layer"],
        )
        self.assertEqual(
            "FAIL_INSUFFICIENT_EVIDENCE",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertNotIn(
            record["evidence_sufficiency_decision"]["decision"],
            {
                "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
                "PASS_DECLARED_SYNTHETIC_BOUNDARY_ONLY",
            },
        )
        self._assert_field_set_pins_and_no_elevation(record)

    def test_catalog_mismatch_unknown_duplicate_and_mixed_partial_fail_closed(self):
        bad_package = copy.deepcopy(self.catalog[0])
        bad_package["package_sha256"] = "f" * 64
        bad_field_set = copy.deepcopy(self.catalog[0])
        bad_field_set["evidence_field_path_set_sha256"] = "e" * 64
        unknown = copy.deepcopy(self.catalog[0])
        unknown["binding_id"] = "unknown_binding"
        cases = (
            ("package_binding_mismatch", [bad_package]),
            ("evidence_field_set_mismatch", [bad_field_set]),
            ("unknown_binding", [unknown]),
            ("duplicate_binding", [self.catalog[0], self.catalog[0]]),
        )
        for expected_code, bindings in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    evaluator.M1EvidenceSufficiencyEvaluatorError
                ) as context:
                    evaluator.evaluate_evidence_sufficiency_for_readonly_review(
                        bindings,
                        repo_root=REPO_ROOT,
                        authority=authority_for([]),
                    )
                self.assertEqual(expected_code, context.exception.code)

        rejected = [
            {
                "source_class": "system_log_public_projection",
                "candidate_projection_sha256": "2" * 64,
                "epistemic_modality": "unknown",
            }
        ]
        with self.assertRaises(
            evaluator.M1EvidenceSufficiencyEvaluatorError
        ) as context:
            evaluator.evaluate_evidence_sufficiency_for_readonly_review(
                [self.catalog[0]],
                repo_root=REPO_ROOT,
                authority=authority_for([self.catalog[0]], rejected),
                rejected_candidates=rejected,
            )
        self.assertEqual("mixed_partial_input", context.exception.code)

    def test_same_input_is_deterministic_and_does_not_mutate_inputs(self):
        accepted = copy.deepcopy(self.catalog)
        authority = authority_for(accepted)
        accepted_before = copy.deepcopy(accepted)
        authority_before = copy.deepcopy(authority)
        first = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            accepted,
            repo_root=REPO_ROOT,
            authority=authority,
        )
        second = evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            copy.deepcopy(accepted),
            repo_root=REPO_ROOT,
            authority=copy.deepcopy(authority),
        )
        self.assertEqual(first, second)
        self.assertEqual(
            evaluator.canonical_json_sha256(first),
            evaluator.canonical_json_sha256(second),
        )
        self.assertEqual(accepted_before, accepted)
        self.assertEqual(authority_before, authority)

    def test_evaluation_preserves_every_protected_byte(self):
        before = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        evaluator.evaluate_evidence_sufficiency_for_readonly_review(
            self.catalog,
            repo_root=REPO_ROOT,
            authority=authority_for(self.catalog),
        )
        after = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(before, after)
        self.assertEqual(PROTECTED_PINS, after)

    def _assert_field_set_pins_and_no_elevation(self, record):
        accepted = record["input_binding"]["accepted_packages"]
        for binding in accepted:
            self.assertRegex(
                binding["evidence_field_path_set_sha256"],
                r"^[0-9a-f]{64}$",
            )
        sufficiency = record["evidence_sufficiency_decision"]
        checker = record["checker_decision"]
        if accepted:
            self.assertIn(
                "EXACT_EVIDENCE_FIELD_SETS_VERIFIED",
                sufficiency["basis_codes"],
            )
        self.assertIn("NO_AUTHORITY_ELEVATION", sufficiency["basis_codes"])
        self.assertIn("NO_AUTHORITY_ELEVATION", checker["basis_codes"])
        self.assertFalse(sufficiency["truth_asserted"])
        self.assertFalse(sufficiency["admission_authority"])
        self.assertFalse(sufficiency["ingestion_authority"])
        self.assertEqual("NONE", sufficiency["stop_authority"])
        self.assertFalse(checker["truth_asserted"])
        self.assertFalse(checker["admission_authority"])
        self.assertFalse(checker["kernel_write_authority"])
        self.assertFalse(checker["certificate_authority"])
        self.assertEqual("NONE", checker["stop_authority"])
        self.assertTrue(
            all(
                value is False
                for value in record["explicit_non_authorizations"].values()
            )
        )


if __name__ == "__main__":
    unittest.main()