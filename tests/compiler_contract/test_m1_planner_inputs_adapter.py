import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.m0_rule_compiler import compile_public_projection  # noqa: E402
from compiler.llm import m1_planner_inputs_adapter as adapter_module  # noqa: E402
from compiler.llm.m1_planner_inputs_adapter import (  # noqa: E402
    ADAPTER_ID,
    ADAPTER_VERSION,
    ADAPTER_DISPOSITION_SHA256,
    AUTHORITY_DESIGN_SHA256,
    COMPILER_SHA256,
    CONTRACT_SHA256,
    M1_FRAMEWORK_SHA256,
    M1AdapterError,
    PROJECTION_SHA256,
    SCHEMA_SHA256,
    SOURCE_CLASS,
    SURFACE_ID,
    adapt_planner_projection,
    verify_adapter_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path(__file__).with_name("fixtures") / "m0_rule_compiler"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def planner_descriptor(projection: dict) -> dict:
    package = compile_public_projection(projection, repo_root=REPO_ROOT)
    present = {claim["source_field"] for claim in package["claims"]}
    schema_fields = json.loads(
        (REPO_ROOT / "schemas/claim-ir-kernel.schema.json").read_text(encoding="utf-8")
    )["$defs"]["source_field"]["enum"]
    return {
        "surface_id": SURFACE_ID,
        "source_class": SOURCE_CLASS,
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "opaque_record_reference": "case_public_001",
        "declared_source_fields": [
            field for field in schema_fields if field in present
        ],
    }


def canonical_sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def activated_authority(descriptor: dict, projection: dict) -> dict:
    descriptor_sha = canonical_sha256(descriptor)
    projection_sha = canonical_sha256(projection)
    return {
        "status": "activated_single_adapter_execute_authorized",
        "target": {
            "surface_id": SURFACE_ID,
            "adapter_id": ADAPTER_ID,
            "source_class": SOURCE_CLASS,
            "only_target": True,
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "m1_framework_sha256": M1_FRAMEWORK_SHA256,
            "adapter_contract_sha256": CONTRACT_SHA256,
            "adapter_implementation_sha256": hashlib.sha256(
                (
                    REPO_ROOT
                    / "src"
                    / "compiler"
                    / "llm"
                    / "m1_planner_inputs_adapter.py"
                ).read_bytes()
            ).hexdigest(),
            "adapter_disposition_sha256": ADAPTER_DISPOSITION_SHA256,
            "schema_sha256": SCHEMA_SHA256,
            "m0_compiler_sha256": COMPILER_SHA256,
            "projection_sha256": PROJECTION_SHA256,
        },
        "pinned_inputs": {
            "descriptor_sha256": descriptor_sha,
            "public_projection_sha256": projection_sha,
        },
        "reserved_result_path": (
            ".tmp/m1_planner_inputs_adapter_tests/"
            f"{descriptor_sha}-{projection_sha}.json"
        ),
        "execute_ledger": {
            "authorized": 1,
            "maximum": 1,
            "started": 0,
            "consumed": 0,
            "remaining": 1,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "output_policy": {
            "mode": "in_memory_structural_only",
            "file_write": False,
            "mint": False,
            "kernel_write": False,
            "admission": False,
        },
        "still_blocked": {
            "production_claim_id_mint": True,
            "kernel_write": True,
            "e_case_write": True,
            "certificate_generation": True,
            "admission": True,
            "catalog_write": True,
            "source_role_assignment": True,
            "lineage_credit": True,
            "quota_credit": True,
            "l2_gate_change": True,
            "m2_implementation_or_fit": True,
            "four_family_llm_finetune": True,
            "registry_permanent_effect": True,
        },
    }


class M1PlannerInputsAdapterTests(unittest.TestCase):
    def test_contract_pins_and_inactive_registry_are_verified(self):
        verify_adapter_pins(REPO_ROOT)

    def test_missing_or_inactive_authority_rejects_before_m0_handoff(self):
        projection = load_fixture("m0_valid_public_projection.json")
        descriptor = planner_descriptor(projection)

        with patch.object(adapter_module, "compile_public_projection") as handoff:
            with self.assertRaises(M1AdapterError) as missing_context:
                adapt_planner_projection(
                    descriptor,
                    projection,
                    repo_root=REPO_ROOT,
                )
            self.assertEqual("missing_authority", missing_context.exception.code)
            handoff.assert_not_called()

        inactive = activated_authority(descriptor, projection)
        inactive["status"] = "design_only_execute_authority_not_activated"
        with patch.object(adapter_module, "compile_public_projection") as handoff:
            with self.assertRaises(M1AdapterError) as inactive_context:
                adapt_planner_projection(
                    descriptor,
                    projection,
                    repo_root=REPO_ROOT,
                    authority=inactive,
                )
            self.assertEqual("not_activated", inactive_context.exception.code)
            handoff.assert_not_called()

    def test_valid_projection_delegates_to_structural_m0_package(self):
        projection = load_fixture("m0_valid_public_projection.json")
        descriptor = planner_descriptor(projection)
        authority = activated_authority(descriptor, projection)
        result_path = REPO_ROOT / authority["reserved_result_path"]
        self.assertFalse(result_path.exists())

        package = adapt_planner_projection(
            descriptor,
            projection,
            repo_root=REPO_ROOT,
            authority=authority,
        )

        self.assertEqual(SURFACE_ID, package["surface_id"])
        self.assertEqual("not_minted", package["claim_id_state"])
        self.assertEqual("not_admitted", package["admission_state"])
        self.assertEqual("pending_kernel_schema", package["kernel_state"])
        self.assertGreater(package["manifest"]["claim_count"], 0)
        self.assertTrue(all(claim["claim_id"] is None for claim in package["claims"]))
        self.assertFalse("adapter_id" in package)
        self.assertFalse("source_class" in package)
        self.assertFalse(result_path.exists())

    def test_four_authority_leak_fixtures_fail_closed(self):
        for fixture_name in (
            "m0_authority_leak_labels.json",
            "m0_authority_leak_hidden_claims.json",
            "m0_authority_leak_realized_outcome.json",
            "m0_authority_leak_oracle_mask.json",
        ):
            with self.subTest(fixture=fixture_name):
                valid = load_fixture("m0_valid_public_projection.json")
                descriptor = planner_descriptor(valid)
                leaking_projection = load_fixture(fixture_name)
                with self.assertRaises(M1AdapterError) as context:
                    adapt_planner_projection(
                        descriptor,
                        leaking_projection,
                        repo_root=REPO_ROOT,
                        authority=activated_authority(
                            descriptor,
                            leaking_projection,
                        ),
                    )
                self.assertEqual("forbidden_field", context.exception.code)

    def test_unknown_descriptor_field_and_path_like_value_reject(self):
        projection = load_fixture("m0_valid_public_projection.json")
        descriptor = planner_descriptor(projection)

        unknown_descriptor = copy.deepcopy(descriptor)
        unknown_descriptor["declared_source_fields"] = [
            *unknown_descriptor["declared_source_fields"],
            "state.unknown",
        ]
        with self.assertRaises(M1AdapterError) as unknown_context:
            adapt_planner_projection(
                unknown_descriptor,
                projection,
                repo_root=REPO_ROOT,
                authority=activated_authority(
                    unknown_descriptor,
                    projection,
                ),
            )
        self.assertEqual("unknown_source_field", unknown_context.exception.code)

        path_like_projection = copy.deepcopy(projection)
        path_like_projection["action"]["target"]["target_value"] = (
            "C:\\raw\\payload.bin"
        )
        with self.assertRaises(M1AdapterError) as path_context:
            adapt_planner_projection(
                descriptor,
                path_like_projection,
                repo_root=REPO_ROOT,
                authority=activated_authority(
                    descriptor,
                    path_like_projection,
                ),
            )
        self.assertEqual("raw_path", path_context.exception.code)

    def test_wrong_pin_consumed_ledger_and_wrong_surface_reject(self):
        projection = load_fixture("m0_valid_public_projection.json")
        descriptor = planner_descriptor(projection)

        bad_pin = activated_authority(descriptor, projection)
        bad_pin["pinned_hashes"]["schema_sha256"] = "0" * 64
        consumed = activated_authority(descriptor, projection)
        consumed["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        wrong_surface = activated_authority(descriptor, projection)
        wrong_surface["target"]["surface_id"] = "other_surface"

        for authority, expected_code in (
            (bad_pin, "authority_pin"),
            (consumed, "authority_ledger"),
            (wrong_surface, "authority_target"),
        ):
            with self.subTest(error_code=expected_code):
                with patch.object(adapter_module, "compile_public_projection") as handoff:
                    with self.assertRaises(M1AdapterError) as context:
                        adapt_planner_projection(
                            descriptor,
                            projection,
                            repo_root=REPO_ROOT,
                            authority=authority,
                        )
                    self.assertEqual(expected_code, context.exception.code)
                    handoff.assert_not_called()


if __name__ == "__main__":
    unittest.main()
