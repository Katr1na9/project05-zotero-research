import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas" / "claim-ir-kernel.schema.json"
PACKAGE_PATH = (
    REPO_ROOT
    / ".tmp"
    / "m0-rule-compiler-run-v0.1"
    / "m0_valid_public_projection.output.json"
)


class M0ClaimIRSchemaValidationTests(unittest.TestCase):
    def test_valid_structural_package_has_zero_draft202012_errors(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))

        errors = list(Draft202012Validator(schema).iter_errors(package))

        self.assertEqual([], errors)
        self.assertEqual("project05_depth2_public", package["surface_id"])
        self.assertEqual("pending_kernel_schema", package["kernel_state"])
        self.assertEqual("not_minted", package["claim_id_state"])
        self.assertEqual("not_admitted", package["admission_state"])
        self.assertTrue(all(claim["claim_id"] is None for claim in package["claims"]))


if __name__ == "__main__":
    unittest.main()
