from __future__ import annotations

import re
import unittest

from tests.unit.test_part_b_b9_contracts import (
    B9_NON_TEST_PATHS,
    CONFIG_DIR,
    CONFIG_PATHS,
    DOCUMENT_PATHS,
    FORBIDDEN_AUTHORITIES,
    FROZEN_UPSTREAM,
    ROOT,
    UPSTREAM_COMMIT,
    expected_frozen_artifacts,
    load_yaml,
    require_file,
)


SLICE_ORDER = ["B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8"]
ALLOWED_CLAIMS = {
    "B0_B8_FROZEN_HASHES_REPLAY",
    "B9_SCHEMAS_VALIDATE",
    "B9_CONTRACTS_INTERNALLY_CONSISTENT",
    "B9_UNKNOWN_CLAIMS_FAIL_CLOSED",
}
DENIED_CLAIMS = {
    "EMPIRICAL_VALIDITY_ESTABLISHED",
    "EXTERNAL_VALIDITY_ESTABLISHED",
    "PERFORMANCE_SUPERIORITY_ESTABLISHED",
    "GLOBAL_OPTIMALITY_ESTABLISHED",
    "HOLDOUT_RELEASED",
    "HOLDOUT_ANALYZED",
    "STATISTICAL_ANALYSIS_EXECUTED",
    "REAL_SOURCE_AUTHORIZED",
    "PLANNER_IMPLEMENTATION_ADMITTED",
    "PLANNER_EXECUTED",
    "SAMPLING_EXECUTED",
    "SCALARIZED_RANKING_VALID",
    "CERTIFICATE_ISSUED",
    "CERTIFIED_STOP_AUTHORIZED",
}
OPEN_GATES = {
    "PB-SI-006": "OPEN_BLOCKS_CONNECTOR_DATA_HOLDOUT_ACCESS",
    "PB-B5-SI-001": "OPEN_BLOCKS_IMPLEMENTATION_ADMISSION_AND_EXECUTION",
    "PB-B8-SI-004": "OPEN_REQUIRES_SEPARATE_EXECUTION_EVIDENCE",
    "HOLDOUT_RELEASE": "OPEN_DEFAULT_DENY",
    "STATISTICAL_EXECUTION": "OPEN_NOT_AUTHORIZED",
    "IMPLEMENTATION_ADMISSION": "OPEN_NOT_ESTABLISHED",
}


