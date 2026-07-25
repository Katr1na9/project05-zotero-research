# Part B B5 Planner-interface boundary v0.8

Status: **LOCAL REVIEW — CONTRACT ONLY**

```text
Authorized slice: B5_PLANNER_INTERFACE
planner_interface_authority=true
bounded_evaluation_contract_authority=true
planner_execution_authority=false
evaluation_execution_authority=false
sampling_authority=false
production_capture_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
NO_BASELINE_EXECUTION
NO_B2_SAMPLER
NO_B3_PRODUCTION_CAPTURE
NO_CONNECTOR
B6–B9: CLOSED
LLM: FORBIDDEN
09-experiments: FORBIDDEN
```

## 1. Authorized result

B5 may freeze the shape of a public Planner state, the action-ID-only decision
envelope, the exact B4 roster binding, implementation-admission rules and a
finite conformance-evaluation envelope. These artifacts are Schemas, abstract
examples, policies and contracts. They are not a Planner, adapter, loader,
factory, evaluator, sampler, experiment or connector.

The only positive authority is to state and validate the interface contracts.
Passing the B5 tests proves `CONTRACT_CONSISTENCY_ONLY`. It provides
`NO_IMPLEMENTATION_VALIDATION`, `NO_PERFORMANCE_VALIDITY` and
`NO_SUPERIORITY_CLAIM`.

## 2. Public-state and decision boundary

The Planner-facing state contains only a case ID, decision step, finite sorted
public claim IDs, admitted-evidence IDs, unresolved-predicate IDs, feasible
action IDs and positive remaining resource bounds. Oracle labels, hidden
ground truth, holdout labels, realized outcomes, evaluator worlds,
certificates and system state are outside the Schema.

A decision binds the exact public-state hash and returns either one feasible
action ID or explicit no action. It carries no action payload, predicted world,
confidence side channel, certificate or system status. An unknown action or a
stale state hash fails closed.

## 3. Runtime and authority boundary

No registered B4 method is executable merely because it can be described by
the B5 interface. `ORACLE_EVALUATION_ONLY` stays evaluator-only and
`NO_ACQUISITION` stays a no-action control. B5 does not read historical
results from `09-experiments`, execute a baseline, run B2 sampling, attach B3
production capture, train or tune a model, invoke an LLM, download data or
connect to an external source.

B5 cannot issue a certificate, system state or `CERTIFIED_STOP`. B6, B7, B8
and B9 remain closed and require separate authorization.
