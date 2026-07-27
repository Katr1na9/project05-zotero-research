import copy
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource


REPO_ROOT = Path(__file__).resolve().parents[2]

EXTERNAL_EVIDENCE_PATH = (
    REPO_ROOT / "schemas" / "claim-ir-external-envelope-evidence-v0.1.schema.json"
)
KERNEL_ADDITIVE_PATH = (
    REPO_ROOT / "schemas" / "claim-ir-kernel-evidence-additive-v0.1.schema.json"
)
CONSUMER_PATH = (
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.2-20260727.json"
)
LEGACY_EXTERNAL_PATH = (
    REPO_ROOT / "schemas" / "claim-ir-external-envelope.schema.json"
)
LEGACY_KERNEL_PATH = REPO_ROOT / "schemas" / "claim-ir-kernel.schema.json"
LEGACY_CONSUMER_PATH = (
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-shared-claim-ir-consumer-contract-effective-v0.1-20260725.json"
)
PLANNER_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "m1_claim_ir_valid_fixture"
    / "synthetic_unminted_claim_ir_v0.1.json"
)

EXTERNAL_EVIDENCE_SHA256 = (
    "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c"
)
KERNEL_ADDITIVE_SHA256 = (
    "d8cccbad36c6cca068fdc9d17ecbd8d0db2e08271f986127d0c0236353a79ce5"
)
CONSUMER_SHA256 = (
    "fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504"
)

LEGACY_PINS = {
    LEGACY_EXTERNAL_PATH: (
        "5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e"
    ),
    LEGACY_KERNEL_PATH: (
        "7c6fa2db0b75d69340be5a8843ba0c373e2d5b25b0d37cf8f1d1c416a787865d"
    ),
    LEGACY_CONSUMER_PATH: (
        "a2a176fdeb2b93205a7f5e11c7c096236e2dc582d1c31f8f4a1534866c008d63"
    ),
}

DRAFT_PINS = {
    REPO_ROOT
    / "schemas"
    / "drafts"
    / "claim-ir-external-envelope-evidence-claim-record-v0.1.draft.schema.json": (
        "0a788c00735078899c87b09d6f64c7ab6a95a6f3eae0c1fa39b7753919f4a20d"
    ),
    REPO_ROOT
    / "schemas"
    / "drafts"
    / "claim-ir-kernel-evidence-claim-record-v0.1.draft.schema.json": (
        "89f9b30cce86d3cf1a0792a793c3d5a31575986e0b9636299be9d83e3c831c64"
    ),
    REPO_ROOT
    / "docs"
    / "kernel"
    / "kernel-v0.8-shared-claim-ir-consumer-contract-evidence-extension-draft-v0.1-20260727.json": (
        "e8fb4d3d5ce19539235b4d9709979c4150825ae018c61e785fb9d2b8be30f811"
    ),
}

PROTECTED_ADAPTER_PINS = {
    REPO_ROOT / "src" / "compiler" / "llm" / "m1_system_log_projection_adapter.py": (
        "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116"
    ),
    REPO_ROOT
    / "src"
    / "compiler"
    / "llm"
    / "m1_provenance_graph_projection_adapter.py": (
        "9068315019a2980bb43b81d9641537c5a7c69ca63f14c4b9e876a653f8ffeae5"
    ),
    REPO_ROOT / "src" / "compiler" / "llm" / "m1_cti_report_projection_adapter.py": (
        "cc0e04dd15372ecc1e0b5b68777458f07a361cb77ec7ce2c318b1ef42a07be3e"
    ),
}

