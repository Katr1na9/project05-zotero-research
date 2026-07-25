import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm.claim_id_planner_reference_importer import (
    ACTIVATION_STATUS,
    AUTHORITY_BASE_COMMIT,
    AUTHORITY_DESIGN_PATH,
    ClaimIDPlannerImport,
    CONTROLLER_ACTIVATION_PATH,
    CONTROLLER_ACTIVATION_SHA256,
    IMPORTER_PATH,
    PLANNER_ADAPTER_PATH,
    PLANNER_RUNTIME_CONTRACT_PATH,
    RECEIPT_PATH,
    ClaimIDPlannerReferenceImportError,
    import_claim_id_planner_reference,
    validate_planner_sidecar,
    verify_planner_import_pins,
)
from src.compiler.llm.claim_id_control_loop_reference_loader import (
    CLAIM_COUNT,
    LOADER_PATH,
    PACKAGE_ID,
    REFERENCE_PATH,
    REFERENCE_SHA256,
    SURFACE_ID,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_PATH = (
    REPO_ROOT
    / "docs/llm-editor/"
    "llm-editor-v0.8-l2-claim-id-planner-import-wiring-"
    "single-execute-activation-v0.1-20260725.json"
)
REFERENCE_FILE = REPO_ROOT / REFERENCE_PATH
ADAPTER_FILE = REPO_ROOT / PLANNER_ADAPTER_PATH
RUN_MVP_FILE = REPO_ROOT / "09-experiments/scripts/run_mvp.py"
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_inputs():
    config = {
        "case_id": "planner-import-test",
        "budget_total": 3,
        "cti_nodes": [
            {
                "node_id": "N1",
                "stage": "execution",
                "critical": True,
                "required_claim_ids": ["E1"],
            }
        ],
        "channel_reliability": {"host": 0.8},
    }
    state = {
        "case_id": "planner-import-test",
        "step_index": 0,
        "matched_cti_node_ids": [],
        "unmatched_cti_node_ids": ["N1"],
        "matched_cti_edge_ids": [],
        "unmatched_cti_edge_ids": [],
        "coverage": {
            "cti_node_coverage": 0.0,
            "cti_edge_coverage": 0.0,
            "critical_gap_count": 1,
        },
        "budget": {
            "budget_total": 3,
            "budget_used": 0,
            "budget_remaining": 3,
        },
        "actions_taken": [],
        "action_feedback": [],
        "remaining_action_ids": ["A-low", "A-high"],
        "visible_claim_ids": ["E1"],
    }
    actions = [
        {
            "action_id": "A-low",
            "case_id": "planner-import-test",
            "action_type": "query",
            "acquisition_channel": "host",
            "target": {"target_type": "node", "target_value": "N1"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N1"],
            "expected_evidence_types": ["host"],
            "expected_stages": ["execution"],
            "expected_effects": {"expected_granularity_gain": 0.1},
            "recoverable_claim_ids": ["E1"],
        },
        {
            "action_id": "A-high",
            "case_id": "planner-import-test",
            "action_type": "query",
            "acquisition_channel": "host",
            "target": {"target_type": "node", "target_value": "N1"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N1"],
            "expected_evidence_types": ["host"],
            "expected_stages": ["execution"],
            "expected_effects": {"expected_granularity_gain": 0.2},
            "recoverable_claim_ids": ["E1"],
        },
    ]
    return config, state, actions


class ClaimIDPlannerReferenceImporterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activation = json.loads(ACTIVATION_PATH.read_text(encoding="utf-8"))
        cls.adapter = load_script(ADAPTER_FILE, "planner_runtime_adapter_claim_id_tests")
        cls.run_mvp = load_script(RUN_MVP_FILE, "run_mvp_planner_import_tests")

    def fresh_activation(self) -> dict:
        activation = copy.deepcopy(self.activation)
        activation["execute_ledger"] = copy.deepcopy(LEDGER_BEFORE)
        activation["execution_audit"] = None
        activation["pinned_hashes"]["planner_reference_importer_sha256"] = (
            sha256(REPO_ROOT / IMPORTER_PATH)
        )
        activation["pinned_hashes"]["planner_runtime_adapter_sha256"] = (
            sha256(ADAPTER_FILE)
        )
        return activation

    def import_with(self, activation: dict):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(pretty_json_bytes(activation))
            return import_claim_id_planner_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
                activation_path=activation_path,
            )

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(ClaimIDPlannerReferenceImportError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def test_frozen_chain_loader_and_contract_remain_unchanged(self):
        verify_planner_import_pins(REPO_ROOT)
        self.assertEqual(
            "3bf033296a4aceb497f8563ef1321998bbe8deb47ad80b41698b9a02017514b9",
            sha256(REPO_ROOT / LOADER_PATH),
        )
        self.assertEqual(
            CONTROLLER_ACTIVATION_SHA256,
            sha256(REPO_ROOT / CONTROLLER_ACTIVATION_PATH),
        )
        contract = json.loads(
            (REPO_ROOT / PLANNER_RUNTIME_CONTRACT_PATH).read_text(encoding="utf-8")
        )
        self.assertEqual("frozen_for_new_runs", contract["status"])
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)

    def test_missing_activation_wrong_pin_and_wrong_path_fail_closed(self):
        self.assert_error_code(
            "missing_activation",
            lambda: import_claim_id_planner_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
            ),
        )
        wrong_pin = self.fresh_activation()
        wrong_pin["pinned_hashes"]["controller_reference_loader_sha256"] = "0" * 64
        self.assert_error_code(
            "activation_pin", lambda: self.import_with(wrong_pin)
        )
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "reference.json"
            copied.write_bytes(REFERENCE_FILE.read_bytes())
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(
                pretty_json_bytes(self.fresh_activation())
            )
            self.assert_error_code(
                "reference_path",
                lambda: import_claim_id_planner_reference(
                    copied,
                    repo_root=REPO_ROOT,
                    activation_path=activation_path,
                ),
            )

    def test_consumed_activation_rejects_second_import(self):
        consumed = self.fresh_activation()
        consumed["execute_ledger"] = copy.deepcopy(LEDGER_AFTER)
        consumed["execution_audit"] = {"decision": "already_consumed"}
        self.assert_error_code(
            "activation_ledger", lambda: self.import_with(consumed)
        )

    def test_direct_mapping_bypass_and_recursive_forbidden_key_are_rejected(self):
        config, state, actions = sample_inputs()
        imported = self.import_with(self.fresh_activation())
        with self.assertRaisesRegex(ValueError, "authorized planner import"):
            self.adapter.build_runtime_view(
                config,
                state,
                actions,
                claim_id_reference_import=dict(imported.provenance),
            )
        forged = ClaimIDPlannerImport(
            provenance=imported.provenance,
            activation_sha256_before=imported.activation_sha256_before,
            execute_ledger_after_required=imported.execute_ledger_after_required,
            _seal=object(),
        )
        with self.assertRaisesRegex(ValueError, "authorized planner import"):
            self.adapter.build_runtime_view(
                config,
                state,
                actions,
                claim_id_reference_import=forged,
            )

        tampered = copy.deepcopy(dict(imported.provenance))
        tampered["registration_ref"] = dict(tampered["registration_ref"])
        tampered["registration_ref"]["required_claim_ids"] = ["clm_forbidden"]
        self.assert_error_code(
            "recursive_forbidden_keys",
            lambda: validate_planner_sidecar(tampered, repo_root=REPO_ROOT),
        )

        wrong_contract_pin = copy.deepcopy(dict(imported.provenance))
        wrong_contract_pin["consumer_contract_ref"] = dict(
            wrong_contract_pin["consumer_contract_ref"]
        )
        wrong_contract_pin["consumer_contract_ref"]["effective_sha256"] = "0" * 64
        self.assert_error_code(
            "provenance_pin",
            lambda: validate_planner_sidecar(
                wrong_contract_pin,
                repo_root=REPO_ROOT,
            ),
        )

    def test_authorized_sidecar_is_additive_and_core_action_choice_is_identical(self):
        imported = self.import_with(self.fresh_activation())
        config, state, actions = sample_inputs()
        baseline = self.adapter.build_runtime_view(config, state, actions)
        wired = self.adapter.build_runtime_view(
            config,
            state,
            actions,
            claim_id_reference_import=imported,
        )
        self.assertEqual(
            {"contract", "config", "state", "actions"}, set(baseline)
        )
        self.assertEqual(
            baseline,
            {key: wired[key] for key in baseline},
        )
        self.assertEqual(
            CLAIM_COUNT,
            len(wired["claim_id_mainline_reference"]["claim_ids"]),
        )
        self.assertEqual(
            REFERENCE_SHA256,
            wired["claim_id_mainline_reference"]["source_reference_sha256"],
        )
        contract = self.adapter.load_contract()["document"]
        forbidden = set(contract["planner_visibility"]["recursive_forbidden_keys"])
        self.assertEqual(
            [],
            self.adapter.recursive_key_hits(
                wired["claim_id_mainline_reference"], forbidden
            ),
        )

        def select_action(view):
            return max(
                view["actions"],
                key=lambda action: (
                    action["expected_effects"]["expected_granularity_gain"],
                    action["action_id"],
                ),
            )["action_id"]

        self.assertEqual(select_action(baseline), select_action(wired))
        serialized_core = json.dumps(
            {key: wired[key] for key in baseline}, sort_keys=True
        )
        self.assertNotIn("clm_", serialized_core)
        self.assertEqual(["E1"], state["visible_claim_ids"])

    def test_ml_feature_row_is_identical_with_and_without_sidecar(self):
        imported = self.import_with(self.fresh_activation())
        config, state, actions = sample_inputs()
        columns = list(
            self.adapter.load_contract()["document"]["ml_feature_contract"]["columns"]
        )

        def feature_builder(public_config, public_state, public_action):
            self.assertNotIn("claim_id_mainline_reference", public_config)
            self.assertNotIn("claim_id_mainline_reference", public_state)
            self.assertNotIn("claim_id_mainline_reference", public_action)
            return {column: float(index) for index, column in enumerate(columns)}

        baseline = self.adapter.build_ml_feature_row(
            config,
            state,
            actions[0],
            feature_builder,
            columns,
        )
        wired = self.adapter.build_ml_feature_row(
            config,
            state,
            actions[0],
            feature_builder,
            columns,
            claim_id_reference_import=imported,
        )
        self.assertEqual(baseline, wired)

    def test_fixed_outputs_remain_byte_identical_after_planner_import(self):
        imported = self.import_with(self.fresh_activation())
        config, state, actions = sample_inputs()
        self.adapter.build_runtime_view(
            config,
            state,
            actions,
            claim_id_reference_import=imported,
        )
        case_dir = REPO_ROOT / "09-experiments/examples/C01"
        case_id = json.loads(
            (case_dir / "case_config.json").read_text(encoding="utf-8")
        )["case_id"]
        with tempfile.TemporaryDirectory() as directory:
            baseline_dir = Path(directory) / "baseline"
            wired_dir = Path(directory) / "wired"
            self.run_mvp.run_all(case_dir, baseline_dir)
            self.run_mvp.run_all(case_dir, wired_dir)
            baseline_paths = self.run_mvp.single_case_output_paths(
                baseline_dir, case_id
            )
            wired_paths = self.run_mvp.single_case_output_paths(wired_dir, case_id)
            for key in ("results", "traces", "summary"):
                self.assertEqual(
                    baseline_paths[key].read_bytes(),
                    wired_paths[key].read_bytes(),
                )
            self.assertNotIn(
                "clm_", baseline_paths["results"].read_text(encoding="utf-8")
            )
            self.assertNotIn(
                "clm_", baseline_paths["traces"].read_text(encoding="utf-8")
            )

    def test_activation_shape_is_separate_and_initially_single_use(self):
        activation = self.fresh_activation()
        self.assertEqual(ACTIVATION_STATUS, activation["status"])
        self.assertEqual(AUTHORITY_BASE_COMMIT, activation["authority_base_commit"])
        self.assertEqual(
            REFERENCE_SHA256,
            activation["selected_input"]["bound_control_loop_reference"]["sha256"],
        )
        self.assertEqual(
            RECEIPT_PATH,
            activation["output_policy"]["versioned_receipt_path"],
        )
        self.assertTrue(
            activation["output_policy"]["production_controller_import_wired"]
        )
        self.assertTrue(
            activation["output_policy"][
                "production_planner_import_wired_after_success"
            ]
        )
        self.assertFalse(
            activation["output_policy"][
                "planner_or_action_selection_algorithm_change"
            ]
        )


if __name__ == "__main__":
    unittest.main()
