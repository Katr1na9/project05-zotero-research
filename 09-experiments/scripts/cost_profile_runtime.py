#!/usr/bin/env python3
"""Versioned cost-profile runtime layered over the byte-locked legacy MVP.

The legacy simulator is inherited by other research lines and therefore remains
byte-identical.  This module is the canonical v0.2 entry point for rubric cost
semantics.  It separates volatility (V) from acquisition burden by default and
retains the original positive-V sum only behind an explicit compatibility flag.
"""

from __future__ import annotations

import importlib.util
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


LEGACY_PATH = Path(__file__).with_name("run_mvp.py")
RUNTIME_ID = "project05-cost-profile-runtime"
RUNTIME_VERSION = "0.2.0"
VOLATILITY_TREATMENTS = ("separate_delay_loss", "legacy_positive_burden")


def _load_legacy() -> Any:
    spec = importlib.util.spec_from_file_location("project05_legacy_mvp", LEGACY_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load legacy MVP from {LEGACY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEGACY = _load_legacy()
LEGACY_APPLY_COST_REGIME = LEGACY.apply_cost_regime
COST_REGIMES = LEGACY.COST_REGIMES
COST_COMPONENTS = LEGACY.COST_COMPONENTS
load_cost_profile = LEGACY.load_cost_profile
cost_profile_identity = LEGACY.cost_profile_identity


def compose_rubric_cost(
    components: dict[str, Any],
    scoring: dict[str, Any],
) -> float:
    """Compose burden while requiring explicit, auditable V semantics."""

    weights = scoring.get("weights")
    if not isinstance(weights, dict) or set(weights) != set(COST_COMPONENTS):
        raise ValueError(
            "Rubric scoring.weights must contain exactly E, V, D, A, and R"
        )
    if not isinstance(components, dict) or set(components) != set(COST_COMPONENTS):
        raise ValueError("Rubric components must contain exactly E, V, D, A, and R")
    volatility_treatment = scoring.get("volatility_treatment")
    if volatility_treatment not in VOLATILITY_TREATMENTS:
        raise ValueError(
            "Rubric scoring.volatility_treatment must be one of "
            f"{VOLATILITY_TREATMENTS}; implicit V-as-burden semantics are forbidden"
        )

    burden_components = (
        COST_COMPONENTS
        if volatility_treatment == "legacy_positive_burden"
        else tuple(component for component in COST_COMPONENTS if component != "V")
    )
    raw = Decimal("0")
    for component in COST_COMPONENTS:
        score = components[component]
        weight = weights[component]
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 3:
            raise ValueError(f"Rubric component {component} must be an integer in [0, 3]")
        if not LEGACY._is_finite_number(weight) or float(weight) <= 0:
            raise ValueError(f"Rubric weight {component} must be finite and positive")
        if component in burden_components:
            raw += Decimal(str(score)) * Decimal(str(weight))

    scale = scoring.get("scale")
    minimum = scoring.get("minimum_cost")
    maximum = scoring.get("maximum_cost")
    if not LEGACY._is_finite_number(scale) or float(scale) <= 0:
        raise ValueError("Rubric scoring.scale must be finite and positive")
    if not LEGACY._is_finite_number(minimum) or not LEGACY._is_finite_number(maximum):
        raise ValueError("Rubric cost bounds must be finite numbers")
    if float(minimum) <= 0 or float(maximum) < float(minimum):
        raise ValueError("Rubric cost bounds must satisfy 0 < minimum_cost <= maximum_cost")
    if scoring.get("rounding") != "half_up":
        raise ValueError("Rubric scoring.rounding must be 'half_up'")

    scaled = raw / Decimal(str(scale))
    rounded = scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    clipped = min(Decimal(str(maximum)), max(Decimal(str(minimum)), rounded))
    return float(clipped)


def apply_cost_regime(
    actions: list[dict[str, Any]],
    case_id: str,
    cost_regime: str = "legacy",
    cost_profile: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, str] | None]:
    """Apply a legacy/uniform/measured profile or governed rubric profile."""

    resolved, metadata = LEGACY_APPLY_COST_REGIME(
        actions, case_id, cost_regime, cost_profile
    )
    if cost_regime != "rubric":
        return resolved, metadata

    assert cost_profile is not None
    document = cost_profile["document"]
    scoring = document.get("scoring")
    if not isinstance(scoring, dict):
        raise ValueError("Cost profile scoring must be an object")
    indexed = LEGACY._profile_entries_by_case(document)
    for action in resolved:
        if LEGACY.is_stop_action(action):
            continue
        entry = indexed[case_id][action["action_id"]]
        action["cost"] = compose_rubric_cost(entry.get("components"), scoring)
        action["cost_breakdown"] = {
            "acquisition_burden_components": {
                component: entry["components"][component]
                for component in ("E", "D", "A", "R")
            },
            "volatility_score": entry["components"]["V"],
            "volatility_treatment": scoring["volatility_treatment"],
        }
    assert metadata is not None
    metadata["cost_runtime_id"] = RUNTIME_ID
    metadata["cost_runtime_version"] = RUNTIME_VERSION
    metadata["volatility_treatment"] = str(scoring["volatility_treatment"])
    return resolved, metadata


def execute_case(*args: Any, **kwargs: Any) -> Any:
    """Execute the legacy simulator with this runtime injected for one call."""

    original = LEGACY.apply_cost_regime
    LEGACY.apply_cost_regime = apply_cost_regime
    try:
        return LEGACY.execute_case(*args, **kwargs)
    finally:
        LEGACY.apply_cost_regime = original


def __getattr__(name: str) -> Any:
    return getattr(LEGACY, name)
