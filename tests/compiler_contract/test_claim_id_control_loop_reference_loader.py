import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_control_loop_reference_loader import (
    ACTIVATION_STATUS,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_ARTIFACT_ID,
    AUTHORITY_DESIGN_PATH,
    AUTHORITY_DESIGN_SHA256,
    AUTHORITY_DESIGN_STATUS,
    CLAIM_COUNT,
    CONTROLLER_ENTRYPOINT_PATH,
    PACKAGE_ID,
    RECEIPT_PATH,
    REFERENCE_MODE,
    REFERENCE_PATH,
    REFERENCE_SHA256,
    SURFACE_ID,
    ClaimIDControlLoopReferenceLoadError,
    load_claim_id_control_loop_reference,
    verify_controller_import_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_PATH = (
    REPO_ROOT
    / "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-controller-import-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
REFERENCE_FILE = REPO_ROOT / REFERENCE_PATH
RUN_MVP_PATH = REPO_ROOT / CONTROLLER_ENTRYPOINT_PATH
LEDGER_BEFORE = {
    "authorized": 1,
    "maximum": 1,
    "started": 0,
    "consumed": 0,
    "remaining": 1,
    "retry": False,
    "resume": False,
    "fallback": False,
}
LEDGER_AFTER = {
    "authorized": 1,
    "maximum": 1,
    "started": 1,
    "consumed": 1,
    "remaining": 0,
    "retry": False,
    "resume": False,
    "fallback": False,
}


def pretty_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode("utf-8")


def load_run_mvp():
    spec = importlib.util.spec_from_file_location(
        "run_mvp_claim_id_controller_import_tests",
        RUN_MVP_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("run_mvp module could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClaimIDControlLoopReferenceLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activation = json.loads(ACTIVATION_PATH.read_text(encoding="utf-8"))
        cls.run_mvp = load_run_mvp()

    def fresh_activation(self) -> dict:
        activation = copy.deepcopy(self.activation)
        activation["execute_ledger"] = copy.deepcopy(LEDGER_BEFORE)
        activation["execution_audit"] = None
        activation["pinned_hashes"]["controller_entrypoint_sha256"] = (
            hashlib.sha256(RUN_MVP_PATH.read_bytes()).hexdigest()
        )
        return activation

    def load_with(self, activation: dict):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(pretty_json_bytes(activation))
            return load_claim_id_control_loop_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ClaimIDControlLoopReferenceLoadError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def test_frozen_pins_and_global_registration_switch_remain_closed(self):
        verify_controller_import_pins(REPO_ROOT)
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)
        design = json.loads(
            (REPO_ROOT / AUTHORITY_DESIGN_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual(AUTHORITY_DESIGN_ARTIFACT_ID, design["artifact_id"])
        self.assertEqual(AUTHORITY_DESIGN_STATUS, design["status"])
        self.assertEqual(AUTHORITY_BASE_COMMIT, design["authority_base_commit"])
        self.assertFalse(
            design["current_authorization_state"][
                "production_controller_import_wired"
            ]
        )

    def test_missing_activation_fails_closed(self):
        self.assert_error_code(
            "missing_activation",
            lambda: load_claim_id_control_loop_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
            ),
        )

    def test_wrong_pin_and_wrong_reference_path_fail_closed(self):
        wrong_pin = self.fresh_activation()
        wrong_pin["pinned_hashes"]["bound_control_loop_reference_sha256"] = (
            "0" * 64
        )
        self.assert_error_code(
            "activation_pin",
            lambda: self.load_with(wrong_pin),
        )

        with tempfile.TemporaryDirectory() as directory:
            copied_reference = Path(directory) / "reference.json"
            copied_reference.write_bytes(REFERENCE_FILE.read_bytes())
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(
                pretty_json_bytes(self.fresh_activation())
            )
            self.assert_error_code(
                "reference_path",
                lambda: load_claim_id_control_loop_reference(
                    copied_reference,
                    repo_root=REPO_ROOT,
                    activation_path=activation_path,
                ),
            )

    def test_consumed_activation_rejects_second_import(self):
        consumed = self.fresh_activation()
        consumed["execute_ledger"] = copy.deepcopy(LEDGER_AFTER)
        consumed["execution_audit"] = {"decision": "already_consumed"}
        self.assert_error_code(
            "activation_ledger",
            lambda: self.load_with(consumed),
        )

    def test_happy_path_returns_only_immutable_read_only_provenance(self):
        activation = self.fresh_activation()
        activation_before = copy.deepcopy(activation)
        loaded = self.load_with(activation)

        self.assertEqual(activation_before, activation)
        self.assertEqual(LEDGER_AFTER, dict(loaded.execute_ledger_after_required))
        view = loaded.view
        self.assertEqual(SURFACE_ID, view.surface_id)
        self.assertEqual(PACKAGE_ID, view.package_id)
        self.assertEqual(CLAIM_COUNT, len(view.claim_ids))
        self.assertTrue(all(claim_id.startswith("clm_") for claim_id in view.claim_ids))
        with self.assertRaises(TypeError):
            view.claim_reference["claim_count"] = 0

        provenance = view.to_provenance()
        self.assertEqual(REFERENCE_MODE, provenance["reference_mode"])
        self.assertTrue(provenance["read_only"])
        self.assertEqual(REFERENCE_SHA256, provenance["source_reference_sha256"])
        self.assertNotIn("required_claim_ids", provenance)
        self.assertNotIn("visible_claim_ids", provenance)
        serialized = json.dumps(provenance, ensure_ascii=False, sort_keys=True)
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

    def test_run_mvp_no_import_is_unchanged_and_enabled_import_is_additive(self):
        loaded = self.load_with(self.fresh_activation())
        provenance = loaded.view.to_provenance()
        case_dir = REPO_ROOT / "09-experiments/examples/C01"
        case_id = json.loads(
            (case_dir / "case_config.json").read_text(encoding="utf-8")
        )["case_id"]

        with tempfile.TemporaryDirectory() as directory:
            baseline_dir = Path(directory) / "baseline"
            wired_dir = Path(directory) / "wired"
            self.run_mvp.run_all(case_dir, baseline_dir)
            self.run_mvp.run_all(
                case_dir,
                wired_dir,
                claim_id_mainline_reference=provenance,
            )

            baseline_paths = self.run_mvp.single_case_output_paths(
                baseline_dir, case_id
            )
            wired_paths = self.run_mvp.single_case_output_paths(
                wired_dir, case_id
            )
            self.assertEqual(
                baseline_paths["results"].read_bytes(),
                wired_paths["results"].read_bytes(),
            )
            self.assertEqual(
                baseline_paths["traces"].read_bytes(),
                wired_paths["traces"].read_bytes(),
            )
            baseline_summary = json.loads(
                baseline_paths["summary"].read_text(encoding="utf-8")
            )
            wired_summary = json.loads(
                wired_paths["summary"].read_text(encoding="utf-8")
            )
            self.assertNotIn("claim_id_mainline_reference", baseline_summary)
            observed_provenance = wired_summary.pop(
                "claim_id_mainline_reference"
            )
            self.assertEqual(provenance, observed_provenance)
            self.assertEqual(baseline_summary, wired_summary)

            csv_text = wired_paths["results"].read_text(encoding="utf-8")
            traces_text = wired_paths["traces"].read_text(encoding="utf-8")
            self.assertNotIn("clm_", csv_text)
            self.assertNotIn("clm_", traces_text)
            self.assertNotIn(
                "claim_id_mainline_reference",
                self.run_mvp.PLANNER_ACTION_FIELDS,
            )
            self.assertNotIn(
                "claim_id_mainline_reference",
                self.run_mvp.PLANNER_STATE_FIELDS,
            )

    def test_activation_shape_pins_loader_entrypoint_and_receipt(self):
        activation = self.fresh_activation()
        self.assertEqual(ACTIVATION_STATUS, activation["status"])
        self.assertEqual(
            AUTHORITY_DESIGN_SHA256,
            activation["authority_design"]["sha256"],
        )
        self.assertEqual(
            REFERENCE_SHA256,
            activation["selected_input"]["bound_control_loop_reference"][
                "sha256"
            ],
        )
        self.assertEqual(
            RECEIPT_PATH,
            activation["output_policy"]["versioned_receipt_path"],
        )
        self.assertFalse(
            activation["output_policy"]["production_planner_import_wired"]
        )
        self.assertFalse(
            activation["output_policy"][
                "planner_or_action_selection_algorithm_change"
            ]
        )


if __name__ == "__main__":
    unittest.main()
