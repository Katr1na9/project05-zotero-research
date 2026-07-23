# Part B B0 specification issues

Status: **B0 DRAFT ISSUE REGISTER — NO RUNTIME AUTHORITY**

## PB-SI-001 — B0 name collision

**State:** `RESOLVED FOR NAMING ONLY`.

The legacy experiment plan uses `B0 no-acquisition` for a baseline condition.
The current slice is `B0_PLANNING_AND_CONTRACTS` under Part B and is never an
experimental arm. Documents and manifests must use the full identifier.

## PB-SI-002 — Part B inheritance and phase numbering

**State:** `CLOSED — APPROVED` on `2026-07-23`.

The following names are the normative v0.8 Part B phase map. This decision
freezes numbering and scope vocabulary only; it does not authorize B1–B9
implementation or execution.

| Slice | Normative name |
|---|---|
| B0 | `B0_PLANNING_AND_CONTRACTS` |
| B1 | `B1_FEDERATION_SCHEMAS` |
| B2 | `B2_STOCHASTIC_OBSERVATION` |
| B3 | `B3_COST_INSTRUMENTATION` |
| B4 | `B4_BASELINE_PREREG` |
| B5 | `B5_PLANNER_INTERFACE` |
| B6 | `B6_CLOSED_LOOP_EVAL` |
| B7 | `B7_BROAD_CONNECTORS` |
| B8 | `B8_HOLDOUT_ANALYSIS` |
| B9 | `B9_FREEZE_AND_CLAIMS` |

The v0.7 B1–B6 stages are a reference lineage and do not map directly by
number to this table. B7–B9 are explicit v0.8 extensions for connectors,
holdout analysis and final claim-boundary closeout. The legacy experimental
arm `B0 no-acquisition` remains distinct from Part B B0. The reference v0.7
raw SHA-256 is
`b1ff751758377afa2e3287ce68a2e579ac0a4bcb8c687bf4731e1927290de0da`.

## PB-SI-003 — TV threshold semantics are underspecified

**State:** `CLOSED — APPROVED FOR EXACT FINITE DECISION SEMANTICS ONLY` on
`2026-07-23`.

The normative decision is
`contracts/part-b-b2-world-pair-delta-decision-v0.8.md`. For the current
candidate \(q\), it partitions all frozen legal worlds into those satisfying
\(q\) and those satisfying \(\neg q\), then freezes their complete
`support × alternative` cross-product before any action outcome. A single
support/alternative witness pair is insufficient. It uses unordered
lexicographically canonical pairs, applies an exact rational per-action
\(\delta_a\) with the
inclusive `>=` comparator, and aggregates multiple pairs by
`MINIMUM_TV_WORST_CASE`.

The closure is deliberately narrow. The approved B2 artifacts remain the
historical non-executable snapshot produced while PB-SI-003 was OPEN. A future
executable catalog must embed \(\delta_a\) before hashing, and its evaluation
manifest must bind the required pair set. Estimated-model admission remains
`UNRESOLVED_PB_B2_SI_003`; simulation reproducibility remains
`UNRESOLVED_PB_B2_SI_002`; `sampling_authority=false`. Therefore this closure
does not itself authorize a sampler, stochastic executor, observation,
evidence admission, Planner/M3*, certificate or `CERTIFIED_STOP`.

## PB-SI-004 — Full-cost measurement governance is not approved

**State:** `CLOSED FOR B3 TRACE INSTRUMENTATION; COST CLAIMS STILL BLOCKED`
on `2026-07-23`.

`B3_COST_INSTRUMENTATION` freezes the eight ordered dimensions, trace-event
sources, exact units, aggregation, `UNKNOWN_NOT_ZERO` missingness and
`SEPARATE_NOT_HIGH_COST` feasibility semantics. Its deterministic aggregator
accepts evaluator-supplied integer events and emits exact-rational values.

This closure does not approve real production capture adapters, mixed-currency
FX normalization, scalar weights, sensitivity grids or performance claims.
Accordingly `sampling_authority=false`, `scalarization_authority=false` and
`performance_claim_authority=false`; the B0 cost hash remains unchanged, and
B3 creates no certificate or `CERTIFIED_STOP` authority.

## PB-SI-005 — Legacy M3* is not a Part B interface

**State:** `CLOSED — APPROVED FOR B5 INTERFACE CONTRACT ONLY`.

Frozen machine-tested state token:
`CLOSED 鈥?APPROVED FOR B5 INTERFACE CONTRACT ONLY`.

Part A SI-007 excludes the legacy stochastic M3* runtime. B0 does not reuse or
validate it. B5 now defines a closed public-state, action-ID-only interface and
preserves Checker-only STOP authority.

B4 cross-reference: `B4_BASELINE_PREREG` registers legacy method identifiers,
roles and future interface obligations only. It does not validate an
implementation or define an executable B5 public-state adapter.

B5 closure is deliberately narrow: it establishes the interface contract but
admits no implementation. `PB-B5-SI-001` remains
`OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`. Therefore:

```text
Legacy M3* implementation admission: NOT ESTABLISHED
Legacy M3* execution authority: NONE
```

## PB-SI-006 — Broad connector and dataset scope is unselected

**State:** `OPEN — BLOCKS CONNECTOR/DATA WORK`.

No semantic family, connector, dataset, external holdout or download is
authorized by B0. Adding a source requires explicit pointer, modality, role,
authority, open/closed-world and adapter-conformance contracts.

## PB-SI-007 — Part A and stochastic certification domains must not mix

**State:** `CLOSED FOR B0 BOUNDARY; RUNTIME DESIGN STILL REQUIRED`.

B0 explicitly forbids a stochastic observation contract from entering the
Part A deterministic Executor, formal ceiling or level certificate. Future
Part B certification semantics require separate authorization and cannot
silently extend `CERTIFIED_STOP` beyond the frozen deterministic Kernel Gamma.

## PB-SI-008 — LLM remains outside the authorized track

**State:** `CLOSED FOR B0 SCOPE`.

The user explicitly authorized B0 without LLM. B0 contains no LLM code, prompt,
model, dataset, training, inference, selector or judge contract. Any later LLM
work is a separate authority decision and cannot be inferred from Part B.
