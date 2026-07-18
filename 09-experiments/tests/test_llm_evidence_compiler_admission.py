import copy
import importlib.util
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_script("build_compiler_public_request")
admission = load_script("validate_compiler_admission")


def fixture_request_candidate(target_predicates=None):
    record = builder.build_record(
        "REC-0000000000000001",
        {
            "operation": "EVENT_WRITE",
            "process": "powershell.exe",
            "path": "C:\\Temp\\A.zip",
        },
        scope={"host_id": "host-a"},
        time_window={
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-01T00:00:01Z",
        },
    )
    artifact = builder.build_artifact(
        "ART-0000000000000001",
        "local_log",
        [record],
        scope={"host_id": "host-a"},
    )
    target = builder.build_target_node(
        "NODE-0000000000000001",
        "A process writes an archive file",
        allowed_claim_types=["file_activity"],
        allowed_predicates=target_predicates or ["wrote"],
    )
    request = builder.build_public_request(
        case_id="C04-compiler-development",
        split="development",
        step_index=0,
        visible_artifacts=[artifact],
        target_nodes=[target],
        predicate_allowlist={"local_log": ["wrote"]},
    )
    run_id = builder.derive_scoped_id("RUN", request["request_id"], "stub")
    candidate_id = builder.derive_scoped_id(
        "CAND", request["request_id"], run_id, "0"
    )
    pointer = {
        "artifact_id": artifact["artifact_id"],
        "record_id": record["record_id"],
    }
    candidate = {
        "compiler_run_id": run_id,
        "request_id": request["request_id"],
        "candidate_id": candidate_id,
        "source_pointer": pointer,
        "source_quote_or_fields": ["powershell.exe", "C:\\Temp\\A.zip"],
        "entity_scope": {"scope_status": "known", "host_id": "host-a"},
        "proposed_claim": {
            "case_id": request["case_id"],
            "source_type": "local_log",
            "claim_type": "file_activity",
            "subject": {"entity_type": "process", "value": "powershell.exe"},
            "predicate": "wrote",
            "object": {"entity_type": "file", "value": "C:\\Temp\\A.zip"},
            "time_window": {
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-01-01T00:00:01Z",
            },
            "observable_status": "visible",
            "source_pointer": copy.deepcopy(pointer),
        },
        "proposed_target_node_ids": [target["node_id"]],
    }
    bundle = {
        "compiler_run_id": run_id,
        "request_id": request["request_id"],
        "status": "completed",
        "candidate_claims": [candidate],
        "abstention_reasons": [],
    }
    return request, candidate, bundle


