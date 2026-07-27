"""Path A -> PB-SI-008 named-open caller tests.

Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation.
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
    part_b_si008_named_open_path_a_evidence_candidacy as named_gate,
)
try:
    from src.scope import (
        part_b_si008_path_a_named_open_caller_wiring as caller,
    )
except ImportError:
    caller = None
from tests.compiler_contract import (
    test_m1_audit_log_to_claim_ir_mapper as v0_2_support,
)
from tests.compiler_contract import (
    test_m1_evidence_to_claim_ir_mapper as v0_1_support,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "part_b_si008_path_a_named_open_caller_wiring"
)
FIXTURE_PATHS = {
    "v0.1": FIXTURE_ROOT / "evidence-v0.1-system-log.json",
    "v0.2": FIXTURE_ROOT / "evidence-v0.2-audit-log.json",
}
HARD_BAN = "Path A readonly GREEN MUST NOT be inferred as L2 PASS, Part B PASS, or unrestricted Part B elevation."
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
RECEIPT_FIELDS = {
    "receipt_version",
    "fixture_id",
    "source_schema_version",
    "source_schema_sha256",
    "consumer_contract_id",
    "consumer_contract_sha256",
    "package_sha256",
    "structural_validation_status",
    "record_class",
    "claim_id_state",
    "admission_state",
    "reference_access_mode",
    "test_only",
    "write_side_effects",
}
PROTECTED_PINS = {
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-caller-wiring-authorization-v0.1-20260727.json": (
        "1d7c72cfb67c48537609c529e52e672e036001a6f99c27d3f8543dcbb13ac067"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-path-a-named-open-caller-wiring-red-design-v0.1-20260727.json": (
        "17bf977802b63ce8601d81dbdfcbfb2fb35be3a2504db7657087fdfec37cd20e"
    ),
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-pb-si008-path-a-named-open-caller-wiring-red-review-packet-v0.1-20260727.json": (
        "03f56ac3f59f6196f25f996a9ebdf6b9179ed1c845343da03a28bacb52779ac2"
    ),
    "docs/kernel/kernel-v0.8-pb-si008-named-open-path-a-evidence-candidacy-green-owner-acceptance-v0.1-20260727.json": (
        "daa5b2b52816cec0d24876fd452c4499150067912de9be3b7c4fdc81ef4a369d"
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
    "src/compiler/llm/claim_id_mainline_handoff.py": (
        "304000b03ad273a26d864e2567c4b3f20ce06bdc5199387d57d46bc64152c35a"
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
    "tests/compiler_contract/fixtures/m1_evidence_modality/synthetic_system_log_projection_v0.1.json": (
        "adaca38945a2068fc3a3b4649dcf450ca3385562907fc752427e9e4e921405b7"
    ),
    "src/compiler/llm/m1_evidence_to_claim_ir_mapper.py": (
        "1dd8f407cc8fe840d90a7bf66c43e2cb11b5131877f2e46f92f2a1ffd372965b"
    ),
    "docs/llm-editor/fixtures/audit-log-public-projection-red-v0.1/synthetic-audit-log-public-projection-minimal-v0.1.json": (
        "3a2e1857e994dddd2fcf9137a106ab05294d5e952924eb2bcf84971f4c32f38a"
    ),
    "src/compiler/llm/m1_audit_log_projection_adapter.py": (
        "93934bc6a28eaa1d7b23932bf5d1ca6c44221df2dc7a3c255b8e969cca311704"
    ),
    "src/compiler/llm/m1_audit_log_to_claim_ir_mapper.py": (
        "4d0fccbdff2b8d902079f7bfa9a949a7fc6ec4660e946f6ad75deed4a4e8e0e9"
    ),
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_only_authority() -> dict:
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


def replay_v0_1_package() -> dict:
    projection = v0_1_support.load_fixture("system_log_public_projection")
    return v0_1_support.mapper.map_validated_projection_to_claim_ir(
        projection,
        repo_root=ROOT,
        authority=v0_1_support.authority_for(projection),
    )


def replay_v0_2_package() -> dict:
    return v0_2_support.map_fixture()


def direct_gate_request(caller_input: dict) -> dict:
    return {
        "request_id": caller_input["request_id"],
        "request_kind": "PROMOTE_TO_PART_B_NAMED_TARGET",
        "promotion_target": caller_input["promotion_target"],
        "reference_kind": caller_input["reference_kind"],
        "named_target_id": (
            "PATH_A_EVIDENCE_CLAIM_IR_STRUCTURAL_CANDIDACY_V0_1"
        ),
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
        "requested_authority_scope": (
            "EVIDENCE_STRUCTURAL_CANDIDACY_ONLY"
        ),
        "reference_access_mode": (
            "CLASSIFY_DECLARED_REFERENCE_ONLY_NO_DEREFERENCE"
        ),
    }


class PartBSI008PathANamedOpenCallerWiringPresenceTests(
    unittest.TestCase
):
    def test_green_00_caller_module_is_present(self):
        self.assertTrue(
            (
                ROOT
                / "src"
                / "scope"
                / "part_b_si008_path_a_named_open_caller_wiring.py"
            ).is_file()
        )


@unittest.skipIf(caller is None, "caller module is not implemented yet")
class PartBSI008PathANamedOpenCallerWiringTests(unittest.TestCase):
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
        self.assertEqual(18, len(PROTECTED_PINS))
        self.assertTrue(
            (
                ROOT
                / "src"
                / "scope"
                / "part_b_si008_path_a_named_open_caller_wiring.py"
            ).is_file()
        )
        self.assertEqual(2, len(self.fixtures))

    def test_green_02_fixtures_replay_package_and_receipt_digests(self):
        packages = {
            "v0.1": replay_v0_1_package(),
            "v0.2": replay_v0_2_package(),
        }
        for version, fixture in self.fixtures.items():
            with self.subTest(version=version):
                package = packages[version]
                package_sha256 = canonical_json_sha256(package)
                self.assertEqual(
                    package_sha256,
                    fixture["source_replay"]["package_sha256"],
                )
                self.assertEqual(
                    package_sha256,
                    fixture["caller_input"]["package_sha256"],
                )
                receipt = fixture["structural_validation_receipt"]
                self.assertEqual(RECEIPT_FIELDS, set(receipt))
                self.assertEqual(
                    package_sha256,
                    receipt["package_sha256"],
                )
                receipt_sha256 = canonical_json_sha256(receipt)
                self.assertEqual(
                    receipt_sha256,
                    fixture["structural_validation_receipt_sha256"],
                )
                self.assertEqual(
                    receipt_sha256,
                    fixture["caller_input"][
                        "structural_validation_receipt_sha256"
                    ],
                )

    def test_green_03_both_exact_pairs_allow_and_equal_direct_gate(self):
        for version, fixture in self.fixtures.items():
            with self.subTest(version=version):
                caller_input = deepcopy(fixture["caller_input"])
                result = caller.evaluate_path_a_structural_binding_for_named_open(
                    caller_input,
                    test_only_authority=test_only_authority(),
                )
                expected = named_gate.evaluate_si008_named_open_request(
                    direct_gate_request(caller_input)
                )
                self.assertEqual(expected, result)
                self.assertEqual(
                    "ALLOW_NAMED_EVIDENCE_CANDIDACY_ONLY",
                    result["decision"],
                )

    def test_green_04_caller_sends_exact_18_fields_and_returns_same_object(self):
        caller_input = deepcopy(self.fixtures["v0.1"]["caller_input"])
        sentinel = {"gate_record": "unchanged"}
        with mock.patch.object(
            caller,
            "evaluate_si008_named_open_request",
            return_value=sentinel,
        ) as gate_mock:
            result = caller.evaluate_path_a_structural_binding_for_named_open(
                caller_input,
                test_only_authority=test_only_authority(),
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
                **test_only_authority(),
                "allow_write": True,
            },
            {
                **test_only_authority(),
                "unknown": "DENY",
            },
        )
        for authority in authorities:
            with self.subTest(authority=authority):
                with mock.patch.object(
                    caller,
                    "evaluate_si008_named_open_request",
                ) as gate_mock:
                    with self.assertRaises(
                        caller.PathACallerWiringDenied
                    ) as context:
                        caller.evaluate_path_a_structural_binding_for_named_open(
                            caller_input,
                            test_only_authority=authority,
                        )
                self.assertEqual(
                    "CALLER-WIRING-001_TEST_ONLY_AUTHORITY_REQUIRED",
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
        for caller_input in (missing, unknown, empty_digest, None):
            with self.subTest(caller_input=caller_input):
                with mock.patch.object(
                    caller,
                    "evaluate_si008_named_open_request",
                ) as gate_mock:
                    with self.assertRaises(
                        caller.PathACallerWiringDenied
                    ) as context:
                        caller.evaluate_path_a_structural_binding_for_named_open(
                            caller_input,
                            test_only_authority=test_only_authority(),
                        )
                self.assertEqual(
                    "CALLER-WIRING-002_CLOSED_WORLD_INPUT_REQUIRED",
                    context.exception.code,
                )
                gate_mock.assert_not_called()

    def test_green_07_wrong_pair_minted_admitted_and_wildcard_deny(self):
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
        )
        for caller_input in cases:
            with self.subTest(caller_input=caller_input):
                result = caller.evaluate_path_a_structural_binding_for_named_open(
                    caller_input,
                    test_only_authority=test_only_authority(),
                )
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-003_REQUEST_NOT_QUALIFIED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_08_claim_authority_and_pass_condition_deny(self):
        base = deepcopy(self.fixtures["v0.2"]["caller_input"])
        for target in ("CLAIM", "AUTHORITY", "PASS_CONDITION"):
            with self.subTest(target=target):
                result = caller.evaluate_path_a_structural_binding_for_named_open(
                    {
                        **base,
                        "promotion_target": target,
                    },
                    test_only_authority=test_only_authority(),
                )
                self.assertEqual("DENY", result["decision"])
                self.assertEqual(
                    "SI008-NAMED-002_PROMOTION_TARGET_NOT_AUTHORIZED",
                    result["reason_code"],
                )
                self._assert_no_elevation(result)

    def test_green_09_same_input_replays_same_record_without_mutation(self):
        caller_input = deepcopy(self.fixtures["v0.2"]["caller_input"])
        before = deepcopy(caller_input)
        first = caller.evaluate_path_a_structural_binding_for_named_open(
            caller_input,
            test_only_authority=test_only_authority(),
        )
        second = caller.evaluate_path_a_structural_binding_for_named_open(
            deepcopy(caller_input),
            test_only_authority=deepcopy(test_only_authority()),
        )
        self.assertEqual(first, second)
        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual(first["hash"], second["hash"])
        self.assertEqual(before, caller_input)

    def test_green_10_no_io_registration_or_authority_elevation(self):
        source = (
            ROOT
            / "src"
            / "scope"
            / "part_b_si008_path_a_named_open_caller_wiring.py"
        ).read_text(encoding="utf-8")
        self.assertIn(HARD_BAN, source)
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
        for fixture in self.fixtures.values():
            result = caller.evaluate_path_a_structural_binding_for_named_open(
                deepcopy(fixture["caller_input"]),
                test_only_authority=test_only_authority(),
            )
            self._assert_no_elevation(result)
            self.assertFalse(result["package_dereferenced"])
            self.assertFalse(result["validation_receipt_dereferenced"])

    def _assert_no_elevation(self, result):
        for field in (
            "allow_is_admission",
            "allow_is_part_b_pass",
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
