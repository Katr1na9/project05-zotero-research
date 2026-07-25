# Part B B8 specification issues

Status: **B8 LOCAL REVIEW — HOLDOUT/ANALYSIS CONTRACT ONLY**

```text
Authorized slice: B8_HOLDOUT_ANALYSIS
holdout_data_access_authority=false
holdout_label_access_authority=false
holdout_result_access_authority=false
statistical_analysis_execution_authority=false
performance_claim_authority=false
stop_authority=NONE
B9=CLOSED
```

## Imported gate: PB-SI-006 — real connector and dataset scope

**State:** `OPEN — BLOCKS CONNECTOR/DATA/HOLDOUT ACCESS`.

B8 replays the B7 deny-only source boundary. No real source, dataset,
external holdout or download is selected. The abstract split commitment is
not a per-source authorization. Every real source still requires PER-SOURCE
SEPARATE AUTHORIZATION, and B8 does not modify
`src/scope/part-b-b0-spec-issues.md`.

## Imported gate: PB-B5-SI-001 — no Planner implementation admitted

**State:** `OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`.

```text
Legacy M3* implementation admission: NOT ESTABLISHED
Legacy M3* execution authority: NONE
B8 disposition: UNCHANGED_OPEN_FROM_B5
```

B8 replays the B4 roster only. It does not modify
`src/scope/part-b-b5-spec-issues.md` or admit any listed method.

## PB-B8-SI-001 — abstract split commitment is not a validated split

**State:** `OPEN — BLOCKS HOLDOUT RELEASE`.

The configured split fingerprint commits an inert phrase solely to test
hash-binding and freeze semantics. It proves no real partition identity,
disjointness, contamination status, completeness or sample size.

## PB-B8-SI-002 — no holdout access or release implementation

**State:** `OPEN — BLOCKS DATA, LABEL AND RESULT ACCESS`.

The release gate is a deny-only contract. No filesystem adapter, data loader,
label reader, result reader, credential resolver, connector or access-control
runtime exists. A Schema-valid artifact cannot change `DENY` to `ALLOW`.

## PB-B8-SI-003 — statistical plan is not an analysis runner

**State:** `OPEN — BLOCKS STATISTICAL EXECUTION`.

The frozen estimands, alpha, multiplicity rule, population, missingness rule,
seed and stopping rule are declarative. No estimator, test, interval,
resampling loop or ranking is implemented or executed.

## PB-B8-SI-004 — no empirical or superiority claim

**State:** `OPEN — DEFERRED TO SEPARATE EXECUTION AUTHORITY AND B9`.

Contract consistency gives no external validity, performance validity,
ranking or superiority result. B3 cost stays an unscalarized
eight-dimensional vector. B9 remains CLOSED, and B8 cannot issue a
certificate, system status or `CERTIFIED_STOP`.
