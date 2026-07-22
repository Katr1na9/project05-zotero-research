import copy
import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.llm.candidate_ir import project_candidate_claim
    from compiler.llm.exceptions import CandidateOnlyViolationError
except ModuleNotFoundError:
    project_candidate_claim = None
    CandidateOnlyViolationError = ValueError


def semantic_proposal(**overrides):
    proposal = {
        "candidate_id": "candidate-001",
        "claim": {
            "subject": "powershell.exe",
            "predicate": "wrote",
            "object": "C:\\Temp\\archive.zip",
        },
    }
    proposal.update(overrides)
    return proposal


class CandidateClaimIRProjectionTests(unittest.TestCase):
    def test_projects_semantic_proposal_with_candidate_only_defaults(self):
        self.assertIsNotNone(
            project_candidate_claim,
            "Candidate Claim IR projection API has not been implemented",
        )

        proposal = semantic_proposal()
        projected = project_candidate_claim(proposal, {"modality": "reported"})

        self.assertEqual("candidate-001", projected["candidate_id"])
        self.assertEqual(proposal["claim"], projected["claim"])
        self.assertEqual("reported", projected["modality"])
        self.assertEqual("candidate", projected["admission_status"])
        self.assertEqual(
            {"allowed": False, "levels": []},
            projected["certification_authority"],
        )
        self.assertEqual("none", projected["promotion_status"])
        self.assertEqual("unbound", projected["binding_status"])
        self.assertEqual({"status": "unbound"}, projected["pointer_suggestion"])
        self.assertEqual("pending_kernel_schema", projected["compatibility_status"])
        self.assertEqual(proposal, semantic_proposal())

    def test_preserves_ambiguous_pointer_suggestion_without_binding_it(self):
        proposal = semantic_proposal(
            pointer_suggestion={
                "status": "ambiguous",
                "candidates": ["REC-1", "REC-2"],
            }
        )

        projected = project_candidate_claim(proposal, {"modality": "derived"})

        self.assertEqual("ambiguous", projected["pointer_suggestion"]["status"])
        self.assertEqual("ambiguous", projected["binding_status"])
        self.assertEqual(["REC-1", "REC-2"], projected["pointer_suggestion"]["candidates"])

    def test_rejects_non_producer_pointer_states(self):
        for status in ("bound", "failed"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(CandidateOnlyViolationError, status):
                    project_candidate_claim(
                        semantic_proposal(pointer_suggestion={"status": status}),
                        {"modality": "observed"},
                    )

    def test_rejects_model_controlled_authority_fields_at_any_depth(self):
        for field in (
            "admission_status",
            "certification_authority",
            "promotion_status",
            "binding_status",
            "lifecycle_state",
        ):
            with self.subTest(field=field):
                proposal = semantic_proposal(claim={"predicate": "wrote", field: "model-value"})
                with self.assertRaisesRegex(CandidateOnlyViolationError, field):
                    project_candidate_claim(proposal, {"modality": "reported"})

    def test_rejects_any_model_supplied_modality_instead_of_overwriting_it(self):
        with self.assertRaisesRegex(CandidateOnlyViolationError, "modality"):
            project_candidate_claim(
                semantic_proposal(modality="observed"),
                {"modality": "reported"},
            )

    def test_projection_is_pure_and_does_not_mutate_its_inputs(self):
        proposal = semantic_proposal(pointer_suggestion={"status": "unbound"})
        metadata = {"modality": "hypothesized"}
        original_proposal = copy.deepcopy(proposal)
        original_metadata = copy.deepcopy(metadata)

        projected = project_candidate_claim(proposal, metadata)
        projected["claim"]["subject"] = "changed"
        projected["certification_authority"]["levels"].append("not-allowed")

        self.assertEqual(original_proposal, proposal)
        self.assertEqual(original_metadata, metadata)


if __name__ == "__main__":
    unittest.main()
