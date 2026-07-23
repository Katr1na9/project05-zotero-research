# Part B B5 public-state / action-ID-only interface contract v0.8

Status: **LOCAL REVIEW — INTERFACE SHAPE ONLY**

## 1. Normative input

The public state is a content-hashed, finite object. Four ID domains are
canonical lists:

1. public claims;
2. admitted evidence;
3. unresolved predicates;
4. currently feasible actions.

Every list is finite, duplicate-free and sorted by its public identifier.
Resource bounds are positive integers. No oracle label, hidden ground truth,
holdout label, realized action outcome or evaluator world may be projected
into the state. The policy rejects any undeclared field.

## 2. Normative output

The decision contains one B4 public selector ID, the exact public-state hash,
one decision status, one feasible action ID or `null`, a reason code and the
document hash. It contains no action body, query material, world prediction,
confidence channel, certificate or STOP signal.

`SELECT_ACTION` requires membership in `feasible_action_ids`.
`NO_ACTION` requires a null selected action. Unknown action IDs and stale
public-state hashes fail closed. Infeasibility remains a separate no-action
condition and is never encoded as a high cost.

## 3. Roster and implementation admission

The B4 13-entry order is replayed exactly. The two non-selector roles remain
separate:

- `ORACLE_EVALUATION_ONLY` is forbidden as a deployable Planner;
- `NO_ACQUISITION` is a no-action control and is not a selector.

PB-SI-005 is `CLOSED — APPROVED FOR B5 INTERFACE CONTRACT ONLY`. For
compatibility with the repository's frozen issue-register spelling, the
machine-tested state token is
`CLOSED 鈥?APPROVED FOR B5 INTERFACE CONTRACT ONLY`.

This closure establishes the interface contract and nothing more.
PB-B5-SI-001 is `OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`; its
machine-tested state token is
`OPEN 鈥?BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`.

```text
Legacy M3* implementation admission: NOT ESTABLISHED
Legacy M3* execution authority: NONE
```

The historical identifier `project05_m3star_h3_dual` remains
`NOT_ADMITTED_UNVERIFIED`. Matching the public-state/action-ID shape does not
validate its feature provenance, learned parameters, runtime behavior,
resource behavior or isolation. The approved implementation list is empty.

## 4. Proof boundary

Schema validity and hash replay prove `CONTRACT_CONSISTENCY_ONLY`.
They provide `NO_IMPLEMENTATION_VALIDATION`, `NO_PERFORMANCE_VALIDITY` and
`NO_SUPERIORITY_CLAIM`. No Planner is run, and no B2 sampler, B3 production
capture, B6 evaluation, B7 connector, B8 holdout analysis, B9 claim freeze,
LLM integration, `09-experiments` access or `CERTIFIED_STOP` authority is
created.
