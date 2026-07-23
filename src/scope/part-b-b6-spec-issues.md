# Part B B6 specification issues

Status: **B6 LOCAL REVIEW — CLOSED-LOOP CONTRACT ONLY**

```text
Authorized slice: B6_CLOSED_LOOP_EVAL
planner_implementation_admission_authority=false
planner_execution_authority=false
evaluation_execution_authority=false
sampling_authority=false
production_capture_authority=false
performance_claim_authority=false
stop_authority=NONE
```

## Imported gate: PB-B5-SI-001 — no Planner implementation is admitted

**State:** `OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`.

```text
Legacy M3* implementation admission: NOT ESTABLISHED
Legacy M3* execution authority: NONE
B6 disposition: UNCHANGED_OPEN_FROM_B5
```

B6 imports this gate without editing
`src/scope/part-b-b5-spec-issues.md`. A public-state/action-ID contract and a
closed-loop envelope do not validate, admit or execute a runtime.

## PB-B6-SI-001 — no closed-loop evaluator is implemented

**State:** `OPEN — BLOCKS EVALUATION EXECUTION`.

The policy, episode and feedback examples are serializable contract objects.
There is no evaluator process, action dispatcher, observation adapter, clock,
resource meter or feedback loop. A separately authorized implementation gate
must define those components and demonstrate conformance before execution.

## PB-B6-SI-002 — evaluator-supplied feedback has no production provenance

**State:** `OPEN — BLOCKS REAL FEEDBACK USE`.

The B6 feedback pointer is a non-executed contract reference. It does not
prove that an observation exists, is complete, is eligible for world
elimination, or may enter Claim IR. B2 sampling, production connectors and
Firewall/admission remain separate authorities.

## PB-B6-SI-003 — no statistical or performance authority

**State:** `OPEN — BLOCKS RANKING AND PERFORMANCE CLAIMS`.

B6 registers contract-conformance counts only. It defines no estimand,
scalarization, sample size, confidence interval, hypothesis test, multiple
comparison rule or superiority criterion.

## PB-B6-SI-004 — external and holdout evaluation remain closed

**State:** `OPEN — DEFERRED TO B7/B8/B9`.

No broad connector, external dataset, HOLDOUT release, final analysis or
claim-freeze package is authorized. B7, B8 and B9 remain closed.

## Preserved boundaries

B6 changes no B2–B5 artifact or hash, no B4 roster or isolation rule, no
Claim IR and no Part A Kernel behavior. It creates no `src/planner/`, sampler,
baseline run, production cost capture, LLM path or `09-experiments` change.
It cannot issue a certificate, system state or `CERTIFIED_STOP`.
