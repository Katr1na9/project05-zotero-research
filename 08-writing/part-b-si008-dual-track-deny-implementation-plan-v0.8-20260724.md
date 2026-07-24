# PB-SI-008 dual-track DENY implementation plan v0.8

## Scope

This local slice implements only a deterministic **dual-track separation**
decision. It distinguishes Part B admission from an independently authorized
experiment track. It is **not a global LLM ban**.

```text
part_b_status=OUTSIDE_AUTHORIZED_TRACK_DENY
experiment_track_status=MAY_PROCEED_UNDER_SEPARATE_AUTHORITY
PB-SI-008=NOT_OPENED
```

## Approved 15-file boundary

The slice is limited to three closed schemas, three non-executable YAML
documents, two contracts, one pure local classifier, two scope/authority
updates, this plan and two unit-test files. Existing Part B artifacts and
their hashes remain unchanged.

## Invariants

- Experiment-only notices receive `NO_PART_B_ADMISSION_REQUEST` and no
  interference.
- Elevation to Part B evidence, claim, authority or a pass condition is
  `DENY`.
- References are classified without dereferencing: **no real LLM call** and
  **no experiment artifact read**.
- Missing, unknown and contradictory requests fail closed for Part B only.
- Part B denial is not experiment failure or STOP.
- Holdout release and SI-006 download remain `DENY`; B5 execution remains
  `NOT_ESTABLISHED`; PB-B8-SI-004 remains `OPEN`; stop authority is `NONE`.

## Validation and delivery boundary

Acceptance requires 16/16 focused tests, full repository regression,
compileall, diff check, canonical hash replay and an exact 15-file porcelain
review. Local review does not authorize commit, push, PR, LLM invocation,
experiment-artifact access or any later queue item.
