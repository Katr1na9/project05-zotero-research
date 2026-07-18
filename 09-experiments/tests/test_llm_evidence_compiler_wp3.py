import copy
import gzip
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
WP3_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "wp3"
WP3_CONTRACT_ROOT = WP3_ROOT / "contracts"
CATALOG_PATH = WP3_ROOT / "component-catalog-v0.1.json"
WP2_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "generated" / "wp2"
RULE_ROOT = WP2_ROOT / "rule-strong-development"
PUBLIC_ROOT = WP2_ROOT / "public"
GENERATED_WP3_ROOT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "generated"
    / "wp3"
    / "reuse-hybrid-development"
)
CANONICAL_CLAIM_ID = re.compile(r"\bC[0-9]{2}(?:-[A-Za-z0-9_-]+)*-EC-[0-9]{3,}\b")


def load_script(name: str):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_script("build_compiler_public_request")
adapter = load_script("adapt_reuse_component_graph")
reuse = load_script("run_compiler_reuse_hybrid")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def fixture_request(*, source_type="cti_text", text=None, report=None):
    if text is None:
        text = (
            "An unrelated preface names neither endpoint. "
            "PowerShell downloaded payload.ps1 from evil.example."
        )
    if report is None:
        report = "A longer field also mentions PowerShell and payload.ps1."
    record = builder.build_record(
        "REC-0000000000000011",
        {"text": text, "report": report},
        location="unit-cti.txt",
    )
    artifact = builder.build_artifact(
        "ART-0000000000000011", source_type, [record]
    )
    return builder.build_public_request(
        case_id="C01-wp3-unit",
        split="unit",
        step_index=0,
        visible_artifacts=[artifact],
        target_nodes=[],
        predicate_allowlist={source_type: ["related_to"]},
    )


def fixture_bundle(request, *, revision=None, triplets=None):
    catalog = load_json(CATALOG_PATH)
    selected = catalog["selected_adapter_profile"]
    if triplets is None:
        triplets = [
            {
                "triplet_id": builder.derive_scoped_id(
                    "TRIP", request["request_id"], "powershell", "payload.ps1"
                ),
                "subject": {"entity_type": "process", "value": "PowerShell"},
                "relation": "downloaded",
                "object": {"entity_type": "file", "value": "payload.ps1"},
                "source_pointer": {
                    "artifact_id": "ART-0000000000000011",
                    "record_id": "REC-0000000000000011",
                },
            }
        ]
    return {
        "schema_version": "0.1.0",
        "output_profile": selected["output_profile"],
        "component_id": selected["component_id"],
        "component_revision": revision or selected["revision"],
        "component_license": selected["license"],
        "component_runtime_executed": False,
        "request_id": request["request_id"],
        "triplets": triplets,
    }


class WP3ContractAndCatalogTests(unittest.TestCase):
    def test_wp3_contracts_are_valid_and_separate_from_m1_contracts(self):
        self.assertEqual(
            {
                "normalized_aligned_triplet_bundle.schema.json",
                "source_grounded_target_graph_sidecar.schema.json",
            },
            {path.name for path in WP3_CONTRACT_ROOT.glob("*.schema.json")},
        )
        for path in sorted(WP3_CONTRACT_ROOT.glob("*.schema.json")):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(load_json(path))
        self.assertEqual(
            6,
            len(
                list(
                    (
                        EXPERIMENT_ROOT
                        / "llm_evidence_compiler_mainline"
                        / "contracts"
                    ).glob("*.schema.json")
                )
            ),
        )

    def test_catalog_freezes_identity_license_and_no_runtime_authority(self):
        catalog = load_json(CATALOG_PATH)
        self.assertFalse(catalog["third_party_code_copied"])
        self.assertEqual(5, len(catalog["components"]))
        selected = catalog["selected_adapter_profile"]
        self.assertEqual("ctinexus", selected["component_id"])
        self.assertEqual(
            "0c688536d85eae72f6055723492b573b0a1ff865",
            selected["revision"],
        )
        self.assertEqual("MIT", selected["license"])
        self.assertFalse(selected["external_runtime_authorized"])
        self.assertTrue(
            all(not component["runtime_authorized"] for component in catalog["components"])
        )
        self.assertTrue(
            all(not component["code_copy_authorized"] for component in catalog["components"])
        )


class CleanRoomAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_json(CATALOG_PATH)
        cls.bundle_schema = load_json(
            WP3_CONTRACT_ROOT / "normalized_aligned_triplet_bundle.schema.json"
        )
        cls.sidecar_schema = load_json(
            WP3_CONTRACT_ROOT / "source_grounded_target_graph_sidecar.schema.json"
        )

    def test_valid_triplet_recovers_shortest_same_record_sentence(self):
        request = fixture_request()
        bundle = fixture_bundle(request)
        Draft202012Validator(self.bundle_schema).validate(bundle)

        before = set(sys.modules)
        sidecar = adapter.adapt_bundle(request, bundle, self.catalog)
        loaded = set(sys.modules) - before

        Draft202012Validator(self.sidecar_schema).validate(sidecar)
        self.assertEqual("completed", sidecar["status"])
        self.assertEqual(1, sidecar["counts"]["accepted_edges"])
        self.assertEqual(2, sidecar["counts"]["output_nodes"])
        self.assertEqual(
            "PowerShell downloaded payload.ps1 from evil.example.",
            sidecar["edges"][0]["support_sentence"],
        )
        self.assertEqual("payload.text", sidecar["edges"][0]["source_pointer"]["field_path"])
        self.assertFalse(sidecar["edges"][0]["controller_eligible"])
        self.assertTrue(all(not node["controller_eligible"] for node in sidecar["nodes"]))
        self.assertFalse({"torch", "transformers", "litellm", "neo4j"} & loaded)
        self.assertFalse(sidecar["third_party_code_copied"])

    def test_missing_support_sentence_fails_closed(self):
        request = fixture_request(
            text="PowerShell appears here. payload.ps1 appears elsewhere.",
            report="This field contains no endpoint surfaces.",
        )
        sidecar = adapter.adapt_bundle(
            request, fixture_bundle(request), self.catalog
        )
        Draft202012Validator(self.sidecar_schema).validate(sidecar)
        self.assertEqual("abstained", sidecar["status"])
        self.assertEqual([], sidecar["edges"])
        self.assertEqual(["all_triplets_rejected"], sidecar["abstention_reasons"])
        self.assertIn(
            "source_surface_not_grounded", sidecar["rejections"][0]["reason_codes"]
        )

    def test_unknown_revision_fails_closed_before_edges(self):
        request = fixture_request()
        bundle = fixture_bundle(request, revision="f" * 40)
        sidecar = adapter.adapt_bundle(request, bundle, self.catalog)
        Draft202012Validator(self.sidecar_schema).validate(sidecar)
        self.assertEqual("abstained", sidecar["status"])
        self.assertEqual([], sidecar["edges"])
        self.assertEqual(
            ["component_revision_mismatch"], sidecar["abstention_reasons"]
        )
        self.assertEqual(
            ["component_revision_mismatch"],
            sidecar["rejections"][0]["reason_codes"],
        )

    def test_external_runtime_flag_is_rejected_while_not_authorized(self):
        request = fixture_request()
        bundle = fixture_bundle(request)
        bundle["component_runtime_executed"] = True
        sidecar = adapter.adapt_bundle(request, bundle, self.catalog)
        self.assertEqual("abstained", sidecar["status"])
        self.assertIn(
            "component_runtime_not_authorized", sidecar["abstention_reasons"]
        )
        self.assertEqual([], sidecar["edges"])

    def test_no_cti_text_artifact_explicitly_abstains(self):
        request = fixture_request(source_type="local_log")
        bundle = fixture_bundle(request, triplets=[])
        sidecar = adapter.adapt_bundle(request, bundle, self.catalog)
        Draft202012Validator(self.sidecar_schema).validate(sidecar)
        self.assertEqual("abstained", sidecar["status"])
        self.assertEqual(
            ["no_visible_cti_text_artifact"], sidecar["abstention_reasons"]
        )
        self.assertEqual(0, sidecar["counts"]["input_triplets"])

    def test_unknown_pointer_and_actor_conclusion_are_rejected(self):
        request = fixture_request()
        unknown = fixture_bundle(request)["triplets"][0]
        unknown["source_pointer"]["record_id"] = "REC-FFFFFFFFFFFFFFFF"
        actor = copy.deepcopy(fixture_bundle(request)["triplets"][0])
        actor["triplet_id"] = builder.derive_scoped_id("TRIP", "actor")
        actor["subject"] = {"entity_type": "threat_actor", "value": "PowerShell"}
        bundle = fixture_bundle(request, triplets=[unknown, actor])
        sidecar = adapter.adapt_bundle(request, bundle, self.catalog)
        reasons = {
            reason
            for rejection in sidecar["rejections"]
            for reason in rejection["reason_codes"]
        }
        self.assertIn("unknown_source_pointer", reasons)
        self.assertIn("unsupported_conclusion_entity", reasons)
        self.assertEqual([], sidecar["edges"])

    def test_duplicate_edges_are_all_rejected(self):
        request = fixture_request()
        first = fixture_bundle(request)["triplets"][0]
        second = copy.deepcopy(first)
        second["triplet_id"] = builder.derive_scoped_id("TRIP", "duplicate")
        sidecar = adapter.adapt_bundle(
            request, fixture_bundle(request, triplets=[first, second]), self.catalog
        )
        self.assertEqual(2, len(sidecar["rejections"]))
        self.assertTrue(
            all(
                "duplicate_edge" in rejection["reason_codes"]
                for rejection in sidecar["rejections"]
            )
        )
        self.assertEqual([], sidecar["edges"])

    def test_private_or_canonical_answer_material_cannot_enter_output(self):
        request = fixture_request()
        canonical = fixture_bundle(request)
        canonical["triplets"][0]["subject"]["value"] = "C01-EC-001"
        with self.assertRaisesRegex(ValueError, "canonical claim identifier"):
            adapter.adapt_bundle(request, canonical, self.catalog)

        private = fixture_bundle(request)
        private["gold"] = "hidden answer"
        with self.assertRaisesRegex(ValueError, "forbidden keys"):
            adapter.adapt_bundle(request, private, self.catalog)

        clean = adapter.adapt_bundle(request, fixture_bundle(request), self.catalog)
        serialized = builder.canonical_json_text(clean)
        self.assertIsNone(CANONICAL_CLAIM_ID.search(serialized))
        self.assertNotIn("private", serialized.casefold())
        self.assertNotIn("canonical", serialized.casefold())