class MechanicalAdmissionTests(unittest.TestCase):
    def assert_rejected_for(self, mutate, reason):
        request, _, bundle = fixture_request_candidate()
        mutate(request, bundle["candidate_claims"][0])
        result = admission.admit_candidates(request, bundle)
        reasons = {
            code
            for row in result["rejections"]
            for code in row["reason_codes"]
        }
        self.assertIn(reason, reasons)
        self.assertEqual([], result["admitted_claims"])

    def test_valid_candidate_becomes_claim_binding_and_support_link(self):
        request, _, bundle = fixture_request_candidate()

        result = admission.admit_candidates(request, bundle)

        self.assertEqual("completed", result["status"])
        self.assertEqual(1, len(result["admitted_claims"]))
        self.assertEqual(2, len(result["entity_bindings"]))
        self.assertEqual(1, len(result["claim_node_links"]))
        claim = result["admitted_claims"][0]
        self.assertRegex(claim["claim_id"], r"^ADM-[A-F0-9]{24}$")
        self.assertEqual("visible", claim["observable_status"])
        self.assertNotIn("mapped_tactic", claim)
        self.assertNotIn("confidence", claim)
        self.assertEqual(
            request["visible_artifacts"][0]["records"][0]["record_sha256"],
            claim["source_pointer"]["hash"],
        )
        self.assertTrue(result["claim_node_links"][0]["controller_eligible"])

    def test_missing_pointer_record_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["source_pointer"].update(
                {"record_id": "REC-FFFFFFFFFFFFFFFF"}
            ),
            "pointer_missing",
        )

    def test_claim_pointer_must_match_envelope_pointer(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["proposed_claim"][
                "source_pointer"
            ].update({"record_id": "REC-FFFFFFFFFFFFFFFF"}),
            "pointer_mismatch",
        )

    def test_surface_value_not_in_record_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["proposed_claim"]["object"].update(
                {"value": "C:\\Secret\\not-visible.bin"}
            ),
            "surface_value_missing",
        )

    def test_predicate_outside_source_allowlist_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["proposed_claim"].update(
                {"predicate": "deleted"}
            ),
            "predicate_not_allowed",
        )

    def test_actor_or_campaign_entity_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["proposed_claim"]["subject"].update(
                {"entity_type": "actor"}
            ),
            "conclusion_entity_forbidden",
        )

    def test_entity_scope_conflict_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["entity_scope"].update(
                {"host_id": "host-b"}
            ),
            "entity_scope_conflict",
        )

    def test_out_of_window_time_is_rejected(self):
        self.assert_rejected_for(
            lambda request, candidate: candidate["proposed_claim"][
                "time_window"
            ].update(
                {
                    "start": "2026-01-02T00:00:00Z",
                    "end": "2026-01-02T00:00:01Z",
                }
            ),
            "time_conflict",
        )

    def test_unknown_target_rejects_link_but_keeps_observation_claim(self):
        request, _, bundle = fixture_request_candidate()
        bundle["candidate_claims"][0]["proposed_target_node_ids"] = [
            "NODE-FFFFFFFFFFFFFFFF"
        ]

        result = admission.admit_candidates(request, bundle)

        self.assertEqual(1, len(result["admitted_claims"]))
        self.assertEqual([], result["claim_node_links"])
        self.assertEqual(result["unlinked_claim_ids"], [result["admitted_claims"][0]["claim_id"]])
        self.assertEqual("target_node_unknown", result["link_rejections"][0]["reason_codes"][0])

    def test_target_eligibility_rejects_link_but_not_claim(self):
        request, _, bundle = fixture_request_candidate(target_predicates=["executed"])

        result = admission.admit_candidates(request, bundle)

        self.assertEqual(1, len(result["admitted_claims"]))
        self.assertEqual([], result["claim_node_links"])
        self.assertIn(
            "target_link_ineligible",
            result["link_rejections"][0]["reason_codes"],
        )

    def test_tampered_record_payload_is_a_request_integrity_hard_stop(self):
        request, _, bundle = fixture_request_candidate()
        request["visible_artifacts"][0]["records"][0]["payload"]["path"] = (
            "C:\\Tampered\\B.zip"
        )

        with self.assertRaisesRegex(ValueError, "record_hash_mismatch"):
            admission.admit_candidates(request, bundle)

    def test_candidate_run_id_mismatch_is_rejected(self):
        request, _, bundle = fixture_request_candidate()
        bundle["candidate_claims"][0]["compiler_run_id"] = "RUN-" + "F" * 24

        result = admission.admit_candidates(request, bundle)

        self.assertEqual("rejected", result["status"])
        self.assertIn(
            "compiler_run_mismatch",
            result["rejections"][0]["reason_codes"],
        )

    def test_invalid_candidate_bundle_status_cannot_reach_admission(self):
        request, _, bundle = fixture_request_candidate()
        bundle["status"] = "invalid"

        result = admission.admit_candidates(request, bundle)

        self.assertEqual("invalid", result["status"])
        self.assertEqual(
            ["candidate_bundle_status_invalid"], result["abstention_reasons"]
        )

    def test_empty_completed_output_becomes_explicit_abstention(self):
        request, _, bundle = fixture_request_candidate()
        bundle["candidate_claims"] = []
        bundle["abstention_reasons"] = ["no_supported_observation"]

        result = admission.admit_candidates(request, bundle)

        self.assertEqual("abstain", result["status"])
        self.assertEqual(["no_supported_observation"], result["abstention_reasons"])
        self.assertEqual(0, result["counts"]["admitted_claims"])

    def test_duplicate_candidates_are_deterministically_merged(self):
        request, candidate, bundle = fixture_request_candidate()
        duplicate = copy.deepcopy(candidate)
        duplicate["candidate_id"] = builder.derive_scoped_id(
            "CAND", request["request_id"], candidate["compiler_run_id"], "1"
        )
        bundle["candidate_claims"].append(duplicate)

        result = admission.admit_candidates(request, bundle)

        self.assertEqual(1, len(result["admitted_claims"]))
        self.assertEqual(1, result["counts"]["duplicates_merged"])


if __name__ == "__main__":
    unittest.main()
