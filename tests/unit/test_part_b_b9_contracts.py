from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

from jsonschema import Draft202012Validator
import yaml

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"

UPSTREAM_COMMIT = "be33ef8906f5c6ca0891d21da11573b9510e941e"

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-freeze-and-claims-policy.schema.json",
    "freeze_record": SCHEMA_DIR / "part-b-freeze-record.schema.json",
    "claim_boundary": SCHEMA_DIR / "part-b-claim-boundary.schema.json",
    "audit": SCHEMA_DIR / "part-b-freeze-audit.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b9-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-freeze-and-claims-policy-v0.8.yaml",
    "freeze_record": CONFIG_DIR / "part-b-freeze-record-example-v0.8.yaml",
    "claim_boundary": CONFIG_DIR / "part-b-claim-boundary-example-v0.8.yaml",
    "audit": CONFIG_DIR / "part-b-freeze-audit-example-v0.8.yaml",
    "manifest": CONFIG_DIR / "part-b-b9-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b9-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b9-freeze-and-claims-v0.8.md",
    ROOT / "contracts" / "part-b-b9-audit-and-claim-boundary-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b9-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b9-implementation-plan-v0.8-20260724.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)
TEST_PATHS = (
    ROOT / "tests" / "unit" / "test_part_b_b9_contracts.py",
    ROOT / "tests" / "unit" / "test_part_b_b9_freeze_and_claims.py",
)
B9_NON_TEST_PATHS = (
    *SCHEMA_PATHS.values(),
    *CONFIG_PATHS.values(),
    *DOCUMENT_PATHS,
)
B9_ALLOWLIST_PATHS = (*B9_NON_TEST_PATHS, *TEST_PATHS)

