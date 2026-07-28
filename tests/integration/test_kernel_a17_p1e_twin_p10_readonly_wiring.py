from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from src.cli.kernel_e2e import DeterministicKernelE2EDriver
from src.executor.deterministic import DeterministicObservationExecutor
from src.planner import twin_p10_readonly_wiring as wiring
from src.scope.system_state import SystemStateDeriver
from tests.integration.test_twin_kernel_e2e_p10 import twin_request


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT
    / "tests"
    / "unit"
    / "fixtures"
    / "kernel_a17_p1e_twin_p10_readonly_wiring_v0.1.json"
)
HISTORICAL_TRACE_PATH = (
    ROOT
    / "tests"
    / "fixtures"
    / "TWIN-COUNTEREXAMPLE-001"
    / "expected"
    / "resource_trace.jsonl"
)


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class KernelA17P1eTwinP10ReadonlyWiringIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_fixture()
        self.authority = deepcopy(self.fixture["test_only_authority"])

    def call(self, input_name):
        return wiring.evaluate_twin_p10_fixed_case_for_depth1_candidacy(
            deepcopy(self.fixture["caller_inputs"][input_name]),
            test_only_authority=deepcopy(self.authority),
        )

    def test_none_mode_calls_no_p5_p10_or_system_state_and_writes_nothing(self):
        before = {
            path: file_sha256(ROOT / path)
            for path in wiring._EXPECTED_FILE_SHA256
        }
        with patch.object(
            DeterministicObservationExecutor,
            "execute",
            side_effect=AssertionError("P5 must not be called"),
        ) as p5, patch.object(
            DeterministicKernelE2EDriver,
            "run",
            side_effect=AssertionError("P10 driver must not be called"),
        ) as p10, patch.object(
            SystemStateDeriver,
            "derive",
            side_effect=AssertionError("system state must not be derived"),
        ) as system_state:
            result = self.call("none")

        p5.assert_not_called()
        p10.assert_not_called()
        system_state.assert_not_called()
        self.assertEqual(
            wiring.STATUS_SIDECAR_NO_TRACE, result["wiring_status"]
        )
        self.assertIsNone(result["resource_trace_binding_receipt"])
        self.assertEqual(
            before,
            {
                path: file_sha256(ROOT / path)
                for path in wiring._EXPECTED_FILE_SHA256
            },
        )

    def test_all_historical_rows_are_passed_unmodified_and_deny_binding(self):
        trace_before = HISTORICAL_TRACE_PATH.read_bytes()
        original_validator = wiring.depth1.validate_resource_trace_binding
        names = {
            "ATTEMPT-001": "historical_attempt_001",
            "ATTEMPT-002": "historical_attempt_002",
            "ATTEMPT-003": "historical_attempt_003",
        }
        for attempt_id, input_name in names.items():
            with self.subTest(attempt_id=attempt_id), patch.object(
                wiring.depth1,
                "validate_resource_trace_binding",
                wraps=original_validator,
            ) as validator:
                result = self.call(input_name)

                self.assertEqual(1, validator.call_count)
                passed_row = validator.call_args.args[1]
                self.assertEqual(
                    set(self.fixture["historical_trace_contract"]["top_level_fields"]),
                    set(passed_row),
                )
                self.assertEqual(5, len(passed_row))
                self.assertEqual(attempt_id, passed_row["attempt_id"])
                self.assertNotIn(
                    "planner_decision_record_hash", passed_row
                )
                self.assertNotIn("resource_budget_hash", passed_row)
                self.assertEqual(
                    wiring.STATUS_SIDECAR_TRACE_DENIED,
                    result["wiring_status"],
                )
                receipt = result["resource_trace_binding_receipt"]
                expected = self.fixture["expected_historical_receipts"][
                    attempt_id
                ]
                self.assertEqual(
                    expected["match_status"], receipt["match_status"]
                )
                self.assertEqual(
                    expected["reason_codes"], receipt["reason_codes"]
                )
                self.assertEqual(
                    expected["receipt_hash"], receipt["receipt_hash"]
                )
                self.assertEqual(
                    result["decision_record"]["reason_codes"],
                    ["P1E-SELECT-001_EXACT_DEPTH1_WORLD_REDUCTION"],
                )

        self.assertEqual(trace_before, HISTORICAL_TRACE_PATH.read_bytes())
        self.assertEqual(
            self.fixture["historical_trace_contract"]["content_sha256"],
            file_sha256(HISTORICAL_TRACE_PATH),
        )

    def test_p10_outcome_stays_separate_and_has_no_planner_decision(self):
        driver = DeterministicKernelE2EDriver()
        before = driver.run(twin_request()).to_outcome_fields()
        sidecar = self.call("none")
        after = driver.run(twin_request()).to_outcome_fields()

        self.assertEqual(before, after)
        self.assertNotIn("planner_decision", before)
        self.assertNotIn("p1e_request", before)
        self.assertNotIn("p1e_decision", before)
        self.assertNotIn("candidacy_sidecar", before)
        self.assertEqual(
            "NEXT_ACTION_CANDIDACY_SIDECAR_ONLY",
            sidecar["result_class"],
        )
        self.assertNotIn(
            sidecar["decision_record"]["record_hash"],
            json.dumps(before),
        )

    def test_protected_pins_and_red_pins_have_zero_drift(self):
        for path, expected in wiring._EXPECTED_FILE_SHA256.items():
            with self.subTest(path=path):
                self.assertEqual(expected, file_sha256(ROOT / path))

        protected = {
            "src/planner/deterministic_depth1.py": (
                "ada6a8065e71fda58dde7e2b71ca19d7"
                "aded9a39f4cf5f67fb20d6fc5d7e38ff"
            ),
            "src/actions/selection.py": (
                "16f26fa8ca5fa0fe39a9b901b8b13a09"
                "9f5527ed0c21f77718fd57763f847a83"
            ),
            "src/executor/deterministic.py": (
                "4e5ec71edc536bfef70fe19f86a723ac5"
                "7b4ab5370bc845fa074ad2d107ba32a"
            ),
            "src/cli/kernel_e2e.py": (
                "8a7807c32d70e98ac5a36bda3a56f227"
                "9ebffbe23e0d2c6a11286bdba9208d60"
            ),
            "tests/integration/test_twin_kernel_e2e_p10.py": (
                "a332cbce5f8bdc9b0fd4467fbc09d025"
                "5d6099716c0405ffc5b47a13cdd26254"
            ),
            "tests/integration/twin_kernel_inputs.py": (
                "16323f3c415e903eeb2e72bdb94e11633"
                "8c1770d8212bbf3f5917d48b4c4bdf3"
            ),
            (
                "tests/fixtures/TWIN-COUNTEREXAMPLE-001/expected/"
                "resource_trace.jsonl"
            ): (
                "2c3e5da8692070fb44e594666e337bcca"
                "6c4d3d09ad8662eabcbd1ee45c92318"
            ),
        }
        for path, expected in protected.items():
            with self.subTest(protected=path):
                self.assertEqual(expected, file_sha256(ROOT / path))

    def test_module_has_no_p10_or_p5_runtime_import(self):
        source = (
            ROOT / "src" / "planner" / "twin_p10_readonly_wiring.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("from src.cli.kernel_e2e import", source)
        self.assertNotIn("import src.cli.kernel_e2e", source)
        self.assertNotIn("from src.executor.deterministic import", source)
        self.assertNotIn("import src.executor.deterministic", source)
        self.assertNotIn("DeterministicKernelE2EDriver(", source)
        self.assertNotIn("DeterministicObservationExecutor(", source)
        self.assertNotIn("SystemStateDeriver(", source)
        self.assertNotIn("MATCH_TEST_ONLY_REPLAY\"", source)
        self.assertFalse(wiring.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(wiring.ACTION_EXECUTION_ENABLED)
        self.assertFalse(wiring.SYSTEM_STATE_AUTHORITY)
        self.assertFalse(wiring.STOP_AUTHORITY)


if __name__ == "__main__":
    unittest.main()