MAPPING_CONTRACTS = (
    (
        "system_log",
        REPO_ROOT
        / "docs"
        / "llm-editor"
        / "llm-editor-v0.8-l2-m1-system-log-to-claim-ir-mapping-contract-v0.1-20260726.json",
        0,
    ),
    (
        "provenance_graph",
        REPO_ROOT
        / "docs"
        / "llm-editor"
        / "llm-editor-v0.8-l2-m1-provenance-graph-to-claim-ir-mapping-contract-v0.1-20260726.json",
        1,
    ),
    (
        "cti_report",
        REPO_ROOT
        / "docs"
        / "llm-editor"
        / "llm-editor-v0.8-l2-m1-cti-report-to-claim-ir-mapping-contract-v0.1-20260726.json",
        2,
    ),
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evidence_packages(external_schema: dict) -> dict[str, dict]:
    packages = {}
    projection_branches = external_schema["$defs"]["evidence_projection_ref"][
        "oneOf"
    ]
    for name, contract_path, branch_index in MAPPING_CONTRACTS:
        contract = load_json(contract_path)
        claims = copy.deepcopy(contract["design_level_example_claims"])
        projection_ref = {
            field: rule["const"]
            for field, rule in projection_branches[branch_index][
                "properties"
            ].items()
        }
        packages[name] = {
            "schema_version": "claim-ir-external-evidence-v0.1",
            "package_id": f"pkg_{name}_schema_green_001",
            "surface_id": "project05_depth2_public",
            "kernel_state": "pending_kernel_schema",
            "claim_id_state": "not_minted",
            "admission_state": "not_admitted",
            "projection_ref": projection_ref,
            "claims": claims,
            "manifest": {
                "claim_count": len(claims),
                "field_path_set": [],
                "evidence_field_path_set": sorted(
                    {claim["evidence_field"] for claim in claims}
                ),
                "projection_sha256": projection_ref["sha256"],
                "content_hash": canonical_sha256(claims),
            },
        }
    return packages


def evaluate_exact_consumer(
    package: dict,
    consumer: dict,
    legacy_schema: dict,
    evidence_schema: dict,
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
        legacy_schema
        if version == "claim-ir-external-v0.1"
        else evidence_schema
    )
    if list(Draft202012Validator(schema).iter_errors(package)):
        return "DENY_SCHEMA_VALIDATION"
    if version == "claim-ir-external-v0.1":
        return route["decision"]

    claims = package["claims"]
    manifest = package["manifest"]
    if manifest["claim_count"] != len(claims):
        return "DENY_MANIFEST_CLAIM_COUNT"
    expected_fields = sorted({claim["evidence_field"] for claim in claims})
    if manifest["evidence_field_path_set"] != expected_fields:
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


class ClaimIREvidenceClaimRecordSchemaGreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.external = load_json(EXTERNAL_EVIDENCE_PATH)
        cls.kernel_additive = load_json(KERNEL_ADDITIVE_PATH)
        cls.consumer = load_json(CONSUMER_PATH)
        cls.legacy_external = load_json(LEGACY_EXTERNAL_PATH)
        cls.legacy_kernel = load_json(LEGACY_KERNEL_PATH)
        cls.packages = evidence_packages(cls.external)

    def test_new_candidate_identities_are_valid_and_not_red_draft_bytes(self):
        Draft202012Validator.check_schema(self.external)
        Draft202012Validator.check_schema(self.kernel_additive)
        self.assertEqual(EXTERNAL_EVIDENCE_SHA256, file_sha256(EXTERNAL_EVIDENCE_PATH))
        self.assertEqual(KERNEL_ADDITIVE_SHA256, file_sha256(KERNEL_ADDITIVE_PATH))
        self.assertEqual(CONSUMER_SHA256, file_sha256(CONSUMER_PATH))
        for path, expected_sha in DRAFT_PINS.items():
            with self.subTest(path=path.name):
                self.assertEqual(expected_sha, file_sha256(path))
        self.assertNotIn(EXTERNAL_EVIDENCE_SHA256, DRAFT_PINS.values())
        self.assertNotIn(KERNEL_ADDITIVE_SHA256, DRAFT_PINS.values())
        self.assertNotIn(CONSUMER_SHA256, DRAFT_PINS.values())
        self.assertNotIn("draft", self.external["$id"])
        self.assertNotIn("draft", self.kernel_additive["$id"])

    def test_legacy_planner_package_still_uses_exact_legacy_route(self):
        fixture = load_json(PLANNER_FIXTURE_PATH)
        self.assertEqual(
            [],
            list(Draft202012Validator(self.legacy_external).iter_errors(fixture)),
        )
        first = evaluate_exact_consumer(
            fixture, self.consumer, self.legacy_external, self.external
        )
        second = evaluate_exact_consumer(
            copy.deepcopy(fixture),
            self.consumer,
            self.legacy_external,
            self.external,
        )
        self.assertEqual("USE_EXISTING_EFFECTIVE_CONSUMER_UNCHANGED", first)
        self.assertEqual(first, second)

    def test_three_evidence_modalities_pass_new_external_identity(self):
        validator = Draft202012Validator(self.external)
        for name, package in self.packages.items():
            with self.subTest(source=name):
                self.assertEqual([], list(validator.iter_errors(package)))
                self.assertEqual("not_minted", package["claim_id_state"])
                self.assertEqual("not_admitted", package["admission_state"])
                self.assertTrue(
                    all(claim["claim_id"] is None for claim in package["claims"])
                )

    def test_evidence_packages_fail_unchanged_legacy_external_schema(self):
        validator = Draft202012Validator(self.legacy_external)
        for name, package in self.packages.items():
            with self.subTest(source=name):
                self.assertNotEqual([], list(validator.iter_errors(package)))

    def test_additive_kernel_oneof_accepts_every_evidence_record(self):
        registry = Registry()
        for schema in (self.legacy_kernel, self.external):
            registry = registry.with_resource(
                schema["$id"], Resource.from_contents(schema)
            )
        validator = Draft202012Validator(
            self.kernel_additive,
            registry=registry,
        )
        for name, package in self.packages.items():
            for index, claim in enumerate(package["claims"]):
                with self.subTest(source=name, claim=index):
                    self.assertEqual([], list(validator.iter_errors(claim)))

    def test_cti_observed_and_derived_are_denied(self):
        validator = Draft202012Validator(self.external)
        for modality in ("observed", "derived"):
            package = copy.deepcopy(self.packages["cti_report"])
            package["claims"][0]["epistemic_modality"] = modality
            with self.subTest(modality=modality):
                self.assertNotEqual([], list(validator.iter_errors(package)))

    def test_source_field_afs_and_planner_claim_kind_leaks_are_denied(self):
        mutations = []
        source_field = copy.deepcopy(self.packages["system_log"])
        source_field["claims"][0]["source_field"] = "config.case_id"
        mutations.append(("source_field", source_field))
        afs = copy.deepcopy(self.packages["system_log"])
        afs["claims"][0]["afs_slot"] = "AFS.case_id"
        mutations.append(("afs_slot", afs))
        planner_kind = copy.deepcopy(self.packages["system_log"])
        planner_kind["claims"][0]["claim_kind"] = "public_config"
        mutations.append(("planner_claim_kind", planner_kind))

        validator = Draft202012Validator(self.external)
        for name, package in mutations:
            with self.subTest(leak=name):
                self.assertNotEqual([], list(validator.iter_errors(package)))

    def test_unknown_missing_draft_or_masquerading_schema_version_is_denied(self):
        candidates = []
        unknown = copy.deepcopy(self.packages["system_log"])
        unknown["schema_version"] = "claim-ir-external-evidence-v9.9"
        candidates.append(("unknown", unknown, "DENY_UNKNOWN_SCHEMA_VERSION"))
        missing = copy.deepcopy(self.packages["system_log"])
        del missing["schema_version"]
        candidates.append(("missing", missing, "DENY_UNKNOWN_SCHEMA_VERSION"))
        draft = copy.deepcopy(self.packages["system_log"])
        draft["schema_version"] = "claim-ir-external-evidence-draft-v0.1"
        candidates.append(("draft", draft, "DENY_UNKNOWN_SCHEMA_VERSION"))
        masquerading = copy.deepcopy(self.packages["system_log"])
        masquerading["schema_version"] = "claim-ir-external-v0.1"
        candidates.append(("legacy_masquerade", masquerading, "DENY_SCHEMA_VALIDATION"))

        for name, package, expected in candidates:
            with self.subTest(version_case=name):
                self.assertEqual(
                    expected,
                    evaluate_exact_consumer(
                        package,
                        self.consumer,
                        self.legacy_external,
                        self.external,
                    ),
                )

    def test_structural_only_consumer_decision_is_deterministic(self):
        expected = (
            "CONSUMABLE_STRUCTURAL_ONLY_NOT_MINTED_NOT_ADMITTED_"
            "NO_INGESTION_AUTHORITY"
        )
        for name, package in self.packages.items():
            first = evaluate_exact_consumer(
                package, self.consumer, self.legacy_external, self.external
            )
            second = evaluate_exact_consumer(
                copy.deepcopy(package),
                self.consumer,
                self.legacy_external,
                self.external,
            )
            with self.subTest(source=name):
                self.assertEqual(expected, first)
                self.assertEqual(first, second)

    def test_consumer_checks_manifest_and_source_binding_fail_closed(self):
        cases = []
        count = copy.deepcopy(self.packages["system_log"])
        count["manifest"]["claim_count"] += 1
        cases.append(("claim_count", count, "DENY_MANIFEST_CLAIM_COUNT"))
        fields = copy.deepcopy(self.packages["system_log"])
        fields["manifest"]["evidence_field_path_set"] = ["evidence.system_log.x"]
        cases.append(
            ("evidence_field_set", fields, "DENY_MANIFEST_EVIDENCE_FIELD_SET")
        )
        projection = copy.deepcopy(self.packages["system_log"])
        projection["manifest"]["projection_sha256"] = "0" * 64
        cases.append(("projection", projection, "DENY_PROJECTION_PIN"))
        source_class = copy.deepcopy(self.packages["system_log"])
        source_class["claims"][0]["source_class"] = (
            "provenance_graph_public_projection"
        )
        cases.append(("source_class", source_class, "DENY_SCHEMA_VALIDATION"))
        duplicate = copy.deepcopy(self.packages["system_log"])
        duplicate["claims"].append(copy.deepcopy(duplicate["claims"][0]))
        duplicate["manifest"]["claim_count"] += 1
        cases.append(
            ("duplicate_identity", duplicate, "DENY_DUPLICATE_RECORD_IDENTITY")
        )

        for name, package, expected in cases:
            with self.subTest(invariant=name):
                self.assertEqual(
                    expected,
                    evaluate_exact_consumer(
                        package,
                        self.consumer,
                        self.legacy_external,
                        self.external,
                    ),
                )

    def test_consumer_has_two_exact_routes_and_no_authority_elevation(self):
        dispatch = self.consumer["exact_schema_dispatch"]
        self.assertTrue(dispatch["exact_match_required"])
        self.assertFalse(dispatch["wildcard_or_fallback"])
        self.assertFalse(dispatch["implicit_default"])
        self.assertEqual(
            [
                "claim-ir-external-v0.1",
                "claim-ir-external-evidence-v0.1",
            ],
            [route["schema_version"] for route in dispatch["routes"]],
        )
        self.assertFalse(dispatch["schema_validation_alone_authorizes_ingestion"])
        boundary = self.consumer["consumption_boundary"]
        for field in (
            "claim_id_mint",
            "admission",
            "kernel_state_transition",
            "kernel_write",
            "e_case_write",
            "certificate_generation",
            "certified_stop",
        ):
            with self.subTest(authority=field):
                self.assertFalse(boundary[field])

    def test_legacy_and_adapter_protected_bytes_remain_exact(self):
        for path, expected_sha in {
            **LEGACY_PINS,
            **PROTECTED_ADAPTER_PINS,
        }.items():
            with self.subTest(path=path.name):
                self.assertEqual(expected_sha, file_sha256(path))
        source_fields = self.legacy_external["$defs"]["source_field"]["enum"]
        claim_kinds = self.legacy_external["$defs"]["claim_kind"]["enum"]
        self.assertEqual(38, len(source_fields))
        self.assertEqual(4, len(claim_kinds))


if __name__ == "__main__":
    unittest.main()
