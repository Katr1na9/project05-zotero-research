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

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-connector-contract-policy.schema.json",
    "descriptor": SCHEMA_DIR / "part-b-connector-descriptor.schema.json",
    "authorization": SCHEMA_DIR / "part-b-source-authorization.schema.json",
    "provenance": SCHEMA_DIR / "part-b-provenance-envelope.schema.json",
    "manifest": SCHEMA_DIR / "part-b-b7-manifest.schema.json",
}
CONFIG_PATHS = {
    "policy": CONFIG_DIR / "part-b-connector-contract-policy-v0.8.yaml",
    "descriptor": (
        CONFIG_DIR / "part-b-connector-descriptor-example-v0.8.yaml"
    ),
    "authorization": (
        CONFIG_DIR / "part-b-source-authorization-example-v0.8.yaml"
    ),
    "provenance": (
        CONFIG_DIR / "part-b-provenance-envelope-example-v0.8.yaml"
    ),
    "manifest": CONFIG_DIR / "part-b-b7-manifest-v0.8.yaml",
}
DOCUMENT_PATHS = (
    ROOT / "contracts" / "part-b-b7-boundary-v0.8.md",
    ROOT / "contracts" / "part-b-b7-broad-connectors-v0.8.md",
    ROOT
    / "contracts"
    / "part-b-b7-provenance-and-source-authorization-v0.8.md",
    ROOT / "src" / "scope" / "part-b-b7-spec-issues.md",
    ROOT
    / "08-writing"
    / "part-b-b7-implementation-plan-v0.8-20260723.md",
    ROOT / "08-writing" / "KERNEL-V0.8-AUTHORITY-STATUS-20260722.md",
)

# B7 must replay these approved B1-B6 documents without editing them.
FROZEN_B1_B6_HASHES = {
    "part-b-federation-contract-v0.8.yaml": (
        "b1_federation_contract_hash",
        "sha256:6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d",
    ),
    "part-b-adapter-conformance-v0.8.yaml": (
        "b1_adapter_conformance_hash",
        "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a",
    ),
    "part-b-b1-manifest-v0.8.yaml": (
        "b1_manifest_hash",
        "sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e",
    ),
    "part-b-stochastic-observation-catalog-v0.8.yaml": (
        "b2_stochastic_catalog_hash",
        "sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5",
    ),
    "part-b-stochastic-tv-policy-v0.8.yaml": (
        "b2_tv_policy_hash",
        "sha256:b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8",
    ),
    "part-b-b2-world-pair-delta-decision-v0.8.yaml": (
        "b2_world_pair_delta_decision_hash",
        "sha256:1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919",
    ),
    "part-b-b2-manifest-v0.8.yaml": (
        "b2_manifest_hash",
        "sha256:6d6f67d9722eff1b2e1aa75277b0c390dc485751067728a347ae89c77f83faed",
    ),
    "part-b-cost-instrumentation-policy-v0.8.yaml": (
        "b3_cost_instrumentation_policy_hash",
        "sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278",
    ),
    "part-b-b3-manifest-v0.8.yaml": (
        "b3_manifest_hash",
        "sha256:9403004d25c1428beeb85f04c6d65eeb02759d6881ede67390a2d97f2b9c82fb",
    ),
    "part-b-baseline-preregistration-v0.8.yaml": (
        "b4_baseline_preregistration_hash",
        "sha256:c51ab64588441855a7ff8413e32695e4b168d6d2a2089674f2cdcd691959906d",
    ),
    "part-b-baseline-isolation-policy-v0.8.yaml": (
        "b4_baseline_isolation_policy_hash",
        "sha256:8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f",
    ),
    "part-b-b4-manifest-v0.8.yaml": (
        "b4_manifest_hash",
        "sha256:2649b2a9067858d5fe2fa4c2f9d6386408384448910c97ee4eb89f1817893afc",
    ),
    "part-b-planner-public-state-example-v0.8.yaml": (
        "b5_planner_public_state_example_hash",
        "sha256:42efd17661a1335f3c84c2c4efbea4de8107087d099dc987a902d20ded50deae",
    ),
    "part-b-planner-decision-example-v0.8.yaml": (
        "b5_planner_decision_example_hash",
        "sha256:144cd24c0d6e3906ee31d25cdcc629f20901648d58204ee030f397daca23da6d",
    ),
    "part-b-planner-interface-policy-v0.8.yaml": (
        "b5_planner_interface_policy_hash",
        "sha256:b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343",
    ),
    "part-b-bounded-evaluation-v0.8.yaml": (
        "b5_bounded_evaluation_hash",
        "sha256:9c1cae4643b95f7e2c87b6398cd096db1836ca3533cca67a1842dd037ec66858",
    ),
    "part-b-b5-manifest-v0.8.yaml": (
        "b5_manifest_hash",
        "sha256:bbe8bde7e6ab4695fc6a03233a8c45f5d205c77b3bed6f2816a89c8f7616c069",
    ),
    "part-b-closed-loop-evaluation-policy-v0.8.yaml": (
        "b6_closed_loop_policy_hash",
        "sha256:f9e225fd0bd90046424183620dc9d20a6e91e9c2f4f24893f62dd2b5f8f9f2b1",
    ),
    "part-b-closed-loop-episode-example-v0.8.yaml": (
        "b6_episode_example_hash",
        "sha256:25216c85648ae7a54b5a8a909773b0714147b64c2fbd4d8ebb6ac98b931f92a7",
    ),
    "part-b-closed-loop-feedback-example-v0.8.yaml": (
        "b6_feedback_example_hash",
        "sha256:01077b5bf717dcbc22b1d65a6e1d0653ce753504dd2ee713fd83b8b064d15a36",
    ),
    "part-b-closed-loop-preregistration-v0.8.yaml": (
        "b6_preregistration_hash",
        "sha256:1c3177a68178d9f940978979ae2ff4c59646bf14e693e78f6592ab5f70f91aca",
    ),
    "part-b-b6-manifest-v0.8.yaml": (
        "b6_manifest_hash",
        "sha256:eca84c24d8e75c3daedbd0e786921c8b00827e8f4405be92a7517cba0e94936d",
    ),
}


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise AssertionError(
            f"missing approved B7 artifact: {path.relative_to(ROOT)}"
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


def walk(value: object):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key), child
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


