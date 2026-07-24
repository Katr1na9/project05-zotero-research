import copy
import json
import re
import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.claim_id_mint_executor import (  # noqa: E402
    ClaimIDMintError,
    UnavailableKeyProvider,
    load_and_validate_slot_mapping,
    mint_claim_ids,
)
from compiler.llm.m0_rule_compiler import compile_public_projection  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]
M0_FIXTURE = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "m0_rule_compiler"
    / "m0_valid_public_projection.json"
)
MINT_FIXTURE_DIR = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "claim_id_mint_executor"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def minted_identifier_count(value) -> int:
    if isinstance(value, dict):
        return sum(minted_identifier_count(nested) for nested in value.values())
    if isinstance(value, list):
        return sum(minted_identifier_count(nested) for nested in value)
    return int(isinstance(value, str) and value.startswith("clm_"))


class ClaimIDMintExecutorTests(unittest.TestCase):
    def test_loads_exact_38_slot_bijection(self):
        mapping = load_and_validate_slot_mapping(REPO_ROOT)

        self.assertEqual(38, len(mapping))
        self.assertEqual(38, len(set(mapping.values())))
        self.assertTrue(
            all(re.fullmatch(r"afs_[0-9]{4}", slot) for slot in mapping.values())
        )

    def test_default_key_provider_is_unavailable(self):
        self.assertIsNone(UnavailableKeyProvider().get_key("test-key-id"))

    def test_valid_structural_package_rejects_without_execute_authority(self):
        structural_package = compile_public_projection(
            load_json(M0_FIXTURE),
            repo_root=REPO_ROOT,
        )
        original = copy.deepcopy(structural_package)

        with self.assertRaises(ClaimIDMintError) as context:
            mint_claim_ids(structural_package, repo_root=REPO_ROOT)

        self.assertEqual("missing_authority", context.exception.code)
        self.assertEqual(original, structural_package)
        self.assertEqual(0, minted_identifier_count(structural_package))
        self.assertEqual("not_minted", structural_package["claim_id_state"])
        self.assertEqual("not_admitted", structural_package["admission_state"])
        self.assertEqual(
            "pending_kernel_schema",
            structural_package["kernel_state"],
        )
        self.assertTrue(
            all(claim["claim_id"] is None for claim in structural_package["claims"])
        )

    def test_three_antileak_fixtures_reject_with_zero_ids(self):
        fixture_names = (
            "mint_antileak_labels_outcomes.json",
            "mint_antileak_paths_payloads.json",
            "mint_antileak_oracle_hidden_mask.json",
        )
        for fixture_name in fixture_names:
            with self.subTest(fixture=fixture_name):
                fixture = load_json(MINT_FIXTURE_DIR / fixture_name)
                original = copy.deepcopy(fixture)

                with self.assertRaises(ClaimIDMintError) as context:
                    mint_claim_ids(fixture, repo_root=REPO_ROOT)

                self.assertEqual("forbidden_field", context.exception.code)
                self.assertEqual(original, fixture)
                self.assertEqual(0, minted_identifier_count(fixture))
                self.assertEqual("not_minted", fixture["claim_id_state"])
                self.assertEqual("not_admitted", fixture["admission_state"])
                self.assertEqual("pending_kernel_schema", fixture["kernel_state"])


if __name__ == "__main__":
    unittest.main()
