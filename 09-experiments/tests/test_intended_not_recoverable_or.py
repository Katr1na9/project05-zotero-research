"""Enforce intended_cti_node_ids != OR(recoverable) answer-key equality."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"

# Historical development cases compiled before the annotation protocol.
# Do not add new case_ids here; C07+ must pass the inequality check.
LEGACY_INTENDED_EQUALS_OR_ALLOWLIST = frozenset(
    {
        "C01-linux-provenance",
        "C02-freebsd-provenance",
        "C03-windows-host",
        "C04-darpa-e3-fivedirections",
        "C05-darpa-e3-cadets",
        "C06-darpa-e3-cadets-0412",
    }
)


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


run_mvp = load_module("run_mvp", "run_mvp.py")


def case_dirs() -> list[Path]:
    dirs: list[Path] = []
    for root in (ROOT / "examples", ROOT / "real_cases"):
        if not root.is_dir():
            continue
        dirs.extend(run_mvp.discover_case_dirs(root))
    return sorted(dirs, key=lambda path: path.name)


class IntendedNotRecoverableOrHelperTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "case_id": "T-intent",
            "cti_nodes": [
                {
                    "node_id": "N1",
                    "required_claim_ids": ["E1"],
                    "critical": True,
                },
                {
                    "node_id": "N2",
                    "required_claim_ids": ["E2"],
                    "critical": True,
                },
            ],
        }

    def test_flags_exact_answer_key_equality(self):
        action = {
            "action_id": "A1",
            "action_type": "recover_network_summary",
            "recoverable_claim_ids": ["E1"],
            "intended_cti_node_ids": ["N1"],
        }
        self.assertTrue(
            run_mvp.intended_equals_recoverable_or(self.config, action)
        )

    def test_accepts_over_declared_intent(self):
        action = {
            "action_id": "A1",
            "action_type": "recover_network_summary",
            "recoverable_claim_ids": ["E1"],
            "intended_cti_node_ids": ["N1", "N2"],
        }
        self.assertFalse(
            run_mvp.intended_equals_recoverable_or(self.config, action)
        )

    def test_noise_action_with_empty_intent_and_coverage_is_not_a_leak(self):
        action = {
            "action_id": "noise",
            "action_type": "human_review",
            "recoverable_claim_ids": ["E-noise"],
            "intended_cti_node_ids": [],
        }
        self.assertFalse(
            run_mvp.intended_equals_recoverable_or(self.config, action)
        )

    def test_stop_action_is_never_flagged(self):
        action = run_mvp.make_stop_action("T-intent")
        self.assertFalse(
            run_mvp.intended_equals_recoverable_or(self.config, action)
        )


class CaseIntendedInequalityTests(unittest.TestCase):
    def test_new_cases_must_not_use_intended_as_recoverable_or_answer_key(self):
        violations: list[str] = []
        legacy_hits: dict[str, int] = {}
        for case_dir in case_dirs():
            config = run_mvp.load_json(case_dir / "case_config.json")
            actions = run_mvp.load_json(case_dir / "acquisition_actions.json")
            case_id = config["case_id"]
            leaking = [
                action["action_id"]
                for action in actions
                if run_mvp.intended_equals_recoverable_or(config, action)
            ]
            if not leaking:
                continue
            if case_id in LEGACY_INTENDED_EQUALS_OR_ALLOWLIST:
                legacy_hits[case_id] = len(leaking)
                continue
            violations.append(f"{case_id}: {', '.join(leaking)}")

        self.assertEqual(
            [],
            violations,
            "intended_cti_node_ids must not equal OR(recoverable) coverage; "
            "see 08-writing/intended-cti-node-annotation-protocol-v0.1-20260710.md. "
            f"Violations: {violations}",
        )
        # Allowlist must not silently shrink without noticing missing cases,
        # and must not grow: every listed legacy case should still exist.
        discovered = {run_mvp.load_json(d / "case_config.json")["case_id"] for d in case_dirs()}
        missing_legacy = sorted(LEGACY_INTENDED_EQUALS_OR_ALLOWLIST - discovered)
        self.assertEqual([], missing_legacy)
        self.assertEqual(
            set(legacy_hits),
            LEGACY_INTENDED_EQUALS_OR_ALLOWLIST,
            "Legacy allowlist out of sync with actual intended==OR leaks; "
            f"hits={legacy_hits}",
        )


if __name__ == "__main__":
    unittest.main()
