"""Enforce intended_cti_node_ids != OR(recoverable) answer-key equality."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"


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
    def test_all_cases_must_not_use_intended_as_recoverable_or_answer_key(self):
        violations: list[str] = []
        for case_dir in case_dirs():
            config = run_mvp.load_json(case_dir / "case_config.json")
            actions = run_mvp.load_json(case_dir / "acquisition_actions.json")
            leaking = [
                action["action_id"]
                for action in actions
                if run_mvp.intended_equals_recoverable_or(config, action)
            ]
            if leaking:
                violations.append(f"{config['case_id']}: {', '.join(leaking)}")

        self.assertEqual(
            [],
            violations,
            "intended_cti_node_ids must not equal OR(recoverable) coverage; "
            "see 08-writing/intended-cti-node-annotation-protocol-v0.1-20260710.md. "
            f"Violations: {violations}",
        )


if __name__ == "__main__":
    unittest.main()
