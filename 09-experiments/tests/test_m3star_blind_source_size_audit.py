import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SIZE_AUDIT = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "sources"
    / "official-source-size-audit-excluding-aviator-v0.1.json"
)
FULL_SIZE_FIELDS = (
    "all_official_file_bytes",
    "all_candidate_related_blob_bytes",
    "all_candidate_related_bytes",
    "all_official_repository_blob_bytes",
    "all_known_root_file_bytes",
)


def load_audit():
    return json.loads(SIZE_AUDIT.read_text(encoding="utf-8"))


def quantified_full_size(source):
    values = [source[field] for field in FULL_SIZE_FIELDS if field in source]
    if len(values) != 1:
        raise AssertionError(
            f"{source['source_id']} must expose exactly one quantified full-size field"
        )
    return values[0]


class BlindSourceSizeAuditTests(unittest.TestCase):
    def test_excluding_aviator_candidate_and_size_totals_are_consistent(self):
        audit = load_audit()
        sources = audit["sources"]
        known = [
            source for source in sources if source["minimum_planned_bytes"] is not None
        ]
        summary = audit["size_summary_excluding_aviator"]

        self.assertEqual(17, len(sources))
        self.assertEqual(95, sum(source["candidate_upper_bound"] for source in sources))
        self.assertEqual(94, sum(source["candidate_upper_bound"] for source in known))
        self.assertNotIn("aviator", {source["source_id"] for source in sources})
        self.assertEqual(
            summary["minimum_planned_download_for_all_94_quantified_candidates_bytes"],
            sum(source["minimum_planned_bytes"] for source in known),
        )
        self.assertEqual(
            summary["download_every_known_official_file_bytes"],
            sum(quantified_full_size(source) for source in known),
        )

    def test_staged_plan_preserves_declared_counts_and_byte_arithmetic(self):
        audit = load_audit()
        sources = {source["source_id"]: source for source in audit["sources"]}
        plan = audit["staged_minimum_download_plan"]
        phase_1 = plan["phase_1"]
        phase_2 = plan["phase_2"]

        self.assertEqual(81, phase_1["candidate_upper_bound"])
        self.assertEqual(3146302753, phase_1["planned_download_bytes"])
        self.assertEqual(89, phase_2["cumulative_candidate_upper_bound_if_all_eight_added"])
        self.assertEqual(
            phase_1["planned_download_bytes"]
            + sources["ait-log-data-set-v2.1"]["minimum_planned_bytes"],
            phase_2["cumulative_planned_download_bytes_if_all_eight_added"],
        )
        self.assertEqual(
            phase_1["planned_download_bytes"]
            - sources["mscad"]["minimum_planned_bytes"],
            plan["theoretical_zero_reserve_79_candidate_plan"][
                "planned_download_bytes"
            ],
        )


if __name__ == "__main__":
    unittest.main()
