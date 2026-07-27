import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = (
    REPO_ROOT
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-m1-evidence-sufficiency-checker-non-null-red-design-v0.1-20260727.json"
)
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
    "docs/kernel/kernel-v0.8-m1-evidence-claim-ir-coverage-expansion-owner-acceptance-v0.1-20260727.json": "f4b00bf3fd10cd8d70afa9cdf3ee71b7ed16bd2da694b6caf31b210a7c3443a4",
    "docs/kernel/kernel-v0.8-m1-evidence-claim-ir-readonly-e2e-owner-acceptance-v0.1-20260727.json": "dd264de3f09a385070098969a5a4809c846ffde246e869a7f4382a8fbff4615c",
    "docs/kernel/kernel-v0.8-claim-ir-evidence-claim-record-schema-green-owner-acceptance-v0.1-20260727.json": "60c31ffef0e4288f031b749ff89807904d13986025b56c769295ef80348ce148",
    "docs/kernel/kernel-v0.8-m1-evidence-to-claim-ir-mapping-green-2-owner-acceptance-v0.1-20260727.json": "138715778a4a9ecc5cbaef913b56244b3b0c52e11e9f774a50bfc2e0b64a66f4",
    "schemas/claim-ir-external-envelope-evidence-v0.1.schema.json": "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c",
    "schemas/claim-ir-kernel-evidence-additive-v0.1.schema.json": "d8cccbad36c6cca068fdc9d17ecbd8d0db2e08271f986127d0c0236353a79ce5",
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.2-20260727.json": "fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504",
    "schemas/claim-ir-external-envelope.schema.json": "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e",
    "schemas/claim-ir-kernel.schema.json": "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d",
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json": "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63",
    "src/compiler/llm/m1_system_log_projection_adapter.py": "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116",
    "src/compiler/llm/m1_provenance_graph_projection_adapter.py": "9068315019a2980bb43b81d9641537c5a7c69ca63f14c4b9e876a653f8ffeae5",
    "src/compiler/llm/m1_cti_report_projection_adapter.py": "cc0e04dd15372ecc1e0b5b68777458f07a361cb77ec7ce2c318b1ef42a07be3e",
    "src/compiler/llm/m1_evidence_to_claim_ir_mapper.py": "1dd8f407cc8fe840d90a7bf66c43e2cb11b5131877f2e46f92f2a1ffd372965b",
}
PACKAGE_BINDING_FIELDS = (
    "binding_id",
    "package_role",
    "source_class",
    "epistemic_modality",
    "package_sha256",
    "claim_count",
    "evidence_field_path_set_sha256",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class M1EvidenceSufficiencyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design = load_json(DESIGN_PATH)
        cls.schema = cls.design["draft_contract_schema"]
        cls.validator = Draft202012Validator(cls.schema)
        cls.examples = {
            name: load_json(path) for name, path in EXAMPLES.items()
        }
        cls.catalog = {
            entry["binding_id"]: entry
            for entry in cls.design["input_binding_catalog"]
        }

    def test_preflight_and_protected_pins_are_exact(self):
        actual = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, actual)

    def test_embedded_draft_schema_and_all_examples_are_valid(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertIn("/drafts/", self.schema["$id"])
        self.assertTrue(
            self.design["this_design_is_not_an_effective_schema_or_runtime"]
        )
        for name, example in self.examples.items():
            with self.subTest(example=name):
                self.assertEqual([], list(self.validator.iter_errors(example)))

    def test_catalog_binds_exact_e2e_and_a1_packages_and_field_sets(self):
        self.assertEqual(6, len(self.catalog))
        self.assertEqual(
            [4, 9, 11, 16, 34, 48],
            sorted(entry["claim_count"] for entry in self.catalog.values()),
        )
        for binding_id, entry in self.catalog.items():
            with self.subTest(binding_id=binding_id):
                self.assertEqual(
                    entry["evidence_field_path_set_sha256"],
                    canonical_sha256(entry["evidence_field_path_set"]),
                )
                self.assertTrue(
                    all(
                        field.startswith("evidence.")
                        for field in entry["evidence_field_path_set"]
                    )
                )

    def test_example_package_bindings_match_catalog_exactly(self):
        for example_name, example in self.examples.items():
            packages = example["input_binding"]["accepted_packages"]
            for binding in packages:
                with self.subTest(
                    example=example_name,
                    binding_id=binding["binding_id"],
                ):
                    catalog = self.catalog[binding["binding_id"]]
                    expected = {
                        field: catalog[field] for field in PACKAGE_BINDING_FIELDS
                    }
                    self.assertEqual(expected, binding)
            self.assertEqual(
                [binding["package_sha256"] for binding in packages],
                example["evidence_sufficiency_decision"][
                    "pinned_package_sha256s"
                ],
            )

    def test_positive_conditional_has_non_null_checker_without_elevation(self):
        record = self.examples["conditional"]
        self.assertEqual(6, len(record["input_binding"]["accepted_packages"]))
        self.assertEqual(
            122,
            sum(
                binding["claim_count"]
                for binding in record["input_binding"]["accepted_packages"]
            ),
        )
        sufficiency = record["evidence_sufficiency_decision"]
        checker = record["checker_decision"]
        self.assertEqual(
            "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
            sufficiency["decision"],
        )
        self.assertEqual([], sufficiency["fail_closed_reasons"])
        self.assertIsInstance(checker, dict)
        self.assertTrue(checker["checker_decision_non_null"])
        self.assertEqual(
            sufficiency["decision_id"],
            checker["sufficiency_decision_ref"],
        )
        self.assertEqual(
            "ACCEPT_CONDITIONAL_FOR_READONLY_REVIEW_ONLY",
            checker["decision"],
        )
        self._assert_no_elevation(record)

    def test_missing_modalities_fail_despite_structural_pass(self):
        record = self.examples["missing"]
        self.assertEqual(
            "PASS_FOR_ACCEPTED_PACKAGES_ONLY",
            record["input_binding"]["schema_validity_layer"],
        )
        self.assertEqual(
            "PASS_STRUCTURAL_ONLY_NO_INGESTION_AUTHORITY",
            record["input_binding"]["consumer_structural_layer"],
        )
        self.assertEqual(
            {"system_log_public_projection"},
            {
                binding["source_class"]
                for binding in record["input_binding"]["accepted_packages"]
            },
        )
        sufficiency = record["evidence_sufficiency_decision"]
        self.assertEqual("FAIL_INSUFFICIENT_EVIDENCE", sufficiency["decision"])
        self.assertEqual(
            {
                "MISSING_PROVENANCE_GRAPH_EVIDENCE",
                "MISSING_CTI_REPORT_EVIDENCE",
            },
            set(sufficiency["fail_closed_reasons"]),
        )
        self.assertEqual(
            "REJECT_FAIL_CLOSED",
            record["checker_decision"]["decision"],
        )
        self._assert_no_elevation(record)

    def test_cti_observed_laundering_is_denied_before_package_input(self):
        record = self.examples["cti_laundering"]
        self.assertEqual([], record["input_binding"]["accepted_packages"])
        rejected = record["input_binding"]["rejected_candidates"]
        self.assertEqual(1, len(rejected))
        self.assertEqual("cti_report_public_projection", rejected[0]["source_class"])
        self.assertEqual("observed", rejected[0]["epistemic_modality"])
        self.assertFalse(rejected[0]["package_emitted"])
        self.assertEqual(
            "DENY_INVALID_OR_LAUNDERED_INPUT",
            record["evidence_sufficiency_decision"]["decision"],
        )
        self.assertEqual(
            "DENY_INVALID_INPUT",
            record["checker_decision"]["decision"],
        )
        self._assert_no_elevation(record)

    def test_cti_accepted_package_rejects_observed_or_derived(self):
        for modality in ("observed", "derived"):
            record = copy.deepcopy(self.examples["conditional"])
            cti = next(
                binding
                for binding in record["input_binding"]["accepted_packages"]
                if binding["source_class"] == "cti_report_public_projection"
            )
            cti["epistemic_modality"] = modality
            with self.subTest(modality=modality):
                self.assertNotEqual([], list(self.validator.iter_errors(record)))

    def test_unknown_modality_supports_abstain_without_package(self):
        record = copy.deepcopy(self.examples["cti_laundering"])
        record["record_id"] = "sufficiency_checker_unknown_001"
        candidate = record["input_binding"]["rejected_candidates"][0]
        candidate.update(
            {
                "source_class": "system_log_public_projection",
                "candidate_projection_sha256": "0" * 64,
                "epistemic_modality": "unknown",
                "reason_code": "UNKNOWN_MODALITY_NO_PACKAGE",
            }
        )
        sufficiency = record["evidence_sufficiency_decision"]
        sufficiency.update(
            {
                "decision_id": "sufficiency_unknown_001",
                "decision": "ABSTAIN_UNRESOLVED_EVIDENCE",
                "basis_codes": [
                    "UNKNOWN_MODALITY_NO_PACKAGE",
                    "STRUCTURAL_VALIDITY_SEPARATE_FROM_SUFFICIENCY",
                    "DECLARED_SYNTHETIC_SCOPE_ONLY",
                    "NO_AUTHORITY_ELEVATION",
                ],
                "fail_closed_reasons": ["UNKNOWN_MODALITY_NO_PACKAGE"],
            }
        )
        checker = record["checker_decision"]
        checker.update(
            {
                "decision_id": "checker_unknown_001",
                "decision": "ABSTAIN_FAIL_CLOSED",
                "sufficiency_decision_ref": "sufficiency_unknown_001",
                "basis_codes": [
                    "CHECKER_OBJECT_SCHEMA_VALID",
                    "UNKNOWN_MODALITY_NO_PACKAGE",
                    "NO_AUTHORITY_ELEVATION",
                ],
            }
        )
        self.assertEqual([], list(self.validator.iter_errors(record)))
        self.assertFalse(candidate["package_emitted"])
        self._assert_no_elevation(record)

    def test_structural_validity_never_implies_sufficiency_or_truth(self):
        layers = self.design["layering_contract"]
        self.assertFalse(
            layers["layer_1_schema_validity"]["automatically_implies_sufficiency"]
        )
        self.assertFalse(
            layers["layer_2_consumer_structural_pass"][
                "automatically_implies_sufficiency"
            ]
        )
        self.assertFalse(
            layers["layer_3_evidence_sufficiency"]["automatically_implies_truth"]
        )
        self.assertFalse(
            layers["layer_4_checker_decision"]["automatically_implies_admission"]
        )

    def test_non_null_checker_is_red_only_and_a3_path_b_stay_denied(self):
        boundary = self.design["checker_integration_boundary"]
        self.assertTrue(
            boundary[
                "non_null_checker_decision_authorized_in_this_red_record_shape"
            ]
        )
        for field in (
            "runtime_checker_execution_authorized",
            "existing_e_case_checker_decision_field_change_authorized",
            "existing_certificate_checker_decision_ref_change_authorized",
            "existing_certified_stop_checker_or_sufficiency_ref_change_authorized",
        ):
            with self.subTest(field=field):
                self.assertFalse(boundary[field])
        blocked = self.design["explicit_non_authorizations"]
        for field in (
            "green_sufficiency_evaluator_runtime",
            "checker_runtime_connection",
            "a3_audit_log",
            "registry_activation",
            "production_execute",
            "claim_id_mint",
            "admission",
            "kernel_ingestion_or_write",
            "e_case_write",
            "certificate_generation",
            "certified_stop",
        ):
            with self.subTest(field=field):
                self.assertFalse(blocked[field])
        source_classes = self.schema["$defs"]["package_binding"]["properties"][
            "source_class"
        ]["enum"]
        self.assertNotIn("audit_log", source_classes)

    def test_readonly_validation_preserves_protected_bytes(self):
        before = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        for example in self.examples.values():
            self.assertEqual([], list(self.validator.iter_errors(example)))
        after = {
            path: file_sha256(REPO_ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(before, after)
        self.assertEqual(PROTECTED_PINS, after)

    def _assert_no_elevation(self, record: dict):
        sufficiency = record["evidence_sufficiency_decision"]
        checker = record["checker_decision"]
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
