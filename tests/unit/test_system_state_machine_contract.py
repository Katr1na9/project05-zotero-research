import unittest


MAIN_STATE_ORDER = (
    "SCOPE_MISMATCH_SUSPECTED",
    "UNKNOWN",
    "CERTIFIED_STOP",
    "CONTINUE",
    "DISTINGUISHABLE_BUT_INFEASIBLE",
    "UNRESOLVABLE_UNDER_CATALOG",
    "NO_KNOWN_DISTINGUISHING_ACTION",
    "BUDGET_EXHAUSTED",
)

STATE_CASES = (
    ({"scope_mismatch": True, "unknown": True}, "SCOPE_MISMATCH_SUSPECTED"),
    ({"unknown": True, "level_complete": True}, "UNKNOWN"),
    ({"level_complete": True}, "CERTIFIED_STOP"),
    (
        {"counterexample": True, "formal_distinguishing_feasible": True},
        "CONTINUE",
    ),
    (
        {"counterexample": True, "formal_distinguishing_infeasible": True},
        "DISTINGUISHABLE_BUT_INFEASIBLE",
    ),
    (
        {"counterexample": True, "catalog_observation_equivalent": True},
        "UNRESOLVABLE_UNDER_CATALOG",
    ),
    ({"counterexample": True}, "NO_KNOWN_DISTINGUISHING_ACTION"),
    ({"budget_exhausted": True}, "BUDGET_EXHAUSTED"),
)


class SystemStateMachineContractTests(unittest.TestCase):
    """P0 freezes precedence examples without implementing the P1 machine."""

    def test_v08_main_state_order_is_complete_and_unique(self):
        self.assertEqual(8, len(MAIN_STATE_ORDER))
        self.assertEqual(8, len(set(MAIN_STATE_ORDER)))
        self.assertNotIn("CONDITIONAL", MAIN_STATE_ORDER)

    def test_only_complete_level_certification_has_stop_authority(self):
        stop_cases = [facts for facts, state in STATE_CASES if state == "CERTIFIED_STOP"]
        self.assertEqual([{"level_complete": True}], stop_cases)
        forbidden_stop_inputs = {"m3star", "llm", "probability_threshold", "human_judgment"}
        self.assertTrue(
            all(not forbidden_stop_inputs.intersection(facts) for facts, _ in STATE_CASES)
        )

    def test_counterexample_routes_to_exactly_one_acquisition_state(self):
        acquisition_states = {
            "CONTINUE",
            "DISTINGUISHABLE_BUT_INFEASIBLE",
            "UNRESOLVABLE_UNDER_CATALOG",
            "NO_KNOWN_DISTINGUISHING_ACTION",
        }
        rows = [(facts, state) for facts, state in STATE_CASES if facts.get("counterexample")]
        self.assertEqual(4, len(rows))
        self.assertEqual(acquisition_states, {state for _, state in rows})

    def test_conditional_is_parallel_label_not_main_state(self):
        self.assertNotIn("CONDITIONAL", {state for _, state in STATE_CASES})


if __name__ == "__main__":
    unittest.main()
