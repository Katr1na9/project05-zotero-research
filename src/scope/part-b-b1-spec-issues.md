# Part B B1 specification issues

Status: **B1 CONTRACT ISSUE REGISTER — NO RUNTIME AUTHORITY**

Authorized slice: `B1_FEDERATION_SCHEMAS`
B2–B9: **CLOSED**
LLM: **NOT AUTHORIZED**
`CERTIFIED_STOP`: **UNCHANGED**

## PB-B1-SI-001 — Abstract families are not real connector scope

**State:** `CLOSED FOR B1 CONTRACT; BLOCKS EXTERNAL CLAIMS`.

B1 registers two abstract semantic-family examples to test structural
heterogeneity. It does not select a real source, dataset or connector and does
not close PB-SI-006. Real connector and provenance work remains B7 and requires
per-source authorization.

## PB-B1-SI-002 — Range semantics are not a Kernel Claim IR field

**State:** `CLOSED — APPROVED` on `2026-07-23`.

The approved decision is `CONFORMANCE_ENVELOPE_ONLY`. The frozen Kernel Claim
IR keeps `byte_or_row_range` but does not gain a `range_semantics` field. B1
conformance continues to require `ROWS_HALF_OPEN` or `BYTES_HALF_OPEN` in the
projection envelope.

The Claim IR range pair is opaque. Units and endpoint convention may not be
inferred from numeric values or other claim fields. A missing or mismatched
versioned conformance contract fails closed under the error rules in
`contracts/part-b-b1-range-semantics-v0.8.md`.

Closure decides field ownership only. It grants no production adapter,
connector, runtime, admission, certification or `CERTIFIED_STOP` authority.
Candidate Compiler ownership remains candidate-only and excludes `pointer`.

## PB-B1-SI-003 — Completeness declarations are not completeness proofs

**State:** `OPEN — BLOCKS CLOSED-WORLD RUNTIME USE`.

B1 validates the presence of scope, time window, snapshot identity,
completeness conditions and absence semantics. It does not verify any condition
against a real source. Therefore a B1-valid closed-bounded declaration cannot
by itself exclude a world or support `CERTIFIED_STOP`.

## PB-B1-SI-004 — Cross-family entity binding has no resolver

**State:** `OPEN — BLOCKS FEDERATION RUNTIME`.

The contract requires namespace and binding-rule provenance and fails closed on
collisions. No resolver, reconciliation algorithm or authoritative identity
registry is selected or implemented.

## PB-B1-SI-005 — Adapter/Kernel authority ownership

**State:** `CLOSED FOR B1 BOUNDARY`.

An adapter cannot grant certification authority, admit/promote evidence, issue
a certificate or set system status. The adapter examples must use
`certification_authority.allowed=false`; any later authority decision remains
policy-gated outside the adapter.

## PB-B1-SI-006 — Runtime conformance checking is absent

**State:** `OPEN — EXPECTED IN B1`.

B1 supplies JSON Schemas, hash-bound examples and unit-level contract tests
only. It intentionally does not implement adapter code, a federation runtime,
downloads, connector clients or production JSON Schema validation.

## PB-B1-SI-007 — Stochastic, cost and planning semantics remain closed

**State:** `CLOSED FOR B1 SCOPE`.

PB-SI-003, PB-SI-004 and PB-SI-005 remain unresolved by B1. This slice does not
authorize random observation execution, cost instrumentation or claims,
Planner/M3*, LLM, training or experiments. B2–B9 remain closed.
