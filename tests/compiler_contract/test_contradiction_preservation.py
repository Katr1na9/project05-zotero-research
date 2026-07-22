import ast
import copy
import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.llm.conflict_preservation import preserve_candidate_conflicts
    from compiler.constrained_decoder.canonical_validator import validate_candidate_claim_ir
except ModuleNotFoundError:
    preserve_candidate_conflicts = None
    validate_candidate_claim_ir = None


def candidate(candidate_id, object_value, *, polarity=True, modality="reported"):
    return {
        "candidate_id": candidate_id,
        "claim": {
            "subject": "powershell.exe",
            "predicate": "originated_from",
            "object": object_value,
            "polarity": polarity,
        },
        "modality": modality,
        "epistemic_role": "background_intelligence",
        "truth_status": "unassessed",
        "admission_status": "candidate",
        "certification_authority": {"allowed": False, "levels": []},
        "promotion_status": "none",
        "binding_status": "unbound",
        "pointer_suggestion": {"status": "unbound"},
        "contradict_claim_ids": [],
        "compatibility_status": "pending_kernel_schema",
    }


POINTERS = {
    "candidate-1": {
        "record_id": "REC-1",
        "source_id": "sensor-a",
        "content_hash": "sha256:111",
    },
    "candidate-2": {
        "record_id": "REC-2",
        "source_id": "sensor-b",
        "content_hash": "sha256:222",
    },
}


class ContradictionPreservationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            preserve_candidate_conflicts,
            "conflict preservation API has not been implemented",
        )

    def test_incompatible_objects_from_distinct_pointers_remain_separate(self):
        inputs = [candidate("candidate-1", "benign.example"), candidate("candidate-2", "evil.example")]
        snapshot = copy.deepcopy(inputs)

        outputs = preserve_candidate_conflicts(
            inputs,
            POINTERS,
            exclusive_object_predicates={"originated_from"},
        )

        self.assertEqual(2, len(outputs))
        self.assertEqual(["candidate-1", "candidate-2"], [item["candidate_id"] for item in outputs])
        self.assertEqual(["conflicted", "conflicted"], [item["truth_status"] for item in outputs])
        self.assertEqual(["candidate-2"], outputs[0]["contradict_claim_ids"])
        self.assertEqual(["candidate-1"], outputs[1]["contradict_claim_ids"])
        for output in outputs:
            self.assertIs(output, validate_candidate_claim_ir(output))
        self.assertEqual(snapshot, inputs)

    def test_opposite_polarities_are_symmetric_conflicts(self):
        inputs = [
            candidate("candidate-1", "evil.example", polarity=True),
            candidate("candidate-2", "evil.example", polarity=False),
        ]

        outputs = preserve_candidate_conflicts(
            inputs,
            POINTERS,
            exclusive_object_predicates={"originated_from"},
        )

        self.assertEqual(["candidate-2"], outputs[0]["contradict_claim_ids"])
        self.assertEqual(["candidate-1"], outputs[1]["contradict_claim_ids"])

    def test_conflict_annotation_preserves_all_candidate_only_controls(self):
        inputs = [
            candidate("candidate-1", "benign.example", modality="reported"),
            candidate("candidate-2", "evil.example", modality="hypothesized"),
        ]

        outputs = preserve_candidate_conflicts(
            inputs,
            POINTERS,
            exclusive_object_predicates={"originated_from"},
        )

        self.assertEqual(["conflicted", "conflicted"], [item["truth_status"] for item in outputs])

        for before, after in zip(inputs, outputs, strict=True):
            for field in (
                "modality",
                "epistemic_role",
                "pointer_suggestion",
                "certification_authority",
                "admission_status",
                "promotion_status",
                "binding_status",
            ):
                self.assertEqual(before[field], after[field], field)

    def test_identical_repeated_candidates_are_retained_without_deduplication(self):
        inputs = [candidate("candidate-1", "evil.example"), candidate("candidate-2", "evil.example")]

        outputs = preserve_candidate_conflicts(inputs, POINTERS)

        self.assertEqual(2, len(outputs))
        self.assertEqual(["unassessed", "unassessed"], [item["truth_status"] for item in outputs])
        self.assertEqual([[], []], [item["contradict_claim_ids"] for item in outputs])

    def test_object_difference_is_not_called_a_conflict_without_predicate_contract(self):
        inputs = [candidate("candidate-1", "benign.example"), candidate("candidate-2", "evil.example")]

        outputs = preserve_candidate_conflicts(inputs, POINTERS)

        self.assertEqual([[], []], [item["contradict_claim_ids"] for item in outputs])

    def test_existing_one_sided_conflict_reference_is_made_symmetric(self):
        inputs = [candidate("candidate-1", "evil.example"), candidate("candidate-2", "evil.example")]
        inputs[0]["contradict_claim_ids"] = ["candidate-2"]
        inputs[0]["truth_status"] = "conflicted"

        outputs = preserve_candidate_conflicts(inputs, POINTERS)

        self.assertEqual(["candidate-2"], outputs[0]["contradict_claim_ids"])
        self.assertEqual(["candidate-1"], outputs[1]["contradict_claim_ids"])
        self.assertEqual(["conflicted", "conflicted"], [item["truth_status"] for item in outputs])

    def test_rejects_input_that_already_leaks_authority(self):
        inputs = [candidate("candidate-1", "evil.example")]
        inputs[0]["certification_authority"] = {"allowed": True, "levels": ["case"]}

        with self.assertRaisesRegex(ValueError, "certification_authority"):
            preserve_candidate_conflicts(inputs, {"candidate-1": POINTERS["candidate-1"]})

    def test_missing_or_same_pointer_identity_does_not_infer_a_conflict(self):
        inputs = [candidate("candidate-1", "benign.example"), candidate("candidate-2", "evil.example")]
        same_pointer = {"candidate-1": POINTERS["candidate-1"], "candidate-2": POINTERS["candidate-1"]}

        same_outputs = preserve_candidate_conflicts(
            inputs,
            same_pointer,
            exclusive_object_predicates={"originated_from"},
        )
        missing_outputs = preserve_candidate_conflicts(
            inputs,
            {},
            exclusive_object_predicates={"originated_from"},
        )

        self.assertEqual([[], []], [item["contradict_claim_ids"] for item in same_outputs])
        self.assertEqual([[], []], [item["contradict_claim_ids"] for item in missing_outputs])

    def test_l1_modules_do_not_import_or_call_kernel_control_surfaces(self):
        forbidden = ("admit_candidates", "checker", "promote", "revoke", "e_case")
        llm_source = SRC_ROOT / "compiler" / "llm"

        for module in llm_source.glob("*.py"):
            tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = [alias.name.casefold() for alias in node.names]
                    if isinstance(node, ast.ImportFrom) and node.module:
                        names.append(node.module.casefold())
                    for name in names:
                        self.assertFalse(
                            any(token in name for token in forbidden),
                            f"{module.name}: {name}",
                        )
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called = node.func.id.casefold()
                    elif isinstance(node.func, ast.Attribute):
                        called = node.func.attr.casefold()
                    else:
                        continue
                    self.assertFalse(
                        any(token in called for token in forbidden),
                        f"{module.name}: {called}",
                    )


if __name__ == "__main__":
    unittest.main()
