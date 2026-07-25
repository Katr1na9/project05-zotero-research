# PB-SI-008 dual-track separation boundary v0.8

Status: **PB-SI-008 = NOT_OPENED**.

This slice establishes **dual-track separation**. For Part B, the state is
`OUTSIDE_AUTHORIZED_TRACK_DENY`; for the independent experiment track, the
state is `MAY_PROCEED_UNDER_SEPARATE_AUTHORITY`. Those states coexist. A
Part B denial is not an experiment failure, suspension or revocation.

This is **not a global LLM ban**. Independent LLM or `09-experiments`
development may proceed under authority granted outside Part B. This slice
does not inspect, approve, reject or execute that work.

The local gate receives only a caller-supplied classification record. It
performs **no real LLM call** and **no experiment artifact read**. LLM-output
and experiment-path references are classified but never dereferenced. The
existence, path or test result of an experiment is never a condition for this
contract to pass.

`EXPERIMENT_TRACK_ONLY` with `promotion_target=NONE` produces
`NO_PART_B_ADMISSION_REQUEST` and
`NO_INTERFERENCE_SEPARATE_AUTHORITY_REQUIRED`. An attempted
`PROMOTE_TO_PART_B` for `EVIDENCE`, `CLAIM`, `AUTHORITY` or
`PASS_CONDITION` fails closed with `DENY`.

The denial applies only to Part B admission. It grants no evidence, claim,
authority, pass condition, holdout release, download, Planner execution,
certificate, system status or STOP authority.

```text
holdout_release=DENY
PB-SI-006 download=DENY
PB-B5 execution=NOT_ESTABLISHED
PB-B8-SI-004=OPEN
stop_authority=NONE
```
