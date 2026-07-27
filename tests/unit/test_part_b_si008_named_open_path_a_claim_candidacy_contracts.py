"""Contract tests for the PB-SI-008 Path A CLAIM candidacy successor.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import unittest

import yaml

from src.scope import (
    part_b_si008_named_open_path_a_claim_candidacy as claim_gate,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_si008_named_open_path_a_claim_candidacy.py"
)
MANIFEST_PATH = (
    ROOT
    / "configs"
    / "part-b-si008-named-open-path-a-claim-candidacy-manifest-v0.8.yaml"
)
CONTRACT_PATH = (
    ROOT
    / "contracts"
    / "part-b-si008-named-open-path-a-claim-candidacy-v0.8.md"
)
PRODUCT_ARTIFACTS = (RUNTIME_PATH, MANIFEST_PATH, CONTRACT_PATH)
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
NAMED_REQUEST_FIELDS = {
    "request_id",
    "request_kind",
    "promotion_target",
    "reference_kind",
    "named_target_id",
    "source_schema_version",
    "source_schema_sha256",
    "consumer_contract_id",
    "consumer_contract_sha256",
    "package_sha256",
    "structural_validation_receipt_sha256",
    "record_class",
    "claim_id",
    "claim_id_state",
    "admission_state",
    "structural_validation_status",
    "requested_authority_scope",
    "reference_access_mode",
}
PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-pb-si008-named-open-claim-target-owner-go-authorization-v0.1-20260727.json": (
        "327eed5f0e39e7256f27c9dcf068159e289692153d70a5936c57b1c07ea83a8b"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-claim-candidacy-red-design-v0.1-20260727.json": (
        "f8107272800ecbc9bf9a05f718091fbdbe8c5b6a79ae32b94f56b7b4844a2bab"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-pb-si008-named-open-path-a-claim-candidacy-red-review-packet-v0.1-20260727.json": (
        "c9a7e274b28425c406f2d3a88598912aa118791cf7f9f495d527296951e939b4"
    ),
    "src/scope/part_b_si008_named_open_path_a_evidence_candidacy.py": (
        "a71358d11a0495f0c6457f9f59061fd982dfda7c3d1921e2f62c7b39cbcaea29"
    ),
    "configs/part-b-si008-named-open-path-a-evidence-candidacy-manifest-v0.8.yaml": (
        "aa01c95f00c7757ae6adea046f2cee0fb4bdee7a404ea5ce40701aad61214ff8"
    ),
    "src/scope/part_b_si008_dual_track_deny.py": (
        "b43c647d45a4aa19722ca8c501a6cb41f0b1add1f4e501e9684033797c7b12fb"
    ),
    "configs/part-b-si008-dual-track-deny-manifest-v0.8.yaml": (
        "a3355c292e1a120fdc12adb32ccced310525f284751019551618d04bf9a023e9"
    ),
    "src/scope/part_b_si008_path_a_named_open_caller_wiring.py": (
        "64fcc81ff7ae6f61ae58d6a8e5d9bb602a5c6f307feef1a25497048643d11ecf"
    ),
    "src/compiler/llm/m1_path_a_named_open_composition_readonly.py": (
        "3b4f86288b1bb4b7d3e5366e24a6adabaddaa028a463c6b067c4470added0cc3"
    ),
}
EXPECTED_REFERENCE_PAIRS = [
    {
        "reference_kind": "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE",
        "source_schema_version": "claim-ir-external-evidence-v0.1",
        "source_schema_sha256": (
            "9abc23e2258298038e137dbbe38168867"
            "d07108fa27719aa68c1c2b752ae2a7c"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.2"
        ),
        "consumer_contract_sha256": (
            "fe5222b9b4e0ddaf990761b34bdfc500"
            "4f45f55d3e2155b09388fb9596a1e504"
        ),
    },
    {
        "reference_kind": "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE",
        "source_schema_version": "claim-ir-external-evidence-v0.2",
        "source_schema_sha256": (
            "e246c44b7513a5bc2f3410a2739a53bd"
            "1f40dad3e767036bb1af3158c9e02ac6"
        ),
        "consumer_contract_id": (
            "shared-claim-ir-consumer-contract-evidence-candidate-"
            "effective-v0.3"
        ),
        "consumer_contract_sha256": (
            "7662762d045381921b8f94a39753d0c4"
            "91322b3a41d473226cc5fe3f4688457c"
        ),
    },
]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBSI008NamedOpenPathAClaimCandidacyContractTests(
    unittest.TestCase
):
    def manifest(self):
        self.assertTrue(
            MANIFEST_PATH.is_file(),
            "CLAIM named-open manifest must be implemented",
        )
        return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_green_01_exact_additive_products_are_present(self):
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual([], missing)

    def test_green_02_auth_red_and_protected_pins_are_exact(self):
        actual = {
            path: file_sha256(ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, actual)
        self.assertEqual(9, len(actual))

    def test_green_03_runtime_exposes_exact_closed_world_claim_surface(self):
        self.assertEqual(
            NAMED_REQUEST_FIELDS,
            set(claim_gate.NAMED_REQUEST_FIELDS),
        )
        self.assertEqual(18, len(claim_gate.NAMED_REQUEST_FIELDS))
        self.assertEqual(
            {
                "PATH_A_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE",
                "PATH_A_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE",
            },
            set(claim_gate.CLAIM_REFERENCE_PAIRS),
        )
        self.assertEqual(
            "PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1",
            claim_gate.NAMED_TARGET_ID,
        )
        self.assertEqual(
            "OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM",
            claim_gate.PB_SI_008_STATUS,
        )

    def test_green_04_manifest_preserves_combined_status_and_boundaries(self):
        manifest = self.manifest()
        self.assertEqual(
            "SI008_OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM",
            manifest["status"],
        )
        self.assertEqual(
            "OPENED_FOR_NAMED_TARGET_ONLY_EVIDENCE_AND_CLAIM",
            manifest["pb_si_008_status"],
        )
        self.assertEqual(
            "NAMED_TARGET_CLAIM_CANDIDACY_ONLY_NO_MINT_NO_ADMISSION",
            manifest["part_b_status"],
        )
        self.assertEqual(
            ["EVIDENCE", "CLAIM"],
            manifest["allowed_promotion_targets"],
        )
        self.assertEqual(
            ["AUTHORITY", "PASS_CONDITION"],
            manifest["denied_promotion_targets"],
        )
        self.assertEqual(
            "ALLOW_NAMED_CLAIM_CANDIDACY_ONLY",
            manifest["qualified_claim_decision"],
        )
        for field in (
            "allow_is_mint",
            "allow_is_admission",
            "allow_is_part_b_pass",
            "allow_is_write_authority",
            "part_b_evidence_authority",
            "part_b_claim_authority",
            "part_b_authority_grant",
            "part_b_pass_condition_authority",
            "path_b_write_authority",
            "production_registration_enabled",
            "mint_authority",
            "admission_authority",
            "kernel_or_e_case_write_authority",
            "certificate_authority",
        ):
            with self.subTest(field=field):
                self.assertFalse(manifest[field])
        self.assertTrue(
            manifest["named_claim_candidacy_classification_authority"]
        )
        self.assertEqual("NONE", manifest["stop_authority"])
        self.assertEqual(HARD_BAN, manifest["hard_ban"])

    def test_green_05_manifest_pins_runtime_and_exact_pairs(self):
        manifest = self.manifest()
        self.assertEqual(
            EXPECTED_REFERENCE_PAIRS,
            manifest["qualifying_claim_reference_pairs"],
        )
        self.assertEqual(
            file_sha256(RUNTIME_PATH),
            manifest["pins"]["claim_successor_runtime_sha256"],
        )
        for path, expected in PROTECTED_PINS.items():
            with self.subTest(path=path):
                self.assertEqual(
                    expected,
                    manifest["pins"]["protected"][path],
                )

    def test_green_06_manifest_preserves_delegation_without_widening(self):
        manifest = self.manifest()
        self.assertEqual(
            "RETURN_EXISTING_EVIDENCE_GATE_RECORD_UNMODIFIED",
            manifest["evidence_compatibility"]["exact_evidence_requests"],
        )
        self.assertEqual(
            "RETURN_PROTECTED_NOT_OPENED_RECORD_UNMODIFIED",
            manifest["legacy_compatibility"]["exact_four_field_requests"],
        )
        self.assertFalse(
            manifest["caller_and_composition"]["caller_widened_to_claim"]
        )
        self.assertFalse(
            manifest["caller_and_composition"][
                "composition_widened_to_claim"
            ]
        )
        self.assertFalse(manifest["named_request"]["wildcard"])
        self.assertFalse(manifest["named_request"]["fallback"])
        self.assertFalse(manifest["named_request"]["package_dereference"])
        self.assertFalse(
            manifest["named_request"]["validation_receipt_dereference"]
        )

    def test_green_07_runtime_has_no_io_or_dynamic_execution_capability(self):
        tree = ast.parse(RUNTIME_PATH.read_text(encoding="utf-8"))
        forbidden_import_roots = {
            "http",
            "pathlib",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_calls = {"open", "eval", "exec", "__import__"}
        forbidden_attributes = {
            "open",
            "read_bytes",
            "read_text",
            "write_bytes",
            "write_text",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(
                    all(
                        alias.name.split(".")[0]
                        not in forbidden_import_roots
                        for alias in node.names
                    )
                )
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn(
                    (node.module or "").split(".")[0],
                    forbidden_import_roots,
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, forbidden_calls)
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(
                        node.func.attr,
                        forbidden_attributes,
                    )

    def test_green_08_hard_ban_and_registration_boundary_are_explicit(self):
        for artifact in PRODUCT_ARTIFACTS:
            with self.subTest(artifact=str(artifact.relative_to(ROOT))):
                self.assertTrue(
                    artifact.is_file(),
                    f"missing GREEN artifact: {artifact.relative_to(ROOT)}",
                )
                self.assertIn(
                    HARD_BAN,
                    artifact.read_text(encoding="utf-8"),
                )
        self.assertEqual(HARD_BAN, claim_gate.HARD_BAN)
        self.assertFalse(claim_gate.PRODUCTION_REGISTRATION_ENABLED)


if __name__ == "__main__":
    unittest.main()
