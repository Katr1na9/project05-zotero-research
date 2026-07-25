# Part B B4 baseline isolation contract v0.8

Status: **LOCAL REVIEW — NON-EXECUTING ISOLATION POLICY**

## 1. Partition rule

The normative order is `TRAIN`, `TUNE`, `EVALUATION`, `HOLDOUT`. The four
partitions must be mutually disjoint.

- TRAIN may serve preregistered model fitting only.
- TUNE may serve preregistered parameter selection only.
- EVALUATION is available only after the registry, parameters, endpoints,
  seeds and tie-break rules are frozen.
- HOLDOUT remains sealed until a separately authorized B8 final analysis.

Evaluation outcomes cannot flow back to training. Holdout outcomes cannot flow
to any model. A Schema-valid policy is not evidence that a real dataset split
exists or is uncontaminated.

## 2. No outcome-dependent mutation

After the first evaluation outcome, the roster, parameters, endpoints, seeds
and tie-break rules are immutable for that preregistered comparison. Any
attempted mutation invalidates the registration and fails closed.

The following material cannot complete or alter registration:

- historical result rows;
- realized action outcomes;
- holdout labels;
- oracle world identifiers;
- parameters, labels or selected actions recovered from `09-experiments/`.

This rule prevents a historical result directory from becoming an implicit
training, tuning or endpoint-selection channel.

## 3. Non-authority

This file provides no data-loading or filesystem enforcement implementation.
It authorizes no baseline execution, sampling, connector, download, training,
LLM, B5 Planner, B6 evaluation, B7 connector, B8 holdout analysis or B9 claim.
It does not change B2/B3 hashes and cannot emit `CERTIFIED_STOP`.
