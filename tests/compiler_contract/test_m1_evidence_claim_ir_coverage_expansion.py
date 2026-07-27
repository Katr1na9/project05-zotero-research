import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_evidence_to_claim_ir_mapper as mapper  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    REPO_ROOT / "tests" / "compiler_contract" / "fixtures" / "m1_evidence_modality"
)
COVERAGE_ROOT = FIXTURE_ROOT / "coverage_v0.1"

ANCHOR_FIXTURES = {
    "system_log_public_projection": (
        FIXTURE_ROOT / "synthetic_system_log_projection_v0.1.json",
        9,
    ),
    "provenance_graph_public_projection": (
        FIXTURE_ROOT / "synthetic_provenance_graph_projection_v0.1.json",
        16,
    ),
    "cti_report_public_projection": (
        FIXTURE_ROOT / "synthetic_cti_report_projection_v0.1.json",
        11,
    ),
}
COVERAGE_FIXTURES = {
    "system_log_public_projection": (
        COVERAGE_ROOT / "synthetic_system_log_projection_coverage_v0.1.json",
        4,
    ),
    "provenance_graph_public_projection": (
        COVERAGE_ROOT / "synthetic_provenance_graph_projection_coverage_v0.1.json",
        48,
    ),
    "cti_report_public_projection": (
        COVERAGE_ROOT / "synthetic_cti_report_projection_coverage_v0.1.json",
        34,
    ),
}

SCHEMA_GREEN_ACCEPTANCE_PATH = (
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-claim-ir-evidence-claim-record-schema-green-owner-acceptance-v0.1-20260727.json"
)
GREEN_2_ACCEPTANCE_PATH = (
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-m1-evidence-to-claim-ir-mapping-green-2-owner-acceptance-v0.1-20260727.json"
)
READONLY_E2E_ACCEPTANCE_PATH = (
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-m1-evidence-claim-ir-readonly-e2e-owner-acceptance-v0.1-20260727.json"
)
PROTECTED_PINS = {
    SCHEMA_GREEN_ACCEPTANCE_PATH: (
        "60c31ffef0e4288f031b749ff89807904d13986025b56c769295ef80348ce148"
    ),
    GREEN_2_ACCEPTANCE_PATH: (
        "138715778a4a9ecc5cbaef913b56244b3b0c52e11e9f774a50bfc2e0b64a66f4"
    ),
    READONLY_E2E_ACCEPTANCE_PATH: (
        "dd264de3f09a385070098969a5a4809c846ffde246e869a7f4382a8fbff4615c"
    ),
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
    REPO_ROOT / mapper.MAPPER_IMPLEMENTATION_PATH: (
        "1dd8f407cc8fe840d90a7bf66c43e2cb11b5131877f2e46f92f2a1ffd372965b"
    ),
}

STRUCTURAL_ONLY_DECISION = (
    "CONSUMABLE_STRUCTURAL_ONLY_NOT_MINTED_NOT_ADMITTED_"
    "NO_INGESTION_AUTHORITY"
)
FORBIDDEN_FIXTURE_KEYS = {
    "path",
    "uri",
    "url",
    "endpoint",
    "raw_source",
    "raw_bytes",
    "raw_payload",
    "body",
    "excerpt",
    "full_text",
    "label",
    "labels",
    "verdict",
    "ground_truth",
    "oracle",
    "secret",
    "credential",
    "hidden_claim_ids",
    "claim_id",
    "certificate",
    "certified_stop",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
            "projection_content_sha256": mapper.canonical_json_sha256(projection),
        },
        "output_policy": copy.deepcopy(mapper._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(mapper._EXPECTED_STILL_BLOCKED),
    }