# This is an intentionally explicit, reviewer-visible freeze list. It is the
# 38-item union of hashes recorded by the B0-B8 manifests, plus the B8 holdout
# envelope. No B9 artifact may dynamically manufacture or extend this list.
FROZEN_UPSTREAM = (
    {
        "slice_id": "B0",
        "artifact_id": "gamma-kernel-v0.8",
        "path": "configs/gamma-kernel-v0.8.yaml",
        "hash": (
            "sha256:"
            "0bad34b682c0b4f79b2423a241880932d655b886ad539d90d53e37917cbf41d2"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "action-catalog-kernel-v0.8",
        "path": "configs/action-catalog-kernel-v0.8.yaml",
        "hash": (
            "sha256:"
            "0cd3ee1331aef81ca955e973ae9bc30c364acd2a2f6c34247438f4dd94add8eb"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "admission-policy-kernel-v0.8",
        "path": "configs/admission-policy-kernel-v0.8.yaml",
        "hash": (
            "sha256:"
            "8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "admission-policy-approval-kernel-v0.8",
        "path": "configs/admission-policy-approval-kernel-v0.8.yaml",
        "hash": (
            "sha256:"
            "2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "part-b-observation-contract-v0.8",
        "path": "configs/part-b-observation-contract-v0.8.yaml",
        "hash": (
            "sha256:"
            "f5db6035452236fb6e316b8e9a5ada7e2a7cbce07c0eedc3b3e7c890bc4fd7d9"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "part-b-cost-contract-v0.8",
        "path": "configs/part-b-cost-contract-v0.8.yaml",
        "hash": (
            "sha256:"
            "b6d36c40f7b52c12733dbe75cbcba6058e952f23d67e2155bd73196f6bcfaf53"
        ),
    },
    {
        "slice_id": "B0",
        "artifact_id": "part-b-b0-manifest-v0.8",
        "path": "configs/part-b-b0-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "22601f9876ecc8b348a9a2d836b3b842576de4f1442124cb2e82807e30096b4f"
        ),
    },
    {
        "slice_id": "B1",
        "artifact_id": "part-b-federation-contract-v0.8",
        "path": "configs/part-b-federation-contract-v0.8.yaml",
        "hash": (
            "sha256:"
            "6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d"
        ),
    },
    {
        "slice_id": "B1",
        "artifact_id": "part-b-adapter-conformance-v0.8",
        "path": "configs/part-b-adapter-conformance-v0.8.yaml",
        "hash": (
            "sha256:"
            "f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a"
        ),
    },
    {
        "slice_id": "B1",
        "artifact_id": "part-b-b1-manifest-v0.8",
        "path": "configs/part-b-b1-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e"
        ),
    },
    {
        "slice_id": "B2",
        "artifact_id": "part-b-stochastic-observation-catalog-v0.8",
        "path": "configs/part-b-stochastic-observation-catalog-v0.8.yaml",
        "hash": (
            "sha256:"
            "200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5"
        ),
    },
    {
        "slice_id": "B2",
        "artifact_id": "part-b-stochastic-tv-policy-v0.8",
        "path": "configs/part-b-stochastic-tv-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8"
        ),
    },
    {
        "slice_id": "B2",
        "artifact_id": "part-b-b2-world-pair-delta-decision-v0.8",
        "path": "configs/part-b-b2-world-pair-delta-decision-v0.8.yaml",
        "hash": (
            "sha256:"
            "1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919"
        ),
    },
    {
        "slice_id": "B2",
        "artifact_id": "part-b-b2-manifest-v0.8",
        "path": "configs/part-b-b2-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "6d6f67d9722eff1b2e1aa75277b0c390dc485751067728a347ae89c77f83faed"
        ),
    },
    {
        "slice_id": "B3",
        "artifact_id": "part-b-cost-instrumentation-policy-v0.8",
        "path": "configs/part-b-cost-instrumentation-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278"
        ),
    },
    {
        "slice_id": "B3",
        "artifact_id": "part-b-b3-manifest-v0.8",
        "path": "configs/part-b-b3-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "9403004d25c1428beeb85f04c6d65eeb02759d6881ede67390a2d97f2b9c82fb"
        ),
    },
    {
        "slice_id": "B4",
        "artifact_id": "part-b-baseline-preregistration-v0.8",
        "path": "configs/part-b-baseline-preregistration-v0.8.yaml",
        "hash": (
            "sha256:"
            "c51ab64588441855a7ff8413e32695e4b168d6d2a2089674f2cdcd691959906d"
        ),
    },
    {
        "slice_id": "B4",
        "artifact_id": "part-b-baseline-isolation-policy-v0.8",
        "path": "configs/part-b-baseline-isolation-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f"
        ),
    },
    {
        "slice_id": "B4",
        "artifact_id": "part-b-b4-manifest-v0.8",
        "path": "configs/part-b-b4-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "2649b2a9067858d5fe2fa4c2f9d6386408384448910c97ee4eb89f1817893afc"
        ),
    },
    {
        "slice_id": "B5",
        "artifact_id": "part-b-planner-public-state-example-v0.8",
        "path": "configs/part-b-planner-public-state-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "42efd17661a1335f3c84c2c4efbea4de8107087d099dc987a902d20ded50deae"
        ),
    },
    {
        "slice_id": "B5",
        "artifact_id": "part-b-planner-decision-example-v0.8",
        "path": "configs/part-b-planner-decision-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "144cd24c0d6e3906ee31d25cdcc629f20901648d58204ee030f397daca23da6d"
        ),
    },
    {
        "slice_id": "B5",
        "artifact_id": "part-b-planner-interface-policy-v0.8",
        "path": "configs/part-b-planner-interface-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343"
        ),
    },
    {
        "slice_id": "B5",
        "artifact_id": "part-b-bounded-evaluation-v0.8",
        "path": "configs/part-b-bounded-evaluation-v0.8.yaml",
        "hash": (
            "sha256:"
            "9c1cae4643b95f7e2c87b6398cd096db1836ca3533cca67a1842dd037ec66858"
        ),
    },
    {
        "slice_id": "B5",
        "artifact_id": "part-b-b5-manifest-v0.8",
        "path": "configs/part-b-b5-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "bbe8bde7e6ab4695fc6a03233a8c45f5d205c77b3bed6f2816a89c8f7616c069"
        ),
    },
    {
        "slice_id": "B6",
        "artifact_id": "part-b-closed-loop-evaluation-policy-v0.8",
        "path": "configs/part-b-closed-loop-evaluation-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "f9e225fd0bd90046424183620dc9d20a6e91e9c2f4f24893f62dd2b5f8f9f2b1"
        ),
    },
    {
        "slice_id": "B6",
        "artifact_id": "part-b-closed-loop-episode-example-v0.8",
        "path": "configs/part-b-closed-loop-episode-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "25216c85648ae7a54b5a8a909773b0714147b64c2fbd4d8ebb6ac98b931f92a7"
        ),
    },
    {
        "slice_id": "B6",
        "artifact_id": "part-b-closed-loop-feedback-example-v0.8",
        "path": "configs/part-b-closed-loop-feedback-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "01077b5bf717dcbc22b1d65a6e1d0653ce753504dd2ee713fd83b8b064d15a36"
        ),
    },
    {
        "slice_id": "B6",
        "artifact_id": "part-b-closed-loop-preregistration-v0.8",
        "path": "configs/part-b-closed-loop-preregistration-v0.8.yaml",
        "hash": (
            "sha256:"
            "1c3177a68178d9f940978979ae2ff4c59646bf14e693e78f6592ab5f70f91aca"
        ),
    },
    {
        "slice_id": "B6",
        "artifact_id": "part-b-b6-manifest-v0.8",
        "path": "configs/part-b-b6-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "eca84c24d8e75c3daedbd0e786921c8b00827e8f4405be92a7517cba0e94936d"
        ),
    },
    {
        "slice_id": "B7",
        "artifact_id": "part-b-connector-contract-policy-v0.8",
        "path": "configs/part-b-connector-contract-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "43c6270078e03ac1764d16c41871a97a09df3a626c060ceebdecc06682b064c3"
        ),
    },
    {
        "slice_id": "B7",
        "artifact_id": "part-b-connector-descriptor-example-v0.8",
        "path": "configs/part-b-connector-descriptor-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "bc3f2934eb65868ba5db3ac8a0d8bbff7d766271eece9094c68183ce8919ac22"
        ),
    },
    {
        "slice_id": "B7",
        "artifact_id": "part-b-source-authorization-example-v0.8",
        "path": "configs/part-b-source-authorization-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "6576f01963ed07f291a19c8ddcf60dbc9ab5fcde5c7868671b43107db3ca15e0"
        ),
    },
    {
        "slice_id": "B7",
        "artifact_id": "part-b-provenance-envelope-example-v0.8",
        "path": "configs/part-b-provenance-envelope-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "f595cdee0a6c51f7a702e540bab71205f2b28a9701d991c214e28f1af8940ac9"
        ),
    },
    {
        "slice_id": "B7",
        "artifact_id": "part-b-b7-manifest-v0.8",
        "path": "configs/part-b-b7-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "28179580dc0e8c4dbc6f1a6cb1d5f0d4939a3ae7466c078e60f20fb16fffac49"
        ),
    },
    {
        "slice_id": "B8",
        "artifact_id": "part-b-holdout-analysis-policy-v0.8",
        "path": "configs/part-b-holdout-analysis-policy-v0.8.yaml",
        "hash": (
            "sha256:"
            "542ed51380c7dc3e5ba1553d3c80b1a55e5ca5b008cb38d3df831fdee828b603"
        ),
    },
    {
        "slice_id": "B8",
        "artifact_id": "part-b-holdout-preregistration-v0.8",
        "path": "configs/part-b-holdout-preregistration-v0.8.yaml",
        "hash": (
            "sha256:"
            "6af52503f38ff70fc640d8e1313ce8d7f02cf6f79bf23f5cc2a8b3bf5ba38342"
        ),
    },
    {
        "slice_id": "B8",
        "artifact_id": "part-b-statistical-analysis-plan-example-v0.8",
        "path": "configs/part-b-statistical-analysis-plan-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "57e24fd84df55adf44fbcae6c0dbf9248750c0901a6075ad845962c11b5e0627"
        ),
    },
    {
        "slice_id": "B8",
        "artifact_id": "part-b-b8-manifest-v0.8",
        "path": "configs/part-b-b8-manifest-v0.8.yaml",
        "hash": (
            "sha256:"
            "4e6e4ec552d3a9c20c8c68e76766205cb1b2ecdf6dfbfe95866085e0b56c593b"
        ),
    },
    {
        "slice_id": "B8",
        "artifact_id": "part-b-holdout-analysis-envelope-example-v0.8",
        "path": "configs/part-b-holdout-analysis-envelope-example-v0.8.yaml",
        "hash": (
            "sha256:"
            "6126bd2145b1a05c91bf53aa81c599992a787d0dd6a43847f5a67f0bb07a07ed"
        ),
    },
)

