# Part B B5 bounded-evaluation contract v0.8

Status: **LOCAL REVIEW — NON-EXECUTING CONFORMANCE ENVELOPE**

## 1. Finite bounds

The B5 evaluation artifact declares positive, finite caps for public-state
bytes, feasible action IDs, decision wall time, decision CPU time, memory and
decisions per case. These caps define
`FINITE_PREDECLARED_CONFORMANCE_ENVELOPE`; they do not start a process, read a
clock, allocate resources or run an evaluation.

There is no automatic retry and no fallback to hidden state. Timeout and
resource exhaustion are `UNKNOWN_NO_RANK`. Unknown failures fail closed.
Infeasibility is `SEPARATE_NO_ACTION`, not a failure score and not a high
cost.

## 2. Cost and metric boundary

The only cost representation referenced by B5 is the frozen B3
`B3_EIGHT_DIMENSION_VECTOR_ONLY` contract. Missing measurements remain
`UNKNOWN_NOT_ZERO`. Scalarization is disabled.

The only contract-level metric shapes are:

- `INTERFACE_CONFORMANCE`;
- `FAILURE_CHANNEL_COUNTS`;
- `UNSCALARIZED_RESOURCE_VECTOR_SHAPE`.

This list authorizes neither measurement nor comparison. Passing these checks
proves `CONTRACT_CONSISTENCY_ONLY`, with `NO_IMPLEMENTATION_VALIDATION`,
`NO_PERFORMANCE_VALIDITY` and `NO_SUPERIORITY_CLAIM`.

## 3. Isolation and non-authority

TRAIN, TUNE, EVALUATION and HOLDOUT remain separated by the frozen B4
isolation policy. Evaluation feedback cannot flow to training; holdout remains
sealed; historical results and `09-experiments/` are forbidden.

No Planner, baseline, B2 sampler, B3 production capture, connector, LLM,
training, tuning, B6, B7, B8 or B9 operation is authorized. This contract
cannot issue a certificate or `CERTIFIED_STOP`.
