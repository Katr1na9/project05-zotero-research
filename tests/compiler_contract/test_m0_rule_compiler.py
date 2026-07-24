import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.m0_rule_compiler import (  # noqa: E402
    M0CompilerError,
    compile_public_projection,
    run_fixture_directory,
    verify_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = Path(__file__).with_name("fixtures") / "m0_rule_compiler"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class M0RuleCompilerTests(unittest.TestCase):
    def test_pins_and_surface_are_verified(self):
        verify_pins(REPO_ROOT)

    def test_valid_fixture_emits_structural_non_admitted_package(self):
        package = compile_public_projection(
            load_fixture("m0_valid_public_projection.json"),
            repo_root=REPO_ROOT,
        )

        self.assertEqual("project05_depth2_public", package["surface_id"])
        self.assertEqual("pending_kernel_schema", package["kernel_state"])
        self.assertEqual("not_minted", package["claim_id_state"])
        self.assertEqual("not_admitted", package["admission_state"])
        self.assertGreater(package["manifest"]["claim_count"], 0)
        self.assertTrue(all(claim["claim_id"] is None for claim in package["claims"]))
        self.assertTrue(
            all(
                claim["claim_id_state"] == "not_minted"
                and claim["admission_state"] == "not_admitted"
                for claim in package["claims"]
            )
        )

    def test_authority_leak_fixtures_fail_closed(self):
        expected_codes = {
            "m0_authority_leak_labels.json": "forbidden_field",
            "m0_authority_leak_hidden_claims.json": "forbidden_field",
            "m0_authority_leak_realized_outcome.json": "forbidden_field",
            "m0_authority_leak_oracle_mask.json": "forbidden_field",
        }
        for fixture_name, expected_code in expected_codes.items():
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(M0CompilerError) as context:
                    compile_public_projection(
                        load_fixture(fixture_name),
                        repo_root=REPO_ROOT,
                    )
                self.assertEqual(expected_code, context.exception.code)

    def test_fixture_runner_emits_only_valid_package_and_sanitized_report(self):
        with TemporaryDirectory() as temporary:
            report = run_fixture_directory(
                FIXTURE_DIR,
                Path(temporary),
                repo_root=REPO_ROOT,
            )

            self.assertEqual(5, len(report["results"]))
            accepted = [
                result
                for result in report["results"]
                if result["outcome"] == "accepted_structural"
            ]
            rejected = [
                result
                for result in report["results"]
                if result["outcome"] == "rejected"
            ]
            self.assertEqual(1, len(accepted))
            self.assertEqual(4, len(rejected))
            self.assertFalse(report["claim_id_minting_performed"])
            self.assertFalse(report["kernel_write_performed"])
            self.assertFalse(report["admission_performed"])


if __name__ == "__main__":
    unittest.main()
