"""Path A CLAIM -> PB-SI-008 named-open caller tests.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or
unrestricted Part B elevation.
"""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

from src.scope import (
    part_b_si008_named_open_path_a_claim_candidacy as claim_gate,
)
try:
    from src.scope import (
        part_b_si008_path_a_claim_named_open_caller_wiring as caller,
    )
except ImportError:
    caller = None


ROOT = Path(__file__).resolve().parents[2]
CALLER_PATH = (
    ROOT
    / "src"
    / "scope"
    / "part_b_si008_path_a_claim_named_open_caller_wiring.py"
)
FIXTURE_ROOT = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "part_b_si008_path_a_claim_named_open_caller_wiring"
)
FIXTURE_PATHS = {
    "v0.1": FIXTURE_ROOT / "claim-v0.1-system-log.json",
    "v0.2": FIXTURE_ROOT / "claim-v0.2-audit-log.json",
}
HARD_BAN = (
    "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, "
    "or unrestricted Part B elevation."
)
CALLER_INPUT_FIELDS = {
    "request_id",
    "promotion_target",
    "reference_kind",
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
}
GATE_REQUEST_FIELDS = {
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
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-claim-caller-wiring-owner-go-authorization-v0.1-20260728.json": (
        "9c96d5271767736c994c974265aebe385ddbfffb3183de0eb32c84aadf05cdec"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-path-a-claim-named-open-caller-wiring-red-design-v0.1-20260728.json": (
        "11c2bab7d947c84786883e13cbd181a97c7f32f244a268d42e835f0c02ce5443"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-pb-si008-path-a-claim-named-open-caller-wiring-red-review-packet-v0.1-20260728.json": (
        "dcfac2fcaeb54112647fab43fd0bdee3a5e40b8632126ac94746a67c6618fc81"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-claim-candidacy-green-owner-acceptance-v0.1-20260727.json": (
        "55d29fd927b1eb9fdc740c090e3c2d40a3384e485e04fa2eb4eb5347065e7325"
    ),
    "src/scope/part_b_si008_named_open_path_a_claim_candidacy.py": (
        "cc85829c8f9eb9cd49d0c856a6b4c7b590a8e922f28b5085f942f424554386ea"
    ),
    "configs/part-b-si008-named-open-path-a-claim-candidacy-manifest-v0.8.yaml": (
        "c660083eb776afd9e14d252a93c4e809439b0f63d313452ce96eb28ba25a89e8"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-path-a-named-open-caller-wiring-green-owner-acceptance-v0.1-20260727.json": (
        "ac85c628eca128f65d3031548fc6257cc35c52663208958c5eff53ddff77ba0c"
    ),
    "src/scope/part_b_si008_path_a_named_open_caller_wiring.py": (
        "64fcc81ff7ae6f61ae58d6a8e5d9bb602a5c6f307feef1a25497048643d11ecf"
    ),
    "tests/unit/fixtures/part_b_si008_path_a_named_open_caller_wiring/evidence-v0.1-system-log.json": (
        "afb695d5730affe057e178be3e6b009b2cb641726e4e8610c67dffb9dc37e135"
    ),
    "tests/unit/fixtures/part_b_si008_path_a_named_open_caller_wiring/evidence-v0.2-audit-log.json": (
        "46937b764485b8410b7e11e5e45e31a4068941a0ebf29d792f15a447a987ad54"
    ),
    "schemas/claim-ir-external-envelope-evidence-v0.1.schema.json": (
        "9abc23e2258298038e137dbbe38168867d07108fa27719aa68c1c2b752ae2a7c"
    ),
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.2-20260727.json": (
        "fe5222b9b4e0ddaf990761b34bdfc5004f45f55d3e2155b09388fb9596a1e504"
    ),
    "schemas/claim-ir-external-envelope-evidence-v0.2.schema.json": (
        "e246c44b7513a5bc2f3410a2739a53bd1f40dad3e767036bb1af3158c9e02ac6"
    ),
    "docs/kernel/kernel-v0.8-shared-claim-ir-consumer-contract-evidence-candidate-effective-v0.3-20260727.json": (
        "7662762d045381921b8f94a39753d0c491322b3a41d473226cc5fe3f4688457c"
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
    "src/compiler/llm/m1_path_a_named_open_composition_readonly.py": (
        "3b4f86288b1bb4b7d3e5366e24a6adabaddaa028a463c6b067c4470added0cc3"
    ),
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_test_only_authority() -> dict:
    return {
        "authority_id": (
            "PB-SI008-PATH-A-CLAIM-CALLER-WIRING-TEST-ONLY-V0_1"
        ),
        "authorization_sha256": (
            "9c96d5271767736c994c974265aebe385"
            "ddbfffb3183de0eb32c84aadf05cdec"
        ),
        "mode": "TEST_ONLY_NO_PRODUCTION_REGISTRATION",
        "allow_write": False,
        "allow_dereference": False,
    }


def direct_gate_request(caller_input: dict) -> dict:
    return {
        "request_id": caller_input["request_id"],
        "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
        "promotion_target": caller_input["promotion_target"],
        "reference_kind": caller_input["reference_kind"],
        "named_target_id": "PATH_A_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1",
        "source_schema_version": caller_input["source_schema_version"],
        "source_schema_sha256": caller_input["source_schema_sha256"],
        "consumer_contract_id": caller_input["consumer_contract_id"],
        "consumer_contract_sha256": caller_input[
            "consumer_contract_sha256"
        ],
        "package_sha256": caller_input["package_sha256"],
        "structural_validation_receipt_sha256": caller_input[
            "structural_validation_receipt_sha256"
        ],
        "record_class": caller_input["record_class"],
        "claim_id": caller_input["claim_id"],
        "claim_id_state": caller_input["claim_id_state"],
        "admission_state": caller_input["admission_state"],
        "structural_validation_status": caller_input[
            "structural_validation_status"
        ],
        "requested_authority_scope": "CLAIM_STRUCTURAL_CANDIDACY_ONLY",
        "reference_access_mode": (
            "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
        ),
    }


class PartBSI008PathAClaimNamedOpenCallerWiringPresenceTests(
    unittest.TestCase
):
    def test_green_00_claim_caller_module_is_present(self):
        self.assertTrue(CALLER_PATH.is_file())


@unittest.skipIf(caller is None, "CLAIM caller module is not implemented")
class PartBSI008PathAClaimNamedOpenCallerWiringTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.fixtures = {
            version: load_json(path)
            for version, path in FIXTURE_PATHS.items()
        }

    def test_green_01_protected_pins_and_exact_products(self):
        actual = {
            path: file_sha256(ROOT / path) for path in PROTECTED_PINS
        }
        self.assertEqual(PROTECTED_PINS, actual)
        self.assertEqual(19, len(PROTECTED_PINS))
        self.assertTrue(CALLER_PATH.is_file())
        self.assertEqual(2, len(self.fixtures))

    def test_green_02_fixtures_reuse_pinned_package_and_receipt(self):
        for version, fixture in self.fixtures.items():
            with self.subTest(version=version):
                binding = fixture["accepted_structural_binding_source"]
                source_path = ROOT / binding["path"]
                self.assertEqual(
                    binding["sha256"],
                    file_sha256(source_path),
                )
                evidence_fixture = load_json(source_path)
                self.assertEqual(
                    binding["package_sha256"],
                    evidence_fixture["source_replay"]["package_sha256"],
                )
                self.assertEqual(
                    binding["structural_validation_receipt_sha256"],
                    evidence_fixture[
                        "structural_validation_receipt_sha256"
                    ],
                )
                self.assertEqual(
                    binding["package_sha256"],
                    fixture["caller_input"]["package_sha256"],
                )
                self.assertEqual(
                    binding["structural_validation_receipt_sha256"],
                    fixture["caller_input"][
                        "structural_validation_receipt_sha256"
                    ],
                )
                self.assertFalse(
                    fixture["claim_binding"]["package_or_receipt_rewritten"]
                )

    def test_green_03_both_exact_pairs_allow_and_equal_direct_gate(self):
        for version, fixture in self.fixtures.items():
            with self.subTest(version=version):
                caller_input = deepcopy(fixture["caller_input"])
                result = caller.evaluate_path_a_claim_structural_binding_for_named_open(
                    caller_input,
                    test_only_authority=_make_test_only_authority(),
                )
                expected = claim_gate.evaluate_si008_named_open_claim_request(
                    direct_gate_request(caller_input)
                )
                self.assertEqual(expected, result)
                self.assertEqual(
                    "ALLOW_NAMED_CLAIM_CANDIDACY_ONLY",
                    result["decision"],
                )
                for field, value in fixture["expected_gate"].items():
                    self.assertEqual(value, result[field])
                self._assert_no_elevation(result)

    def test_green_04_sends_exact_18_fields_and_returns_same_object(self):
        caller_input = deepcopy(self.fixtures["v0.1"]["caller_input"])
        sentinel = {"gate_record": "unchanged"}
        with mock.patch.object(
            caller,
            "evaluate_si008_named_open_claim_request",
            return_value=sentinel,
        ) as gate_mock:
            result = caller.evaluate_path_a_claim_structural_binding_for_named_open(
                caller_input,
                test_only_authority=_make_test_only_authority(),
            )
        self.assertIs(sentinel, result)
        gate_mock.assert_called_once()
        request = gate_mock.call_args.args[0]
        self.assertEqual(GATE_REQUEST_FIELDS, set(request))
        self.assertEqual(18, len(request))
        self.assertEqual(direct_gate_request(caller_input), request)

    def test_green_05_test_only_authority_fails_before_gate(self):
        caller_input = deepcopy(self.fixtures["v0.1"]["caller_input"])
        authorities = (
            None,
            {},
            {
                **_make_test_only_authority(),
                "authorization_sha256": "0" * 64,
            },
            {
                **_make_test_only_authority(),
                "allow_write": True,
            },
            {
                **_make_test_only_authority(),
                "unknown": "DENY",
            },
        )
        for authority in authorities:
            with self.subTest(authority=authority):
                with mock.patch.object(
                    caller,
                    "evaluate_si008_named_open_claim_request",
                ) as gate_mock:
                    with self.assertRaises(
                        caller.PathAClaimCallerWiringDenied
                    ) as context:
                        caller.evaluate_path_a_claim_structural_binding_for_named_open(
                            caller_input,
                            test_only_authority=authority,
                        )
                self.assertEqual(
                    "CLAIM-CALLER-WIRING-001_TEST_ONLY_AUTHORITY_REQUIRED",
                    context.exception.code,
                )
                gate_mock.assert_not_called()

    def test_green_06_closed_world_input_fails_before_gate(self):
        base = deepcopy(self.fixtures["v0.1"]["caller_input"])
        missing = deepcopy(base)
        missing.pop("package_sha256")
        unknown = deepcopy(base)
        unknown["path"] = "C:/forbidden"
        empty_digest = deepcopy(base)
        empty_digest["package_sha256"] = ""
        raw_bytes = deepcopy(base)
        raw_bytes["package_sha256"] = b"forbidden"
        for caller_input in (
            missing,
            unknown,
            empty_digest,
            raw_bytes,
            None,
        ):
            with self.subTest(caller_input=caller_input):
                with mock.patch.object(
                    caller,
                    "evaluate_si008_named_open_claim_request",
                ) as gate_mock:
                    with self.assertRaises(
                        caller.PathAClaimCallerWiringDenied
                    ) as context:
                        caller.evaluate_path_a_claim_structural_binding_for_named_open(
                            caller_input,
                            test_only_authority=_make_test_only_authority(),
                        )
                self.assertEqual(
                    "CLAIM-CALLER-WIRING-002_CLOSED_WORLD_INPUT_REQUIRED",
                    context.exception.code,
                )
                gate_mock.assert_not_called()

    def test_green_07_wrong_pair_state_wildcard_and_digest_deny(self):
        base = deepcopy(self.fixtures["v0.1"]["caller_input"])
        cases = (
            {
                **base,
                "consumer_contract_sha256": self.fixtures["v0.2"][
                    "caller_input"
                ]["consumer_contract_sha256"],
            },
            {
                **base,
                "claim_id": "pkg_minted_forbidden",
                "claim_id_state": "minted",
            },
            {
                **base,
                "admission_state": "admitted",
            },
            {
                **base,
                "reference_kind": "*",
            },
            {
                **base,
                "source_schema_sha256": "A" * 64,
            },
            {
                **base,
                "package_sha256": "file:///forbidden",
            },
        )
        for caller_input in cases:
            with self.subTest(caller_input=caller_input):
                result = caller.evaluate_path_a_claim_structural_binding_for_named_open(
                    caller_input,
                    test_only_authority=_make_test_only_authority(),
                )
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_08_evidence_authority_and_pass_condition_deny(self):
        base = deepcopy(self.fixtures["v0.2"]["caller_input"])
        expected_codes = {
            "EVIDENCE": "SI008-NAMED-CLAIM-003_REQUEST_NOT_QUALIFIED",
            "AUTHORITY": (
                "SI008-NAMED-CLAIM-002_PROMOTION_TARGET_NOT_AUTHORIZED"
            ),
            "PASS_CONDITION": (
                "SI008-NAMED-CLAIM-002_PROMOTION_TARGET_NOT_AUTHORIZED"
            ),
        }
        for target, reason_code in expected_codes.items():
            with self.subTest(target=target):
                result = caller.evaluate_path_a_claim_structural_binding_for_named_open(
                    {
                        **base,
                        "promotion_target": target,
                    },
                    test_only_authority=_make_test_only_authority(),
                )
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(reason_code, result["reason_code"])
                self._assert_no_elevation(result)

    def test_green_09_same_input_replays_without_mutation(self):
        caller_input = deepcopy(self.fixtures["v0.2"]["caller_input"])
        before = deepcopy(caller_input)
        first = caller.evaluate_path_a_claim_structural_binding_for_named_open(
            caller_input,
            test_only_authority=_make_test_only_authority(),
        )
        second = caller.evaluate_path_a_claim_structural_binding_for_named_open(
            deepcopy(caller_input),
            test_only_authority=deepcopy(_make_test_only_authority()),
        )
        self.assertEqual(first, second)
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(before, caller_input)

    def test_green_10_no_io_registration_or_authority_elevation(self):
        source = CALLER_PATH.read_text(encoding="utf-8")
        self.assertEqual(HARD_BAN, caller.HARD_BAN)
        self.assertIn("PRODUCTION_REGISTRATION_ENABLED = False", source)
        tree = ast.parse(source)
        forbidden_modules = {
            "pathlib",
            "requests",
            "socket",
            "subprocess",
            "urllib",
        }
        forbidden_calls = {
            "__import__",
            "compile",
            "eval",
            "exec",
            "open",
        }
        forbidden_attributes = {
            "connect",
            "open",
            "read_bytes",
            "read_text",
            "request",
            "urlopen",
            "write_bytes",
            "write_text",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotIn(
                        alias.name.split(".", 1)[0],
                        forbidden_modules,
                    )
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn(
                    (node.module or "").split(".", 1)[0],
                    forbidden_modules,
                )
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, forbidden_calls)
                elif isinstance(node.func, ast.Attribute):
                    self.assertNotIn(
                        node.func.attr,
                        forbidden_attributes,
                    )
        self.assertNotIn("http://", source)
        self.assertNotIn("https://", source)
        self.assertFalse(caller.PRODUCTION_REGISTRATION_ENABLED)
        for fixture in self.fixtures.values():
            result = caller.evaluate_path_a_claim_structural_binding_for_named_open(
                deepcopy(fixture["caller_input"]),
                test_only_authority=_make_test_only_authority(),
            )
            self._assert_no_elevation(result)
            self.assertFalse(result["package_dereferenced"])
            self.assertFalse(result["validation_receipt_dereferenced"])

    def _assert_no_elevation(self, result):
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
            "production_registration_authority",
            "mint_authority",
            "admission_authority",
            "kernel_or_e_case_write_authority",
            "certificate_authority",
        ):
            self.assertFalse(result[field])
        self.assertEqual("DENY", result["holdout_release"])
        self.assertEqual("DENY", result["pb_si_006_download"])
        self.assertEqual("NOT_ESTABLISHED", result["pb_b5_execution"])
        self.assertEqual("NONE", result["stop_authority"])
        self.assertEqual("NOT_AUTHORIZED", result["certified_stop"])
        self.assertEqual(HARD_BAN, result["hard_ban"])


if __name__ == "__main__":
    unittest.main()
