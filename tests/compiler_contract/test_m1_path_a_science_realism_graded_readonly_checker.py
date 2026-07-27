import ast
import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.llm import (  # noqa: E402
        m1_path_a_science_realism_graded_readonly_checker as realism,
    )
except ImportError:
    realism = None

from compiler.llm import (  # noqa: E402
    m1_path_a_sufficiency_beyond_synthetic_readonly_checker as slice2,
)


FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "m1_path_a_science_realism_graded_fixture_v0.1.json"
)
RUNTIME_PATH = (
    REPO_ROOT
    / "src"
    / "compiler"
    / "llm"
    / "m1_path_a_science_realism_graded_readonly_checker.py"
)
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
CASE_FIELDS = {
    "case_id",
    "suite_version",
    "declared_origin",
    "surface_id",
    "catalog_version",
    "realism_grade",
    "distortion_id",
    "ordered_binding_ids",
    "requested_review_scope",
    "authority_request",
    "audit_log_binding_request",
}
OUTPUT_FIELDS = {
    "record_class",
    "scope_id",
    "case_id",
    "suite_version",
    "declared_origin",
    "realism_grade",
    "distortion_id",
    "delegated_decision_case",
    "sufficiency_decision",
    "checker_decision",
    "basis_codes",
    "partial_result",
    "scientific_ceiling",
    "explicit_non_authorizations",
    "hard_ban",
    "record_hash",
}
PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-path-a-science-realism-graded-fixture-authorization-v0.1-20260727.json": (
        "dc680b50512eb3c7f35c4a41b0aea258b3cb665afe4febd26b497deee5e6b001"
    ),
    "docs/kernel/kernel-v0.8-path-a-science-realism-graded-fixture-red-design-v0.1-20260727.json": (
        "1a2a98b701a3a3cd2c3a4e8448ea0be8f026bae4c257cdd0ae3a3c92551321d4"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-path-a-science-realism-graded-fixture-red-review-packet-v0.1-20260727.json": (
        "9a067c148715acdf0d85f8fc6a01518cd11b629a913141cfe140a1750272b744"
    ),
    "docs/kernel/kernel-v0.8-slice2-authority-base-pin-hygiene-authorization-v0.1-20260727.json": (
        "e9cfee2b2f99d2782b0a0eb61d3e3c7f1d27852dbe6bb42aa7d9708594592f1c"
    ),
    "src/compiler/llm/m1_path_a_sufficiency_beyond_synthetic_readonly_checker.py": (
        "508b875026ae80f13728bd899b0da7bc23ba3c9b147bc11aa69c0ba81311a0c0"
    ),
    "tests/compiler_contract/test_m1_path_a_sufficiency_beyond_synthetic_readonly_checker.py": (
        "d4685e641a572f50c3b5f699001e1b2044084cf783e021d629043b4b6ac916f2"
    ),
    "src/compiler/llm/m1_evidence_sufficiency_evaluator.py": (
        "ad4e5af8dd9af0012f5174b14822ce9146a6d0f491c07881b5b401d85d62e78f"
    ),
    "src/scope/part_b_si008_named_open_path_a_evidence_candidacy.py": (
        "a71358d11a0495f0c6457f9f59061fd982dfda7c3d1921e2f62c7b39cbcaea29"
    ),
    "configs/part-b-si008-named-open-path-a-evidence-candidacy-manifest-v0.8.yaml": (
        "aa01c95f00c7757ae6adea046f2cee0fb4bdee7a404ea5ce40701aad61214ff8"
    ),
    "src/scope/part_b_si008_path_a_named_open_caller_wiring.py": (
        "64fcc81ff7ae6f61ae58d6a8e5d9bb602a5c6f307feef1a25497048643d11ecf"
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


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_only_authority() -> dict:
    return {
        "mode": "TEST_ONLY_READONLY",
        "allow_write": False,
        "allow_download": False,
        "allow_registry": False,
        "allow_authority_elevation": False,
    }


class M1PathAScienceRealismGradedProductPresenceTests(
    unittest.TestCase
):
    def test_green_00_runtime_and_fixture_are_present(self):
        self.assertTrue(RUNTIME_PATH.is_file())
        self.assertTrue(FIXTURE_PATH.is_file())


@unittest.skipIf(
    realism is None or not FIXTURE_PATH.is_file(),
    "realism-graded runtime and fixture are not implemented yet",
)
class M1PathAScienceRealismGradedReadonlyCheckerTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_json(FIXTURE_PATH)
        cls.cases = {
            entry["case_spec"]["case_id"]: entry
            for entry in cls.suite["cases"]
        }

    def evaluate(self, case_spec):
        return realism.evaluate_realism_graded_synthetic_case(
            copy.deepcopy(case_spec),
            test_only_authority=test_only_authority(),
        )

    def test_green_01_fixture_is_closed_declared_synthetic_suite(self):
        self.assertEqual(
            {
                "fixture_suite_id",
                "suite_version",
                "declared_origin",
                "surface_id",
                "catalog_version",
                "hard_ban",
                "test_only",
                "cases",
            },
            set(self.suite),
        )
        self.assertEqual(
            "PATH_A_REALISM_GRADED_SYNTHETIC_DISTORTION_V0_1",
            self.suite["suite_version"],
        )
        self.assertEqual(
            "SYNTHETIC_DECLARED_SCOPE",
            self.suite["declared_origin"],
        )
        self.assertEqual(HARD_BAN, self.suite["hard_ban"])
        self.assertTrue(self.suite["test_only"])
        self.assertEqual(7, len(self.suite["cases"]))
        for entry in self.suite["cases"]:
            with self.subTest(case_id=entry["case_spec"]["case_id"]):
                self.assertEqual(
                    {"case_spec", "expected"},
                    set(entry),
                )
                self.assertEqual(CASE_FIELDS, set(entry["case_spec"]))
                self.assertEqual(
                    self.suite["suite_version"],
                    entry["case_spec"]["suite_version"],
                )
                self.assertEqual(
                    self.suite["surface_id"],
                    entry["case_spec"]["surface_id"],
                )
                self.assertEqual(
                    self.suite["catalog_version"],
                    entry["case_spec"]["catalog_version"],
                )

    def test_green_02_rg0_through_rg4_delegated_cases_match_matrix(self):
        delegated_case_ids = (
            "RG0-EXACT-SIX-CONTROL",
            "RG1-MISSING-CRITICAL-MODALITY",
            "RG2-AMBIGUOUS-BINDINGS",
            "RG3-CTI-MODALITY-LAUNDERING",
            "RG4-AUTHORITY-ELEVATION",
        )
        for case_id in delegated_case_ids:
            entry = self.cases[case_id]
            with self.subTest(case_id=case_id):
                with mock.patch.object(
                    realism.slice2,
                    "evaluate_checker_facing_sufficiency_decision_robustness",
                    wraps=(
                        slice2
                        .evaluate_checker_facing_sufficiency_decision_robustness
                    ),
                ) as delegated:
                    record = self.evaluate(entry["case_spec"])
                delegated.assert_called_once()
                expected = entry["expected"]
                self.assertEqual(
                    expected["delegated_decision_case"],
                    record["delegated_decision_case"],
                )
                self.assertEqual(
                    expected["sufficiency_decision"],
                    record["sufficiency_decision"],
                )
                self.assertEqual(
                    expected["checker_decision"],
                    record["checker_decision"],
                )
                self._assert_common_boundary(record)

    def test_green_03_origin_misrepresentation_denies_without_delegate(self):
        entry = self.cases["RG4-ORIGIN-MISREPRESENTATION"]
        with mock.patch.object(
            realism.slice2,
            "evaluate_checker_facing_sufficiency_decision_robustness",
        ) as delegated:
            record = self.evaluate(entry["case_spec"])
        delegated.assert_not_called()
        self.assertEqual(
            "NOT_DELEGATED_ORIGIN_MISREPRESENTATION",
            record["delegated_decision_case"],
        )
        self.assertEqual(
            "DENY_ORIGIN_MISREPRESENTATION",
            record["sufficiency_decision"],
        )
        self.assertEqual(
            "DENY_INVALID_INPUT",
            record["checker_decision"],
        )
        self.assertIn(
            "NON_SYNTHETIC_EXTERNAL_VALIDITY_NOT_ESTABLISHED",
            record["basis_codes"],
        )
        self.assertFalse(
            record["scientific_ceiling"][
                "non_synthetic_external_validity_established"
            ]
        )
        self._assert_common_boundary(record)

    def test_green_04_unknown_case_and_shape_fail_before_delegate(self):
        unknown = self.cases["UNKNOWN-CASE-OR-GRADE"]["case_spec"]
        missing = copy.deepcopy(self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"])
        missing.pop("distortion_id")
        extra = copy.deepcopy(self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"])
        extra["path"] = "C:/forbidden"
        wildcard = copy.deepcopy(
            self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"]
        )
        wildcard["realism_grade"] = "*"
        for case_spec in (unknown, missing, extra, wildcard, None):
            with self.subTest(case_spec=case_spec):
                with mock.patch.object(
                    realism.slice2,
                    "evaluate_checker_facing_sufficiency_decision_robustness",
                ) as delegated:
                    with self.assertRaises(
                        realism.PathARealismGradedError
                    ) as context:
                        self.evaluate(case_spec)
                delegated.assert_not_called()
                self.assertIn(
                    context.exception.code,
                    {
                        "case_type",
                        "case_shape",
                        "case_enum",
                    },
                )

    def test_green_05_test_only_authority_fails_before_delegate(self):
        case_spec = self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"]
        authorities = (
            None,
            {},
            {**test_only_authority(), "allow_write": True},
            {**test_only_authority(), "unknown": False},
        )
        for authority in authorities:
            with self.subTest(authority=authority):
                with mock.patch.object(
                    realism.slice2,
                    "evaluate_checker_facing_sufficiency_decision_robustness",
                ) as delegated:
                    with self.assertRaises(
                        realism.PathARealismGradedError
                    ) as context:
                        realism.evaluate_realism_graded_synthetic_case(
                            copy.deepcopy(case_spec),
                            test_only_authority=authority,
                        )
                delegated.assert_not_called()
                self.assertEqual(
                    "test_only_authority",
                    context.exception.code,
                )

    def test_green_06_constants_and_no_audit_catalog_extension(self):
        base = self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"]
        cases = (
            {**base, "suite_version": "wildcard"},
            {**base, "surface_id": "other_surface"},
            {**base, "catalog_version": "other_catalog"},
            {**base, "audit_log_binding_request": True},
            {**base, "declared_origin": "NON_SYNTHETIC_RECORDED"},
        )
        for case_spec in cases:
            with self.subTest(case_spec=case_spec):
                with self.assertRaises(
                    realism.PathARealismGradedError
                ):
                    self.evaluate(case_spec)

    def test_green_07_cti_observed_and_derived_both_deny(self):
        base = copy.deepcopy(
            self.cases["RG3-CTI-MODALITY-LAUNDERING"]["case_spec"]
        )
        for review_scope in (
            slice2.CTI_OBSERVED_LAUNDERING_SCOPE,
            slice2.CTI_DERIVED_LAUNDERING_SCOPE,
        ):
            with self.subTest(review_scope=review_scope):
                record = self.evaluate(
                    {
                        **base,
                        "requested_review_scope": review_scope,
                    }
                )
                self.assertEqual(
                    "DENY_INVALID_OR_LAUNDERED_INPUT",
                    record["sufficiency_decision"],
                )
                self.assertEqual(
                    "DENY_INVALID_INPUT",
                    record["checker_decision"],
                )
                self._assert_common_boundary(record)

    def test_green_08_every_elevation_request_denies(self):
        base = copy.deepcopy(
            self.cases["RG4-AUTHORITY-ELEVATION"]["case_spec"]
        )
        for authority_request in sorted(slice2._ELEVATION_REQUESTS):
            with self.subTest(authority_request=authority_request):
                record = self.evaluate(
                    {
                        **base,
                        "authority_request": authority_request,
                    }
                )
                self.assertEqual(
                    "DENY_AUTHORITY_ELEVATION_REQUEST",
                    record["sufficiency_decision"],
                )
                self.assertEqual(
                    "DENY_INVALID_AUTHORITY_REQUEST",
                    record["checker_decision"],
                )
                self._assert_common_boundary(record)

    def test_green_09_same_case_same_record_hash_without_mutation(self):
        case_spec = copy.deepcopy(
            self.cases["RG2-AMBIGUOUS-BINDINGS"]["case_spec"]
        )
        before = copy.deepcopy(case_spec)
        first = self.evaluate(case_spec)
        second = self.evaluate(copy.deepcopy(case_spec))
        self.assertEqual(first, second)
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual(before, case_spec)
        payload = {
            key: value
            for key, value in first.items()
            if key != "record_hash"
        }
        self.assertEqual(
            realism.canonical_json_sha256(payload),
            first["record_hash"],
        )

    def test_green_10_output_boundary_residual_and_hard_ban(self):
        for case_id in (
            "RG0-EXACT-SIX-CONTROL",
            "RG4-ORIGIN-MISREPRESENTATION",
        ):
            with self.subTest(case_id=case_id):
                record = self.evaluate(self.cases[case_id]["case_spec"])
                self.assertEqual(OUTPUT_FIELDS, set(record))
                self.assertEqual(HARD_BAN, record["hard_ban"])
                self.assertEqual(
                    "SYNTHETIC_DECLARED_SCOPE_ONLY",
                    record["scientific_ceiling"]["ceiling"],
                )
                self.assertTrue(
                    record["scientific_ceiling"][
                        "evidence_origin_remains_synthetic_declared_scope"
                    ]
                )
                self.assertFalse(
                    record["scientific_ceiling"][
                        "non_synthetic_external_validity_established"
                    ]
                )
                self.assertTrue(
                    all(
                        value is False
                        for value in record[
                            "explicit_non_authorizations"
                        ].values()
                    )
                )
                self._assert_common_boundary(record)

    def test_green_11_protected_pins_and_registration_zero_drift(self):
        before = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, before)
        self.assertEqual(13, len(PROTECTED_PINS))
        self.evaluate(self.cases["RG0-EXACT-SIX-CONTROL"]["case_spec"])
        after = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, after)
        self.assertFalse(realism.PRODUCTION_REGISTRATION_ENABLED)
        handoff = (
            REPO_ROOT
            / "src"
            / "compiler"
            / "llm"
            / "claim_id_mainline_handoff.py"
        ).read_text(encoding="utf-8")
        self.assertIn("PRODUCTION_REGISTRATION_ENABLED = False", handoff)

    def test_green_12_runtime_has_no_io_or_authority_capability(self):
        source = RUNTIME_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_roots = {
            "http",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_call_names = {
            "__import__",
            "eval",
            "exec",
            "open",
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
                for alias in node.names:
                    self.assertNotIn(
                        alias.name.split(".", 1)[0],
                        forbidden_import_roots,
                    )
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn(
                    (node.module or "").split(".", 1)[0],
                    forbidden_import_roots,
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, forbidden_call_names)
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(
                        node.func.attr,
                        forbidden_attributes,
                    )
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)
        self.assertIn(HARD_BAN, source)

    def _assert_common_boundary(self, record):
        self.assertEqual(
            "path_a_realism_graded_synthetic_readonly_decision_record",
            record["record_class"],
        )
        self.assertEqual(
            "PATH_A_REALISM_GRADED_SYNTHETIC_DISTORTION_SUITE_V0_1",
            record["scope_id"],
        )
        self.assertFalse(record["partial_result"])
        self.assertIn("NO_AUTHORITY_ELEVATION", record["basis_codes"])
        self.assertEqual(HARD_BAN, record["hard_ban"])
        self.assertTrue(record["record_hash"])
        self.assertFalse(
            record["scientific_ceiling"][
                "non_synthetic_external_validity_established"
            ]
        )
        self.assertTrue(
            all(
                value is False
                for value in record["explicit_non_authorizations"].values()
            )
        )


if __name__ == "__main__":
    unittest.main()
