import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm.m1_dual_adapter_exact_selection import (  # noqa: E402
    DENY_OUTCOME,
    FIXTURE_ADAPTER_ID,
    FIXTURE_ADAPTER_VERSION,
    FIXTURE_SOURCE_CLASS,
    INVALID_FIXTURE_SOURCE_CLASS,
    M1DualAdapterSelectionError,
    PLANNER_ADAPTER_ID,
    PLANNER_ADAPTER_VERSION,
    PLANNER_IMPLEMENTATION_PATH,
    PLANNER_IMPLEMENTATION_SHA256,
    PLANNER_SOURCE_CLASS,
    SUCCESS_OUTCOME,
    SURFACE_ID,
    design_registry_records,
    select_adapter,
    verify_selection_pins,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def request(
    source_class: str,
    adapter_id: str,
    adapter_version: str = "0.1.0",
    surface_id: str = SURFACE_ID,
) -> dict:
    return {
        "surface_id": surface_id,
        "source_class": source_class,
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
    }


class M1DualAdapterExactSelectionTests(unittest.TestCase):
    def test_selection_pins_and_design_registry_are_verified(self):
        verify_selection_pins(REPO_ROOT)
        records = design_registry_records(REPO_ROOT)

        self.assertEqual(2, len(records))
        self.assertEqual(
            {PLANNER_SOURCE_CLASS, FIXTURE_SOURCE_CLASS},
            {record["source_class"] for record in records},
        )
        self.assertTrue(
            all(
                record["execution_authorized_by_this_design"] is False
                for record in records
            )
        )

    def test_exact_planner_and_fixture_requests_select_design_records_only(self):
        with patch(
            "compiler.llm.m1_planner_inputs_adapter.adapt_planner_projection"
        ) as planner_execute, patch(
            "compiler.llm.m1_claim_ir_valid_fixture_adapter."
            "adapt_claim_ir_valid_fixture"
        ) as fixture_execute:
            planner = select_adapter(
                request(
                    PLANNER_SOURCE_CLASS,
                    PLANNER_ADAPTER_ID,
                    PLANNER_ADAPTER_VERSION,
                ),
                repo_root=REPO_ROOT,
            )
            fixture = select_adapter(
                request(
                    FIXTURE_SOURCE_CLASS,
                    FIXTURE_ADAPTER_ID,
                    FIXTURE_ADAPTER_VERSION,
                ),
                repo_root=REPO_ROOT,
            )

        for result, expected_source in (
            (planner, PLANNER_SOURCE_CLASS),
            (fixture, FIXTURE_SOURCE_CLASS),
        ):
            with self.subTest(source_class=expected_source):
                self.assertEqual(SUCCESS_OUTCOME, result["decision"])
                self.assertEqual(expected_source, result["source_class"])
                self.assertFalse(result["adapter_executed"])
                self.assertFalse(result["registry_activated"])
                self.assertEqual(64, len(result["contract_sha256"]))
        planner_execute.assert_not_called()
        fixture_execute.assert_not_called()

    def test_wrong_class_and_wrong_version_fail_closed(self):
        cases = (
            (
                request(FIXTURE_SOURCE_CLASS, PLANNER_ADAPTER_ID),
                "wrong_class",
            ),
            (
                request(FIXTURE_SOURCE_CLASS, FIXTURE_ADAPTER_ID, "0.1.1"),
                "wrong_version",
            ),
        )
        for selection_request, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(M1DualAdapterSelectionError) as context:
                    select_adapter(selection_request, repo_root=REPO_ROOT)
                self.assertEqual(expected_code, context.exception.code)
                self.assertEqual(DENY_OUTCOME, context.exception.decision)

    def test_ambiguous_duplicate_records_fail_closed(self):
        records = list(design_registry_records(REPO_ROOT))
        fixture_record = next(
            record
            for record in records
            if record["source_class"] == FIXTURE_SOURCE_CLASS
        )
        records.append(dict(fixture_record))

        with self.assertRaises(M1DualAdapterSelectionError) as context:
            select_adapter(
                request(FIXTURE_SOURCE_CLASS, FIXTURE_ADAPTER_ID),
                repo_root=REPO_ROOT,
                registry_records=records,
            )

        self.assertEqual("ambiguous_selection", context.exception.code)
        self.assertEqual(DENY_OUTCOME, context.exception.decision)

    def test_implicit_default_and_wildcard_fail_closed(self):
        implicit = {
            "surface_id": SURFACE_ID,
            "source_class": FIXTURE_SOURCE_CLASS,
            "adapter_id": None,
            "adapter_version": None,
        }
        wildcard = request("*", "m1a_*", "latest")

        for selection_request, expected_code in (
            (implicit, "implicit_default"),
            (wildcard, "wildcard_forbidden"),
        ):
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(M1DualAdapterSelectionError) as context:
                    select_adapter(selection_request, repo_root=REPO_ROOT)
                self.assertEqual(expected_code, context.exception.code)
                self.assertEqual(DENY_OUTCOME, context.exception.decision)

    def test_cross_surface_certificate_and_authority_leak_fail_closed(self):
        cases = (
            (
                request(
                    FIXTURE_SOURCE_CLASS,
                    FIXTURE_ADAPTER_ID,
                    surface_id="another_surface",
                ),
                "cross_surface",
            ),
            (
                request(
                    "certificate_experiment_inputs",
                    "m1a_certificate_inputs_v0_1",
                ),
                "certificate_out_of_scope",
            ),
            (
                request(INVALID_FIXTURE_SOURCE_CLASS, FIXTURE_ADAPTER_ID),
                "authority_leak_deny",
            ),
        )
        for selection_request, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with self.assertRaises(M1DualAdapterSelectionError) as context:
                    select_adapter(selection_request, repo_root=REPO_ROOT)
                self.assertEqual(expected_code, context.exception.code)
                self.assertEqual(DENY_OUTCOME, context.exception.decision)

    def test_planner_adapter_bytes_remain_frozen(self):
        actual = hashlib.sha256(
            (REPO_ROOT / PLANNER_IMPLEMENTATION_PATH).read_bytes()
        ).hexdigest()
        self.assertEqual(PLANNER_IMPLEMENTATION_SHA256, actual)


if __name__ == "__main__":
    unittest.main()
