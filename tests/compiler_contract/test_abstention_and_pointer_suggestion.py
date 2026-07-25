import sys
import unittest
from pathlib import Path


SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

try:
    from compiler.llm.abstention import (
        AbstentionReason,
        create_abstention,
    )
    from compiler.llm.pointer_suggestion import (
        PointerSuggestionError,
        suggest_pointer,
    )
except ModuleNotFoundError:
    AbstentionReason = None
    create_abstention = None
    PointerSuggestionError = ValueError
    suggest_pointer = None


VISIBLE_CATALOG = (
    {
        "record_id": "REC-1",
        "source_id": "sensor-a",
        "content_hash": "sha256:111",
    },
    {
        "record_id": "REC-2",
        "source_id": "sensor-b",
        "content_hash": "sha256:222",
    },
)


class AbstentionAndPointerSuggestionTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(create_abstention, "abstention API has not been implemented")
        self.assertIsNotNone(suggest_pointer, "pointer suggestion API has not been implemented")

    def test_no_pointer_candidate_is_unbound_without_case_evidence(self):
        suggestion = suggest_pointer((), VISIBLE_CATALOG)

        self.assertEqual({"status": "unbound"}, suggestion)
        self.assertNotIn("case_evidence", suggestion)
        self.assertNotIn("binding_transition", suggestion)

    def test_equally_plausible_catalog_pointers_are_ambiguous_suggestions(self):
        suggestion = suggest_pointer(VISIBLE_CATALOG, VISIBLE_CATALOG)

        self.assertEqual(
            {"status": "ambiguous", "candidates": ["REC-1", "REC-2"]},
            suggestion,
        )
        self.assertNotIn("binding_transition", suggestion)
        self.assertNotIn("bound", suggestion.values())

    def test_incomplete_pointer_identity_abstains_without_fabricating_fields(self):
        abstention = create_abstention(AbstentionReason.INCOMPLETE_POINTER_IDENTITY)

        self.assertEqual(
            {
                "status": "abstained",
                "reason_code": "incomplete_pointer_identity",
            },
            abstention,
        )
        self.assertNotIn("most_likely_entity", abstention)
        self.assertNotIn("record_id", abstention)

        with self.assertRaisesRegex(PointerSuggestionError, "incomplete"):
            suggest_pointer(({"record_id": "REC-1", "source_id": "sensor-a"},), VISIBLE_CATALOG)

    def test_rejects_pointer_identity_absent_from_visible_catalog(self):
        unseen = {
            "record_id": "REC-9",
            "source_id": "sensor-a",
            "content_hash": "sha256:111",
        }

        with self.assertRaisesRegex(PointerSuggestionError, "visible pointer catalog"):
            suggest_pointer((unseen,), VISIBLE_CATALOG)

    def test_abstention_reason_codes_are_stable_and_never_name_an_entity(self):
        abstention = create_abstention(AbstentionReason.NO_POINTER_CANDIDATES)

        self.assertEqual("no_pointer_candidates", abstention["reason_code"])
        self.assertEqual({"status", "reason_code"}, set(abstention))

    def test_single_catalog_pointer_remains_unbound_and_never_exposes_binding(self):
        suggestion = suggest_pointer((VISIBLE_CATALOG[0],), VISIBLE_CATALOG)

        self.assertEqual({"status": "unbound"}, suggestion)
        self.assertNotIn("binding_transition", suggestion)
        self.assertNotIn("case_evidence", suggestion)


if __name__ == "__main__":
    unittest.main()