class PartBB7ContractTests(unittest.TestCase):
    def test_red_01_required_b7_artifacts_exist(self) -> None:
        """RED-01: the exact sixteen non-test B7 artifacts are mandatory."""
        paths = (
            *SCHEMA_PATHS.values(),
            *CONFIG_PATHS.values(),
            *DOCUMENT_PATHS,
        )
        missing = [
            str(path.relative_to(ROOT)) for path in paths if not path.is_file()
        ]
        self.assertEqual(
            missing,
            [],
            "missing approved B7 artifacts: " + ", ".join(missing),
        )

    def test_red_02_schemas_are_closed_draft_2020_12_contracts(self) -> None:
        """RED-02: every B7 schema is valid and rejects top-level expansion."""
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
        """RED-03: all B7 examples validate; undeclared authority does not."""
        for name in SCHEMA_PATHS:
            with self.subTest(artifact=name):
                schema = load_json(SCHEMA_PATHS[name])
                instance = load_yaml(CONFIG_PATHS[name])
                self.assertEqual(validate(instance, schema), [])
                expanded = deepcopy(instance)
                expanded["unexpected_b7_authority"] = True
                self.assertNotEqual(validate(expanded, schema), [])

    def test_red_04_hashes_replay_and_tampering_is_visible(self) -> None:
        """RED-04: every B7 document uses the approved canonical hash rule."""
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

    def test_red_05_b1_b6_hashes_are_exact_read_only_bindings(self) -> None:
        """RED-05: B7 replays every approved B1-B6 hash exactly."""
        expected_bindings = {}
        for filename, (binding_key, expected_hash) in (
            FROZEN_B1_B6_HASHES.items()
        ):
            with self.subTest(upstream=filename):
                upstream = load_yaml(CONFIG_DIR / filename)
                self.assertEqual(upstream.get("hash"), expected_hash)
                self.assertEqual(canonical_document_hash(upstream), expected_hash)
                expected_bindings[binding_key] = expected_hash

        for name in ("policy", "manifest"):
            with self.subTest(b7_artifact=name):
                document = load_yaml(CONFIG_PATHS[name])
                self.assertEqual(document.get("bindings"), expected_bindings)

    def test_red_06_manifest_grants_contract_authority_only(self) -> None:
        """RED-06: B7 cannot execute a connector or expand other authority."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest.get("status"), "B7_CONTRACT_ONLY")
        self.assertEqual(
            manifest.get("authorized_slice"), "B7_BROAD_CONNECTORS"
        )
        self.assertIs(manifest.get("connector_contract_authority"), True)
        self.assertIs(manifest.get("provenance_contract_authority"), True)
        for field in (
            "source_selection_authority",
            "source_authorization_authority",
            "connector_execution_authority",
            "retrieval_authority",
            "download_authority",
            "credential_use_authority",
            "planner_execution_authority",
            "sampling_authority",
            "evaluation_execution_authority",
            "performance_claim_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(manifest.get(field), False)
        self.assertEqual(manifest.get("stop_authority"), "NONE")

    def test_red_07_b8_b9_and_every_runtime_remain_closed(self) -> None:
        """RED-07: opening B7 does not open B8/B9 or any runtime."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(manifest.get("closed_slices"), ["B8", "B9"])
        self.assertEqual(manifest.get("llm_integration"), "FORBIDDEN")
        policy = load_yaml(CONFIG_PATHS["policy"])
        runtime = policy.get("runtime_boundary", {})
        self.assertEqual(
            runtime,
            {
                "connector_runtime": False,
                "network_access": False,
                "credential_resolution": False,
                "data_download": False,
                "data_retrieval": False,
                "sampling": False,
                "planner_execution": False,
                "evaluation_execution": False,
            },
        )

    def test_red_08_pb_si_006_remains_a_per_source_gate(self) -> None:
        """RED-08: a generic contract does not select or authorize a source."""
        b0_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b0-spec-issues.md"
        ).read_text(encoding="utf-8")
        b7_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b7-spec-issues.md"
        ).read_text(encoding="utf-8")
        combined = (b0_issue + "\n" + b7_issue).upper()
        self.assertIn("PB-SI-006", combined)
        self.assertIn("BLOCKS CONNECTOR/DATA WORK", combined)
        self.assertIn("PER-SOURCE", combined)
        self.assertIn("SEPARATE AUTHORIZATION", combined)
        self.assertNotIn("PB-SI-006: CLOSED", combined)

    def test_red_09_pb_b5_si_001_remains_open(self) -> None:
        """RED-09: B7 cannot admit a Planner implementation."""
        b5_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b5-spec-issues.md"
        ).read_text(encoding="utf-8")
        b7_issue = require_file(
            ROOT / "src" / "scope" / "part-b-b7-spec-issues.md"
        ).read_text(encoding="utf-8")
        combined = (b5_issue + "\n" + b7_issue).upper()
        self.assertIn("PB-B5-SI-001", combined)
        self.assertIn("OPEN", combined)
        self.assertIn("NOT ESTABLISHED", combined)
        self.assertNotIn("PLANNER EXECUTION AUTHORITY: GRANTED", combined)

    def test_red_10_configs_contain_no_source_or_retrieval_material(self) -> None:
        """RED-10: contract examples contain no real source access material."""
        url_pattern = re.compile(r"(?:https?|s3|gs|ftp)://", re.IGNORECASE)
        path_pattern = re.compile(r"(?:[a-z]:\\\\|/var/|/home/|/data/)")
        forbidden_exact_keys = {
            "url",
            "uri",
            "endpoint",
            "host",
            "port",
            "credential",
            "credentials",
            "token",
            "secret",
            "api_key",
            "query",
            "command",
            "download_path",
            "dataset_path",
            "payload",
        }
        for name, path in CONFIG_PATHS.items():
            with self.subTest(artifact=name):
                document = load_yaml(path)
                for key, value in walk(document):
                    self.assertNotIn(key.lower(), forbidden_exact_keys)
                    if isinstance(value, str):
                        self.assertIsNone(url_pattern.search(value))
                        self.assertIsNone(path_pattern.search(value))

    def test_red_11_documents_freeze_the_per_source_boundary(self) -> None:
        """RED-11: all human-facing B7 records deny implicit source access."""
        text = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        ).upper()
        for required in (
            "B7_BROAD_CONNECTORS",
            "CONTRACT ONLY",
            "PER-SOURCE",
            "SEPARATE AUTHORIZATION",
            "NO CONNECTOR RUNTIME",
            "NO DOWNLOAD",
            "PB-SI-006",
            "PB-B5-SI-001",
            "CERTIFIED_STOP",
            "B8",
            "B9",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_red_12_b7_proves_contract_consistency_only(self) -> None:
        """RED-12: passing B7 cannot imply external or performance validity."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        self.assertEqual(
            manifest.get("proof_boundary"),
            {
                "contract_consistency_only": True,
                "source_conformance_validated": False,
                "connector_implementation_validated": False,
                "connector_execution": False,
                "data_acquisition": False,
                "external_validity": False,
                "performance_validity": False,
                "superiority_claim": False,
            },
        )
        text = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        ).upper()
        self.assertIn("CONTRACT_CONSISTENCY_ONLY", text)
        self.assertIn("NO EXTERNAL VALIDITY", text)
        self.assertIn("NO PERFORMANCE CLAIM", text)


if __name__ == "__main__":
    unittest.main()
