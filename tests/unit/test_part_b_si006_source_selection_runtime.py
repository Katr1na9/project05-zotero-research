from __future__ import annotations

from copy import deepcopy
import importlib
import json
import unittest


ADAPTER_CONFORMANCE_HASH = (
    "sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a"
)
RUNTIME_MODULE = "src.scope.part_b_si006_source_selection"


def require_runtime(test: unittest.TestCase):
    try:
        return importlib.import_module(RUNTIME_MODULE)
    except ModuleNotFoundError as error:
        if error.name == RUNTIME_MODULE:
            test.fail(
                "missing approved SI-006 source-selection module: "
                "src/scope/part_b_si006_source_selection.py"
            )
        raise


def abstract_candidate() -> dict[str, object]:
    return {
        "selection_id": "si006-selection-fixture-001",
        "source_pointer": {
            "source_id": "abstract-si006-source-not-authorized",
            "record_id": "abstract-si006-record-001",
            "content_hash": "sha256:" + "1" * 64,
            "range": {
                "kind": "ROWS",
                "start": 0,
                "end": 1,
                "end_semantics": "EXCLUSIVE",
            },
            "range_semantics": "ROWS_HALF_OPEN",
        },
        "source_status": "ABSTRACT_CONTRACT_FIXTURE_NOT_AUTHORIZED",
        "source_authorization": "NOT_AUTHORIZED",
        "modality": "observed",
        "truth_status": "unassessed",
        "epistemic_role": "background_intelligence",
        "certification_authority": {
            "allowed": False,
            "levels": [],
            "basis_rule_id": None,
            "policy_hash": None,
        },
        "world_semantics": {
            "mode": "OPEN_WORLD",
            "zero_hit_semantics": "UNKNOWN_NOT_ABSENCE",
            "completeness_attestation": None,
        },
        "adapter_conformance": {
            "contract_id": "part-b-adapter-conformance-v0.8",
            "contract_hash": ADAPTER_CONFORMANCE_HASH,
            "decision": "CONFORMANT",
            "pointer_ownership_transferred": False,
        },
        "requested_authorities": {
            "source_authorization": False,
            "retrieval": False,
            "download": False,
            "credential_use": False,
            "connector_execution": False,
            "holdout_release": False,
            "certified_stop": False,
        },
    }


def evaluate(test: unittest.TestCase, candidate: dict[str, object]) -> dict:
    runtime = require_runtime(test)
    evaluator = getattr(runtime, "evaluate_source_selection", None)
    if evaluator is None:
        test.fail(
            "missing approved SI-006 source-selection API: "
            "evaluate_source_selection"
        )
    result = evaluator(candidate)
    test.assertIsInstance(result, dict)
    return result


def assert_authority_denied(
    test: unittest.TestCase, result: dict[str, object]
) -> None:
    authority = result["authority_boundary"]
    for field in (
        "source_authorization_authority",
        "retrieval_authority",
        "download_authority",
        "credential_use_authority",
        "connector_execution_authority",
        "planner_execution_authority",
    ):
        with test.subTest(field=field):
            test.assertIs(authority[field], False)
    test.assertEqual(authority["holdout_release"], "DENY")
    test.assertEqual(authority["stop_authority"], "NONE")


