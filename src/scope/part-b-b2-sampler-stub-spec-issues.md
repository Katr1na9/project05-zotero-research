# Part B B2 sampler stub specification issues

Status: **LOCAL STUB REVIEW — ALL ADJACENT AUTHORITIES DENIED**

```text
PB-B2-SI-002: CLOSED FOR REPRODUCIBLE LOCAL FIXTURE SUBSET ONLY
PB-B2-SI-003: OPEN_BLOCKS_EMPIRICAL_MODEL_ADMISSION
PB-SI-006: OPEN_DEFAULT_DENY
PB-B5-SI-001: OPEN_DEFAULT_DENY
holdout release: DENY
catalog_ceiling_eligible=false
CERTIFIED_STOP: DENY
```

## PB-B2-STUB-SI-001 — Scope of the SI-002 subset closure

**State:** `CLOSED_LOCAL_STUB_REPRODUCIBILITY_ONLY_REMAINDER_OPEN`.

The approved subset fixes a deterministic generator/version, seed commitment,
finite non-adaptive trial budget, canonical request/trace identity, resource
accounting and explicit failure semantics for a frozen local fixture. It does
not close production simulation reproducibility, cross-runtime equivalence,
parallel execution, persistence, real-source behavior or empirical validity.

## PB-B2-STUB-SI-002 — Estimated models remain inadmissible

**State:** `OPEN_BLOCKS_EMPIRICAL_MODEL_ADMISSION`.

`PB-B2-SI-003` remains OPEN. No estimator, dataset, calibration, uncertainty
interval, drift policy, acceptance rule or holdout evidence exists. The exact
finite contract tables cannot be described as learned or externally valid.

## PB-B2-STUB-SI-003 — Fixture catalog is not a formal ceiling

**State:** `CLOSED FOR DENY-ONLY SEPARATION`.

The new fixture binds the unchanged B2 design catalog and permits no other
action or world. Every fixture and emitted trace has
`catalog_ceiling_eligible=false`. The stub does not enter the Part A Executor,
world elimination, certificate or `CERTIFIED_STOP` path.

## PB-B2-STUB-SI-004 — Real sources and holdout remain closed

**State:** `OPEN_DEFAULT_DENY`.

`PB-SI-006` remains OPEN and no source is selected. There is no connector,
credential, download, quarantine source, real-data adapter, holdout access or
holdout release. The caller supplies already parsed frozen mappings; the stub
performs no I/O.

## PB-B2-STUB-SI-005 — Planner authority remains closed

**State:** `OPEN_DEFAULT_DENY`.

`PB-B5-SI-001` remains OPEN. The sampler does not accept public state from,
select an action for, send feedback to, evaluate or execute a Planner/M3*.

## Preserved frozen boundary

No B0–B9 artifact is rewritten, and no approved artifact hash changes.
Passing tests proves local contract consistency only. It grants no evidence,
performance, external-validity, certificate, system-state or STOP claim.