class PartBB9FreezeAndClaimsTests(unittest.TestCase):
    def setUp(self) -> None:
        """Keep RED counting one missing-artifact failure per test method."""
        for path in B9_NON_TEST_PATHS:
            require_file(path)

    def test_red_15_freeze_record_has_exact_slices_and_baseline(self) -> None:
        """RED-15: B9 freezes B0-B8 at the merged be33ef8 baseline."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        self.assertEqual(record.get("status"), "B9_CONTRACT_ONLY")
        self.assertEqual(
            record.get("authorized_slice"),
            "B9_FREEZE_AND_CLAIMS",
        )
        self.assertEqual(record.get("upstream_commit"), UPSTREAM_COMMIT)
        self.assertEqual(record.get("slice_order"), SLICE_ORDER)

    def test_red_16_freeze_inventory_is_finite_unique_and_has_no_b9(self) -> None:
        """RED-16: the 39-entry inventory has no extra or self-binding."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        artifacts = record["frozen_artifacts"]
        self.assertEqual(artifacts, expected_frozen_artifacts())
        self.assertEqual(len(artifacts), 39)
        self.assertNotIn("B9", {item["slice_id"] for item in artifacts})
        self.assertEqual(
            {item["slice_id"] for item in artifacts},
            set(SLICE_ORDER),
        )

    def test_red_17_every_frozen_identity_and_path_is_unique(self) -> None:
        """RED-17: path, artifact identity and hash are explicit and unique."""
        artifacts = load_yaml(CONFIG_PATHS["freeze_record"])[
            "frozen_artifacts"
        ]
        for field in ("artifact_id", "path", "hash"):
            values = [item[field] for item in artifacts]
            with self.subTest(field=field):
                self.assertEqual(len(values), len(set(values)))
        for item in artifacts:
            with self.subTest(artifact=item["artifact_id"]):
                self.assertRegex(item["hash"], r"^sha256:[0-9a-f]{64}$")
                self.assertTrue((ROOT / item["path"]).is_file())
                self.assertIn(item["slice_id"], SLICE_ORDER)

    def test_red_18_freeze_cannot_rewrite_or_activate_upstream(self) -> None:
        """RED-18: content freeze is not authority or runtime activation."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        self.assertEqual(
            record.get("freeze_semantics"),
            {
                "content_freeze": True,
                "authority_freeze": True,
                "upstream_rewrite": False,
                "runtime_activation": False,
                "execution_evidence_created": False,
            },
        )
        self.assertEqual(
            record["frozen_artifacts"],
            [dict(item) for item in FROZEN_UPSTREAM],
        )

    def test_red_19_claim_taxonomy_is_finite_closed_and_unique(self) -> None:
        """RED-19: allowed and denied claim IDs form a closed registry."""
        boundary = load_yaml(CONFIG_PATHS["claim_boundary"])
        allowed = boundary["allowed_claims"]
        denied = boundary["denied_claims"]
        allowed_ids = [entry["claim_id"] for entry in allowed]
        denied_ids = [entry["claim_id"] for entry in denied]
        self.assertEqual(set(allowed_ids), ALLOWED_CLAIMS)
        self.assertEqual(set(denied_ids), DENIED_CLAIMS)
        self.assertEqual(len(allowed_ids), len(set(allowed_ids)))
        self.assertEqual(len(denied_ids), len(set(denied_ids)))
        self.assertTrue(set(allowed_ids).isdisjoint(denied_ids))

    def test_red_20_allowed_claims_never_exceed_contract_consistency(self) -> None:
        """RED-20: the positive claim set is exact and contract-only."""
        boundary = load_yaml(CONFIG_PATHS["claim_boundary"])
        self.assertEqual(
            boundary.get("evidence_ceiling"),
            "CONTRACT_CONSISTENCY_ONLY",
        )
        for claim in boundary["allowed_claims"]:
            with self.subTest(claim=claim["claim_id"]):
                self.assertIn(claim["claim_id"], ALLOWED_CLAIMS)
                self.assertEqual(claim["decision"], "ALLOW_CONTRACT_ONLY")
                self.assertEqual(
                    claim["evidence_level"],
                    "CONTRACT_CONSISTENCY_ONLY",
                )

    def test_red_21_empirical_superiority_and_stop_claims_are_denied(self) -> None:
        """RED-21: every empirical, ranking and authority claim is denied."""
        boundary = load_yaml(CONFIG_PATHS["claim_boundary"])
        denied = {
            entry["claim_id"]: entry for entry in boundary["denied_claims"]
        }
        self.assertEqual(set(denied), DENIED_CLAIMS)
        for claim_id, claim in denied.items():
            with self.subTest(claim=claim_id):
                self.assertEqual(claim["decision"], "DENY")
                self.assertNotEqual(
                    claim.get("evidence_level"),
                    "EMPIRICALLY_VALIDATED",
                )

    def test_red_22_unknown_claims_fail_closed(self) -> None:
        """RED-22: an unregistered claim cannot be inferred or released."""
        boundary = load_yaml(CONFIG_PATHS["claim_boundary"])
        self.assertEqual(
            boundary.get("unknown_claim_behavior"),
            "DENY_UNKNOWN_CLAIM",
        )
        self.assertIs(boundary.get("claim_inference_authority"), False)
        self.assertIs(boundary.get("claim_release_authority"), False)

    def test_red_23_audit_binds_the_complete_b9_hash_chain(self) -> None:
        """RED-23: audit is last in the acyclic B9 identity chain."""
        record = load_yaml(CONFIG_PATHS["freeze_record"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        boundary = load_yaml(CONFIG_PATHS["claim_boundary"])
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        audit = load_yaml(CONFIG_PATHS["audit"])
        self.assertEqual(
            audit["bindings"],
            {
                "freeze_record_hash": record["hash"],
                "freeze_and_claims_policy_hash": policy["hash"],
                "claim_boundary_hash": boundary["hash"],
                "b9_manifest_hash": manifest["hash"],
            },
        )
        self.assertEqual(
            audit["checks"],
            {
                "frozen_artifact_count": 39,
                "frozen_paths_resolve": True,
                "frozen_hashes_replay": True,
                "schemas_validate": True,
                "claim_boundary_validates": True,
                "upstream_content_rewritten": False,
            },
        )

    def test_red_24_audit_contains_no_data_metrics_or_rankings(self) -> None:
        """RED-24: an audit snapshot is not empirical evidence."""
        audit = load_yaml(CONFIG_PATHS["audit"])
        self.assertEqual(
            audit["evidence_inventory"],
            {
                "real_source_data_present": False,
                "holdout_data_present": False,
                "holdout_labels_present": False,
                "holdout_results_present": False,
                "statistics_present": False,
                "metrics_present": False,
                "rankings_present": False,
                "execution_trace_present": False,
            },
        )

    def test_red_25_every_unresolved_gate_remains_open_or_deny(self) -> None:
        """RED-25: B9 records gates but cannot close or satisfy them."""
        audit = load_yaml(CONFIG_PATHS["audit"])
        policy = load_yaml(CONFIG_PATHS["policy"])
        self.assertEqual(audit.get("gate_states"), OPEN_GATES)
        self.assertEqual(policy.get("gate_states"), OPEN_GATES)
        self.assertEqual(
            policy["holdout_gate"]["default_decision"],
            "DENY",
        )
        self.assertIs(
            policy["holdout_gate"]["contract_unseals_holdout"],
            False,
        )

    def test_red_26_no_runtime_source_planner_sampler_or_llm_is_opened(
        self,
    ) -> None:
        """RED-26: closeout contracts cannot execute any Part B component."""
        policy = load_yaml(CONFIG_PATHS["policy"])
        runtime = policy["runtime_boundary"]
        expected_false = (
            "real_source_access",
            "holdout_access",
            "statistical_analysis",
            "connector_execution",
            "planner_execution",
            "sampling",
            "baseline_execution",
            "evaluation_execution",
            "llm_integration",
            "experiment_access",
        )
        for field in expected_false:
            with self.subTest(runtime=field):
                self.assertIs(runtime[field], False)
        for field in FORBIDDEN_AUTHORITIES:
            self.assertIs(policy[field], False)

    def test_red_27_no_certificate_system_state_or_stop_is_emitted(self) -> None:
        """RED-27: final claim freeze has no Part A certification power."""
        manifest = load_yaml(CONFIG_PATHS["manifest"])
        audit = load_yaml(CONFIG_PATHS["audit"])
        self.assertEqual(manifest["stop_authority"], "NONE")
        self.assertIs(manifest["certificate_authority"], False)
        self.assertIs(manifest["claim_release_authority"], False)
        self.assertEqual(
            audit["outputs"],
            {
                "certificate_issued": False,
                "system_status_emitted": False,
                "certified_stop_emitted": False,
                "performance_claim_released": False,
            },
        )

    def test_red_28_docs_state_local_contract_review_and_no_delivery(self) -> None:
        """RED-28: all human-readable B9 boundaries agree with the manifest."""
        combined = "\n".join(
            require_file(path).read_text(encoding="utf-8")
            for path in DOCUMENT_PATHS
        )
        required_tokens = (
            "B9_FREEZE_AND_CLAIMS",
            "B9_CONTRACT_ONLY",
            "CONTRACT_CONSISTENCY_ONLY",
            "PB-SI-006",
            "PB-B5-SI-001",
            "PB-B8-SI-004",
            "holdout",
            "CERTIFIED_STOP",
        )
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, combined)
        self.assertRegex(
            combined,
            re.compile(
                r"(commit|push|PR).{0,80}(NOT AUTHORIZED|未授权|禁止)",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertRegex(
            combined,
            re.compile(
                r"(holdout release|holdout 释放).{0,100}"
                r"(OPEN|DENY|NOT AUTHORIZED|未授权)",
                re.IGNORECASE | re.DOTALL,
            ),
        )
        self.assertNotRegex(
            combined,
            re.compile(
                r"(performance superiority|性能优越性).{0,60}"
                r"(established|validated|成立|已验证)",
                re.IGNORECASE | re.DOTALL,
            ),
        )


if __name__ == "__main__":
    unittest.main()
