# PB-SI-008 dual-track separation issue register

Status: **NOT_OPENED**.

The authorized sub-slice establishes a local, deterministic **dual-track
separation** gate with these simultaneous states:

```text
part_b_status=OUTSIDE_AUTHORIZED_TRACK_DENY
experiment_track_status=MAY_PROCEED_UNDER_SEPARATE_AUTHORITY
PB-SI-008=NOT_OPENED
```

Part B rejects attempts to elevate an LLM output or experiment path into
evidence, a claim, authority or a pass condition. The gate classifies the
caller-supplied reference only: **no real LLM call** and **no experiment
artifact read** occur.

This is **not a global LLM ban**. Experiment-track work may proceed under
separate authority. A Part B `DENY` is not an experiment STOP or failure, and
this issue remains `NOT_OPENED`.

Adjacent boundaries remain unchanged:

```text
holdout release: DENY
PB-SI-006 download: DENY
PB-B5 execution: NOT_ESTABLISHED
PB-B8-SI-004: OPEN
stop_authority=NONE
```

This narrow gate grants no Part B evidence, claim, authority, pass condition,
LLM execution, experiment-artifact access, certificate or
`CERTIFIED_STOP`.
