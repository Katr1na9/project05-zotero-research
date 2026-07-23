# Part B B3 cost-instrumentation boundary v0.8

Status: **LOCAL REVIEW — INSTRUMENTATION ONLY**

```text
Authorized slice: B3_COST_INSTRUMENTATION
instrumentation_authority=true
action_execution_authority=false
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
CERTIFIED_STOP authority: NONE
B4–B9: CLOSED
```

## 1. Authorized behavior

B3 may deterministically aggregate evaluator-supplied integer trace events
into the ordered eight-dimensional vector

```text
[T_human, T_wall, T_CPU, M_byte_sec, D_scan, N_record, C_money, T_auth]
```

The aggregation module may validate provenance, reject malformed events,
represent measured values as exact rationals, preserve partial traces and
mark absent measurements `UNKNOWN_NOT_ZERO`.

B3 does not execute an action, read a wall clock, hook the Part A Executor,
open a connector, sample an observation, admit evidence, eliminate worlds,
invoke Planner/M3*, or modify Claim IR.

## 2. Fail-closed boundaries

- Missing measurement: `UNKNOWN_NOT_ZERO`; implicit zero is forbidden.
- Feasibility: `SEPARATE_NOT_HIGH_COST`; infeasible actions may retain
  measured authorization/attempt overhead but receive no invented scalar.
- Currency: zero or one ISO-4217 currency per trace; mixed currency fails
  closed because no FX contract is approved.
- Arithmetic: non-negative integer input and reduced exact-rational output;
  binary floating point is not normative.
- Event identity: unique non-empty event IDs; input order is non-semantic.

## 3. Claim boundary

An internally schema-valid trace establishes trace consistency only. It does
not establish real-world capture completeness, cross-source comparability,
external validity, cost superiority or planner performance.

`scalarization_authority=false` and `performance_claim_authority=false`.
Weights, normalization, sensitivity grids, FX conversion and preregistered
comparison claims remain later decisions. B3 cannot issue a certificate,
system status or `CERTIFIED_STOP`.
