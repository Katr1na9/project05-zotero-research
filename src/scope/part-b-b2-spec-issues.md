# Part B B2 specification issues

Status: **B2 CONTRACT ISSUE REGISTER — NO RUNTIME AUTHORITY**

```text
Authorized slice: B2_STOCHASTIC_OBSERVATION
execution_authority=false
sampling_authority=false
LLM: FORBIDDEN
CERTIFIED_STOP: NONE
```

## PB-B2-SI-001 — Inherited TV policy decision is unresolved

**State:** `CLOSED — APPROVED FOR EXACT FINITE WORLD-PAIR / DELTA SEMANTICS`
on `2026-07-23`.

The separate decision contract
`contracts/part-b-b2-world-pair-delta-decision-v0.8.md` closes the portion
carried from `PB-SI-003`: partition all frozen legal worlds by candidate
\(q\), compare the complete `support × alternative` cross-product (not only
the first SAT witnesses), use canonical unordered orientation and pre-outcome
pair-set binding, exact rational
per-action \(\delta_a\), inclusive `>=`, and `MINIMUM_TV_WORST_CASE`.

The three approved B2 hashes are unchanged and remain an audit snapshot made
while PB-SI-003 was OPEN. Their examples remain non-executable. Closing this
issue gives decision-rule semantics only: `sampling_authority=false`.
Estimated-model admission remains `UNRESOLVED_PB_B2_SI_003` under
PB-B2-SI-003, and simulation reproducibility remains
`UNRESOLVED_PB_B2_SI_002`. There is no executable stochastic catalog, sampler,
case-evidence path or `CERTIFIED_STOP` authority.

## PB-B2-SI-002 — Simulation reproducibility policy is not approved

**State:** `OPEN — BLOCKS SIMULATION RUNTIME`.

A future simulation needs a generator specification, seed commitment, trial
budget, trace identity, resource policy and failure semantics. B2 documents
the required categories but does not select values or implement a simulator.

## PB-B2-SI-003 — Estimated observation-model provenance is undefined

**State:** `OPEN — BLOCKS EMPIRICAL MODEL ADMISSION`.

No dataset, estimator, calibration method, uncertainty interval, drift rule,
holdout boundary or acceptance test is authorized. Design-table probabilities
must not be described as learned, calibrated or externally valid.

## PB-B2-SI-004 — Schema cannot prove cross-field normalization

**State:** `OPEN — CONTRACT TEST MITIGATION ONLY`.

JSON Schema validates structure and exact rational types but does not prove
that every row names exactly the declared outcomes and sums to one. B2 tests
perform that check for frozen examples. A future runtime needs an independently
reviewed validator before it can consume any new catalog.

## PB-B2-SI-005 — Part A and B2 authority must remain separate

**State:** `CLOSED FOR CONTRACT BOUNDARY; RUNTIME STILL UNAUTHORIZED`.

B2 entries have `catalog_ceiling_eligible=false`. They cannot enter the Part A
deterministic Executor, formal ceiling, world elimination, level certificate
or `CERTIFIED_STOP` path. This closure records separation only and grants no
runtime, sampling, LLM or Planner/M3* authority.

## Deferred gates

B3–B9 remain closed. Connector/data, cost, baseline, Planner, closed-loop,
holdout and claim-boundary decisions must not be implemented under B2.