def all_object_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(str(key).lower().replace("-", "_") for key in value)
        for nested in value.values():
            keys.update(all_object_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(all_object_keys(nested))
    return keys


def evaluate_exact_consumer(
    package: dict,
    consumer: dict,
    legacy_external: dict,
    evidence_external: dict,
) -> str:
    version = package.get("schema_version")
    routes = {
        route["schema_version"]: route
        for route in consumer["exact_schema_dispatch"]["routes"]
    }
    route = routes.get(version)
    if route is None:
        return consumer["exact_schema_dispatch"]["unknown_schema_version"]
    schema = (
        legacy_external
        if version == "claim-ir-external-v0.1"
        else evidence_external
    )
    if list(Draft202012Validator(schema).iter_errors(package)):
        return "DENY_SCHEMA_VALIDATION"
    if version == "claim-ir-external-v0.1":
        return route["decision"]
    claims = package["claims"]
    manifest = package["manifest"]
    if manifest["claim_count"] != len(claims):
        return "DENY_MANIFEST_CLAIM_COUNT"
    if manifest["evidence_field_path_set"] != sorted(
        {claim["evidence_field"] for claim in claims}
    ):
        return "DENY_MANIFEST_EVIDENCE_FIELD_SET"
    if manifest["projection_sha256"] != package["projection_ref"]["sha256"]:
        return "DENY_PROJECTION_PIN"
    if any(
        claim["source_class"] != package["projection_ref"]["source_class"]
        for claim in claims
    ):
        return "DENY_SOURCE_CLASS_BINDING"
    identities = [
        (
            claim["claim_kind"],
            claim["evidence_field"],
            claim["occurrence_key"],
            claim["source_record_ref"],
        )
        for claim in claims
    ]
    if len(identities) != len(set(identities)):
        return "DENY_DUPLICATE_RECORD_IDENTITY"
    return route["decision"]


class M1EvidenceClaimIRCoverageExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.external = load_json(REPO_ROOT / mapper.EXTERNAL_EVIDENCE_SCHEMA_PATH)
        cls.kernel = load_json(REPO_ROOT / mapper.KERNEL_ADDITIVE_SCHEMA_PATH)
        cls.legacy_external = load_json(
            REPO_ROOT / mapper.LEGACY_EXTERNAL_SCHEMA_PATH
        )
        cls.legacy_kernel = load_json(REPO_ROOT / mapper.LEGACY_KERNEL_SCHEMA_PATH)
        cls.consumer = load_json(REPO_ROOT / mapper.CONSUMER_CONTRACT_PATH)
        registry = Registry()
        for schema in (cls.legacy_kernel, cls.external):
            registry = registry.with_resource(
                schema["$id"], Resource.from_contents(schema)
            )
        cls.kernel_validator = Draft202012Validator(
            cls.kernel,
            registry=registry,
        )

    def assert_full_readonly_chain(self, projection: dict, expected_count: int):
        package = mapper.map_validated_projection_to_claim_ir(
            projection,
            repo_root=REPO_ROOT,
            authority=authority_for(projection),
        )
        self.assertEqual(mapper.SCHEMA_VERSION, package["schema_version"])
        self.assertEqual(expected_count, len(package["claims"]))
        self.assertEqual(expected_count, package["manifest"]["claim_count"])
        self.assertEqual(
            [],
            list(Draft202012Validator(self.external).iter_errors(package)),
        )
        for claim in package["claims"]:
            self.assertEqual([], list(self.kernel_validator.iter_errors(claim)))
            self.assertEqual("public_evidence_declaration", claim["record_class"])
            self.assertIsNone(claim["claim_id"])
            self.assertEqual("not_minted", claim["claim_id_state"])
            self.assertEqual("not_admitted", claim["admission_state"])
            self.assertTrue(claim["claim_kind"].startswith("evidence."))
            self.assertTrue(claim["evidence_field"].startswith("evidence."))
            self.assertNotIn("source_field", claim)
            self.assertNotIn("afs_slot", claim)
            self.assertNotIn(claim["claim_kind"], mapper._PLANNER_CLAIM_KINDS)
        self.assertEqual(
            STRUCTURAL_ONLY_DECISION,
            evaluate_exact_consumer(
                package,
                self.consumer,
                self.legacy_external,
                self.external,
            ),
        )
        return package

    def test_authority_and_protected_pins_are_exact(self):
        mapper.verify_mapper_pins(REPO_ROOT)
        actual = {path: file_sha256(path) for path in PROTECTED_PINS}
        self.assertEqual(PROTECTED_PINS, actual)

    def test_original_e2e_anchor_fixtures_remain_9_16_11(self):
        for source_class, (path, expected_count) in ANCHOR_FIXTURES.items():
            with self.subTest(source_class=source_class):
                package = self.assert_full_readonly_chain(
                    load_json(path), expected_count
                )
                self.assertEqual(
                    source_class,
                    package["projection_ref"]["source_class"],
                )

    def test_expanded_fixtures_pass_full_readonly_chain(self):
        for source_class, (path, expected_count) in COVERAGE_FIXTURES.items():
            with self.subTest(source_class=source_class):
                package = self.assert_full_readonly_chain(
                    load_json(path), expected_count
                )
                self.assertEqual(
                    source_class,
                    package["projection_ref"]["source_class"],
                )

    def test_expanded_stress_points_are_explicit_and_deterministic(self):
        system_log = load_json(COVERAGE_FIXTURES["system_log_public_projection"][0])
        self.assertNotIn("principal", system_log)
        self.assertEqual(
            {"event_id", "event_time", "provider"},
            set(system_log["event"]),
        )
        self.assertEqual(
            "derived",
            system_log["source_metadata"]["epistemic_modality"],
        )

        provenance = load_json(
            COVERAGE_FIXTURES["provenance_graph_public_projection"][0]
        )
        self.assertEqual(5, len(provenance["graph"]["nodes"]))
        self.assertEqual(6, len(provenance["graph"]["edges"]))
        self.assertEqual(
            [1, 2, 1, 2],
            [
                entry["count"]
                for entry in provenance["graph"]["summary"][
                    "relationship_counts"
                ]
            ],
        )

        cti = load_json(COVERAGE_FIXTURES["cti_report_public_projection"][0])
        self.assertEqual(4, len(cti["report"]["public_objects"]))
        self.assertEqual(3, len(cti["report"]["public_techniques"]))
        self.assertEqual(6, len(cti["report"]["public_relations"]))
        self.assertEqual("reported", cti["source_metadata"]["epistemic_modality"])

        for source_class, (path, expected_count) in COVERAGE_FIXTURES.items():
            projection = load_json(path)
            first = self.assert_full_readonly_chain(projection, expected_count)
            second = self.assert_full_readonly_chain(
                copy.deepcopy(projection), expected_count
            )
            with self.subTest(source_class=source_class):
                self.assertEqual(first, second)
                self.assertEqual(
                    mapper.canonical_json_sha256(first),
                    mapper.canonical_json_sha256(second),
                )

    def test_new_fixtures_are_declaration_only_without_hidden_authority(self):
        for source_class, (path, _) in COVERAGE_FIXTURES.items():
            fixture = load_json(path)
            with self.subTest(source_class=source_class):
                self.assertEqual(set(), all_object_keys(fixture) & FORBIDDEN_FIXTURE_KEYS)
                self.assertEqual(
                    "project05_depth2_public",
                    fixture["descriptor"]["surface_id"],
                )

    def test_system_log_unknown_modality_abstains_without_partial_emission(self):
        projection = load_json(COVERAGE_FIXTURES["system_log_public_projection"][0])
        projection["source_metadata"].update(
            {
                "epistemic_modality": "unknown",
                "modality_basis_code": "UNRESOLVED_BASIS",
            }
        )
        before = copy.deepcopy(projection)
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
        self.assertEqual("abstain_unknown_modality", context.exception.code)
        self.assertEqual(before, projection)

    def test_provenance_missing_required_field_fails_closed(self):
        projection = load_json(
            COVERAGE_FIXTURES["provenance_graph_public_projection"][0]
        )
        del projection["graph"]["summary"]["edge_count"]
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
        self.assertEqual("projection_shape", context.exception.code)

    def test_cti_observed_and_derived_laundering_fail_closed(self):
        for modality in ("observed", "derived"):
            projection = load_json(
                COVERAGE_FIXTURES["cti_report_public_projection"][0]
            )
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

    def test_cross_modality_and_planner_namespace_smuggling_are_denied(self):
        system_log = load_json(
            COVERAGE_FIXTURES["system_log_public_projection"][0]
        )
        cti = load_json(COVERAGE_FIXTURES["cti_report_public_projection"][0])
        merged = copy.deepcopy(system_log)
        merged["report"] = copy.deepcopy(cti["report"])
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                merged,
                repo_root=REPO_ROOT,
                authority=authority_for(merged),
            )
        self.assertEqual("cross_modality_merge", context.exception.code)

        smuggled = copy.deepcopy(system_log)
        smuggled["event"]["claim_kind"] = "public_config"
        with self.assertRaises(mapper.M1EvidenceToClaimIRMapperError) as context:
            mapper.map_validated_projection_to_claim_ir(
                smuggled,
                repo_root=REPO_ROOT,
                authority=authority_for(smuggled),
            )
        self.assertEqual("forbidden_planner_namespace", context.exception.code)

    def test_draft_schema_version_remains_exact_dispatch_deny(self):
        projection = load_json(COVERAGE_FIXTURES["system_log_public_projection"][0])
        package = self.assert_full_readonly_chain(projection, 4)
        package["schema_version"] = "claim-ir-external-evidence-draft-v0.1"
        self.assertEqual(
            "DENY_UNKNOWN_SCHEMA_VERSION",
            evaluate_exact_consumer(
                package,
                self.consumer,
                self.legacy_external,
                self.external,
            ),
        )

    def test_readonly_execution_preserves_protected_bytes(self):
        before = {path: file_sha256(path) for path in PROTECTED_PINS}
        for path, expected_count in COVERAGE_FIXTURES.values():
            self.assert_full_readonly_chain(load_json(path), expected_count)
        after = {path: file_sha256(path) for path in PROTECTED_PINS}
        self.assertEqual(before, after)
        self.assertEqual(PROTECTED_PINS, after)


if __name__ == "__main__":
    unittest.main()
