# Part B B3 specification issues

Status: **B3 LOCAL REVIEW — INSTRUMENTATION AUTHORITY ONLY**

```text
Authorized slice: B3_COST_INSTRUMENTATION
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
CERTIFIED_STOP: NONE
```

## PB-B3-SI-001 — Production capture adapters are not implemented

**State:** `OPEN — BLOCKS CLAIMS ABOUT REAL EXECUTOR MEASUREMENTS`.

B3 aggregates evaluator-supplied integer events. It does not hook operating
system clocks, CPU/memory accounting, analyst activity, authorization systems,
billing APIs or source connectors. A later adapter must prove its units and
provenance before a trace can be called a real production measurement.

## PB-B3-SI-002 — Memory integral capture cadence is unapproved

**State:** `OPEN — BLOCKS PRODUCTION M_byte_sec CAPTURE`.

The aggregator accepts `byte_nanoseconds`, but capture cadence, interpolation,
process-tree boundaries and child-process accounting are outside B3. Missing
capture remains `UNKNOWN_NOT_ZERO`.

## PB-B3-SI-003 — Cross-currency normalization is unapproved

**State:** `OPEN — MIXED CURRENCY FAILS CLOSED`.

B3 accepts zero or one ISO-4217 currency per trace. It provides no FX source,
valuation timestamp, base currency or rounding rule.

## PB-B3-SI-004 — Scalarization and superiority claims are unapproved

**State:** `OPEN — BLOCKS SCALAR COST AND PERFORMANCE CLAIMS`.

Weights, normalization, sensitivity grids, budgets and preregistered claim
rules remain unset. `scalarization_authority=false` and
`performance_claim_authority=false`.

## PB-B3-SI-005 — Feasibility remains separate

**State:** `CLOSED FOR B3 CONTRACT`.

The implementation enforces `SEPARATE_NOT_HIGH_COST`, preserves partial trace
events and emits no invented scalar for infeasible actions. This closure
grants no Planner/M3*, sampling, action execution, certificate or
`CERTIFIED_STOP` authority.

## PB-B3-SI-006 — JSON Schema cannot prove trace cross-field invariants

**State:** `CLOSED FOR B3 BY RUNTIME VALIDATION + CONTRACT TESTS`.

JSON Schema describes the eight rows but cannot by itself prove that
`complete` agrees with all measurement statuses or that the source events
replay the vector. `CostTraceInstrumenter` constructs the output
deterministically, rejects undeclared missingness and binds a source-trace
hash; tests then validate the generated document. Arbitrary externally
supplied trace JSON is not admitted as a B3 measurement merely because it is
Schema-valid. `sampling_authority=false`,
`performance_claim_authority=false`, `scalarization_authority=false`, and no
`CERTIFIED_STOP` authority follows.
