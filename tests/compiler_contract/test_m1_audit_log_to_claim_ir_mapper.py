import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_audit_log_projection_adapter as adapter  # noqa: E402
from compiler.llm import m1_audit_log_to_claim_ir_mapper as mapper  # noqa: E402
from compiler.llm import m1_evidence_sufficiency_evaluator as a2  # noqa: E402


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fixture() -> dict:
    return load_json(REPO_ROOT / adapter.RED_FIXTURE_PATH)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def adapter_authority_for(projection: dict) -> dict:
    return {
        "status": adapter.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(adapter._EXPECTED_AUTHORITY_SCOPE),
        "pinned_hashes": {
            "a3_red_acceptance_sha256": adapter.A3_RED_ACCEPTANCE_SHA256,
            "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "mapping_contract_sha256": adapter.MAPPING_CONTRACT_SHA256,
            "external_evidence_v0_2_sha256": (
                adapter.EXTERNAL_EVIDENCE_V0_2_SHA256
            ),
            "kernel_additive_v0_2_sha256": (
                adapter.KERNEL_ADDITIVE_V0_2_SHA256
            ),
            "consumer_v0_3_sha256": adapter.CONSUMER_V0_3_SHA256,
            "adapter_implementation_sha256": file_sha256(
                REPO_ROOT / adapter.ADAPTER_IMPLEMENTATION_PATH
            ),
        },
        "pinned_input": {
            "source_class": adapter.SOURCE_CLASS,
            "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "projection_content_sha256": adapter.canonical_json_sha256(
                projection
            ),
        },
        "output_policy": copy.deepcopy(adapter._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(adapter._EXPECTED_STILL_BLOCKED),
    }


def mapper_authority_for(projection: dict) -> dict:
    return {
        "status": mapper.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(mapper._EXPECTED_SCOPE),
        "pinned_hashes": {
            "a3_red_acceptance_sha256": adapter.A3_RED_ACCEPTANCE_SHA256,
            "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "mapping_contract_sha256": adapter.MAPPING_CONTRACT_SHA256,
            "external_evidence_v0_2_sha256": (
                mapper.EXTERNAL_EVIDENCE_V0_2_SHA256
            ),
            "kernel_additive_v0_2_sha256": (
                mapper.KERNEL_ADDITIVE_V0_2_SHA256
            ),
            "consumer_v0_3_sha256": mapper.CONSUMER_V0_3_SHA256,
            "adapter_implementation_sha256": (
                mapper.ADAPTER_IMPLEMENTATION_SHA256
            ),
            "mapper_implementation_sha256": file_sha256(
                REPO_ROOT / mapper.MAPPER_IMPLEMENTATION_PATH
            ),
        },
        "pinned_input": {
            "source_class": mapper.SOURCE_CLASS,
            "projection_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "projection_content_sha256": mapper.canonical_json_sha256(
                projection
            ),
        },
        "output_policy": copy.deepcopy(mapper._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(mapper._EXPECTED_STILL_BLOCKED),
    }


def validate_external_v0_2(package: dict) -> list:
    v0_1 = load_json(REPO_ROOT / mapper.EXTERNAL_EVIDENCE_V0_1_PATH)
    v0_2 = load_json(REPO_ROOT / mapper.EXTERNAL_EVIDENCE_V0_2_PATH)
    registry = Registry().with_resource(
        v0_1["$id"],
        Resource.from_contents(v0_1),
    )
    return list(Draft202012Validator(v0_2, registry=registry).iter_errors(package))


def map_fixture(projection: dict | None = None) -> dict:
    projection = projection or load_fixture()
    validated = adapter.adapt_audit_log_public_projection(
        projection,
        repo_root=REPO_ROOT,
        authority=adapter_authority_for(projection),
    )
    return mapper.map_validated_audit_log_projection_to_claim_ir(
        validated,
        repo_root=REPO_ROOT,
        authority=mapper_authority_for(validated),
    )