class ReuseHybridDevelopmentTests(unittest.TestCase):
    def test_runner_reuses_frozen_rule_and_abstains_without_cti(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "reuse-hybrid"
            snapshot = reuse.run(PUBLIC_ROOT, RULE_ROOT, CATALOG_PATH, output)
            results = load_json(output / "reuse-hybrid-development-results.json")

        self.assertEqual(
            "wp3_adapter_interface_pass_component_performance_not_evaluable",
            snapshot["status"],
        )
        self.assertEqual(3, snapshot["case_count"])
        self.assertEqual(26, snapshot["rule_admitted_claim_count"])
        self.assertEqual(15, snapshot["rule_admitted_link_count"])
        self.assertEqual(3, snapshot["cti_component_abstention_count"])
        self.assertEqual(0, snapshot["cti_component_accepted_edge_count"])
        self.assertEqual([], snapshot["test_case_ids_processed"])
        self.assertFalse(snapshot["third_party_component_executed"])
        self.assertFalse(snapshot["model_runtime_used"])
        self.assertFalse(snapshot["reference_data_used"])
        self.assertFalse(snapshot["controller_payload_emitted"])
        self.assertFalse(snapshot["component_performance_claim_authorized"])
        self.assertFalse(snapshot["wp4_model_gate_authorized"])
        self.assertTrue(
            all(
                row["cti_component_route"]["abstention_reasons"]
                == ["no_visible_cti_text_artifact"]
                for row in results["rows"]
            )
        )
        self.assertTrue(
            all(not row["merged_controller_payload_emitted"] for row in results["rows"])
        )

    def test_saved_snapshot_and_implementation_hashes_are_immutable(self):
        snapshot = load_json(
            GENERATED_WP3_ROOT / "reuse-hybrid-development-snapshot.json"
        )
        results = load_json(
            GENERATED_WP3_ROOT / "reuse-hybrid-development-results.json"
        )
        self.assertEqual(snapshot["results_sha256"], builder.sha256_value(results))
        implementation_paths = {
            "adapt_reuse_component_graph.py": EXPERIMENT_ROOT
            / "scripts"
            / "adapt_reuse_component_graph.py",
            "run_compiler_reuse_hybrid.py": EXPERIMENT_ROOT
            / "scripts"
            / "run_compiler_reuse_hybrid.py",
            "component-catalog-v0.1.json": CATALOG_PATH,
            "normalized_aligned_triplet_bundle.schema.json": WP3_CONTRACT_ROOT
            / "normalized_aligned_triplet_bundle.schema.json",
            "source_grounded_target_graph_sidecar.schema.json": WP3_CONTRACT_ROOT
            / "source_grounded_target_graph_sidecar.schema.json",
        }
        self.assertEqual(
            set(implementation_paths), set(snapshot["implementation_sha256"])
        )
        for name, path in implementation_paths.items():
            with self.subTest(path=name):
                self.assertEqual(
                    snapshot["implementation_sha256"][name], sha256_file(path)
                )
        self.assertEqual([], snapshot["test_case_ids_processed"])
        self.assertFalse(snapshot["component_performance_claim_authorized"])


if __name__ == "__main__":
    unittest.main()
