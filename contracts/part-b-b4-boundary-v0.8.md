# Part B B4 baseline-preregistration boundary v0.8

Status: **LOCAL REVIEW — CONTRACT ONLY**

```text
Authorized slice: B4_BASELINE_PREREG
execution_authority=false
sampling_authority=false
planner_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
NO_BASELINE_EXECUTION
NO_DATA_ACQUISITION
NO_CONNECTOR_DOWNLOAD
NO_STOCHASTIC_SAMPLER
B5–B9: CLOSED
```

## 1. Authorized result

B4 may freeze a finite baseline roster, the public/evaluator interface role of
each entry, deterministic tie-breaking and failure semantics, and the
separation of train, tune, evaluation and holdout partitions. It may bind
those contracts to the already frozen B2 and B3 artifact hashes.

These are preregistration records. They are not an executable registry,
factory, loader, model, sampler, connector, data splitter, evaluator or
Planner interface. `implementation_status=UNVERIFIED_FAIL_CLOSED` and
`CONTRACT_DEFINED_NOT_EXECUTABLE` both forbid invocation.

## 2. Information boundary

Every deployable or reference baseline receives public state and returns only
an action ID or no action. Oracle labels, hidden ground truth, holdout labels
and realized action outcomes are forbidden deployment inputs.

`ORACLE_EVALUATION_ONLY` is a separate evaluator-only comparator. It is not
deployable and cannot enter a deployable ranking or justify a performance
claim. Its presence does not grant any baseline access to evaluator state.

The legacy `NO_ACQUISITION` arm is distinct from the normative Part B phase
`B0_PLANNING_AND_CONTRACTS`.

## 3. Authority boundary

B2 contract algebra does not become a B2 sampler through B4. B3 trace
instrumentation does not become production cost capture or scalar cost
through B4. PB-SI-005 remains open, so the legacy M3 family is not a verified
B5 interface.

B4 cannot run an experiment, read `09-experiments`, collect data, select a
connector, fit a model, reuse a legacy model, calculate superiority, sign a
certificate, emit system state or extend `CERTIFIED_STOP`. LLM integration is
forbidden. B5, B6, B7, B8 and B9 require separate explicit authorization.
