# Part B B2 stochastic-observation and simulation contract v0.8

Status: **APPROVED — CONTRACT ONLY / NO RUNTIME AUTHORITY**

```text
Authorized slice: B2_STOCHASTIC_OBSERVATION
execution_authority=false
sampling_authority=false
PB-SI-003: OPEN
LLM / Planner / M3*: FORBIDDEN
CERTIFIED_STOP authority: NONE
```

## 1. Mathematical object

For a design entry \(a\), the catalog represents:

- a finite world set \(W_a\);
- a finite outcome set \(O_a\); and
- an exact rational conditional distribution
  \(P_a(o\mid w)\) for each \(w\in W_a\) and \(o\in O_a\).

Every row is complete and obeys

\[
\sum_{o\in O_a}P_a(o\mid w)=1.
\]

Binary floating-point values are not normative. A malformed, incomplete or
non-normalized table fails contract validation.

## 2. Total-variation replay

For an explicitly named design pair \((w_i,w_j)\), the contract test may
recompute:

\[
D_{\mathrm{TV}}\left(P_a(\cdot\mid w_i),P_a(\cdot\mid w_j)\right)
=\frac{1}{2}\sum_{o\in O_a}
\left|P_a(o\mid w_i)-P_a(o\mid w_j)\right|.
\]

The registered value is a representation checksum. It is not a production
eligibility result, action ranking, threshold decision or performance claim.

The two examples deliberately have different structures: one binary
two-world table and one three-world/three-outcome table. Only named design
pairs are replayed. This does not imply that omitted pairs are irrelevant.

## 3. Unresolved production policy

`PB-SI-003` remains OPEN. The B2 policy therefore fixes the following values:

```text
world_pair_selection: UNRESOLVED_PB_SI_003
threshold_scope: UNRESOLVED_PB_SI_003
multi_pair_aggregation: UNRESOLVED_PB_SI_003
estimated_model_acceptance: UNRESOLVED_PB_SI_003
missing_decision_behavior: FAIL_CLOSED_NO_SAMPLING
```

No component may infer those decisions from the example tables, from the
registered TV values or from B0 wording.

## 4. Future simulation-envelope requirements

If a later slice separately authorizes simulation, its request must bind:

- the approved catalog and TV-policy hashes;
- one in-domain action ID and world ID;
- a preregistered trial-budget identifier;
- a preregistered seed commitment and generator specification; and
- an approved `PB-SI-003` decision artifact.

Its result must preserve:

- counts for every declared outcome;
- request and trace identities;
- explicit timeout/resource/model-invalid/infeasible status; and
- a clear separation between simulated output and admitted case evidence.

This section defines review requirements only. B2 provides no request/result
Schema, generator, seed, trial loop, estimator or executable command.

## 5. Failure and epistemic boundary

Timeout and resource exhaustion are `UNKNOWN`, not samples and not UNSAT.
Model invalidity is `UNKNOWN`; infeasibility is a feasibility result. None may
be inserted into \(O_a\) or normalized as if it were an observation.

A simulated value would remain simulated until a separately authorized
epistemic policy handles it. It cannot be laundered into observed
`case_evidence`, used to eliminate worlds, or presented as external
validation.

## 6. No STOP or adjacent authority

B2 cannot emit certificates, `system_status` or `CERTIFIED_STOP`, and cannot
extend Part A's deterministic formal ceiling. LLM, training, connectors,
downloads, real data, cost instrumentation, Planner/M3* and B3–B9 remain
outside this contract.
