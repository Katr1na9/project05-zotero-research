#!/usr/bin/env python3
"""Frozen multi-gold scoring and claim Gates for LLM Phase 1."""

from __future__ import annotations

import unicodedata
from collections import defaultdict
from typing import Any


MATCH_PATHS = (
    ("source_type",),
    ("subject", "entity_type"),
    ("subject", "value"),
    ("predicate",),
    ("object", "entity_type"),
    ("object", "value"),
    ("source_pointer", "artifact_id"),
    ("source_pointer", "record_id"),
)


def normalize_exact(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.strip().split()).casefold()


def observation_key(claim: dict[str, Any]) -> tuple[str, ...]:
    values = []
    for path in MATCH_PATHS:
        current: Any = claim
        for part in path:
            current = current[part]
        values.append(normalize_exact(current))
    return tuple(values)


def matches_any_acceptable_gold(
    candidate: dict[str, Any],
    acceptable_gold: list[dict[str, Any]],
) -> bool:
    key = observation_key(candidate)
    return any(key == observation_key(gold) for gold in acceptable_gold)


def score_project_gold_packet(
    packet: dict[str, Any],
    admitted_claims: list[dict[str, Any]],
    private_gold: dict[str, Any],
) -> dict[str, Any]:
    acceptable = list(private_gold.get("acceptable_observations") or [])
    matched = [
        claim
        for claim in admitted_claims
        if matches_any_acceptable_gold(claim, acceptable)
    ]
    unsupported = [
        claim
        for claim in admitted_claims
        if not matches_any_acceptable_gold(claim, acceptable)
    ]
    role = str(packet.get("packet_role") or "")
    status = str(packet.get("compiler_status") or "")
    if role == "positive":
        success = bool(matched) and not unsupported
    elif role == "null":
        success = status == "abstain" and not admitted_claims
    else:
        raise ValueError(f"unsupported packet role for scoring: {role}")
    total = len(admitted_claims)
    return {
        "case_id": packet.get("case_id"),
        "packet_role": role,
        "packet_success": success,
        "project_gold_packet_agreement": 1.0 if success else 0.0,
        "matched_count": len(matched),
        "unsupported_count": len(unsupported),
        "unsupported_rate": len(unsupported) / total if total else 0.0,
        "positive_coverage": 1.0 if role == "positive" and total else 0.0,
        "abstained": status == "abstain",
    }


def case_macro(rows: list[dict[str, Any]], metric: str) -> float:
    by_case: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        by_case[str(row["case_id"])].append(float(row[metric]))
    if not by_case:
        raise ValueError("case macro requires at least one case")
    case_means = [sum(values) / len(values) for values in by_case.values()]
    return sum(case_means) / len(case_means)


def name_metrics(metrics: dict[str, float], g2_valid: bool) -> dict[str, float]:
    if g2_valid:
        return {
            "GPS": float(metrics["agreement"]),
            "UCR": float(metrics["unsupported"]),
            "ceiling_violation_rate": float(metrics["ceiling"]),
            "invalid_pointer_rate": float(metrics["invalid_pointer"]),
        }
    return {
        "project_gold_packet_agreement": float(metrics["agreement"]),
        "ceiling_violation_rate": float(metrics["ceiling"]),
        "invalid_pointer_rate": float(metrics["invalid_pointer"]),
    }


def evaluate_claim_gates(
    summary: dict[str, Any],
    g2_status: dict[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    g2_gate = g2_status.get("valid") is True
    if g2_status.get("kappa") is not None:
        g2_gate = g2_gate and float(g2_status["kappa"]) >= 0.70
    if g2_status.get("unassessable_rate") is not None:
        g2_gate = (
            g2_gate and float(g2_status["unassessable_rate"]) <= 0.20
        )
    if not g2_gate:
        failures.append("g2_gate:invalid")

    rule = summary.get("llm_over_rule")
    if not isinstance(rule, dict):
        rule_gate = False
        failures.append("llm_over_rule:missing_summary")
    else:
        rule_checks = {
            "delta_gps": float(rule.get("delta_gps", float("-inf"))) >= 0.05,
            "noninferior_cases": int(rule.get("noninferior_cases", -1)) >= 4
            and int(rule.get("case_count", -1)) == 6,
            "unsupported_rate": rule.get("unsupported_rate_no_worse") is True,
            "invalid_pointer_rate": rule.get("invalid_pointer_rate_no_worse")
            is True,
            "refusal_only_win": rule.get("refusal_only_win") is False,
        }
        rule_gate = all(rule_checks.values())
        failures.extend(
            f"llm_over_rule:{name}"
            for name, passed in rule_checks.items()
            if not passed
        )

    structured = summary.get("structured_over_direct")
    if not isinstance(structured, dict):
        structured_gate = False
        failures.append("structured_over_direct:missing_summary")
    else:
        structured_checks = {
            "delta_ucr": float(structured.get("delta_ucr", float("inf")))
            <= -0.05,
            "favorable_cases": int(structured.get("favorable_cases", -1)) >= 4
            and int(structured.get("case_count", -1)) == 6,
            "positive_coverage_drop": float(
                structured.get("positive_coverage_drop", float("inf"))
            )
            <= 0.05,
        }
        structured_gate = all(structured_checks.values())
        failures.extend(
            f"structured_over_direct:{name}"
            for name, passed in structured_checks.items()
            if not passed
        )

    title_gate = g2_gate and rule_gate and structured_gate
    return {
        "g2_gate": g2_gate,
        "llm_over_rule": rule_gate,
        "structured_over_direct": structured_gate,
        "title_gate": title_gate,
        "failure_reasons": failures,
    }


if __name__ == "__main__":
    raise SystemExit(
        "Use this module after public G0 validation; it is the only G1 reader."
    )
