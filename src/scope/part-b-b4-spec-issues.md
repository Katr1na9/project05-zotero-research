# Part B B4 specification issues

Status: **B4 LOCAL REVIEW — PREREGISTRATION CONTRACT ONLY**

```text
Authorized slice: B4_BASELINE_PREREG
execution_authority=false
sampling_authority=false
planner_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
```

## PB-B4-SI-001 — Baseline implementations are not verified

**State:** `OPEN — BLOCKS BASELINE EXECUTION`.

B4 freezes names, roles and interface obligations. It does not bind an
implementation module, executable artifact, dependency lock, parameter file,
feature extractor or model checksum. All registered methods therefore remain
`UNVERIFIED_FAIL_CLOSED` or `CONTRACT_DEFINED_NOT_EXECUTABLE`.

## PB-B4-SI-002 — B5 public-state adapter is not approved

**State:** `OPEN — BLOCKS PLANNER INTEGRATION`.

The B4 interface declaration is a preregistration envelope, not the B5
Planner API. PB-SI-005 remains open. No legacy M3*, M3a, M3b or other method
may be treated as a verified action-ID-only Planner implementation.

## PB-B4-SI-003 — Execution-ready parameter bundles are absent

**State:** `OPEN — BLOCKS RANDOMIZED OR LEARNED BASELINE EXECUTION`.

The registry declares which entries require training or tuning and fixes the
single `RANDOM_FEASIBLE` contract seed value. It supplies no run-to-case seed
schedule, data split, learned coefficient, tree model, hyperparameter or
endpoint. Any future executable manifest must bind these before evaluation
without reading evaluation or holdout outcomes.

## PB-B4-SI-004 — Oracle metric and regret semantics are not approved

**State:** `OPEN — BLOCKS ORACLE ANALYSIS`.

`ORACLE_EVALUATION_ONLY` is registered only as an evaluator-side role. B4
does not define its information set, objective, cost comparison, regret
formula or statistical claim. It cannot enter deployable rankings.

## PB-B4-SI-005 — Isolation is contractual, not production enforcement

**State:** `OPEN — BLOCKS CLAIMS OF CONTAMINATION-FREE EVALUATION`.

B4 freezes partition and information-flow requirements but implements no data
splitter, access-control layer, artifact store, audit trail or contamination
detector. B8 holdout analysis and B9 claims remain closed.

## Preserved boundaries

B4 does not run a baseline, stochastic sampler, experiment, connector,
training job, LLM, scalarization or superiority analysis. It does not modify
Claim IR, B2/B3 frozen hashes, Part A behavior, certificates or
`CERTIFIED_STOP`.
