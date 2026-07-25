import ast
import copy
import hashlib
import json
import tempfile
import unittest
import uuid
from pathlib import Path

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_control_loop_reference_binder import (
    ACTIVATION_STATUS,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    BINDER_PATH,
    EFFECTIVE_CONSUMER_CONTRACT_SHA256,
    HANDOFF_DESIGN_SHA256,
    INGESTED_FIXTURE_PATH,
    INGESTED_FIXTURE_SHA256,
    INGESTION_RECEIPT_SHA256,
    PACKAGE_ID,
    REFERENCE_MODE,
    REFERENCE_STATUS,
    REGISTRATION_ACTIVATION_PATH,
    REGISTRATION_ACTIVATION_SHA256,
    REGISTRATION_EXECUTOR_SHA256,
    REGISTRATION_RECEIPT_PATH,
    REGISTRATION_RECEIPT_SHA256,
    REGISTRATION_RECORD_PATH,
    REGISTRATION_RECORD_SHA256,
    SCHEMA_SHA256,
    ClaimIDControlLoopReferenceError,
    bind_claim_id_control_loop_reference,
    verify_control_loop_reference_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def activated_authority(case: str) -> dict:
    output_path = (
        f".tmp/compiler-contract/claim-id-control-loop-reference-{case}-"
        f"{uuid.uuid4().hex}/reference.json"
    )
    return {
        "artifact_id": f"claim_id_control_loop_reference_test_{case}_v0_1",
        "artifact_type": (
            "claim_id_control_loop_reference_wiring_single_execute_activation"
        ),
        "version": "0.1",
        "created_date": "2026-07-25",
        "authority_base_commit": AUTHORITY_BASE_COMMIT,
        "status": ACTIVATION_STATUS,
        "authority_design": {
            "artifact_id": AUTHORITY_DESIGN_ARTIFACT_ID,
            "path": AUTHORITY_DESIGN_PATH,
            "sha256": AUTHORITY_DESIGN_SHA256,
            "status": AUTHORITY_DESIGN_STATUS,
        },
        "target": {
            "surface_id": "project05_depth2_public",
            "source_class": "planner_experiment_inputs",
            "adapter_id": "m1a_planner_inputs_v0_1",
            "package_id": PACKAGE_ID,
            "reference_mode": REFERENCE_MODE,
            "execution_scope": "single_versioned_reference_bind_only",
        },
        "pinned_hashes": {
            "authority_design_sha256": AUTHORITY_DESIGN_SHA256,
            "registration_record_sha256": REGISTRATION_RECORD_SHA256,
            "registration_receipt_sha256": REGISTRATION_RECEIPT_SHA256,
            "exhausted_registration_activation_sha256": (
                REGISTRATION_ACTIVATION_SHA256
            ),
            "registration_executor_sha256": REGISTRATION_EXECUTOR_SHA256,
            "mainline_handoff_design_sha256": HANDOFF_DESIGN_SHA256,
            "effective_consumer_contract_sha256": (
                EFFECTIVE_CONSUMER_CONTRACT_SHA256
            ),
            "external_envelope_schema_sha256": SCHEMA_SHA256,
            "ingested_fixture_sha256": INGESTED_FIXTURE_SHA256,
            "sanitized_ingestion_receipt_sha256": INGESTION_RECEIPT_SHA256,
            "reference_binder_sha256": sha256(REPO_ROOT / BINDER_PATH),
        },
        "selected_input": {
            "registration_record": {
                "path": REGISTRATION_RECORD_PATH,
                "sha256": REGISTRATION_RECORD_SHA256,
            },
            "registration_receipt": {
                "path": REGISTRATION_RECEIPT_PATH,
                "sha256": REGISTRATION_RECEIPT_SHA256,
            },
            "exhausted_registration_activation": {
                "path": REGISTRATION_ACTIVATION_PATH,
                "sha256": REGISTRATION_ACTIVATION_SHA256,
            },
            "ingested_fixture": {
                "path": INGESTED_FIXTURE_PATH,
                "sha256": INGESTED_FIXTURE_SHA256,
                "package_id": PACKAGE_ID,
            },
        },
        "execute_ledger": {
            "authorized": 1,
            "maximum": 1,
            "started": 0,
            "consumed": 0,
            "remaining": 1,
            "retry": False,
            "resume": False,
            "fallback": False,
        },
        "output_policy": {
            "mode": "versioned_reference_contract_only",
            "reference_artifact_path": output_path,
            "reference_artifact_write": True,
            "production_controller_import_wired": False,
            "production_planner_import_wired": False,
            "controller_or_planner_algorithm_change": False,
            "kernel_store_write": False,
            "e_case_write": False,
            "certificate_generation": False,
            "certified_stop": False,
            "claim_lifecycle_mutation": False,
        },
        "still_blocked": {
            "second_reference_bind": True,
            "production_controller_import_wiring": True,
            "production_planner_import_wiring": True,
            "controller_or_planner_algorithm_change": True,
            "kernel_store_write": True,
            "e_case_write": True,
            "checker_or_promotion": True,
            "certificate_generation": True,
            "certified_stop": True,
            "si_llm_001_closure": True,
            "catalog_role_credit_l2": True,
            "part_b_elevation": True,
            "m2_fit": True,
            "four_family_llm_finetune": True,
        },
        "execution_audit": None,
    }


def pretty_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


class ClaimIDControlLoopReferenceBinderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registration_record_bytes = (REPO_ROOT / REGISTRATION_RECORD_PATH).read_bytes()
        cls.registration_receipt_bytes = (REPO_ROOT / REGISTRATION_RECEIPT_PATH).read_bytes()
        cls.registration_record = json.loads(cls.registration_record_bytes.decode("utf-8"))
        cls.ingested_fixture = json.loads(
            (REPO_ROOT / INGESTED_FIXTURE_PATH).read_text(encoding="utf-8")
        )
        cls.admitted_only_bytes = (
            REPO_ROOT
            / "docs/llm-editor/fixtures/claim-ir-admitted/"
            "project05-depth2-public-minted-admitted-v0.1/package.json"
        ).read_bytes()

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ClaimIDControlLoopReferenceError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def bind_with(
        self,
        authority: dict,
        *,
        record_bytes: bytes | None = None,
        receipt_bytes: bytes | None = None,
    ):
        if record_bytes is None:
            record_bytes = self.registration_record_bytes
        if receipt_bytes is None:
            receipt_bytes = self.registration_receipt_bytes
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(pretty_json_bytes(authority))
            return bind_claim_id_control_loop_reference(
                record_bytes,
                receipt_bytes,
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

    def test_pins_and_binder_has_no_persistent_write_surface(self):
        verify_control_loop_reference_pins(REPO_ROOT)
        self.assertEqual(
            AUTHORITY_DESIGN_SHA256,
            sha256(REPO_ROOT / AUTHORITY_DESIGN_PATH),
        )
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)

        tree = ast.parse((REPO_ROOT / BINDER_PATH).read_text(encoding="utf-8"))
        forbidden_methods = {
            "write_bytes",
            "write_text",
            "mkdir",
            "rename",
            "unlink",
        }
        observed = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in forbidden_methods
        }
        self.assertEqual(set(), observed)

    def test_missing_registration_fails_closed(self):
        authority = activated_authority("missing_registration")
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(pretty_json_bytes(authority))
            self.assert_error_code(
                "missing_registration",
                lambda: bind_claim_id_control_loop_reference(
                    None,
                    self.registration_receipt_bytes,
                    repo_root=REPO_ROOT,
                    activation_path=activation_path,
                ),
            )

    def test_wrong_pin_fails_closed(self):
        authority = activated_authority("wrong_pin")
        authority["pinned_hashes"]["registration_record_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin",
            lambda: self.bind_with(authority),
        )

    def test_consumed_ledger_rejects_second_bind(self):
        authority = activated_authority("consumed")
        authority["execute_ledger"].update(
            {"started": 1, "consumed": 1, "remaining": 0}
        )
        authority["execution_audit"] = {"decision": "already_consumed"}
        self.assert_error_code(
            "activation_ledger",
            lambda: self.bind_with(authority),
        )

    def test_admitted_only_and_unregistered_inputs_fail_closed(self):
        self.assert_error_code(
            "registration_record_pin",
            lambda: self.bind_with(
                activated_authority("admitted_only"),
                record_bytes=self.admitted_only_bytes,
            ),
        )

        unregistered = copy.deepcopy(self.registration_record)
        unregistered["status"] = "not_registered"
        self.assert_error_code(
            "registration_record_pin",
            lambda: self.bind_with(
                activated_authority("unregistered"),
                record_bytes=pretty_json_bytes(unregistered),
            ),
        )

    def test_versioned_reference_fixture_matches_closed_consumer_contract(self):
        reference_path = (
            REPO_ROOT
            / "docs/llm-editor/fixtures/claim-id-control-loop-reference/"
            "project05-depth2-public-v0.1/reference.json"
        )
        activation_path = (
            REPO_ROOT
            / "docs/llm-editor/"
            "llm-editor-v0.8-l2-claim-id-control-loop-reference-wiring-"
            "single-execute-activation-v0.1-20260725.json"
        )
        design = json.loads((REPO_ROOT / AUTHORITY_DESIGN_PATH).read_text(encoding="utf-8"))
        activation = json.loads(activation_path.read_text(encoding="utf-8"))
        reference = json.loads(reference_path.read_text(encoding="utf-8"))

        self.assertEqual(
            set(design["reference_payload_contract"]["required_fields"]),
            set(reference),
        )
        self.assertEqual(
            sha256(reference_path),
            activation["execution_audit"]["reference_artifact"]["sha256"],
        )
        self.assertEqual(
            [claim["claim_id"] for claim in self.ingested_fixture["claims"]],
            reference["claim_ids"],
        )
        self.assertFalse(
            reference["runtime_reference_boundary"][
                "production_controller_import_wired"
            ]
        )
        self.assertFalse(
            reference["runtime_reference_boundary"][
                "production_planner_import_wired"
            ]
        )

    def test_valid_activation_binds_complete_opaque_reference_once(self):
        authority = activated_authority("happy")
        authority_before = copy.deepcopy(authority)

        result = self.bind_with(authority)

        self.assertEqual(authority_before, authority)
        self.assertEqual(
            {
                "authorized": 1,
                "maximum": 1,
                "started": 1,
                "consumed": 1,
                "remaining": 0,
                "retry": False,
                "resume": False,
                "fallback": False,
            },
            result["execute_ledger_after_required"],
        )
        reference = result["reference_artifact"]
        self.assertEqual(REFERENCE_STATUS, reference["status"])
        self.assertEqual(REFERENCE_MODE, reference["reference_mode"])
        self.assertEqual(PACKAGE_ID, reference["package_id"])
        self.assertEqual(
            [claim["claim_id"] for claim in self.ingested_fixture["claims"]],
            reference["claim_ids"],
        )
        self.assertEqual(
            41,
            reference["claim_reference"]["claim_count"],
        )
        self.assertEqual(
            EFFECTIVE_CONSUMER_CONTRACT_SHA256,
            reference["consumer_contract_ref"]["effective_sha256"],
        )
        boundary = reference["runtime_reference_boundary"]
        self.assertTrue(boundary["runtime_control_loop_reference_authorized"])
        self.assertTrue(boundary["runtime_planner_reference_authorized"])
        self.assertFalse(boundary["production_controller_import_wired"])
        self.assertFalse(boundary["production_planner_import_wired"])
        self.assertFalse(boundary["evidence_sufficiency_asserted"])
        self.assertFalse(boundary["certified_stop_asserted"])
        self.assertTrue(
            all(value is False for value in reference["side_effects"].values())
        )
        serialized = json.dumps(reference, ensure_ascii=False, sort_keys=True)
        for forbidden in (
            '"value":',
            '"raw_path":',
            '"label":',
            '"outcome":',
            '"oracle":',
            '"certificate":',
            '"e_case":',
        ):
            self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
