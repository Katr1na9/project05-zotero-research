import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm import claim_id_durable_replay_attacher as durable
from src.compiler.llm.claim_id_control_loop_reference_loader import (
    ClaimIDControlLoopReferenceLoadError,
    load_claim_id_control_loop_reference,
)
from src.compiler.llm.claim_id_planner_reference_importer import (
    ClaimIDPlannerReferenceImportError,
    import_claim_id_planner_reference,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_FILE = REPO_ROOT / durable.REFERENCE_PATH
CAPABILITY_ACTIVATION_FILE = REPO_ROOT / durable.ACTIVATION_PATH
CAPABILITY_RECEIPT_FILE = REPO_ROOT / durable.CAPABILITY_RECEIPT_PATH
CONTROLLER_ACTIVATION_FILE = REPO_ROOT / durable.CONTROLLER_ACTIVATION_PATH
PLANNER_ACTIVATION_FILE = REPO_ROOT / durable.PLANNER_ACTIVATION_PATH
RUN_MVP_FILE = REPO_ROOT / durable.CONTROLLER_ENTRYPOINT_PATH
PLANNER_ADAPTER_FILE = REPO_ROOT / durable.PLANNER_ADAPTER_PATH


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


def sample_planner_inputs():
    config = {
        "case_id": "durable-replay-test",
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
        "case_id": "durable-replay-test",
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
            "case_id": "durable-replay-test",
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
            "case_id": "durable-replay-test",
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


class ClaimIDDurableReplayAttacherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.activation = json.loads(
            CAPABILITY_ACTIVATION_FILE.read_text(encoding="utf-8")
        )
        cls.receipt = json.loads(CAPABILITY_RECEIPT_FILE.read_text(encoding="utf-8"))
        cls.receipt_sha256 = sha256(CAPABILITY_RECEIPT_FILE)
        cls.run_mvp = load_script(
            RUN_MVP_FILE, "run_mvp_claim_id_durable_replay_tests"
        )
        cls.planner_adapter = load_script(
            PLANNER_ADAPTER_FILE,
            "planner_runtime_adapter_claim_id_durable_replay_tests",
        )

    def fresh_capability_activation(self) -> dict:
        activation = copy.deepcopy(self.activation)
        activation["execute_ledger"] = copy.deepcopy(durable._LEDGER_BEFORE)
        activation["execution_audit"] = None
        activation["pinned_hashes"] = durable._activation_runtime_pins(REPO_ROOT)
        return activation

    def enable_with(self, activation: dict):
        with tempfile.TemporaryDirectory() as directory:
            activation_path = Path(directory) / "activation.json"
            activation_path.write_bytes(pretty_json_bytes(activation))
            return durable.enable_durable_replay_attach_capability(
                activation_path,
                repo_root=REPO_ROOT,
            )

    def load_durable(self, receipt_sha256: str | None = None):
        return durable.load_claim_id_durable_replay_attachment(
            REFERENCE_FILE,
            CAPABILITY_RECEIPT_FILE,
            receipt_sha256 or self.receipt_sha256,
            repo_root=REPO_ROOT,
        )

    def assert_error_code(self, expected: str, callable_):
        with self.assertRaises(durable.ClaimIDDurableReplayAttachError) as raised:
            callable_()
        self.assertEqual(expected, raised.exception.code)

    def test_static_pins_and_registration_switch_remain_closed(self):
        durable.verify_durable_replay_static_pins(REPO_ROOT)
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)
        self.assertEqual(
            durable.CONTROLLER_LOADER_SHA256,
            sha256(REPO_ROOT / durable.CONTROLLER_LOADER_PATH),
        )
        self.assertEqual(
            durable.PLANNER_IMPORTER_SHA256,
            sha256(REPO_ROOT / durable.PLANNER_IMPORTER_PATH),
        )

    def test_historical_single_execute_paths_still_reject_exhausted_activation(self):
        with self.assertRaises(ClaimIDControlLoopReferenceLoadError) as controller:
            load_claim_id_control_loop_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
                activation_path=CONTROLLER_ACTIVATION_FILE,
            )
        self.assertEqual("activation_pin", controller.exception.code)

        with self.assertRaises(ClaimIDPlannerReferenceImportError) as planner:
            import_claim_id_planner_reference(
                REFERENCE_FILE,
                repo_root=REPO_ROOT,
                activation_path=PLANNER_ACTIVATION_FILE,
            )
        self.assertEqual("activation_pin", planner.exception.code)

        controller_activation = json.loads(
            CONTROLLER_ACTIVATION_FILE.read_text(encoding="utf-8")
        )
        controller_activation["pinned_hashes"][
            "controller_entrypoint_sha256"
        ] = sha256(RUN_MVP_FILE)
        planner_activation = json.loads(
            PLANNER_ACTIVATION_FILE.read_text(encoding="utf-8")
        )
        planner_activation["pinned_hashes"][
            "planner_reference_importer_sha256"
        ] = sha256(REPO_ROOT / durable.PLANNER_IMPORTER_PATH)
        planner_activation["pinned_hashes"][
            "planner_runtime_adapter_sha256"
        ] = sha256(PLANNER_ADAPTER_FILE)
        with tempfile.TemporaryDirectory() as directory:
            controller_path = Path(directory) / "controller-activation.json"
            planner_path = Path(directory) / "planner-activation.json"
            controller_path.write_bytes(pretty_json_bytes(controller_activation))
            planner_path.write_bytes(pretty_json_bytes(planner_activation))
            with self.assertRaises(ClaimIDControlLoopReferenceLoadError) as controller:
                load_claim_id_control_loop_reference(
                    REFERENCE_FILE,
                    repo_root=REPO_ROOT,
                    activation_path=controller_path,
                )
            self.assertEqual("activation_ledger", controller.exception.code)
            with self.assertRaises(ClaimIDPlannerReferenceImportError) as planner:
                import_claim_id_planner_reference(
                    REFERENCE_FILE,
                    repo_root=REPO_ROOT,
                    activation_path=planner_path,
                )
            self.assertEqual("activation_ledger", planner.exception.code)

    def test_capability_activation_missing_wrong_pin_and_consumed_fail_closed(self):
        self.assert_error_code(
            "missing_activation",
            lambda: durable.enable_durable_replay_attach_capability(
                None, repo_root=REPO_ROOT
            ),
        )
        wrong_pin = self.fresh_capability_activation()
        wrong_pin["pinned_hashes"]["bound_reference_sha256"] = "0" * 64
        self.assert_error_code("activation_pin", lambda: self.enable_with(wrong_pin))
        self.assert_error_code(
            "activation_ledger",
            lambda: durable.enable_durable_replay_attach_capability(
                CAPABILITY_ACTIVATION_FILE,
                repo_root=REPO_ROOT,
            ),
        )

    def test_fresh_test_activation_enables_once_and_proof_attaches_are_stable(self):
        before_controller = sha256(CONTROLLER_ACTIVATION_FILE)
        before_planner = sha256(PLANNER_ACTIVATION_FILE)
        grant = self.enable_with(self.fresh_capability_activation())
        first = grant.attach_for_enablement_proof().to_provenance()
        second = grant.attach_for_enablement_proof().to_provenance()
        first_sha = durable.canonical_json_sha256(first)
        second_sha = durable.canonical_json_sha256(second)
        self.assertEqual(first_sha, second_sha)
        receipt = durable.build_capability_receipt(
            grant,
            [first_sha, second_sha],
        )
        self.assertEqual(durable.CAPABILITY_RECEIPT_STATUS, receipt["status"])
        self.assertEqual(2, receipt["repeatable_attach_proof"]["attach_call_count"])
        self.assertFalse(
            receipt["repeatable_attach_proof"][
                "successful_attach_consumes_per_run_ledger"
            ]
        )
        self.assertEqual(before_controller, sha256(CONTROLLER_ACTIVATION_FILE))
        self.assertEqual(before_planner, sha256(PLANNER_ACTIVATION_FILE))

    def test_durable_receipt_missing_or_wrong_pin_fails_closed(self):
        self.assert_error_code(
            "missing_receipt",
            lambda: durable.load_claim_id_durable_replay_attachment(
                REFERENCE_FILE,
                None,
                self.receipt_sha256,
                repo_root=REPO_ROOT,
            ),
        )
        self.assert_error_code(
            "missing_receipt_pin",
            lambda: durable.load_claim_id_durable_replay_attachment(
                REFERENCE_FILE,
                CAPABILITY_RECEIPT_FILE,
                None,
                repo_root=REPO_ROOT,
            ),
        )
        self.assert_error_code(
            "capability_receipt_pin",
            lambda: self.load_durable("0" * 64),
        )

    def test_before_ledger_and_tampered_receipt_states_are_rejected(self):
        controller = json.loads(
            CONTROLLER_ACTIVATION_FILE.read_text(encoding="utf-8")
        )
        controller["execute_ledger"] = copy.deepcopy(durable._LEDGER_BEFORE)
        controller["execution_audit"] = None
        self.assert_error_code(
            "historical_activation",
            lambda: durable._validate_historical_activation(
                controller, "controller"
            ),
        )

        tampered = copy.deepcopy(self.receipt)
        tampered["terminal_state"]["algorithm_changed"] = True
        self.assert_error_code(
            "capability_receipt",
            lambda: durable._validate_capability_receipt(
                tampered,
                runtime_pins=durable._runtime_pins(REPO_ROOT),
            ),
        )

    def test_receipt_and_exhausted_capability_activation_are_cross_bound(self):
        activation = copy.deepcopy(self.activation)
        mismatched_receipt = copy.deepcopy(self.receipt)
        mismatched_receipt["authority"]["activation"]["sha256_before"] = "0" * 64
        self.assert_error_code(
            "cross_binding",
            lambda: durable._validate_receipt_activation_cross_binding(
                mismatched_receipt,
                activation,
                receipt_sha256=self.receipt_sha256,
                current_runtime_pins=durable._runtime_pins(REPO_ROOT),
            ),
        )

        mismatched_receipt = copy.deepcopy(self.receipt)
        mismatched_receipt["repeatable_attach_proof"][
            "first_provenance_sha256"
        ] = "1" * 64
        mismatched_receipt["repeatable_attach_proof"][
            "second_provenance_sha256"
        ] = "1" * 64
        self.assert_error_code(
            "cross_binding",
            lambda: durable._validate_receipt_activation_cross_binding(
                mismatched_receipt,
                activation,
                receipt_sha256=self.receipt_sha256,
                current_runtime_pins=durable._runtime_pins(REPO_ROOT),
            ),
        )
        tampered = copy.deepcopy(self.receipt)
        tampered["side_effects"]["kernel_store_write"] = True
        self.assert_error_code(
            "capability_receipt",
            lambda: durable._validate_capability_receipt(
                tampered,
                runtime_pins=durable._runtime_pins(REPO_ROOT),
            ),
        )

    def test_two_runtime_attaches_are_stable_and_consume_no_ledger(self):
        activation_before = CAPABILITY_ACTIVATION_FILE.read_bytes()
        first = self.load_durable()
        second = self.load_durable()
        first_provenance = durable.validate_durable_replay_attachment(first)
        second_provenance = durable.validate_durable_replay_attachment(second)
        self.assertEqual(first_provenance, second_provenance)
        self.assertEqual(
            durable.canonical_json_sha256(first_provenance),
            durable.canonical_json_sha256(second_provenance),
        )
        self.assertEqual(41, len(first_provenance["claim_ids"]))
        self.assertTrue(first_provenance["read_only"])
        self.assertEqual(activation_before, CAPABILITY_ACTIVATION_FILE.read_bytes())

    def test_planner_sidecar_is_sealed_additive_and_ml_features_are_identical(self):
        attachment = self.load_durable()
        config, state, actions = sample_planner_inputs()
        baseline = self.planner_adapter.build_runtime_view(config, state, actions)
        wired = self.planner_adapter.build_runtime_view(
            config,
            state,
            actions,
            claim_id_durable_replay_attachment=attachment,
        )
        self.assertEqual(baseline, {key: wired[key] for key in baseline})
        self.assertEqual(
            [],
            self.planner_adapter.recursive_key_hits(
                wired["claim_id_mainline_reference"],
                set(
                    self.planner_adapter.load_contract()["document"][
                        "planner_visibility"
                    ]["recursive_forbidden_keys"]
                ),
            ),
        )
        self.assertNotIn(
            "clm_",
            json.dumps({key: wired[key] for key in baseline}, sort_keys=True),
        )
        self.assertEqual(["E1"], state["visible_claim_ids"])

        with self.assertRaisesRegex(ValueError, "authorized durable replay"):
            self.planner_adapter.build_runtime_view(
                config,
                state,
                actions,
                claim_id_durable_replay_attachment=attachment.to_provenance(),
            )

        columns = list(
            self.planner_adapter.load_contract()["document"][
                "ml_feature_contract"
            ]["columns"]
        )

        def feature_builder(public_config, public_state, public_action):
            self.assertNotIn("claim_id_mainline_reference", public_config)
            self.assertNotIn("claim_id_mainline_reference", public_state)
            self.assertNotIn("claim_id_mainline_reference", public_action)
            return {column: float(index) for index, column in enumerate(columns)}

        baseline_features = self.planner_adapter.build_ml_feature_row(
            config,
            state,
            actions[0],
            feature_builder,
            columns,
        )
        wired_features = self.planner_adapter.build_ml_feature_row(
            config,
            state,
            actions[0],
            feature_builder,
            columns,
            claim_id_durable_replay_attachment=attachment,
        )
        self.assertEqual(baseline_features, wired_features)

    def test_controller_outputs_are_identical_except_additive_summary_sidecar(self):
        first = self.run_mvp.load_claim_id_durable_replay_reference(
            REFERENCE_FILE,
            CAPABILITY_RECEIPT_FILE,
            self.receipt_sha256,
        )
        second = self.run_mvp.load_claim_id_durable_replay_reference(
            REFERENCE_FILE,
            CAPABILITY_RECEIPT_FILE,
            self.receipt_sha256,
        )
        self.assertEqual(first["provenance"], second["provenance"])
        self.assertFalse(first["per_attach_ledger_consumed"])

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
                claim_id_mainline_reference=first["provenance"],
            )
            baseline_paths = self.run_mvp.single_case_output_paths(
                baseline_dir, case_id
            )
            wired_paths = self.run_mvp.single_case_output_paths(wired_dir, case_id)
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
            self.assertEqual(
                first["provenance"],
                wired_summary.pop("claim_id_mainline_reference"),
            )
            self.assertEqual(baseline_summary, wired_summary)
            self.assertNotIn(
                "clm_", wired_paths["results"].read_text(encoding="utf-8")
            )
            self.assertNotIn(
                "clm_", wired_paths["traces"].read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
