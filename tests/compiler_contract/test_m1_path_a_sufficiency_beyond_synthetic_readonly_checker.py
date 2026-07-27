import ast
import copy
import hashlib
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_evidence_sufficiency_evaluator as a2  # noqa: E402
from compiler.llm import (  # noqa: E402
    m1_path_a_sufficiency_beyond_synthetic_readonly_checker as checker,
)


PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-part-b-elevation-no-go-and-next-slices-authorization-v0.1-20260727.json": (
        "08f491fd3a0806eca4078455fb2f7558637710d6e3bcd71ce85599d2e2479220"
    ),
    "docs/kernel/kernel-v0.8-part-b-reopen-scope-blockers-go-nogo-readonly-v0.1-20260727.json": (
        "09a1a4d68570f9898eafa5d88d06fdbae2c75c751bd5dcf6f32665a97fd34cf1"
    ),
    "docs/kernel/kernel-v0.8-path-a-to-part-b-dual-track-readonly-alignment-v0.1-20260727.json": (
        "beded9f5d903110a25661a5250412590c36631985e59e5ceea888131e0a8a84f"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-path-a-part-b-readonly-alignment-review-packet-v0.1-20260727.json": (
        "561d53923d6ca4ed222e46d5fdfadd6abc82c565b1f7d743c1239d35ac909580"
    ),
    "docs/kernel/kernel-v0.8-path-a-part-b-readonly-alignment-owner-acceptance-v0.1-20260727.json": (
        "59a39938682968376b1b64089b4b1b8e43b949df19919585cb3e90eba7ae6d96"
    ),
    checker.RED_DESIGN_PATH: checker.RED_DESIGN_SHA256,
    checker.RED_REVIEW_PACKET_PATH: checker.RED_REVIEW_PACKET_SHA256,
    checker.RED_ACCEPTANCE_PATH: checker.RED_ACCEPTANCE_SHA256,
    a2.EVALUATOR_IMPLEMENTATION_PATH: checker.A2_EVALUATOR_SHA256,
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


HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or Part B elevation."
)
def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class M1PathASufficiencyBeyondSyntheticReadonlyCheckerTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.catalog = a2.package_binding_catalog(REPO_ROOT)
        cls.catalog_ids = [entry["binding_id"] for entry in cls.catalog]

    def request(self, **overrides):
        value = {
            "request_id": "slice2-checker-facing-request-001",
            "surface_id": checker.SURFACE_ID,
            "catalog_version": checker.CATALOG_VERSION,
            "ordered_binding_ids": copy.deepcopy(self.catalog_ids),
            "requested_review_scope": checker.READONLY_REVIEW_SCOPE,
            "authority_request": checker.TEST_ONLY_AUTHORITY_REQUEST,
            "audit_log_binding_request": False,
        }
        value.update(overrides)
        return value

    def evaluate(self, request):
        return checker.evaluate_checker_facing_sufficiency_decision_robustness(
            request,
            repo_root=REPO_ROOT,
        )

    def test_exact_six_catalog_is_conditional_and_calls_a2(self):
        request = self.request()
        request_before = copy.deepcopy(request)
        with mock.patch.object(
            a2,
            "evaluate_evidence_sufficiency_for_readonly_review",
            wraps=a2.evaluate_evidence_sufficiency_for_readonly_review,
        ) as delegated:
            first = self.evaluate(request)
        second = self.evaluate(copy.deepcopy(request))

        self.assertGreaterEqual(delegated.call_count, 1)
        self.assertEqual(first, second)
        self.assertEqual(request_before, request)
        self.assertEqual(
            "exact_six_catalog_readonly_review",
            first["decision_case"],
        )
        self.assertEqual(
            "CONDITIONAL_SUFFICIENT_DECLARED_SCOPE_ONLY",
            first["sufficiency_decision"],
        )
        self.assertEqual(
            "ACCEPT_CONDITIONAL_FOR_READONLY_REVIEW_ONLY",
            first["checker_decision"],
        )
        self._assert_common_boundary(first)

    def test_missing_binding_fails_despite_structural_catalog_membership(self):
        record = self.evaluate(
            self.request(ordered_binding_ids=self.catalog_ids[:-1])
        )
        self.assertEqual(
            "missing_required_binding_or_field_set",
            record["decision_case"],
        )
        self.assertEqual(
            "FAIL_INSUFFICIENT_EVIDENCE",
            record["sufficiency_decision"],
        )
        self.assertEqual("REJECT_FAIL_CLOSED", record["checker_decision"])
        self._assert_common_boundary(record)

    def test_cti_observed_and_derived_laundering_are_denied(self):
        for scope in (
            checker.CTI_OBSERVED_LAUNDERING_SCOPE,
            checker.CTI_DERIVED_LAUNDERING_SCOPE,
        ):
            with self.subTest(scope=scope):
                record = self.evaluate(
                    self.request(
                        ordered_binding_ids=[],
                        requested_review_scope=scope,
                    )
                )
                self.assertEqual(
                    "cti_modality_laundering",
                    record["decision_case"],
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

    def test_unknown_binding_or_modality_abstains_without_partial_result(self):
        cases = (
            self.request(
                ordered_binding_ids=[
                    *self.catalog_ids[:-1],
                    "unknown_binding",
                ]
            ),
            self.request(
                ordered_binding_ids=[],
                requested_review_scope="UNRECOGNIZED_MODALITY_REVIEW",
            ),
            self.request(
                ordered_binding_ids=list(reversed(self.catalog_ids))
            ),
            self.request(
                ordered_binding_ids=[
                    self.catalog_ids[0],
                    self.catalog_ids[0],
                ]
            ),
        )
        for request in cases:
            with self.subTest(request=request):
                record = self.evaluate(request)
                self.assertEqual(
                    "unknown_binding_or_unknown_modality",
                    record["decision_case"],
                )
                self.assertEqual(
                    "ABSTAIN_UNRESOLVED_EVIDENCE",
                    record["sufficiency_decision"],
                )
                self.assertEqual(
                    "ABSTAIN_FAIL_CLOSED",
                    record["checker_decision"],
                )
                self.assertFalse(record["partial_result"])
                self._assert_common_boundary(record)

    def test_audit_log_binding_is_denied_and_catalog_stays_six(self):
        record = self.evaluate(
            self.request(audit_log_binding_request=True)
        )
        self.assertEqual(
            "audit_log_binding_without_named_sub_authority",
            record["decision_case"],
        )
        self.assertEqual(
            "DENY_UNKNOWN_BINDING",
            record["sufficiency_decision"],
        )
        self.assertEqual("DENY_INVALID_INPUT", record["checker_decision"])
        self.assertEqual(6, record["catalog"]["count"])
        self.assertFalse(record["catalog"]["extended"])
        self.assertEqual(
            "DENY_UNKNOWN_BINDING",
            record["catalog"]["audit_log_binding"],
        )
        self._assert_common_boundary(record)

    def test_every_elevation_request_is_denied(self):
        for authority_request in sorted(checker._ELEVATION_REQUESTS):
            with self.subTest(authority_request=authority_request):
                record = self.evaluate(
                    self.request(authority_request=authority_request)
                )
                self.assertEqual(
                    "authority_elevation_request",
                    record["decision_case"],
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

    def test_request_is_closed_world_and_exact_surface_catalog(self):
        unknown_field = self.request()
        unknown_field["extra"] = True
        cases = (
            ("request_shape", unknown_field),
            ("request_shape", {"request_id": "only-one-field"}),
            ("surface_id", self.request(surface_id="other_surface")),
            ("catalog_version", self.request(catalog_version="wildcard")),
            (
                "audit_log_binding_request",
                self.request(audit_log_binding_request="false"),
            ),
        )
        for expected_code, request in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(
                    checker.PathAReadonlyCheckerError
                ) as context:
                    self.evaluate(request)
                self.assertEqual(expected_code, context.exception.code)

    def test_helper_has_no_direct_file_or_network_io(self):
        source_path = (
            REPO_ROOT
            / "src"
            / "compiler"
            / "llm"
            / "m1_path_a_sufficiency_beyond_synthetic_readonly_checker.py"
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        forbidden_import_roots = {
            "http",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_call_names = {"open", "exec", "eval", "__import__"}
        forbidden_attrs = {
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
                    self.assertNotIn(
                        node.func.id,
                        forbidden_call_names,
                    )
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(node.func.attr, forbidden_attrs)

    def test_protected_pins_remain_exact_before_and_after_evaluation(self):
        before = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, before)
        self.evaluate(self.request())
        after = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, after)
        self.assertEqual(12, len(PROTECTED_PINS))
        handoff = (
            REPO_ROOT
            / "src"
            / "compiler"
            / "llm"
            / "claim_id_mainline_handoff.py"
        ).read_text(encoding="utf-8")
        self.assertIn("PRODUCTION_REGISTRATION_ENABLED = False", handoff)

    def _assert_common_boundary(self, record):
        self.assertEqual(checker.RECORD_CLASS, record["record_class"])
        self.assertEqual(checker.SCOPE_ID, record["scope_id"])
        self.assertTrue(record["sufficiency_decision"])
        self.assertTrue(record["checker_decision"])
        self.assertEqual(
            checker.NO_AUTHORITY_ELEVATION,
            record["required_marker"],
        )
        self.assertIn(
            checker.NO_AUTHORITY_ELEVATION,
            record["basis_codes"],
        )
        self.assertEqual("NO_GO", record["part_b_elevation"])
        self.assertEqual("NOT_OPENED", record["pb_si_008"])
        self.assertFalse(record["production_registration_enabled"])
        self.assertFalse(record["partial_result"])
        self.assertEqual(checker.HARD_BAN, record["hard_ban"])
        self.assertEqual(HARD_BAN, record["hard_ban"])
        self.assertTrue(record["delegated_a2_evaluation"]["called"])
        self.assertTrue(
            all(
                value is False
                for value in record["explicit_non_authorizations"].values()
            )
        )
        ceiling = record["scientific_ceiling"]
        self.assertTrue(
            ceiling["evidence_remains_synthetic_declared_scope"]
        )
        self.assertFalse(ceiling["external_validity_established"])
        self.assertFalse(ceiling["real_or_production_checker_connected"])


if __name__ == "__main__":
    unittest.main()
