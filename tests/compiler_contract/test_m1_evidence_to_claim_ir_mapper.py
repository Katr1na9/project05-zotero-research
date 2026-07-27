import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_evidence_to_claim_ir_mapper as mapper  # noqa: E402


FIXTURE_ROOT = (
    REPO_ROOT / "tests" / "compiler_contract" / "fixtures" / "m1_evidence_modality"
)
FIXTURES = {
    "system_log_public_projection": (
        FIXTURE_ROOT / "synthetic_system_log_projection_v0.1.json"
    ),
    "provenance_graph_public_projection": (
        FIXTURE_ROOT / "synthetic_provenance_graph_projection_v0.1.json"
    ),
    "cti_report_public_projection": (
        FIXTURE_ROOT / "synthetic_cti_report_projection_v0.1.json"
    ),
}
EXPECTED_CLAIM_COUNTS = {
    "system_log_public_projection": 9,
    "provenance_graph_public_projection": 16,
    "cti_report_public_projection": 11,
}
PROTECTED_PINS = {
    REPO_ROOT / mapper.EXTERNAL_EVIDENCE_SCHEMA_PATH: (
        mapper.EXTERNAL_EVIDENCE_SCHEMA_SHA256
    ),
    REPO_ROOT / mapper.KERNEL_ADDITIVE_SCHEMA_PATH: (
        mapper.KERNEL_ADDITIVE_SCHEMA_SHA256
    ),
    REPO_ROOT / mapper.CONSUMER_CONTRACT_PATH: mapper.CONSUMER_CONTRACT_SHA256,
    REPO_ROOT / mapper.LEGACY_EXTERNAL_SCHEMA_PATH: (
        mapper.LEGACY_EXTERNAL_SCHEMA_SHA256
    ),
    REPO_ROOT / mapper.LEGACY_KERNEL_SCHEMA_PATH: (
        mapper.LEGACY_KERNEL_SCHEMA_SHA256
    ),
    REPO_ROOT / mapper.LEGACY_CONSUMER_CONTRACT_PATH: (
        mapper.LEGACY_CONSUMER_CONTRACT_SHA256
    ),
    REPO_ROOT / mapper.SYSTEM_LOG_ADAPTER_PATH: mapper.SYSTEM_LOG_ADAPTER_SHA256,
    REPO_ROOT / mapper.PROVENANCE_GRAPH_ADAPTER_PATH: (
        mapper.PROVENANCE_GRAPH_ADAPTER_SHA256
    ),
    REPO_ROOT / mapper.CTI_REPORT_ADAPTER_PATH: mapper.CTI_REPORT_ADAPTER_SHA256,
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture(source_class: str) -> dict:
    return load_json(FIXTURES[source_class])


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority_for(projection: dict) -> dict:
    source_class = projection["descriptor"]["source_class"]
    spec = mapper._SPECS[source_class]
    return {
        "status": mapper.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(mapper._EXPECTED_SCOPE),
        "pinned_hashes": {
            "schema_green_acceptance_sha256": (
                mapper.SCHEMA_GREEN_ACCEPTANCE_SHA256
            ),
            "external_evidence_schema_sha256": (
                mapper.EXTERNAL_EVIDENCE_SCHEMA_SHA256
            ),
            "kernel_additive_schema_sha256": (
                mapper.KERNEL_ADDITIVE_SCHEMA_SHA256
            ),
            "consumer_contract_sha256": mapper.CONSUMER_CONTRACT_SHA256,
            "mapping_framework_sha256": mapper.MAPPING_FRAMEWORK_SHA256,
            "system_log_mapping_contract_sha256": mapper._SPECS[
                "system_log_public_projection"
            ]["mapping_contract_sha256"],
            "provenance_graph_mapping_contract_sha256": mapper._SPECS[
                "provenance_graph_public_projection"
            ]["mapping_contract_sha256"],
            "cti_report_mapping_contract_sha256": mapper._SPECS[
                "cti_report_public_projection"
            ]["mapping_contract_sha256"],
            "system_log_adapter_sha256": mapper.SYSTEM_LOG_ADAPTER_SHA256,
            "provenance_graph_adapter_sha256": (
                mapper.PROVENANCE_GRAPH_ADAPTER_SHA256
            ),
            "cti_report_adapter_sha256": mapper.CTI_REPORT_ADAPTER_SHA256,
            "mapper_implementation_sha256": file_sha256(
                REPO_ROOT / mapper.MAPPER_IMPLEMENTATION_PATH
            ),
        },
        "pinned_input": {
            "source_class": source_class,
            "projection_sha256": spec["projection_sha256"],
            "projection_content_sha256": mapper.canonical_json_sha256(
                projection
            ),
        },
        "output_policy": copy.deepcopy(mapper._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(mapper._EXPECTED_STILL_BLOCKED),
    }


class M1EvidenceToClaimIRMapperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.external_schema = load_json(
            REPO_ROOT / mapper.EXTERNAL_EVIDENCE_SCHEMA_PATH
        )

    def test_mapper_pins_owner_acceptance_effective_identities_and_contracts(self):
        mapper.verify_mapper_pins(REPO_ROOT)
        acceptance = load_json(REPO_ROOT / mapper.SCHEMA_GREEN_ACCEPTANCE_PATH)
        self.assertEqual("accept", acceptance["decision"])
        self.assertEqual(
            "green_accepted_exact_candidate_bytes_now_effective_for_structural_dispatch_only",
            acceptance["status"],
        )
        self.assertFalse(
            acceptance["authorized_now"]["green_2_nonempty_mapper_runtime"]
        )

    def test_missing_or_mutated_test_authority_fails_closed(self):
        projection = load_fixture("system_log_public_projection")
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("missing_authority", context.exception.code)

        authority = authority_for(projection)
        authority["output_policy"]["mint"] = True
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority,
            )
        self.assertEqual("constant", context.exception.code)

    def test_three_modalities_emit_nonempty_effective_schema_packages(self):
        validator = Draft202012Validator(self.external_schema)
        for source_class in FIXTURES:
            projection = load_fixture(source_class)
            package = mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
            with self.subTest(source_class=source_class):
                self.assertEqual([], list(validator.iter_errors(package)))
                self.assertEqual(mapper.SCHEMA_VERSION, package["schema_version"])
                self.assertEqual(
                    EXPECTED_CLAIM_COUNTS[source_class],
                    len(package["claims"]),
                )
                self.assertEqual(
                    len(package["claims"]),
                    package["manifest"]["claim_count"],
                )
                self.assertEqual("not_minted", package["claim_id_state"])
                self.assertEqual("not_admitted", package["admission_state"])
                self.assertEqual(
                    "pending_kernel_schema",
                    package["kernel_state"],
                )
                self.assertTrue(
                    all(claim["claim_id"] is None for claim in package["claims"])
                )

    def test_same_projection_produces_same_package_and_claim_order(self):
        for source_class in FIXTURES:
            projection = load_fixture(source_class)
            authority = authority_for(projection)
            first = mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority,
            )
            second = mapper.map_validated_projection_to_claim_ir(
                copy.deepcopy(projection),
                repo_root=REPO_ROOT,
                authority=copy.deepcopy(authority),
            )
            with self.subTest(source_class=source_class):
                self.assertEqual(first, second)
                self.assertEqual(
                    mapper.canonical_json_sha256(first),
                    mapper.canonical_json_sha256(second),
                )

    def test_output_uses_only_evidence_namespaces_and_structural_states(self):
        for source_class in FIXTURES:
            projection = load_fixture(source_class)
            package = mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
            for claim in package["claims"]:
                with self.subTest(
                    source_class=source_class,
                    evidence_field=claim["evidence_field"],
                ):
                    self.assertEqual(
                        "public_evidence_declaration",
                        claim["record_class"],
                    )
                    self.assertTrue(claim["claim_kind"].startswith("evidence."))
                    self.assertTrue(
                        claim["evidence_field"].startswith("evidence.")
                    )
                    self.assertNotIn("source_field", claim)
                    self.assertNotIn("afs_slot", claim)
                    self.assertNotIn(
                        claim["claim_kind"],
                        mapper._PLANNER_CLAIM_KINDS,
                    )
                    self.assertEqual("not_minted", claim["claim_id_state"])
                    self.assertEqual("not_admitted", claim["admission_state"])

    def test_cti_observed_and_derived_are_denied_as_laundering(self):
        for modality in ("observed", "derived"):
            projection = load_fixture("cti_report_public_projection")
            projection["source_metadata"]["epistemic_modality"] = modality
            with self.subTest(modality=modality):
                with self.assertRaises(
                    mapper.M1EvidenceToClaimIRMapperError
                ) as context:
                    mapper.map_validated_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual("modality_laundering", context.exception.code)

    def test_unknown_modality_abstains_without_partial_emission(self):
        cases = {
            "system_log_public_projection": {
                "epistemic_modality": "unknown",
                "modality_basis_code": "UNRESOLVED_BASIS",
            },
            "provenance_graph_public_projection": {
                "epistemic_modality": "unknown",
                "materialization_class": "MIXED_OR_UNRESOLVED_GRAPH",
                "modality_basis_code": "MIXED_UNSPLIT_OR_UNRESOLVED_BASIS",
            },
            "cti_report_public_projection": {
                "epistemic_modality": "unknown",
                "modality_basis_code": "UNRESOLVED_REPORTING_BASIS",
            },
        }
        for source_class, metadata_patch in cases.items():
            projection = load_fixture(source_class)
            projection["source_metadata"].update(metadata_patch)
            before = copy.deepcopy(projection)
            with self.subTest(source_class=source_class):
                with self.assertRaises(
                    mapper.M1EvidenceToClaimIRMapperError
                ) as context:
                    mapper.map_validated_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(
                    "abstain_unknown_modality",
                    context.exception.code,
                )
                self.assertEqual(before, projection)

    def test_source_field_afs_and_planner_kind_smuggling_are_denied(self):
        source_field = load_fixture("system_log_public_projection")
        source_field["event"]["source_field"] = "config.case_id"
        afs = load_fixture("system_log_public_projection")
        afs["event"]["afs_slot"] = "AFS.case_id"
        planner_kind = load_fixture("system_log_public_projection")
        planner_kind["event"]["claim_kind"] = "public_config"
        for name, projection, expected in (
            ("source_field", source_field, "forbidden_input_field"),
            ("afs", afs, "forbidden_input_field"),
            (
                "planner_kind",
                planner_kind,
                "forbidden_planner_namespace",
            ),
        ):
            with self.subTest(smuggling=name):
                with self.assertRaises(
                    mapper.M1EvidenceToClaimIRMapperError
                ) as context:
                    mapper.map_validated_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(expected, context.exception.code)

    def test_cross_modality_merge_and_unknown_source_class_are_denied(self):
        system_log = load_fixture("system_log_public_projection")
        cti = load_fixture("cti_report_public_projection")
        merged = copy.deepcopy(system_log)
        merged["report"] = copy.deepcopy(cti["report"])
        unknown = copy.deepcopy(system_log)
        unknown["descriptor"]["source_class"] = "unknown_public_projection"

        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                [system_log, cti],
                repo_root=REPO_ROOT,
            )
        self.assertEqual("cross_modality_merge", context.exception.code)

        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                merged,
                repo_root=REPO_ROOT,
                authority=authority_for(merged),
            )
        self.assertEqual("cross_modality_merge", context.exception.code)

        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                unknown,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("unknown_source_class", context.exception.code)

    def test_optional_fields_can_be_absent_without_synthesized_claims(self):
        system_log = load_fixture("system_log_public_projection")
        system_log["event"].pop("severity")
        system_log["event"].pop("result_code")
        system_log.pop("principal")

        provenance = load_fixture("provenance_graph_public_projection")
        provenance["graph"].pop("nodes")
        provenance["graph"].pop("edges")
        provenance["graph"]["summary"] = {
            "node_count": 0,
            "edge_count": 0,
        }

        cti = load_fixture("cti_report_public_projection")
        for field in (
            "publisher_ref",
            "public_objects",
            "public_techniques",
            "public_relations",
        ):
            cti["report"].pop(field)

        for projection, expected_count in (
            (system_log, 4),
            (provenance, 6),
            (cti, 4),
        ):
            source_class = projection["descriptor"]["source_class"]
            package = mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
            with self.subTest(source_class=source_class):
                self.assertEqual(expected_count, len(package["claims"]))
                self.assertEqual([], package["manifest"]["field_path_set"])

    def test_missing_required_field_and_bad_basis_fail_closed(self):
        missing = load_fixture("system_log_public_projection")
        del missing["event"]["event_id"]
        bad_basis = load_fixture("provenance_graph_public_projection")
        bad_basis["source_metadata"]["modality_basis_code"] = (
            "ONE_OR_MORE_ELEMENTS_TRANSFORMED_OR_INFERRED"
        )
        for name, projection, expected in (
            ("missing", missing, "projection_shape"),
            ("basis", bad_basis, "modality_mapping"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(
                    mapper.M1EvidenceToClaimIRMapperError
                ) as context:
                    mapper.map_validated_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(expected, context.exception.code)

    def test_mapping_has_no_write_side_effect_and_protected_bytes_stay_exact(self):
        before = {path: file_sha256(path) for path in PROTECTED_PINS}
        for source_class in FIXTURES:
            projection = load_fixture(source_class)
            mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
        after = {path: file_sha256(path) for path in PROTECTED_PINS}
        self.assertEqual(before, after)
        self.assertEqual(PROTECTED_PINS, after)


if __name__ == "__main__":
    unittest.main()
