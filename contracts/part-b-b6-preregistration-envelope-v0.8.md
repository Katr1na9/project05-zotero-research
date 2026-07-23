# Part B B6 preregistration-envelope contract v0.8

Status: **CONTRACT FREEZE ONLY — NO EVALUATION RUN**

## 1. Freeze point

The envelope must be frozen `BEFORE_FIRST_FEEDBACK`. After that point it
forbids mutation of:

- the B4 roster and role assignment;
- inherited artifact hashes;
- registered contract metrics;
- TRAIN/TUNE/EVALUATION/HOLDOUT partitions;
- finite decision bounds; and
- tie-break rules.

A violation yields `FAIL_CLOSED_EVALUATION_NOT_PREREGISTERED`. The contract
contains no waiver or automatic retry.

## 2. Isolation

The four B4 partitions remain mutually disjoint. EVALUATION feedback cannot
flow to TRAIN or TUNE. HOLDOUT stays sealed until a separately authorized B8
final-analysis gate and cannot feed any model. Historical result access is
false; the `09-experiments/` prefix is listed only as forbidden material and
is not read by B6.

## 3. Registered contract metrics

The only B6 contract metrics are:

```text
INTERFACE_CONFORMANCE
FEEDBACK_BOUNDARY_CONFORMANCE
FAILURE_CHANNEL_COUNTS
UNSCALARIZED_RESOURCE_VECTOR_SHAPE
```

They validate a contract shape. They do not measure success, cost advantage,
regret, statistical power, external validity or superiority.

## 4. Preserved limits

The B5 bounded-evaluation caps are copied by exact hash and value. Copying
them creates no clock, process, memory meter or evaluator. B6 does not admit a
Planner implementation, sample observations, collect production cost,
execute a baseline or release HOLDOUT.

This envelope cannot issue a certificate, system status or
`CERTIFIED_STOP`. B7–B9 remain closed.