class PartBSI006SourceSelectionRuntimeTests(unittest.TestCase):
    def test_red_09_abstract_candidate_is_selected_contract_only(self) -> None:
        """RED-09: local evaluation may emit only a contract selection."""
        result = evaluate(self, abstract_candidate())
        self.assertEqual(result["decision"], "SELECTED_CONTRACT_ONLY")
        self.assertEqual(
            result["reason_code"],
            "SI006-SELECTION-000_CONTRACT_ONLY",
        )
        self.assertEqual(
            result["source_status"],
            "ABSTRACT_CONTRACT_FIXTURE_NOT_AUTHORIZED",
        )
        self.assertEqual(result["source_authorization"], "NOT_AUTHORIZED")
        assert_authority_denied(self, result)

    def test_red_10_same_input_replays_same_record_and_hash(self) -> None:
        """RED-10: source-selection records are byte-for-value reproducible."""
        candidate = abstract_candidate()
        first = evaluate(self, candidate)
        second = evaluate(self, deepcopy(candidate))
        self.assertEqual(first, second)
        self.assertRegex(
            first["selection_record_hash"], r"^sha256:[0-9a-f]{64}$"
        )
        serialized = json.dumps(first, sort_keys=True, separators=(",", ":"))
        self.assertEqual(
            serialized,
            json.dumps(second, sort_keys=True, separators=(",", ":")),
        )

    def test_red_11_missing_required_fields_fail_closed(self) -> None:
        """RED-11: absent pointer/epistemic/conformance fields are denied."""
        for field in (
            "source_pointer",
            "modality",
            "truth_status",
            "epistemic_role",
            "certification_authority",
            "world_semantics",
            "adapter_conformance",
            "requested_authorities",
        ):
            with self.subTest(field=field):
                candidate = abstract_candidate()
                del candidate[field]
                result = evaluate(self, candidate)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "SI006-SELECTION-001_MISSING_REQUIRED_FIELD",
                )
                assert_authority_denied(self, result)

    def test_red_12_unknown_fields_fail_closed(self) -> None:
        """RED-12: the local selector has a closed input surface."""
        candidate = abstract_candidate()
        candidate["undeclared_dataset_authority"] = True
        result = evaluate(self, candidate)
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(
            result["reason_code"],
            "SI006-SELECTION-002_UNKNOWN_FIELD",
        )
        assert_authority_denied(self, result)

    def test_red_13_pointer_units_and_ranges_cannot_be_inferred(self) -> None:
        """RED-13: malformed or implicit pointer semantics are denied."""
        variants = []

        missing_semantics = abstract_candidate()
        del missing_semantics["source_pointer"]["range_semantics"]
        variants.append(missing_semantics)

        mismatched_units = abstract_candidate()
        mismatched_units["source_pointer"]["range_semantics"] = (
            "BYTES_HALF_OPEN"
        )
        variants.append(mismatched_units)

        inclusive_end = abstract_candidate()
        inclusive_end["source_pointer"]["range"]["end_semantics"] = (
            "INCLUSIVE"
        )
        variants.append(inclusive_end)

        empty_range = abstract_candidate()
        empty_range["source_pointer"]["range"]["end"] = 0
        variants.append(empty_range)

        for candidate in variants:
            with self.subTest(candidate=candidate["source_pointer"]):
                result = evaluate(self, candidate)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "SI006-SELECTION-003_POINTER_INVALID",
                )
                assert_authority_denied(self, result)

    def test_red_14_adapter_conformance_must_match_frozen_contract(self) -> None:
        """RED-14: missing, wrong or ownership-widening conformance is denied."""
        variants = []

        wrong_hash = abstract_candidate()
        wrong_hash["adapter_conformance"]["contract_hash"] = (
            "sha256:" + "0" * 64
        )
        variants.append(wrong_hash)

        wrong_contract = abstract_candidate()
        wrong_contract["adapter_conformance"]["contract_id"] = (
            "unknown-adapter-contract"
        )
        variants.append(wrong_contract)

        not_conformant = abstract_candidate()
        not_conformant["adapter_conformance"]["decision"] = "UNKNOWN"
        variants.append(not_conformant)

        owns_pointer = abstract_candidate()
        owns_pointer["adapter_conformance"][
            "pointer_ownership_transferred"
        ] = True
        variants.append(owns_pointer)

        for candidate in variants:
            with self.subTest(conformance=candidate["adapter_conformance"]):
                result = evaluate(self, candidate)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "SI006-SELECTION-004_ADAPTER_CONFORMANCE_INVALID",
                )
                assert_authority_denied(self, result)

    def test_red_15_real_endpoint_or_authority_request_is_denied(self) -> None:
        """RED-15: a selector cannot turn a real endpoint into an access grant."""
        endpoint = abstract_candidate()
        endpoint["source_pointer"]["source_id"] = (
            "https://example.invalid/real-source"
        )
        endpoint_result = evaluate(self, endpoint)
        self.assertEqual(endpoint_result["decision"], "DENY")
        self.assertEqual(
            endpoint_result["reason_code"],
            "SI006-SELECTION-005_SOURCE_NOT_ABSTRACT",
        )
        assert_authority_denied(self, endpoint_result)

        for authority in (
            "source_authorization",
            "retrieval",
            "download",
            "credential_use",
            "connector_execution",
            "holdout_release",
            "certified_stop",
        ):
            with self.subTest(authority=authority):
                requested = abstract_candidate()
                requested["requested_authorities"][authority] = True
                result = evaluate(self, requested)
                self.assertEqual(result["decision"], "DENY")
                self.assertEqual(
                    result["reason_code"],
                    "SI006-SELECTION-007_AUTHORITY_REQUEST_FORBIDDEN",
                )
                assert_authority_denied(self, result)

    def test_red_16_world_semantics_fail_closed_without_completeness(
        self,
    ) -> None:
        """RED-16: open zero-hit stays unknown; closed absence needs proof."""
        open_world = evaluate(self, abstract_candidate())
        self.assertEqual(
            open_world["world_semantics"]["zero_hit_semantics"],
            "UNKNOWN_NOT_ABSENCE",
        )
        self.assertIsNone(
            open_world["world_semantics"]["completeness_attestation"]
        )

        closed_without_attestation = abstract_candidate()
        closed_without_attestation["world_semantics"] = {
            "mode": "CLOSED_BOUNDED",
            "zero_hit_semantics": "ABSENCE_ONLY_WITH_COMPLETE_ATTESTATION",
            "completeness_attestation": None,
        }
        result = evaluate(self, closed_without_attestation)
        self.assertEqual(result["decision"], "DENY")
        self.assertEqual(
            result["reason_code"],
            "SI006-SELECTION-006_WORLD_SEMANTICS_INVALID",
        )
        assert_authority_denied(self, result)


if __name__ == "__main__":
    unittest.main()
