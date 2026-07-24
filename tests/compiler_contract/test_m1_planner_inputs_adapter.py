import copy
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.m0_rule_compiler import compile_public_projection  # noqa: E402
from compiler.llm.m1_planner_inputs_adapter import (  # noqa: E402
    ADAPTER_ID,
    ADAPTER_VERSION,
    M1AdapterError,
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


class M1PlannerInputsAdapterTests(unittest.TestCase):
    def test_contract_pins_and_inactive_registry_are_verified(self):
        verify_adapter_pins(REPO_ROOT)

    def test_valid_projection_delegates_to_structural_m0_package(self):
        projection = load_fixture("m0_valid_public_projection.json")
        descriptor = planner_descriptor(projection)

        with TemporaryDirectory() as temporary:
            package = adapt_planner_projection(
                descriptor,
                projection,
                repo_root=REPO_ROOT,
            )
            self.assertEqual([], list(Path(temporary).iterdir()))

        self.assertEqual(SURFACE_ID, package["surface_id"])
        self.assertEqual("not_minted", package["claim_id_state"])
        self.assertEqual("not_admitted", package["admission_state"])
        self.assertEqual("pending_kernel_schema", package["kernel_state"])
        self.assertGreater(package["manifest"]["claim_count"], 0)
        self.assertTrue(all(claim["claim_id"] is None for claim in package["claims"]))
        self.assertFalse("adapter_id" in package)
        self.assertFalse("source_class" in package)

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
                with self.assertRaises(M1AdapterError) as context:
                    adapt_planner_projection(
                        descriptor,
                        load_fixture(fixture_name),
                        repo_root=REPO_ROOT,
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
            )
        self.assertEqual("raw_path", path_context.exception.code)


if __name__ == "__main__":
    unittest.main()
