from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
import yaml


ROOT = Path(__file__).resolve().parents[2]

IDENTITY_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-planner-implementation-identity-example-v0.8.yaml"
)
EVIDENCE_PATH = (
    ROOT
    / "configs"
    / "part-b-b5-planner-admission-evidence-example-v0.8.yaml"
)
POLICY_PATH = (
    ROOT / "configs" / "part-b-b5-planner-admission-policy-v0.8.yaml"
)
RECORD_SCHEMA_PATH = (
    ROOT / "schemas" / "part-b-b5-planner-admission-record.schema.json"
)

LEGACY_IMPLEMENTATION_ID = "project05_m3star_h3_dual"

try:
    admission_api = importlib.import_module(
        "src.scope.part_b_b5_planner_admission"
    )
except (ImportError, ModuleNotFoundError):
    admission_api = None


def load_yaml(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(
            "missing approved B5 planner-admission artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AssertionError(
            "missing approved B5 planner-admission artifact: "
            f"{path.relative_to(ROOT)}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


class PartBB5PlannerAdmissionRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertIsNotNone(
            admission_api,
            "missing approved B5 planner-admission module: "
            "src.scope.part_b_b5_planner_admission",
        )
        self.identity = load_yaml(IDENTITY_PATH)
        self.evidence = load_yaml(EVIDENCE_PATH)
        self.policy = load_yaml(POLICY_PATH)
        self.record_schema = load_json(RECORD_SCHEMA_PATH)

    def evaluate(
        self,
        *,
        identity: dict[str, object] | None = None,
        evidence: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return admission_api.evaluate_admission(
            identity=self.identity if identity is None else identity,
            evidence=self.evidence if evidence is None else evidence,
            policy=self.policy,
        )

    def test_red_09_identical_inputs_replay_identical_admission_record(
        self,
    ) -> None:
        """RED-09: the local admission decision is deterministic."""
        left = self.evaluate()
        right = self.evaluate()
        self.assertEqual(left, right)
        self.assertRegex(left["record_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertRegex(left["hash"], r"^sha256:[0-9a-f]{64}$")

    def test_red_10_verified_skeleton_is_conformance_only(self) -> None:
        """RED-10: admission may pass while execution remains denied."""
        record = self.evaluate()
        self.assertEqual(
            record["decision"],
            "ADMITTED_CONFORMANCE_ONLY",
        )
        self.assertEqual(
            record["admission_scope"],
            "INTERFACE_CONFORMANCE_ONLY",
        )
        self.assertEqual(
            record["implementation_id"],
            self.identity["implementation_id"],
        )
        self.assertFalse(record["planner_execution_authority"])
        self.assertFalse(record["evaluation_execution_authority"])
        self.assertEqual(record["stop_authority"], "NONE")

    def test_red_11_legacy_m3star_is_explicitly_not_admitted(self) -> None:
        """RED-11: the legacy identifier never inherits skeleton admission."""
        identity = deepcopy(self.identity)
        evidence = deepcopy(self.evidence)
        identity["implementation_id"] = LEGACY_IMPLEMENTATION_ID
        evidence["implementation_id"] = LEGACY_IMPLEMENTATION_ID

        record = self.evaluate(identity=identity, evidence=evidence)
        self.assertEqual(
            record["decision"],
            "DENY_NOT_ADMITTED_UNVERIFIED",
        )
        self.assertIn(
            "B5-ADM-LEGACY-NOT-ADMITTED",
            record["reason_codes"],
        )
        self.assertFalse(record["planner_execution_authority"])

    def test_red_12_unknown_implementation_id_fails_closed(self) -> None:
        """RED-12: no unregistered implementation can obtain a record."""
        identity = deepcopy(self.identity)
        evidence = deepcopy(self.evidence)
        identity["implementation_id"] = "UNKNOWN-PLANNER-ID"
        evidence["implementation_id"] = "UNKNOWN-PLANNER-ID"

        record = self.evaluate(identity=identity, evidence=evidence)
        self.assertEqual(
            record["decision"],
            "DENY_UNKNOWN_IMPLEMENTATION",
        )
        self.assertIn("B5-ADM-UNKNOWN-ID", record["reason_codes"])
        self.assertFalse(record["planner_execution_authority"])

    def test_red_13_missing_or_mismatched_evidence_is_denied(self) -> None:
        """RED-13: incomplete or stale evidence never degrades to admit."""
        incomplete = deepcopy(self.evidence)
        incomplete["evidence_slots"].pop("runtime_conformance")
        incomplete_record = self.evaluate(evidence=incomplete)
        self.assertEqual(
            incomplete_record["decision"],
            "DENY_EVIDENCE_INCOMPLETE",
        )

        mismatched = deepcopy(self.evidence)
        mismatched["implementation_identity_hash"] = "sha256:" + ("0" * 64)
        mismatch_record = self.evaluate(evidence=mismatched)
        self.assertEqual(
            mismatch_record["decision"],
            "DENY_EVIDENCE_HASH_MISMATCH",
        )

    def test_red_14_runtime_conformance_failure_is_not_unknown_success(
        self,
    ) -> None:
        """RED-14: failed runtime conformance has one explicit deny channel."""
        failed = deepcopy(self.evidence)
        failed["evidence_slots"]["runtime_conformance"]["status"] = "FAILED"
        record = self.evaluate(evidence=failed)
        self.assertEqual(
            record["decision"],
            "DENY_RUNTIME_CONFORMANCE_FAILED",
        )
        self.assertIn(
            "B5-ADM-RUNTIME-CONFORMANCE-FAILED",
            record["reason_codes"],
        )
        self.assertFalse(record["planner_execution_authority"])

    def test_red_15_record_has_no_action_performance_or_stop_output(
        self,
    ) -> None:
        """RED-15: admission emits evidence status, never Planner output."""
        record = self.evaluate()
        for forbidden_key in (
            "selected_action_id",
            "action_payload",
            "public_state",
            "cost",
            "scalar_score",
            "rank",
            "performance_metric",
            "superiority_claim",
            "certificate",
            "system_status",
            "CERTIFIED_STOP",
        ):
            with self.subTest(forbidden_key=forbidden_key):
                self.assertNotIn(forbidden_key, record)
                self.assertNotIn(forbidden_key, record.values())

    def test_red_16_record_is_schema_valid_and_evidence_bound(self) -> None:
        """RED-16: the record binds identity/evidence without execution."""
        record = self.evaluate()
        self.assertEqual(
            list(
                Draft202012Validator(
                    self.record_schema
                ).iter_errors(record)
            ),
            [],
        )
        self.assertEqual(
            record["implementation_identity_hash"],
            self.identity["hash"],
        )
        self.assertEqual(
            record["admission_evidence_hash"],
            self.evidence["hash"],
        )
        self.assertEqual(
            record["policy_hash"],
            self.policy["hash"],
        )
        self.assertFalse(record["holdout_release_authority"])
        self.assertFalse(record["performance_claim_authority"])
        self.assertFalse(record["scalarization_authority"])


if __name__ == "__main__":
    unittest.main()
