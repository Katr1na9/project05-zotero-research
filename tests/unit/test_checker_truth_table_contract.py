import unittest


NOT_RUN = "NOT_RUN"
CHECKER_TRUTH_TABLE = (
    ("UNSAT", NOT_RUN, NOT_RUN, "SCOPE_MISMATCH_SUSPECTED"),
    ("SAT", "UNSAT", NOT_RUN, "REJECT_CANDIDATE"),
    ("SAT", "SAT", "SAT", "COUNTEREXAMPLE_FOUND"),
    ("SAT", "SAT", "UNSAT", "CANDIDATE_CERTIFIED"),
    ("SAT", "TIMEOUT", NOT_RUN, "UNKNOWN"),
    ("SAT", "SAT", "TIMEOUT", "UNKNOWN"),
    ("TIMEOUT", NOT_RUN, NOT_RUN, "UNKNOWN"),
)


class CheckerTruthTableContractTests(unittest.TestCase):
    """P0 freezes truth-table cases; P1 will bind them to checker code."""

    def test_v08_inherits_all_seven_v07_checker_rows(self):
        self.assertEqual(7, len(CHECKER_TRUTH_TABLE))
        self.assertEqual(7, len(set(CHECKER_TRUTH_TABLE)))
        self.assertEqual(
            {
                "SCOPE_MISMATCH_SUSPECTED",
                "REJECT_CANDIDATE",
                "COUNTEREXAMPLE_FOUND",
                "CANDIDATE_CERTIFIED",
                "UNKNOWN",
            },
            {row[3] for row in CHECKER_TRUTH_TABLE},
        )

    def test_timeout_or_resource_exhaustion_is_never_unsat(self):
        timeout_rows = [row for row in CHECKER_TRUTH_TABLE if "TIMEOUT" in row[:3]]
        self.assertEqual(3, len(timeout_rows))
        self.assertTrue(all(row[3] == "UNKNOWN" for row in timeout_rows))

    def test_counterexample_and_candidate_certification_require_support_sat(self):
        decisive = {
            row[3]: row
            for row in CHECKER_TRUTH_TABLE
            if row[3] in {"COUNTEREXAMPLE_FOUND", "CANDIDATE_CERTIFIED"}
        }
        self.assertEqual("SAT", decisive["COUNTEREXAMPLE_FOUND"][1])
        self.assertEqual("SAT", decisive["CANDIDATE_CERTIFIED"][1])


if __name__ == "__main__":
    unittest.main()