class M1AuditLogToClaimIRMapperTests(unittest.TestCase):
    def test_reported_adapter_to_mapper_v0_2_kernel_and_consumer_pass(self):
        package = map_fixture()
        self.assertEqual([], validate_external_v0_2(package))
        self.assertEqual(mapper.SCHEMA_VERSION, package["schema_version"])
        self.assertEqual(10, package["manifest"]["claim_count"])
        self.assertEqual(10, len(package["claims"]))
        self.assertEqual("not_minted", package["claim_id_state"])
        self.assertEqual("not_admitted", package["admission_state"])
        self.assertEqual("pending_kernel_schema", package["kernel_state"])
        for claim in package["claims"]:
            self.assertEqual(
                "public_evidence_declaration",
                claim["record_class"],
            )
            self.assertIsNone(claim["claim_id"])
            self.assertEqual("not_minted", claim["claim_id_state"])
            self.assertEqual("not_admitted", claim["admission_state"])
            self.assertTrue(
                claim["claim_kind"].startswith("evidence.audit_log.")
            )
            self.assertTrue(
                claim["evidence_field"].startswith("evidence.audit_log.")
            )
            self.assertNotIn("source_field", claim)
            self.assertNotIn("afs_slot", claim)

        consumer = load_json(REPO_ROOT / mapper.CONSUMER_V0_3_PATH)
        routes = consumer["exact_schema_dispatch"]["routes"]
        route = [
            item
            for item in routes
            if item["schema_version"] == mapper.SCHEMA_VERSION
        ]
        self.assertEqual(1, len(route))
        self.assertEqual(mapper.SOURCE_CLASS, route[0]["new_source_class"])
        self.assertIn("STRUCTURAL_ONLY", route[0]["decision"])

    def test_same_projection_produces_same_package_and_exact_ten_field_order(self):
        first = map_fixture()
        second = map_fixture(copy.deepcopy(load_fixture()))
        self.assertEqual(first, second)
        self.assertEqual(
            mapper.canonical_json_sha256(first),
            mapper.canonical_json_sha256(second),
        )
        mapping_contract = load_json(REPO_ROOT / adapter.MAPPING_CONTRACT_PATH)
        self.assertEqual(
            [
                item["evidence_field"]
                for item in mapping_contract["field_to_claim_mapping"]
            ],
            [claim["evidence_field"] for claim in first["claims"]],
        )

    def test_optional_refs_absent_emit_seven_core_claims_only(self):
        projection = load_fixture()
        for field in (
            "public_actor_ref",
            "public_change_ref",
            "public_request_ref",
        ):
            projection["audit_entry"].pop(field)
        package = map_fixture(projection)
        self.assertEqual(7, len(package["claims"]))
        self.assertEqual(7, package["manifest"]["claim_count"])
        kinds = {claim["claim_kind"] for claim in package["claims"]}
        self.assertNotIn("evidence.audit_log.actor_reference", kinds)
        self.assertNotIn("evidence.audit_log.change_reference", kinds)
        self.assertNotIn("evidence.audit_log.request_reference", kinds)

    def test_missing_or_elevated_mapper_authority_fails_closed(self):
        projection = load_fixture()
        with self.assertRaises(
            mapper.M1AuditLogToClaimIRMapperError
        ) as context:
            mapper.map_validated_audit_log_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("MISSING_TEST_ONLY_AUTHORITY", context.exception.code)

        authority = mapper_authority_for(projection)
        authority["output_policy"]["mint"] = True
        with self.assertRaises(
            mapper.M1AuditLogToClaimIRMapperError
        ) as context:
            mapper.map_validated_audit_log_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority,
            )
        self.assertEqual(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            context.exception.code,
        )

    def test_unknown_abstains_and_observed_derived_are_denied_without_package(self):
        unknown = load_fixture()
        unknown["source_metadata"].update(
            {
                "epistemic_modality": "unknown",
                "modality_basis_code": "UNRESOLVED_AUDIT_BASIS",
            }
        )
        with self.assertRaises(
            mapper.M1AuditLogToClaimIRMapperError
        ) as context:
            mapper.map_validated_audit_log_projection_to_claim_ir(
                unknown,
                repo_root=REPO_ROOT,
                authority=mapper_authority_for(unknown),
            )
        self.assertEqual("ABSTAIN_NO_PACKAGE", context.exception.code)

        for modality in ("observed", "derived"):
            projection = load_fixture()
            projection["source_metadata"]["epistemic_modality"] = modality
            with self.subTest(modality=modality):
                with self.assertRaises(
                    mapper.M1AuditLogToClaimIRMapperError
                ) as context:
                    mapper.map_validated_audit_log_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=mapper_authority_for(projection),
                    )
                self.assertEqual(
                    "DENY_MODALITY_LAUNDERING",
                    context.exception.code,
                )

    def test_namespace_smuggling_and_cross_modality_merge_are_denied(self):
        planner = load_fixture()
        planner["audit_entry"]["source_field"] = "config.case_id"
        alias = load_fixture()
        alias["audit_entry"]["public_change_ref"] = (
            "evidence.system_log.event.event_id"
        )
        merged = load_fixture()
        merged["event"] = {"event_id": "smuggled"}
        for name, projection, expected in (
            ("planner", planner, "DENY_PLANNER_NAMESPACE"),
            ("alias", alias, "DENY_NAMESPACE_ALIAS"),
            ("merged", merged, "DENY_CROSS_MODALITY_MERGE"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(
                    mapper.M1AuditLogToClaimIRMapperError
                ) as context:
                    mapper.map_validated_audit_log_projection_to_claim_ir(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=mapper_authority_for(projection),
                    )
                self.assertEqual(expected, context.exception.code)

        with self.assertRaises(
            mapper.M1AuditLogToClaimIRMapperError
        ) as context:
            mapper.map_validated_audit_log_projection_to_claim_ir(
                [load_fixture(), load_fixture()],
                repo_root=REPO_ROOT,
            )
        self.assertEqual("DENY_CROSS_MODALITY_MERGE", context.exception.code)

    def test_same_audit_claims_against_old_v0_1_expected_fail_closed(self):
        package = map_fixture()
        legacy_candidate = copy.deepcopy(package)
        legacy_candidate["schema_version"] = (
            "claim-ir-external-evidence-v0.1"
        )
        old_schema = load_json(
            REPO_ROOT / mapper.EXTERNAL_EVIDENCE_V0_1_PATH
        )
        errors = list(
            Draft202012Validator(old_schema).iter_errors(legacy_candidate)
        )
        self.assertTrue(errors)

    def test_a2_catalog_remains_six_and_audit_binding_is_unknown(self):
        catalog = a2.package_binding_catalog(REPO_ROOT)
        self.assertEqual(6, len(catalog))
        self.assertNotIn(
            mapper.SOURCE_CLASS,
            {item["source_class"] for item in catalog},
        )
        package = map_fixture()
        audit_binding = {
            "binding_id": "audit_log_not_authorized_in_a2_v0_1",
            "package_role": "optional_a3_not_in_a2_catalog",
            "source_class": mapper.SOURCE_CLASS,
            "epistemic_modality": "reported",
            "package_sha256": mapper.canonical_json_sha256(package),
            "claim_count": len(package["claims"]),
            "evidence_field_path_set_sha256": mapper.canonical_json_sha256(
                package["manifest"]["evidence_field_path_set"]
            ),
        }
        with self.assertRaises(
            a2.M1EvidenceSufficiencyEvaluatorError
        ) as context:
            a2.evaluate_evidence_sufficiency_for_readonly_review(
                [audit_binding],
                repo_root=REPO_ROOT,
            )
        self.assertEqual("unknown_binding", context.exception.code)

    def test_mapping_preserves_every_red_and_protected_pin_byte(self):
        review = load_json(REPO_ROOT / adapter.RED_REVIEW_PACKET_PATH)
        expected = {
            item["path"]: item["sha256"]
            for item in review["mandatory_pin_table"]
        }
        expected.update(
            {
                adapter.A3_RED_ACCEPTANCE_PATH: (
                    adapter.A3_RED_ACCEPTANCE_SHA256
                ),
                adapter.RED_DESIGN_PATH: adapter.RED_DESIGN_SHA256,
                adapter.PROJECTION_CONTRACT_PATH: (
                    adapter.PROJECTION_CONTRACT_SHA256
                ),
                adapter.MAPPING_CONTRACT_PATH: (
                    adapter.MAPPING_CONTRACT_SHA256
                ),
                adapter.RED_FIXTURE_PATH: adapter.RED_FIXTURE_SHA256,
                adapter.RED_REVIEW_PACKET_PATH: (
                    adapter.RED_REVIEW_PACKET_SHA256
                ),
            }
        )
        before = {
            path: file_sha256(REPO_ROOT / path) for path in expected
        }
        map_fixture()
        after = {
            path: file_sha256(REPO_ROOT / path) for path in expected
        }
        self.assertEqual(expected, before)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
