from __future__ import annotations

import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "llm"
    / "audit_liwa_field_isolation_exclusion.py"
)
SPEC = importlib.util.spec_from_file_location("liwa_isolation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


CONTRACT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "llm-editor"
    / "llm-editor-v0.8-l2-liwa-field-isolation-protected-exclusion-contract-v0.1-20260722.json"
)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class LiwaIsolationContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_field_map_separates_raw_detector_and_binder_fields(self) -> None:
        self.assertEqual(
            MODULE.classify_field("source.rule.mitre.technique", self.contract),
            "forbidden_supervision",
        )
        self.assertEqual(
            MODULE.classify_field("source.rule.description", self.contract),
            "detector_summary",
        )
        self.assertEqual(
            MODULE.classify_field(
                "source.data.win.system.eventRecordID", self.contract
            ),
            "binder_only",
        )
        self.assertEqual(
            MODULE.classify_field("source.data.command", self.contract),
            "candidate_raw_event",
        )
        self.assertEqual(
            MODULE.classify_field("unregistered.column", self.contract),
            "unknown",
        )

    def test_forbidden_canary_never_enters_model_or_binder_view(self) -> None:
        headers = [
            "source.rule.description",
            "source.rule.mitre.technique",
            "source.data.command",
            "source.data.win.system.eventRecordID",
        ]
        actions = MODULE.compile_field_actions(headers, self.contract)
        isolated = MODULE.isolate_row(
            actions,
            ["CANARY_RULE", "CANARY_TECHNIQUE", "natural attack command", "42"],
        )
        serialized = json.dumps(
            {"model": isolated["model_view"], "binder": isolated["binder"]}
        )
        self.assertNotIn("CANARY_RULE", serialized)
        self.assertNotIn("CANARY_TECHNIQUE", serialized)
        self.assertIn("natural attack command", serialized)

    def test_unknown_header_fails_closed_before_row_isolation(self) -> None:
        with self.assertRaises(MODULE.AuditBlocked):
            MODULE.compile_field_actions(["unknown-field"], self.contract)

    def test_pointer_output_contains_hashes_not_raw_path(self) -> None:
        raw_path = "scenario/attack_run_01.csv"
        pointer = MODULE.build_pointer_audit(
            archive_sha256="a" * 64,
            record_revision=7,
            member_path_hash=digest(raw_path),
            member_content_hash="b" * 64,
            row_index=3,
            raw_record_hash="c" * 64,
            binder_values=[["record_id", "42"]],
            model_view_values=[["message", "event"]],
        )
        self.assertNotIn(raw_path, json.dumps(pointer))
        self.assertEqual(pointer["binding_status"], "unbound")

    def test_protected_scanner_exact_near_and_clean_controls(self) -> None:
        protected = "abcdefghijklmnopqrstuvwxyz0123456789"
        normalized_hash = digest(MODULE.normalized_text(protected))
        grams = MODULE.hashed_character_ngrams(protected, 5)
        lock = {
            "contains_raw_test_payload": False,
            "contains_raw_private_gold": False,
            "blocked_family_ids": sorted(MODULE.EXPECTED_PROTECTED_FAMILIES),
            "character_ngram_n": 5,
            "minimum_protected_text_chars": 16,
            "near_duplicate_threshold": 0.85,
            "normalized_text_hashes": [normalized_hash],
            "ngram_signatures": [
                {
                    "ngram_count": len(grams),
                    "ngram_hashes": sorted(grams),
                    "normalized_text_sha256": normalized_hash,
                }
            ],
        }
        scanner = MODULE.ProtectedScanner(lock)
        self.assertTrue(scanner.scan(protected).exact)
        near = scanner.scan(protected + "x")
        self.assertTrue(near.near)
        self.assertGreaterEqual(near.maximum_jaccard, 0.85)
        clean = scanner.scan("a completely different harmless control string")
        self.assertFalse(clean.matched)

    def test_threshold_or_family_change_is_rejected(self) -> None:
        lock = {
            "contains_raw_test_payload": False,
            "contains_raw_private_gold": False,
            "blocked_family_ids": sorted(MODULE.EXPECTED_PROTECTED_FAMILIES),
            "character_ngram_n": 5,
            "minimum_protected_text_chars": 16,
            "near_duplicate_threshold": 0.86,
            "normalized_text_hashes": ["a"],
            "ngram_signatures": [{"ngram_count": 1, "ngram_hashes": ["b"]}],
        }
        with self.assertRaises(MODULE.AuditBlocked):
            MODULE.validate_protected_lock(lock)


if __name__ == "__main__":
    unittest.main()
