# Part B B3 capture fixture specification issues

Status: **B3 FIXTURE PATH ONLY — REAL ADAPTER OPEN**

This document records the narrow local fixture decision. It does not rewrite
the frozen B3 cost-instrumentation policy, B3 manifest, or Part A semantics.

## PB-B3-SI-001 — Production capture adapters

**State:** `FIXTURE_PATH_ONLY_REAL_ADAPTER_OPEN`.

The approved module consumes synthetic evaluator-supplied events only. It does
not hook OS clocks, CPU/memory counters, analyst activity, authorization
systems, billing APIs or connectors. A future real adapter needs its own
cadence, unit, provenance and authority review.

## PB-B3-SI-002 — Memory integral cadence

**State:** `OPEN`.

The fixture can replay a supplied `byte_nanoseconds` event, but this is not
evidence that a production cadence, interpolation rule or process-tree
boundary has been validated. Missing capture remains `UNKNOWN_NOT_ZERO`.

## PB-B3-SI-003 — Cross-currency normalization

**State:** `OPEN`.

Mixed currencies fail closed with no FX. No exchange-rate source, valuation
time, base currency or rounding authority is introduced here.

## PB-B3-SI-004 — Scalarization and performance claims

**State:** `OPEN`.

The result preserves the vector and emits no scalar cost, ranking, superiority
claim or performance claim.

## Adjacent gates

SI-006, B5 planner execution, holdout release and `CERTIFIED_STOP` remain
closed/denied. This fixture cannot admit evidence, issue a certificate,
produce system status or alter any B0–B9 frozen artifact.
