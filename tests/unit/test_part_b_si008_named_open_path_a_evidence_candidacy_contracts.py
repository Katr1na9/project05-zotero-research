from __future__ import annotations

import ast
import hashlib
from pathlib import Path
import unittest

import yaml

from src.scope import (
    part_b_si008_named_open_path_a_evidence_candidacy as named_gate,
)


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_si008_named_open_path_a_evidence_candidacy.py"
)
MANIFEST_PATH = (
    ROOT
    / "configs"
    / "part-b-si008-named-open-path-a-evidence-candidacy-manifest-v0.8.yaml"
)
CONTRACT_PATH = (
    ROOT
    / "contracts"
    / "part-b-si008-named-open-path-a-evidence-candidacy-v0.8.md"
)
PRODUCT_ARTIFACTS = (RUNTIME_PATH, MANIFEST_PATH, CONTRACT_PATH)
HARD_BAN = "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."
PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-pb-si008-named-open-owner-go-authorization-v0.1-20260727.json": (
        "521735a220c3af9be92be5b4e036b1584bddaf1b85249be6410d8ea0dae3bc2f"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-evidence-candidacy-red-design-v0.1-20260727.json": (
        "9ce860f4388ed0341fee47ba738a17870ef191bc7f62ac2082bb3d6906754eb9"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-pb-si008-named-open-red-review-packet-v0.1-20260727.json": (
        "f2a82e65f1f095265756309ecdc2b376ceb3217fda80c95ec3e5d474d0b6550a"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-evidence-candidacy-red-owner-acceptance-v0.1-20260727.json": (
        "895646551b15e678e92502e0ebb7c93f59bf1f7fb395c28ff47a72e9f6ef6593"
    ),
    "src/scope/part_b_si008_dual_track_deny.py": (
        "b43c647d45a4aa19722ca8c501a6cb41f0b1add1f4e501e9684033797c7b12fb"
    ),
    "configs/part-b-si008-dual-track-deny-manifest-v0.8.yaml": (
        "a3355c292e1a120fdc12adb32ccced310525f284751019551618d04bf9a023e9"
    ),
    "src/compiler/llm/claim_id_mainline_handoff.py": (
        "304000b03ad273a26d864e2567c4b3f20ce06bdc5199387d57d46bc64152c35a"
    ),
}
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PartBSI008NamedOpenEvidenceCandidacyContractTests(
    unittest.TestCase
):
    def test_green_01_exact_additive_products_are_present(self):
        missing = [
            str(path.relative_to(ROOT))
            for path in PRODUCT_ARTIFACTS
            if not path.is_file()
        ]
        self.assertEqual(missing, [])

    def test_green_02_owner_red_and_current_gate_pins_are_exact(self):
        actual = {
            path: file_sha256(ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, actual)
        self.assertEqual(7, len(PROTECTED_PINS))
        self.assertEqual(
            "a71358d11a0495f0c6457f9f59061fd982dfda7c3d1921e2f62c7b39cbcaea29",
            file_sha256(RUNTIME_PATH),
        )

    def test_green_03_runtime_declares_exact_closed_world_surface(self):
        self.assertEqual(
            NAMED_REQUEST_FIELDS,
            set(named_gate.NAMED_REQUEST_FIELDS),
        )
        self.assertEqual(18, len(named_gate.NAMED_REQUEST_FIELDS))
        self.assertEqual(
            {
                "PATH_A_EVIDENCE_CLAIM_IR_V0_1_STRUCTURAL_REFERENCE",
                "PATH_A_EVIDENCE_CLAIM_IR_V0_2_STRUCTURAL_REFERENCE",
            },
            set(named_gate.REFERENCE_PAIRS),
        )
        self.assertEqual(
            "PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1",
            named_gate.NAMED_TARGET_ID,
        )

    def test_green_04_manifest_preserves_named_and_adjacent_boundaries(self):
        manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            "SI008_OPENED_FOR_NAMED_TARGET_ONLY",
            manifest["status"],
        )
        self.assertEqual(
            "OPENED_FOR_NAMED_TARGET_ONLY",
            manifest["pb_si_008_status"],
        )
        self.assertEqual(
            "NAMED_TARGET_EVIDENCE_CANDIDACY_ONLY_NO_ADMISSION",
            manifest["part_b_status"],
        )
        self.assertEqual(["EVIDENCE"], manifest["allowed_promotion_targets"])
        self.assertEqual(
            ["CLAIM", "AUTHORITY", "PASS_CONDITION"],
            manifest["denied_promotion_targets"],
        )
        self.assertFalse(manifest["allow_is_admission"])
        self.assertFalse(manifest["allow_is_part_b_pass"])
        self.assertFalse(manifest["part_b_evidence_authority"])
        self.assertTrue(
            manifest[
                "named_evidence_candidacy_classification_authority"
            ]
        )
        self.assertFalse(manifest["production_registration_enabled"])
        self.assertEqual("DENY", manifest["holdout_release"])
        self.assertEqual("DENY", manifest["pb_si_006_download"])
        self.assertEqual("NOT_ESTABLISHED", manifest["pb_b5_execution"])
        self.assertEqual("NONE", manifest["stop_authority"])
        self.assertEqual(HARD_BAN, manifest["hard_ban"])
        self.assertEqual(
            file_sha256(RUNTIME_PATH),
            manifest["pins"]["additive_successor_runtime_sha256"],
        )

    def test_green_05_contract_is_boundary_document_not_authority_grant(self):
        text = CONTRACT_PATH.read_text(encoding="utf-8")
        for phrase in (
            HARD_BAN,
            "not a new admission, write, production-registration",
            "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY",
            "There is no wildcard or fallback.",
            "Paths and URIs are not request fields.",
            "stop_authority=NONE",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_green_06_runtime_has_no_dereference_or_network_capability(self):
        source = RUNTIME_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {
            "http",
            "pathlib",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_calls = {
            "open",
            "eval",
            "exec",
            "__import__",
        }
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
        self.assertIn("evaluate_dual_track_request", source)

    def test_green_07_hard_ban_and_non_elevation_are_explicit(self):
        green_artifacts = (
            RUNTIME_PATH,
            MANIFEST_PATH,
            CONTRACT_PATH,
            Path(__file__).resolve(),
            ROOT
            / "tests"
            / "unit"
            / "test_part_b_si008_named_open_path_a_evidence_candidacy_runtime.py",
            ROOT
            / "docs"
            / "kernel"
            / "kernel-v0.8-pb-si008-named-open-path-a-evidence-candidacy-green-design-v0.1-20260727.json",
            ROOT
            / "docs"
            / "llm-editor"
            / "llm-editor-v0.8-l2-kernel-owner-pb-si008-named-open-green-review-packet-v0.1-20260727.json",
        )
        for artifact in green_artifacts:
            with self.subTest(artifact=str(artifact.relative_to(ROOT))):
                self.assertIn(
                    HARD_BAN,
                    artifact.read_text(encoding="utf-8"),
                )
        self.assertEqual(HARD_BAN, named_gate.HARD_BAN)
        self.assertEqual(
            "OPENED_FOR_NAMED_TARGET_ONLY",
            named_gate.PB_SI_008_STATUS,
        )
        self.assertEqual(
            "NAMED_TARGET_EVIDENCE_CANDIDACY_ONLY_NO_ADMISSION",
            named_gate.PART_B_STATUS,
        )
        handoff = (
            ROOT
            / "src"
            / "compiler"
            / "llm"
            / "claim_id_mainline_handoff.py"
        ).read_text(encoding="utf-8")
        self.assertIn("PRODUCTION_REGISTRATION_ENABLED = False", handoff)


if __name__ == "__main__":
    unittest.main()