CONTRACT_AUTHORITIES = (
    "freeze_contract_authority",
    "audit_contract_authority",
    "claim_boundary_contract_authority",
)
FORBIDDEN_AUTHORITIES = (
    "execution_authority",
    "holdout_release_authority",
    "holdout_data_access_authority",
    "holdout_label_access_authority",
    "holdout_result_access_authority",
    "statistical_analysis_execution_authority",
    "source_selection_authority",
    "source_authorization_authority",
    "connector_execution_authority",
    "retrieval_authority",
    "download_authority",
    "planner_implementation_admission_authority",
    "planner_execution_authority",
    "sampling_authority",
    "baseline_execution_authority",
    "evaluation_execution_authority",
    "scalarization_authority",
    "performance_claim_authority",
    "claim_release_authority",
    "certificate_authority",
)


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B9 artifact: {path.relative_to(ROOT)}"
        )
    return path


def load_json(path: Path) -> dict[str, object]:
    return json.loads(require_file(path).read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(require_file(path).read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


def expected_frozen_artifacts() -> list[dict[str, str]]:
    return [dict(item) for item in FROZEN_UPSTREAM]


class PartBB9ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        """Keep RED counting one missing-artifact failure per test method."""
        for path in B9_NON_TEST_PATHS:
            require_file(path)

    def test_red_01_required_b9_artifacts_exist(self) -> None:
        """RED-01: the exact sixteen non-test B9 artifacts are mandatory."""
        missing = [
            str(path.relative_to(ROOT))
            for path in B9_NON_TEST_PATHS
            if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B9 artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        """RED-02: all B9 schemas are closed Draft 2020-12 objects."""
        for name, path in SCHEMA_PATHS.items():
            with self.subTest(schema=name):
                schema = load_json(path)
                Draft202012Validator.check_schema(schema)
                self.assertEqual(
                    schema.get("$schema"),
                    "https://json-schema.org/draft/2020-12/schema",
                )
                self.assertEqual(schema.get("type"), "object")
                self.assertFalse(schema.get("additionalProperties", True))

    def test_red_03_configs_validate_and_unknown_fields_fail_closed(self) -> None:
        """RED-03: examples validate and undeclared B9 authority is rejected."""
        for name in SCHEMA_PATHS:
            with self.subTest(artifact=name):
                schema = load_json(SCHEMA_PATHS[name])
                instance = load_yaml(CONFIG_PATHS[name])
                self.assertEqual(validate(instance, schema), [])
                expanded = deepcopy(instance)
                expanded["unexpected_b9_authority"] = True
                self.assertNotEqual(validate(expanded, schema), [])

    def test_red_04_hashes_replay_and_tampering_is_visible(self) -> None:
        """RED-04: all B9 YAML identities follow the canonical hash rule."""
        for name, path in CONFIG_PATHS.items():
            with self.subTest(artifact=name):
                document = load_yaml(path)
                self.assertEqual(
                    document.get("hash"),
                    canonical_document_hash(document),
                )
                tampered = deepcopy(document)
                tampered["schema_version"] = "0.8.0-tampered"
                self.assertNotEqual(
                    document.get("hash"),
                    canonical_document_hash(tampered),
                )

    def test_red_05_freeze_record_is_exact_39_item_inventory(self) -> None:
        """RED-05: B9 freezes exactly the explicit 38+1 upstream list."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        self.assertEqual(len(FROZEN_UPSTREAM), 39)
        self.assertEqual(
            record.get("frozen_artifacts"),
            expected_frozen_artifacts(),
        )

    def test_red_06_frozen_paths_and_hashes_match_be33ef8_disk(self) -> None:
        """RED-06: every frozen path and hash replays from the baseline disk."""
        for item in FROZEN_UPSTREAM:
            with self.subTest(artifact=item["artifact_id"]):
                path = require_file(ROOT / item["path"])
                document = load_yaml(path)
                self.assertEqual(document.get("hash"), item["hash"])
                self.assertEqual(
                    canonical_document_hash(document),
                    item["hash"],
                )

    def test_red_07_b9_hash_graph_is_directed_and_acyclic(self) -> None:
        """RED-07: upstream→record→policy/claim→manifest→audit only."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        claim = load_yaml(CONFIG_PATHS["claim_boundary"])
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        audit = load_yaml(CONFIG_PATHS["audit"])

        self.assertEqual(
            policy.get("bindings"),
            {"freeze_record_hash": record["hash"]},
        )
        self.assertEqual(
            claim.get("bindings"),
            {
                "freeze_record_hash": record["hash"],
                "freeze_and_claims_policy_hash": policy["hash"],
            },
        )
        self.assertEqual(
            manifest.get("artifacts"),
            {
                "freeze_record_hash": record["hash"],
                "freeze_and_claims_policy_hash": policy["hash"],
                "claim_boundary_hash": claim["hash"],
            },
        )
        self.assertEqual(
            audit.get("bindings"),
            {
                "freeze_record_hash": record["hash"],
                "freeze_and_claims_policy_hash": policy["hash"],
                "claim_boundary_hash": claim["hash"],
                "b9_manifest_hash": manifest["hash"],
            },
        )

    def test_red_08_manifest_grants_contract_authority_only(self) -> None:
        """RED-08: the final-slice manifest grants only three contracts."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest.get("status"), "B9_CONTRACT_ONLY")
        self.assertEqual(
            manifest.get("authorized_slice"),
            "B9_FREEZE_AND_CLAIMS",
        )
        for field in CONTRACT_AUTHORITIES:
            with self.subTest(authority=field):
                self.assertIs(manifest.get(field), True)
        for field in FORBIDDEN_AUTHORITIES:
            with self.subTest(non_authority=field):
                self.assertIs(manifest.get(field), False)
        self.assertEqual(manifest.get("stop_authority"), "NONE")
        self.assertEqual(manifest.get("llm_integration"), "FORBIDDEN")

    def test_red_09_every_runtime_and_release_authority_is_false(self) -> None:
        """RED-09: policy and manifest cannot activate a runtime or release."""
        for name in ("policy", "manifest"):
            document = load_yaml(CONFIG_PATHS[name])
            with self.subTest(artifact=name):
                for field in FORBIDDEN_AUTHORITIES:
                    self.assertIs(document.get(field), False)
                self.assertEqual(document.get("stop_authority"), "NONE")

    def test_red_10_evidence_and_claim_ceiling_is_contract_only(self) -> None:
        """RED-10: no B9 proof may exceed CONTRACT_CONSISTENCY_ONLY."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        claim = load_yaml(CONFIG_PATHS["claim_boundary"])
        self.assertEqual(
            manifest.get("evidence_ceiling"),
            "CONTRACT_CONSISTENCY_ONLY",
        )
        self.assertEqual(
            policy.get("evidence_ceiling"),
            "CONTRACT_CONSISTENCY_ONLY",
        )
        self.assertEqual(
            claim.get("evidence_ceiling"),
            "CONTRACT_CONSISTENCY_ONLY",
        )
        self.assertEqual(
            manifest.get("proof_boundary"),
            {
                "contract_consistency_only": True,
                "frozen_hashes_replayed": True,
                "schema_contracts_validated": True,
                "external_validity": False,
                "performance_validity": False,
                "superiority_claim": False,
                "global_optimality_claim": False,
                "holdout_validated": False,
                "statistical_analysis_executed": False,
            },
        )

    def test_red_11_pb_si_006_remains_open_and_fail_closed(self) -> None:
        """RED-11: final freeze cannot select or authorize a real source."""
        combined = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        self.assertIn("PB-SI-006", combined)
        self.assertRegex(
            combined,
            re.compile(
                r"PB-SI-006.{0,200}OPEN",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertNotRegex(
            combined,
            re.compile(
                r"PB-SI-006.{0,80}CLOSED",
                re.IGNORECASE | re.DOTALL,
            ),
        )

    def test_red_12_planner_and_empirical_claim_gates_remain_open(self) -> None:
        """RED-12: B5 admission and B8 empirical gates are not closed."""
        combined = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        for issue_id in ("PB-B5-SI-001", "PB-B8-SI-004"):
            with self.subTest(issue=issue_id):
                self.assertIn(issue_id, combined)
                self.assertRegex(
                    combined,
                    re.compile(
                        rf"{re.escape(issue_id)}.{{0,240}}"
                        r"(OPEN|NOT SATISFIED|UNCHANGED)",
                        re.IGNORECASE | re.DOTALL,
                    ),
                )

    def test_red_13_b4_isolation_and_b8_holdout_deny_are_preserved(self) -> None:
        """RED-13: freeze does not unseal HOLDOUT or change isolation."""
        b4 = load_yaml(
            CONFIG_DIR / "part-b-baseline-isolation-policy-v0.8.yaml"
        )
        b8 = load_yaml(CONFIG_DIR / "part-b-holdout-analysis-policy-v0.8.yaml")
        b9 = load_yaml(CONFIG_PATHS["policy"])
        self.assertEqual(
            b4.get("hash"),
            "sha256:"
            "8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f",
        )
        self.assertEqual(b8["release_gate"]["default_decision"], "DENY")
        self.assertEqual(
            b8["release_gate"]["failure_behavior"],
            "FAIL_CLOSED_NO_ACCESS",
        )
        self.assertEqual(b9["holdout_gate"]["default_decision"], "DENY")
        self.assertIs(b9["holdout_gate"]["contract_unseals_holdout"], False)

    def test_red_14_documents_freeze_the_exact_18_file_allowlist(self) -> None:
        """RED-14: B9 documents its exact scope and forbids upstream edits."""
        plan_path = (
            ROOT
            / "08-writing"
            / "part-b-b9-implementation-plan-v0.8-20260724.md"
        )
        plan = require_file(plan_path).read_text(encoding="utf-8")
        for path in B9_ALLOWLIST_PATHS:
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(allowlisted=relative):
                self.assertIn(relative, plan)
        self.assertIn("18", plan)
        self.assertRegex(plan, re.compile(r"B0.{0,5}B8", re.DOTALL))
        self.assertRegex(
            plan,
            re.compile(
                r"(must not|must remain|forbidden|禁止).{0,160}"
                r"(modify|rewrite|改).{0,80}B0.{0,5}B8",
                re.IGNORECASE | re.DOTALL,
            ),
        )


if __name__ == "__main__":
    unittest.main()
