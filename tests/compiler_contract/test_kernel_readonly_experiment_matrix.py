import hashlib
import json
from pathlib import Path
import unittest

from src.compiler.llm import claim_id_mainline_handoff as handoff_module
from src.compiler.llm import kernel_readonly_experiment_matrix_runner as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = REPO_ROOT / (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-readonly-experiment-"
    "matrix-design-v0.1-20260725.json"
)
RESULT_PATH = REPO_ROOT / (
    "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/"
    "project05-depth2-public-v0.1/matrix-result.json"
)
RECEIPT_PATH = RESULT_PATH.with_name("sanitized-receipt.json")
RED_REVIEW_PACKET_PATH = REPO_ROOT / (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-readonly-experiment-"
    "matrix-review-packet-v0.1-20260725.json"
)
GREEN_REVIEW_PACKET_PATH = REPO_ROOT / (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-readonly-experiment-"
    "matrix-green-review-packet-v0.1-20260726.json"
)
INTAKE_PATH = REPO_ROOT / (
    "docs/kernel/kernel-v0.8-claim-id-certificate-track-handoff-intake-"
    "and-experiment-plan-v0.1-20260725.json"
)
INTAKE_SHA256 = "5da2ceedb63ccdb3ca8d409d3dfd23aec0a274da4c01ee3747276d42f8c232cf"
ACCEPTANCE_PATH = REPO_ROOT / runner.OWNER_ACCEPTANCE_PATH
ACCEPTANCE_SHA256 = (
    "a95a07cb302c8231cbe66336422af0998e15d869c687a42ba6cbac9a06d3263a"
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


class KernelReadonlyExperimentMatrixArtifactTests(unittest.TestCase):
    def test_accepted_design_retains_exact_abc_scope(self):
        design = load_json(DESIGN_PATH)
        self.assertEqual(
            "RED_DRAFT_PENDING_KERNEL_OWNER_REVIEW_NOT_EFFECTIVE",
            design["status"],
        )
        self.assertEqual(
            [
                "A_baseline_no_claim_id_provenance",
                "B_claim_id_provenance_attached_read_only",
                "C_negative_mixlayer_rejected",
            ],
            [arm["arm_id"] for arm in design["matrix_arms"]],
        )
        self.assertFalse(
            design["owner_review_gate"]["green_implementation_authorized"]
        )

    def test_design_pin_table_exactly_replays_intake_verified_pins(self):
        self.assertEqual(INTAKE_SHA256, sha256(INTAKE_PATH))
        intake = load_json(INTAKE_PATH)
        expected = {
            name: {
                "path": item["path"],
                "sha256": item["content_sha256"],
            }
            for name, item in intake["verification"]["verified_pins"].items()
        }
        expected["handoff_intake"] = {
            "path": str(INTAKE_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "sha256": INTAKE_SHA256,
        }
        design = load_json(DESIGN_PATH)
        self.assertEqual(expected, design["pin_table"])
        for item in expected.values():
            path = REPO_ROOT / item["path"]
            with self.subTest(path=item["path"]):
                self.assertEqual(item["sha256"], sha256(path))

    def test_owner_acceptance_exact_pin_and_semantics(self):
        self.assertEqual(ACCEPTANCE_SHA256, sha256(ACCEPTANCE_PATH))
        acceptance = runner.verify_owner_acceptance(REPO_ROOT)
        self.assertEqual("accept", acceptance["decision"])
        self.assertTrue(
            acceptance["answers_to_owner_questions"][
                "green_may_proceed_without_new_activation"
            ]
        )
        self.assertFalse(acceptance["not_authorized"]["git_commit"])
        self.assertFalse(acceptance["not_authorized"]["new_write_activation"])
        self.assertEqual(
            runner.RED_REVIEW_PACKET_SHA256, sha256(RED_REVIEW_PACKET_PATH)
        )

    def test_result_and_receipt_are_green_read_only_records(self):
        result = load_json(RESULT_PATH)
        receipt = load_json(RECEIPT_PATH)
        self.assertEqual("GREEN_PASS_READ_ONLY", result["status"])
        self.assertEqual("GREEN_PASS_READ_ONLY", receipt["status"])
        self.assertEqual(
            ["PASS", "PASS", "PASS"],
            [arm["status"] for arm in result["arms"]],
        )
        self.assertEqual("none", receipt["write_side_effects"])
        self.assertTrue(receipt["owner_acceptance_present"])
        self.assertFalse(receipt["effective"])

    def test_green_review_packet_pins_outputs_and_is_not_owner_approval(self):
        packet = load_json(GREEN_REVIEW_PACKET_PATH)
        self.assertEqual(
            "GREEN_REVIEW_PACKET_PENDING_KERNEL_OWNER_REREVIEW_NOT_EFFECTIVE",
            packet["status"],
        )
        self.assertTrue(packet["this_packet_is_not_owner_approval"])
        self.assertFalse(packet["effective"])
        self.assertIsNone(packet["requested_owner_decision"]["current_value"])
        self.assertEqual(
            ["accept", "request_revision", "reject"],
            packet["requested_owner_decision"]["allowed_values"],
        )
        artifact_paths = {
            "design": DESIGN_PATH,
            "owner_acceptance": ACCEPTANCE_PATH,
            "runner": REPO_ROOT / runner.__file__.replace(
                str(REPO_ROOT) + "\\", ""
            ),
            "tests": Path(__file__),
            "matrix_result": RESULT_PATH,
            "sanitized_receipt": RECEIPT_PATH,
        }
        for name, path in artifact_paths.items():
            with self.subTest(artifact=name):
                self.assertEqual(
                    sha256(path),
                    packet["submitted_artifacts"][name]["sha256"],
                )
        identity = packet["packet_identity"]
        reported = identity["self_reported_canonical_sha256"]
        packet["packet_identity"]["self_reported_canonical_sha256"] = None
        self.assertEqual(reported, canonical_sha256(packet))


class KernelReadonlyExperimentMatrixRuntimeTests(unittest.TestCase):
    def run_matrix(self) -> dict:
        return runner.run_matrix(REPO_ROOT)

    def test_arm_a_and_b_are_reproducible_and_algorithm_identical(self):
        first = self.run_matrix()
        second = self.run_matrix()
        self.assertEqual(canonical_sha256(first), canonical_sha256(second))
        arms = {arm["arm_id"]: arm for arm in first["arms"]}
        arm_a = arms["A_baseline_no_claim_id_provenance"]
        arm_b = arms["B_claim_id_provenance_attached_read_only"]
        self.assertEqual("PASS", arm_a["status"])
        self.assertEqual("PASS", arm_b["status"])
        self.assertFalse(arm_a["claim_id_provenance_attached"])
        self.assertTrue(arm_b["claim_id_provenance_attached"])
        self.assertEqual(arm_a["action_id"], arm_b["action_id"])
        self.assertEqual("A-high", arm_a["action_id"])
        self.assertFalse(arm_a["algorithm_changed"])
        self.assertFalse(arm_b["algorithm_changed"])

    def test_clm_identifiers_never_enter_case_local_e1_or_scoring(self):
        result = self.run_matrix()
        for arm in result["arms"][:2]:
            with self.subTest(arm=arm["arm_id"]):
                self.assertEqual(["E1"], arm["case_local_visible_evidence"])
                self.assertEqual([], arm["scoring_claim_id_hits"])
                self.assertFalse(
                    any(
                        isinstance(item, str) and item.startswith("clm_")
                        for item in arm["case_local_visible_evidence"]
                    )
                )

    def test_arm_c_rejects_all_three_mixlayer_requests(self):
        result = self.run_matrix()
        arm_c = {
            arm["arm_id"]: arm for arm in result["arms"]
        }["C_negative_mixlayer_rejected"]
        self.assertEqual("PASS", arm_c["status"])
        self.assertEqual(
            [
                "store_as_e_case",
                "certificate_as_certified_stop",
                "certified_stop_as_run_mvp_stop",
            ],
            [item["case_id"] for item in arm_c["rejections"]],
        )
        self.assertTrue(
            all(
                item["decision"] == "FAIL_CLOSED_DENY"
                for item in arm_c["rejections"]
            )
        )
        self.assertTrue(
            all(not item["write_path_invoked"] for item in arm_c["rejections"])
        )
        self.assertFalse(arm_c["ordinary_run_mvp_stop_emitted"])

    def test_no_protected_bytes_or_activation_ledgers_change(self):
        before = runner.snapshot_protected_state(REPO_ROOT)
        result = self.run_matrix()
        after = runner.snapshot_protected_state(REPO_ROOT)
        self.assertEqual(before, after)
        self.assertTrue(result["protected_bytes_identical"])
        self.assertEqual("none", result["write_side_effects"])
        self.assertFalse(result["activation_ledger_replayed"])

    def test_registration_and_authority_boundaries_remain_closed(self):
        result = self.run_matrix()
        self.assertFalse(handoff_module.PRODUCTION_REGISTRATION_ENABLED)
        self.assertFalse(result["production_registration_enabled"])
        self.assertIsNone(result["checker_decision"])
        self.assertIsNone(result["evidence_sufficiency"])
        self.assertFalse(result["l2_authorized"])
        self.assertFalse(result["part_b_elevated"])
        self.assertFalse(result["m2_fit_authorized"])
        self.assertFalse(result["four_family_ingestion_authorized"])
        self.assertFalse(result["certified_stop_executed"])


if __name__ == "__main__":
    unittest.main()
