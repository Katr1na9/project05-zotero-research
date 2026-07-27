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
        m1_path_a_named_open_composition_readonly as composition,
    )
except ImportError:
    composition = None

from compiler.llm import (  # noqa: E402
    m1_path_a_science_realism_graded_readonly_checker as realism,
)
from src.scope import (  # noqa: E402
    part_b_si008_path_a_named_open_caller_wiring as caller,
)


FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "compiler_contract"
    / "fixtures"
    / "m1_path_a_named_open_composition_v0.1.json"
)
RUNTIME_PATH = (
    REPO_ROOT
    / "src"
    / "compiler"
    / "llm"
    / "m1_path_a_named_open_composition_readonly.py"
)
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
COMPOSITION_INPUT_FIELDS = {
    "composition_case_id",
    "composition_contract_version",
    "realism_fixture_id",
    "realism_fixture_sha256",
    "realism_case_id",
    "realism_case_spec",
    "realism_case_spec_sha256",
    "named_open_fixture_id",
    "named_open_fixture_sha256",
    "caller_input_variant",
    "caller_input",
    "caller_input_sha256",
    "requested_output_mode",
}
OUTPUT_FIELDS = {
    "record_class",
    "composition_contract_version",
    "composition_case_id",
    "science_record",
    "named_open_gate_record",
    "science_branch_classification",
    "named_open_branch_classification",
    "composition_disposition",
    "records_amalgamated",
    "part_b_pass",
    "admission",
    "write_authority",
    "explicit_non_authorizations",
    "hard_ban",
    "record_hash",
}
PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-path-a-named-open-composition-authorization-v0.1-20260727.json": (
        "87e6a798c6c9dfb7f05a468daa99fb248d0d75a3a57fed0d8a2f8a115b194858"
    ),
    "docs/kernel/kernel-v0.8-path-a-named-open-composition-red-design-v0.1-20260727.json": (
        "72b7bf493a49907ac47d04d499974d7ca909ba7d55fbbe7c9e5452e7736fe342"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-path-a-named-open-composition-red-review-packet-v0.1-20260727.json": (
        "55caa95e824bb7cb2fd7b4b5f7cbaf3c4a2d8ff74e25e207c14598aacb265eaa"
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
    "src/compiler/llm/m1_path_a_science_realism_graded_readonly_checker.py": (
        "1e38f90cbe093d616933a8115b441ea01546db134223e82eb470bc7efa52fd6c"
    ),
    "src/compiler/llm/m1_path_a_sufficiency_beyond_synthetic_readonly_checker.py": (
        "508b875026ae80f13728bd899b0da7bc23ba3c9b147bc11aa69c0ba81311a0c0"
    ),
    "src/compiler/llm/m1_evidence_sufficiency_evaluator.py": (
        "ad4e5af8dd9af0012f5174b14822ce9146a6d0f491c07881b5b401d85d62e78f"
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


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def composition_authority() -> dict:
    return {
        "authority_id": "PATH-A-NAMED-OPEN-COMPOSITION-TEST-ONLY-V0_1",
        "authorization_sha256": (
            "87e6a798c6c9dfb7f05a468daa99fb248d0d75a3a57fed0d8a2f8a115b194858"
        ),
        "mode": "TEST_ONLY_READONLY_NO_PRODUCTION_REGISTRATION",
        "allow_write": False,
        "allow_download": False,
        "allow_registry": False,
        "allow_dereference": False,
        "allow_authority_elevation": False,
    }


def realism_authority() -> dict:
    return {
        "mode": "TEST_ONLY_READONLY",
        "allow_write": False,
        "allow_download": False,
        "allow_registry": False,
        "allow_authority_elevation": False,
    }


def caller_authority() -> dict:
    return {
        "authority_id": "PB-SI008-PATH-A-CALLER-WIRING-TEST-ONLY-V0_1",
        "authorization_sha256": (
            "1d7c72cfb67c48537609c529e52e672e"
            "036001a6f99c27d3f8543dcbb13ac067"
        ),
        "mode": "TEST_ONLY_NO_PRODUCTION_REGISTRATION",
        "allow_write": False,
        "allow_dereference": False,
    }


class M1PathANamedOpenCompositionPresenceTests(unittest.TestCase):
    def test_green_00_runtime_and_fixture_are_present(self):
        self.assertTrue(RUNTIME_PATH.is_file())
        self.assertTrue(FIXTURE_PATH.is_file())


@unittest.skipIf(
    composition is None or not FIXTURE_PATH.is_file(),
    "composition runtime and fixture are not both implemented yet",
)
class M1PathANamedOpenCompositionReadonlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suite = load_json(FIXTURE_PATH)
        cls.cases = {
            entry["composition_input"]["composition_case_id"]: entry
            for entry in cls.suite["cases"]
        }

    def compose(self, value):
        return composition.compose_path_a_science_and_named_open_evidence_candidacy(
            copy.deepcopy(value),
            test_only_authority=composition_authority(),
        )

    def test_green_01_fixture_is_exact_closed_world_six_case_suite(self):
        self.assertEqual(
            {
                "fixture_suite_id",
                "composition_contract_version",
                "realism_fixture_id",
                "realism_fixture_path",
                "realism_fixture_sha256",
                "named_open_fixtures",
                "hard_ban",
                "test_only",
                "cases",
            },
            set(self.suite),
        )
        self.assertEqual(HARD_BAN, self.suite["hard_ban"])
        self.assertTrue(self.suite["test_only"])
        self.assertEqual(6, len(self.suite["cases"]))
        self.assertEqual(
            self.suite["realism_fixture_sha256"],
            file_sha256(REPO_ROOT / self.suite["realism_fixture_path"]),
        )
        for fixture in self.suite["named_open_fixtures"].values():
            self.assertEqual(
                fixture["sha256"],
                file_sha256(REPO_ROOT / fixture["path"]),
            )
        for entry in self.suite["cases"]:
            with self.subTest(
                composition_case_id=entry["composition_input"][
                    "composition_case_id"
                ]
            ):
                value = entry["composition_input"]
                self.assertEqual(
                    {"composition_input", "expected"},
                    set(entry),
                )
                self.assertEqual(COMPOSITION_INPUT_FIELDS, set(value))
                self.assertEqual(
                    canonical_json_sha256(value["realism_case_spec"]),
                    value["realism_case_spec_sha256"],
                )
                self.assertEqual(
                    canonical_json_sha256(value["caller_input"]),
                    value["caller_input_sha256"],
                )

    def test_green_02_exact_positive_pairs_return_real_unmodified_records(self):
        for case_id in ("COMP-RG0-V01-EXACT", "COMP-RG0-V02-EXACT"):
            entry = self.cases[case_id]
            value = entry["composition_input"]
            with self.subTest(case_id=case_id):
                expected_science = (
                    realism.evaluate_realism_graded_synthetic_case(
                        copy.deepcopy(value["realism_case_spec"]),
                        test_only_authority=realism_authority(),
                    )
                )
                expected_named = (
                    caller.evaluate_path_a_structural_binding_for_named_open(
                        copy.deepcopy(value["caller_input"]),
                        test_only_authority=caller_authority(),
                    )
                )
                record = self.compose(value)
                self.assertEqual(expected_science, record["science_record"])
                self.assertEqual(
                    expected_named,
                    record["named_open_gate_record"],
                )
                self.assertEqual(
                    "DUAL_RECORDS_RETURNED_NO_AMALGAMATION",
                    record["composition_disposition"],
                )
                self._assert_expected(entry, record)
                self._assert_non_amalgamation(record)

    def test_green_03_science_deny_and_named_allow_fails_closed(self):
        entry = self.cases["COMP-RG3-V01-SCIENCE-DENY"]
        record = self.compose(entry["composition_input"])
        self._assert_expected(entry, record)
        self.assertEqual(
            "FAIL_CLOSED_SCIENCE_NONQUALIFYING",
            record["composition_disposition"],
        )
        self.assertEqual(
            "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY",
            record["named_open_gate_record"]["decision"],
        )
        self._assert_non_amalgamation(record)

    def test_green_04_science_conditional_and_named_deny_fails_closed(self):
        entry = self.cases["COMP-RG0-V01-NAMED-DENY"]
        record = self.compose(entry["composition_input"])
        self._assert_expected(entry, record)
        self.assertEqual("DENY", record["named_open_gate_record"]["decision"])
        self.assertEqual(
            "SI008-NAMED-002_PROMOTION_TARGET_NOT_AUTHORIZED",
            record["named_open_gate_record"]["reason_code"],
        )
        self.assertEqual(
            "FAIL_CLOSED_NAMED_OPEN_DENY",
            record["composition_disposition"],
        )
        self._assert_non_amalgamation(record)

    def test_green_05_both_deny_and_mixed_pair_are_distinct_failures(self):
        expectations = {
            "COMP-RG3-V02-BOTH-DENY": (
                "FAIL_CLOSED_BOTH_BRANCHES_NONQUALIFYING",
                "SI008-NAMED-002_PROMOTION_TARGET_NOT_AUTHORIZED",
            ),
            "COMP-RG0-V01-MIXED-PAIR-DENY": (
                "FAIL_CLOSED_MIXED_REFERENCE_PAIR",
                "SI008-NAMED-003_REQUEST_NOT_QUALIFIED",
            ),
        }
        for case_id, (disposition, reason_code) in expectations.items():
            with self.subTest(case_id=case_id):
                entry = self.cases[case_id]
                record = self.compose(entry["composition_input"])
                self._assert_expected(entry, record)
                self.assertEqual(
                    disposition,
                    record["composition_disposition"],
                )
                self.assertEqual(
                    reason_code,
                    record["named_open_gate_record"]["reason_code"],
                )
                self._assert_non_amalgamation(record)

    def test_green_06_authority_rejects_before_either_branch(self):
        value = self.cases["COMP-RG0-V01-EXACT"]["composition_input"]
        invalid_authorities = (
            None,
            {},
            {**composition_authority(), "allow_write": True},
            {**composition_authority(), "unknown": False},
        )
        for authority in invalid_authorities:
            with self.subTest(authority=authority):
                with mock.patch.object(
                    composition.realism,
                    "evaluate_realism_graded_synthetic_case",
                ) as science_call, mock.patch.object(
                    composition.caller,
                    "evaluate_path_a_structural_binding_for_named_open",
                ) as caller_call:
                    with self.assertRaises(
                        composition.PathANamedOpenCompositionDenied
                    ) as context:
                        composition.compose_path_a_science_and_named_open_evidence_candidacy(
                            copy.deepcopy(value),
                            test_only_authority=authority,
                        )
                self.assertEqual(
                    "COMPOSITION-001_TEST_ONLY_AUTHORITY_REQUIRED",
                    context.exception.code,
                )
                science_call.assert_not_called()
                caller_call.assert_not_called()

    def test_green_07_shape_pair_and_digest_fail_before_branches(self):
        base = self.cases["COMP-RG0-V01-EXACT"]["composition_input"]
        missing = copy.deepcopy(base)
        missing.pop("caller_input_sha256")
        extra = copy.deepcopy(base)
        extra["wildcard"] = "*"
        unknown_pair = {
            **copy.deepcopy(base),
            "composition_case_id": "UNKNOWN",
        }
        bad_digest = {
            **copy.deepcopy(base),
            "caller_input_sha256": "0" * 64,
        }
        cases = (
            (missing, "COMPOSITION-002_CLOSED_WORLD_INPUT_REQUIRED"),
            (extra, "COMPOSITION-002_CLOSED_WORLD_INPUT_REQUIRED"),
            (unknown_pair, "COMPOSITION-003_EXACT_PAIR_NOT_ALLOWLISTED"),
            (bad_digest, "COMPOSITION-004_PIN_OR_CANONICAL_DIGEST_MISMATCH"),
        )
        for value, code in cases:
            with self.subTest(code=code):
                with mock.patch.object(
                    composition.realism,
                    "evaluate_realism_graded_synthetic_case",
                ) as science_call, mock.patch.object(
                    composition.caller,
                    "evaluate_path_a_structural_binding_for_named_open",
                ) as caller_call:
                    with self.assertRaises(
                        composition.PathANamedOpenCompositionDenied
                    ) as context:
                        self.compose(value)
                self.assertEqual(code, context.exception.code)
                science_call.assert_not_called()
                caller_call.assert_not_called()

    def test_green_08_branch_rejections_never_return_partial_record(self):
        value = self.cases["COMP-RG0-V01-EXACT"]["composition_input"]
        with mock.patch.object(
            composition.realism,
            "evaluate_realism_graded_synthetic_case",
            side_effect=realism.PathARealismGradedError("case", "denied"),
        ), mock.patch.object(
            composition.caller,
            "evaluate_path_a_structural_binding_for_named_open",
        ) as caller_call:
            with self.assertRaises(
                composition.PathANamedOpenCompositionDenied
            ) as context:
                self.compose(value)
        self.assertEqual(
            "COMPOSITION-005_SCIENCE_BRANCH_REJECTED",
            context.exception.code,
        )
        caller_call.assert_not_called()

        with mock.patch.object(
            composition.caller,
            "evaluate_path_a_structural_binding_for_named_open",
            side_effect=caller.PathACallerWiringDenied(
                "CALLER-WIRING-002_CLOSED_WORLD_INPUT_REQUIRED"
            ),
        ):
            with self.assertRaises(
                composition.PathANamedOpenCompositionDenied
            ) as context:
                self.compose(value)
        self.assertEqual(
            "COMPOSITION-006_NAMED_OPEN_CALLER_REJECTED",
            context.exception.code,
        )

    def test_green_09_same_input_same_record_hash_and_no_input_mutation(self):
        value = copy.deepcopy(
            self.cases["COMP-RG0-V02-EXACT"]["composition_input"]
        )
        before = copy.deepcopy(value)
        first = self.compose(value)
        second = self.compose(copy.deepcopy(value))
        self.assertEqual(before, value)
        self.assertEqual(first, second)
        self.assertEqual(first["record_hash"], second["record_hash"])
        payload = {
            key: item
            for key, item in first.items()
            if key != "record_hash"
        }
        self.assertEqual(
            canonical_json_sha256(payload),
            first["record_hash"],
        )

    def test_green_10_every_case_has_exact_non_amalgamation_envelope(self):
        for case_id, entry in self.cases.items():
            with self.subTest(case_id=case_id):
                record = self.compose(entry["composition_input"])
                self.assertEqual(OUTPUT_FIELDS, set(record))
                self._assert_expected(entry, record)
                self._assert_non_amalgamation(record)

    def test_green_11_claim_authority_or_pass_condition_cannot_enter(self):
        base = self.cases["COMP-RG0-V01-NAMED-DENY"][
            "composition_input"
        ]
        for target in ("AUTHORITY", "PASS_CONDITION"):
            value = copy.deepcopy(base)
            value["caller_input"]["promotion_target"] = target
            value["caller_input_sha256"] = canonical_json_sha256(
                value["caller_input"]
            )
            with self.subTest(target=target):
                with self.assertRaises(
                    composition.PathANamedOpenCompositionDenied
                ) as context:
                    self.compose(value)
                self.assertEqual(
                    "COMPOSITION-004_PIN_OR_CANONICAL_DIGEST_MISMATCH",
                    context.exception.code,
                )

    def test_green_12_protected_pins_and_registration_remain_zero_drift(self):
        before = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, before)
        self.assertEqual(12, len(PROTECTED_PINS))
        self.compose(
            self.cases["COMP-RG0-V01-EXACT"]["composition_input"]
        )
        after = {
            path: file_sha256(REPO_ROOT / path)
            for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, after)
        self.assertFalse(composition.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(realism.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(caller.PRODUCTION_REGISTRATION_ENABLED)

    def test_green_13_runtime_has_no_direct_gate_slice2_or_io_capability(self):
        source = RUNTIME_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        forbidden_import_fragments = {
            "m1_path_a_sufficiency_beyond_synthetic_readonly_checker",
            "part_b_si008_named_open_path_a_evidence_candidacy",
        }
        forbidden_import_roots = {
            "http",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_call_names = {"__import__", "eval", "exec", "open"}
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
                    self.assertFalse(
                        any(
                            fragment in alias.name
                            for fragment in forbidden_import_fragments
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                self.assertNotIn(
                    module.split(".", 1)[0],
                    forbidden_import_roots,
                )
                self.assertFalse(
                    any(
                        fragment in module
                        for fragment in forbidden_import_fragments
                    )
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

    def _assert_expected(self, entry, record):
        expected = entry["expected"]
        self.assertEqual(
            expected["science_branch_classification"],
            record["science_branch_classification"],
        )
        self.assertEqual(
            expected["science_sufficiency_decision"],
            record["science_record"]["sufficiency_decision"],
        )
        self.assertEqual(
            expected["science_checker_decision"],
            record["science_record"]["checker_decision"],
        )
        self.assertEqual(
            expected["named_open_branch_classification"],
            record["named_open_branch_classification"],
        )
        self.assertEqual(
            expected["named_open_decision"],
            record["named_open_gate_record"]["decision"],
        )
        self.assertEqual(
            expected["named_open_reason_code"],
            record["named_open_gate_record"]["reason_code"],
        )
        self.assertEqual(
            expected["composition_disposition"],
            record["composition_disposition"],
        )

    def _assert_non_amalgamation(self, record):
        self.assertEqual(
            "path_a_science_named_open_composition_readonly_record",
            record["record_class"],
        )
        self.assertEqual(HARD_BAN, record["hard_ban"])
        self.assertFalse(record["records_amalgamated"])
        self.assertFalse(record["part_b_pass"])
        self.assertFalse(record["admission"])
        self.assertFalse(record["write_authority"])
        self.assertTrue(record["record_hash"])
        self.assertTrue(
            all(
                value is False
                for value in record["explicit_non_authorizations"].values()
            )
        )
        self.assertFalse(
            record["named_open_gate_record"]["allow_is_part_b_pass"]
        )
        self.assertFalse(
            record["named_open_gate_record"]["allow_is_admission"]
        )


if __name__ == "__main__":
    unittest.main()
