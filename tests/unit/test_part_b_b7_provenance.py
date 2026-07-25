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

SCHEMA_PATHS = {
    "policy": SCHEMA_DIR / "part-b-connector-contract-policy.schema.json",
    "descriptor": SCHEMA_DIR / "part-b-connector-descriptor.schema.json",
    "authorization": SCHEMA_DIR / "part-b-source-authorization.schema.json",
    "provenance": SCHEMA_DIR / "part-b-provenance-envelope.schema.json",
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


def validation_errors(
    instance: dict[str, object], schema: dict[str, object]
) -> list:
    return sorted(
        Draft202012Validator(schema).iter_errors(instance),
        key=lambda error: list(error.absolute_path),
    )


class PartBB7ProvenanceTests(unittest.TestCase):
    def test_red_13_connector_domain_is_finite_versioned_and_b1_bound(
        self,
    ) -> None:
        """RED-13: connector kinds are finite and use registered B1 families."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        federation = load_yaml(
            CONFIG_DIR / "part-b-federation-contract-v0.8.yaml"
        )
        kinds = policy["connector_contract"]["connector_kinds"]
        self.assertGreater(len(kinds), 0)
        self.assertEqual(len(kinds), len(set(kinds)))
        self.assertTrue(all(isinstance(item, str) and item for item in kinds))

        descriptor = load_yaml(CONFIG_PATHS["descriptor"])
        family_ids = {
            item["family_id"] for item in federation["semantic_families"]
        }
        self.assertIn(descriptor["connector_kind"], kinds)
        self.assertIn(descriptor["semantic_family"]["family_id"], family_ids)
        self.assertEqual(
            descriptor["semantic_family"]["family_version"], "0.8.0"
        )
        self.assertEqual(descriptor["descriptor_version"], "0.8.0")

    def test_red_14_unknown_family_schema_or_conformance_fails_closed(
        self,
    ) -> None:
        """RED-14: no connector may silently widen B1 conformance."""
        schema = load_json(SCHEMA_PATHS["descriptor"])
        descriptor = load_yaml(CONFIG_PATHS["descriptor"])
        error_codes = load_yaml(CONFIG_PATHS["policy"])["error_semantics"]
        for field, expected_code in (
            ("unknown_family", "B7-CONN-001_UNKNOWN_FAMILY"),
            ("unknown_source_schema", "B7-CONN-002_UNKNOWN_SOURCE_SCHEMA"),
            (
                "conformance_hash_mismatch",
                "B7-CONN-003_CONFORMANCE_HASH_MISMATCH",
            ),
        ):
            with self.subTest(field=field):
                self.assertEqual(error_codes.get(field), expected_code)

        unknown_family = deepcopy(descriptor)
        unknown_family["semantic_family"]["family_id"] = "unregistered"
        self.assertNotEqual(validation_errors(unknown_family, schema), [])

        unknown_schema = deepcopy(descriptor)
        unknown_schema["semantic_family"]["source_schema_id"] = "unknown.v9"
        self.assertNotEqual(validation_errors(unknown_schema, schema), [])

        bad_hash = deepcopy(descriptor)
        bad_hash["bindings"]["b1_adapter_conformance_hash"] = (
            "sha256:" + "0" * 64
        )
        self.assertNotEqual(validation_errors(bad_hash, schema), [])

    def test_red_15_source_authorization_is_separate_and_default_deny(
        self,
    ) -> None:
        """RED-15: a descriptor is not a source authorization."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        descriptor = load_yaml(CONFIG_PATHS["descriptor"])
        authorization = load_yaml(CONFIG_PATHS["authorization"])
        self.assertEqual(
            policy["source_authorization"]["default_decision"], "DENY"
        )
        self.assertEqual(
            policy["source_authorization"]["grant_mode"],
            "SEPARATE_PER_SOURCE_ARTIFACT",
        )
        self.assertEqual(descriptor["source_status"], "CONTRACT_FIXTURE_ONLY")
        self.assertIs(descriptor["source_selected"], False)
        self.assertIs(descriptor["execution_authority"], False)
        self.assertEqual(
            authorization["decision"], "NOT_AUTHORIZED"
        )
        self.assertEqual(
            authorization["reason_code"],
            "B7-SOURCE-001_SEPARATE_AUTHORIZATION_REQUIRED",
        )

    def test_red_16_missing_wrong_or_tampered_authorization_fails_closed(
        self,
    ) -> None:
        """RED-16: source access requires an exact, independently bound grant."""
        schema = load_json(SCHEMA_PATHS["authorization"])
        authorization = load_yaml(CONFIG_PATHS["authorization"])

        missing = deepcopy(authorization)
        del missing["bindings"]["descriptor_hash"]
        self.assertNotEqual(validation_errors(missing, schema), [])

        wrong = deepcopy(authorization)
        wrong["bindings"]["descriptor_hash"] = "sha256:" + "0" * 64
        self.assertNotEqual(validation_errors(wrong, schema), [])

        grant = deepcopy(authorization)
        grant["decision"] = "AUTHORIZED"
        self.assertNotEqual(validation_errors(grant, schema), [])

    def test_red_17_provenance_requires_exact_pointer_and_range_semantics(
        self,
    ) -> None:
        """RED-17: source, record, hash and explicit range are mandatory."""
        schema = load_json(SCHEMA_PATHS["provenance"])
        provenance = load_yaml(CONFIG_PATHS["provenance"])
        pointer = provenance["pointer"]
        self.assertTrue(pointer["source_id"])
        self.assertTrue(pointer["record_id"])
        self.assertRegex(pointer["content_hash"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            pointer["range_semantics"],
            f"{pointer['range']['kind']}_HALF_OPEN",
        )
        self.assertLess(pointer["range"]["start"], pointer["range"]["end"])

        for field in ("source_id", "record_id", "content_hash", "range"):
            with self.subTest(field=field):
                missing = deepcopy(provenance)
                del missing["pointer"][field]
                self.assertNotEqual(validation_errors(missing, schema), [])

    def test_red_18_range_units_and_endpoints_cannot_be_inferred(self) -> None:
        """RED-18: numeric ranges never imply rows/bytes or endpoint rules."""
        schema = load_json(SCHEMA_PATHS["provenance"])
        provenance = load_yaml(CONFIG_PATHS["provenance"])

        missing = deepcopy(provenance)
        del missing["pointer"]["range_semantics"]
        self.assertNotEqual(validation_errors(missing, schema), [])

        mismatched = deepcopy(provenance)
        mismatched["pointer"]["range_semantics"] = (
            "BYTES_HALF_OPEN"
            if provenance["pointer"]["range"]["kind"] == "ROWS"
            else "ROWS_HALF_OPEN"
        )
        self.assertNotEqual(validation_errors(mismatched, schema), [])

        inclusive = deepcopy(provenance)
        inclusive["pointer"]["range"]["end_semantics"] = "INCLUSIVE"
        self.assertNotEqual(validation_errors(inclusive, schema), [])

    def test_red_19_pointer_provenance_is_preserved_exactly(self) -> None:
        """RED-19: connector projection may not rewrite B1 provenance."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        descriptor = load_yaml(CONFIG_PATHS["descriptor"])
        provenance = load_yaml(CONFIG_PATHS["provenance"])
        self.assertEqual(
            policy["provenance_rules"]["pointer_provenance"],
            "PRESERVE_EXACTLY",
        )
        self.assertEqual(
            provenance["bindings"]["descriptor_id"],
            descriptor["descriptor_id"],
        )
        self.assertEqual(
            provenance["input_provenance"], provenance["pointer"]
        )
        self.assertEqual(
            policy["error_semantics"]["pointer_rewrite"],
            "B7-PROV-001_POINTER_REWRITE",
        )

    def test_red_20_epistemic_fields_are_separate_and_no_self_grant(
        self,
    ) -> None:
        """RED-20: provenance cannot collapse or elevate epistemic fields."""
        schema = load_json(SCHEMA_PATHS["provenance"])
        provenance = load_yaml(CONFIG_PATHS["provenance"])
        expected = {
            "modality",
            "truth_status",
            "epistemic_role",
            "certification_authority",
        }
        self.assertTrue(expected.issubset(provenance))
        authority = provenance["certification_authority"]
        self.assertEqual(
            authority,
            {
                "allowed": False,
                "levels": [],
                "basis_rule_id": None,
                "policy_hash": None,
            },
        )
        elevated = deepcopy(provenance)
        elevated["certification_authority"]["allowed"] = True
        elevated["certification_authority"]["levels"] = ["level-complete"]
        self.assertNotEqual(validation_errors(elevated, schema), [])

    def test_red_21_capability_never_implies_evidence_or_stop_authority(
        self,
    ) -> None:
        """RED-21: declared capabilities do not admit evidence or eliminate worlds."""
        descriptor = load_yaml(CONFIG_PATHS["descriptor"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        for field in (
            "claim_admission_authority",
            "world_elimination_authority",
            "certificate_authority",
            "system_status_authority",
            "certified_stop_authority",
        ):
            with self.subTest(field=field):
                self.assertIs(descriptor["authority_boundary"][field], False)
                self.assertIs(policy["authority_boundary"][field], False)

    def test_red_22_zero_hit_respects_open_closed_world_boundary(self) -> None:
        """RED-22: only separately proven completeness can support absence."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        provenance = load_yaml(CONFIG_PATHS["provenance"])
        world = provenance["world_semantics"]
        if world["mode"] == "OPEN_WORLD":
            self.assertEqual(world["zero_hit_semantics"], "UNKNOWN_NOT_ABSENCE")
            self.assertIsNone(world["completeness_attestation"])
        else:
            self.assertEqual(world["mode"], "CLOSED_BOUNDED")
            self.assertEqual(
                world["zero_hit_semantics"],
                "ABSENCE_ONLY_WHEN_SEPARATELY_PROVEN_COMPLETE",
            )
            self.assertIsNotNone(world["completeness_attestation"])
        self.assertEqual(
            policy["world_semantics"]["closed_world_gate"],
            "SEPARATE_COMPLETENESS_ATTESTATION_REQUIRED",
        )

    def test_red_23_failures_are_unknown_not_zero_hit_or_unsat(self) -> None:
        """RED-23: partial retrieval failures cannot masquerade as absence."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        self.assertEqual(
            policy["failure_semantics"],
            {
                "timeout": "UNKNOWN_NO_ZERO_HIT",
                "resource_exhaustion": "UNKNOWN_NO_ZERO_HIT",
                "partial_result": "UNKNOWN_INCOMPLETE",
                "parse_failure": "REJECTED_UNKNOWN",
                "schema_mismatch": "REJECTED_UNKNOWN",
                "authorization_missing": "DENY_NO_ACCESS",
                "connector_unavailable": "UNKNOWN_NO_ZERO_HIT",
            },
        )
        flattened = " ".join(policy["failure_semantics"].values())
        self.assertNotIn("UNSAT", flattened)
        self.assertNotIn("ABSENCE", flattened)

    def test_red_24_examples_are_nonexecuting_and_emit_no_authority(
        self,
    ) -> None:
        """RED-24: B7 examples are inert contracts, not connector outputs."""
        for name in ("descriptor", "authorization", "provenance"):
            with self.subTest(artifact=name):
                document = load_yaml(CONFIG_PATHS[name])
                boundary = document["execution_boundary"]
                self.assertEqual(
                    boundary,
                    {
                        "network_access": False,
                        "credential_use": False,
                        "retrieval": False,
                        "download": False,
                        "connector_execution": False,
                    },
                )
                serialized = json.dumps(document, sort_keys=True)
                self.assertNotIn("CERTIFIED_STOP", serialized)
                self.assertNotIn('"system_status"', serialized)
                self.assertNotIn('"certificate"', serialized)


if __name__ == "__main__":
    unittest.main()
