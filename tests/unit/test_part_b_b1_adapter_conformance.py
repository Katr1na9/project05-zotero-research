from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
CONFIG_DIR = ROOT / "configs"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, object]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate(instance: dict[str, object], schema: dict[str, object]) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB1AdapterConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_json(
            SCHEMA_DIR / "part-b-adapter-conformance.schema.json"
        )
        cls.federation_schema = load_json(
            SCHEMA_DIR / "part-b-federation-contract.schema.json"
        )
        cls.contract = load_yaml(
            CONFIG_DIR / "part-b-adapter-conformance-v0.8.yaml"
        )
        cls.federation = load_yaml(
            CONFIG_DIR / "part-b-federation-contract-v0.8.yaml"
        )

    def test_two_structurally_distinct_families_share_one_contract(self) -> None:
        examples = self.contract["conformance_examples"]
        self.assertGreaterEqual(len(examples), 2)
        self.assertGreaterEqual(
            len({example["family_id"] for example in examples}),
            2,
        )
        self.assertGreaterEqual(
            len({example["input_shape"] for example in examples}),
            2,
        )
        mapping_shapes = {
            tuple(mapping["output_field"] for mapping in example["field_mappings"])
            for example in examples
        }
        self.assertGreaterEqual(len(mapping_shapes), 2)
        self.assertEqual(validate(self.contract, self.schema), [])

    def test_pointer_requires_identity_hash_and_range_semantics(self) -> None:
        required_pointer_fields = (
            "source_id",
            "record_id",
            "content_hash",
            "byte_or_row_range",
            "range_semantics",
        )
        for index, example in enumerate(self.contract["conformance_examples"]):
            pointer = example["projected_claim_envelope"]["pointer"]
            self.assertTrue(all(field in pointer for field in required_pointer_fields))
            for field in required_pointer_fields:
                invalid = deepcopy(self.contract)
                del invalid["conformance_examples"][index][
                    "projected_claim_envelope"
                ]["pointer"][field]
                with self.subTest(example=example["example_id"], missing=field):
                    self.assertTrue(validate(invalid, self.schema))

    def test_adapter_preserves_pointer_provenance_exactly(self) -> None:
        range_semantics = {
            ("ROWS", "EXCLUSIVE"): "ROWS_HALF_OPEN",
            ("BYTES", "EXCLUSIVE"): "BYTES_HALF_OPEN",
        }
        for example in self.contract["conformance_examples"]:
            source = example["input_provenance"]
            pointer = example["projected_claim_envelope"]["pointer"]
            self.assertEqual(pointer["source_id"], source["source_id"])
            self.assertEqual(pointer["record_id"], source["record_id"])
            self.assertEqual(pointer["content_hash"], source["content_hash"])
            self.assertEqual(
                pointer["byte_or_row_range"],
                [source["range"]["start"], source["range"]["end"]],
            )
            self.assertEqual(
                pointer["range_semantics"],
                range_semantics[
                    (source["range"]["kind"], source["range"]["end_semantics"])
                ],
            )
        self.assertEqual(
            self.contract["adapter_rules"]["pointer_provenance"],
            "PRESERVE_EXACTLY",
        )

    def test_epistemic_fields_are_separate_and_required(self) -> None:
        fields = (
            "modality",
            "truth_status",
            "epistemic_role",
            "certification_authority",
        )
        for index, example in enumerate(self.contract["conformance_examples"]):
            envelope = example["projected_claim_envelope"]
            self.assertTrue(all(field in envelope for field in fields))
            self.assertNotIn("epistemic_state", envelope)
            for field in fields:
                invalid = deepcopy(self.contract)
                del invalid["conformance_examples"][index][
                    "projected_claim_envelope"
                ][field]
                with self.subTest(example=example["example_id"], missing=field):
                    self.assertTrue(validate(invalid, self.schema))

    def test_adapter_cannot_self_grant_certification_authority(self) -> None:
        self.assertEqual(
            self.contract["adapter_rules"]["certification_authority"],
            "POLICY_GATED_OUTSIDE_ADAPTER",
        )
        for index, example in enumerate(self.contract["conformance_examples"]):
            authority = example["projected_claim_envelope"][
                "certification_authority"
            ]
            self.assertEqual(
                authority,
                {
                    "allowed": False,
                    "levels": [],
                    "basis_rule_id": None,
                    "policy_hash": None,
                },
            )
            invalid = deepcopy(self.contract)
            invalid["conformance_examples"][index]["projected_claim_envelope"][
                "certification_authority"
            ] = {
                "allowed": True,
                "levels": ["L1"],
                "basis_rule_id": "adapter-self-grant",
                "policy_hash": "sha256:" + "1" * 64,
            }
            with self.subTest(example=example["example_id"]):
                self.assertTrue(validate(invalid, self.schema))

    def test_open_world_zero_hit_cannot_imply_absence(self) -> None:
        open_families = [
            family
            for family in self.federation["semantic_families"]
            if family["world_semantics"]["mode"] == "OPEN_WORLD"
        ]
        self.assertTrue(open_families)
        for family in open_families:
            semantics = family["world_semantics"]
            self.assertEqual(
                semantics["zero_hit_semantics"],
                "UNKNOWN_NOT_ABSENCE",
            )
            self.assertIsNone(semantics["completeness_contract"])

            invalid = deepcopy(self.federation)
            target = next(
                item
                for item in invalid["semantic_families"]
                if item["family_id"] == family["family_id"]
            )
            target["world_semantics"]["zero_hit_semantics"] = (
                "ZERO_HIT_EXCLUDES_IN_SCOPE_RECORD"
            )
            self.assertTrue(validate(invalid, self.federation_schema))

    def test_closed_world_requires_explicit_completeness_contract(self) -> None:
        closed_families = [
            family
            for family in self.federation["semantic_families"]
            if family["world_semantics"]["mode"] == "CLOSED_BOUNDED"
        ]
        self.assertTrue(closed_families)
        required = (
            "scope",
            "time_window",
            "snapshot_identity",
            "completeness_conditions",
            "absence_semantics",
        )
        for family in closed_families:
            completeness = family["world_semantics"]["completeness_contract"]
            self.assertTrue(all(field in completeness for field in required))
            for field in required:
                invalid = deepcopy(self.federation)
                target = next(
                    item
                    for item in invalid["semantic_families"]
                    if item["family_id"] == family["family_id"]
                )
                del target["world_semantics"]["completeness_contract"][field]
                with self.subTest(family=family["family_id"], missing=field):
                    self.assertTrue(validate(invalid, self.federation_schema))

    def test_unknown_inputs_have_explicit_fail_closed_codes(self) -> None:
        self.assertEqual(
            self.contract["error_semantics"],
            {
                "unknown_family": "B1-FED-001_UNKNOWN_FAMILY",
                "unknown_predicate": "B1-FED-002_UNKNOWN_PREDICATE",
                "unknown_schema_version": "B1-FED-003_UNKNOWN_SCHEMA_VERSION",
                "pointer_provenance_mismatch": (
                    "B1-FED-004_POINTER_PROVENANCE_MISMATCH"
                ),
                "namespace_collision": "B1-FED-005_NAMESPACE_COLLISION",
                "authority_self_grant": "B1-FED-006_AUTHORITY_SELF_GRANT",
                "open_world_zero_hit": "B1-FED-007_OPEN_WORLD_ZERO_HIT",
                "closed_world_incomplete": "B1-FED-008_CLOSED_WORLD_INCOMPLETE",
                "unauthorized_execution": "B1-FED-009_UNAUTHORIZED_EXECUTION",
            },
        )
        self.assertEqual(
            self.contract["adapter_rules"]["unknown_input_policy"],
            "FAIL_CLOSED_WITH_ERROR",
        )

    def test_cross_family_ids_require_namespace_bindings_and_collision_failure(
        self,
    ) -> None:
        identity = self.contract["adapter_rules"]["entity_identity"]
        self.assertTrue(identity["namespace_required"])
        self.assertTrue(identity["binding_required"])
        self.assertEqual(identity["collision_policy"], "FAIL_CLOSED")
        self.assertEqual(
            identity["collision_error_code"],
            "B1-FED-005_NAMESPACE_COLLISION",
        )

        seen: set[tuple[str, str]] = set()
        for example in self.contract["conformance_examples"]:
            binding = example["entity_binding"]
            key = (binding["namespace_id"], binding["source_entity_id"])
            self.assertNotIn(key, seen)
            seen.add(key)
            self.assertTrue(binding["canonical_entity_id"])
            self.assertTrue(binding["binding_rule_id"])

    def test_examples_emit_no_system_state_certificate_or_stop(self) -> None:
        forbidden_keys = {
            "system_status",
            "system_state",
            "certificate",
            "level_certificate",
            "stop_result",
        }

        def visit(value: object) -> None:
            if isinstance(value, dict):
                for key, child in value.items():
                    self.assertNotIn(str(key).lower(), forbidden_keys)
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
            elif isinstance(value, str):
                self.assertNotEqual(value, "CERTIFIED_STOP")

        visit(self.contract["conformance_examples"])
        self.assertFalse(self.contract["execution_authority"])

    def test_range_semantics_is_conformance_envelope_only(self) -> None:
        kernel_schema = load_json(SCHEMA_DIR / "claim-ir-kernel.schema.json")
        kernel_pointer = kernel_schema["$defs"]["pointer"]
        self.assertNotIn("range_semantics", kernel_pointer["properties"])
        self.assertNotIn("range_semantics", kernel_pointer["required"])
        self.assertFalse(kernel_pointer["additionalProperties"])

        fixture_path = (
            ROOT
            / "tests"
            / "fixtures"
            / "TWIN-COUNTEREXAMPLE-001"
            / "claims"
            / "case_evidence.jsonl"
        )
        claim = json.loads(fixture_path.read_text(encoding="utf-8").splitlines()[0])
        injected = deepcopy(claim)
        injected["pointer"]["range_semantics"] = "ROWS_HALF_OPEN"
        self.assertTrue(validate(injected, kernel_schema))

        conformance_pointer = self.schema["$defs"]["claimPointer"]
        self.assertIn("range_semantics", conformance_pointer["required"])
        self.assertEqual(
            conformance_pointer["properties"]["range_semantics"]["enum"],
            ["ROWS_HALF_OPEN", "BYTES_HALF_OPEN"],
        )

        candidate_interface = load_json(
            ROOT / "src" / "ir" / "candidate-claim-ir-interface-v0.8.json"
        )
        self.assertIn(
            "pointer",
            candidate_interface["compiler_forbidden_fields"],
        )

        manifest = load_yaml(CONFIG_DIR / "part-b-b1-manifest-v0.8.yaml")
        self.assertEqual(
            self.federation["hash"],
            "sha256:6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d",
        )
        self.assertEqual(
            self.contract["hash"],
            "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a",
        )
        self.assertEqual(
            manifest["hash"],
            "sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e",
        )

        decision_contract = (
            ROOT / "contracts" / "part-b-b1-range-semantics-v0.8.md"
        ).read_text(encoding="utf-8")
        for required_text in (
            "CLOSED — APPROVED",
            "CONFORMANCE_ENVELOPE_ONLY",
            "INFERENCE_FORBIDDEN",
            "FAIL_CLOSED",
            "B1-RANGE-001_CONFORMANCE_CONTRACT_REQUIRED",
            "Candidate Compiler",
            "no production adapter authority",
        ):
            with self.subTest(required_text=required_text):
                self.assertIn(required_text, decision_contract)


if __name__ == "__main__":
    unittest.main()
