# Part B B0 boundary contract v0.8

Status: **DRAFT FOR HUMAN REVIEW — CONTRACT ONLY**

- Contract ID: `part-b-b0-boundary-v0.8`
- Authorized slice: `B0_PLANNING_AND_CONTRACTS`
- Authorization date: `2026-07-23`
- Execution authority: **none**
- Next default action: **stop after B0 review**

## 1. Normative position

This contract operationalizes only the planning/artifact boundary implied by
Part B of `active-attribution-experiment-revision-plan-v0.8-20260721.md`. The
v0.8 Part B section inherits concepts from v0.7 but does not define a B0
runtime phase. This document therefore does not silently modify v0.8 or turn a
design choice into approved scientific policy.

The machine-readable authority record is
`configs/part-b-b0-manifest-v0.8.yaml`. Its authorized slice is exactly
`B0_PLANNING_AND_CONTRACTS`. B1–B9 remain closed.

## 2. Authorized outputs

B0 may create or update only:

- planning and authority-status Markdown;
- boundary and canonicalization contracts;
- JSON Schemas for future Part B artifacts;
- non-executable contract examples and manifests;
- schema/hash/invariant tests; and
- a Part B spec-issue register.

B0 may not implement or execute a stochastic observation model, connector,
planner, M3*, baseline, cost collector, experiment, recertification path, or
certificate issuer. It may not modify the Part A Gamma, admission policy,
action catalog, formal ceiling, Checker, Firewall, Executor, or STOP gate.

LLM code, models, prompts, datasets, training, inference, selectors, judges,
and compiler integration are outside this authorization. Merely mentioning
the exclusion is not LLM integration.

## 3. Stochastic-observation draft contract

The B0 artifact is a type/provenance contract, not an observation model ready
for execution. Any later stochastic action must, before execution authority:

1. declare finite world and outcome domains;
2. encode every conditional probability as an exact rational;
3. provide a complete normalized row for every in-scope world;
4. preregister the compared world pairs and
   \(D_{TV}(P,Q)=\frac12\sum_o|P(o)-Q(o)|\);
5. bind the per-action threshold \(\delta_a\) into an approved catalog hash;
6. keep timeout, resource exhaustion, model invalidity, and infeasibility out
   of the observation outcome distribution; and
7. remain unable to create a Part A level certificate or `CERTIFIED_STOP`.

`configs/part-b-observation-contract-v0.8.yaml` contains one explicitly
non-catalog design example so the representation is testable. It confers no
action or sampling authority.

## 4. Full-cost draft contract

The ordered vector is inherited from v0.7:

```text
[T_human, T_wall, T_CPU, M_byte_sec, D_scan, N_record, C_money, T_auth]
```

Each value must eventually come from a versioned executor/authorization trace.
Missing measurements are `UNKNOWN`, never zero. An infeasible action is a
feasibility result, not an arbitrarily high cost. Volatility is represented as
delay loss or a deadline outside the cost vector. Risk requires a separate
future contract.

B0 does not approve scalarization. A later slice must preregister weights,
units, normalization and sensitivity grids before making scalar cost claims.

## 5. Authority separation

- Part A deterministic Kernel certification remains unchanged.
- A Part B stochastic model cannot be passed to the Part A deterministic
  Executor or formal-ceiling verifier.
- A Planner or M3* may propose an action in a future authorized slice but can
  never issue a level certificate or declare `CERTIFIED_STOP`.
- A B0 manifest or hash proves artifact identity only; it proves no external
  validity, performance, calibration, cost superiority or stochastic
  distinguishability.

## 6. B0 error semantics

| Code | Meaning |
|---|---|
| `B0-CONTRACT-001_NO_EXECUTION_AUTHORITY` | A caller attempted runtime use of a contract-only artifact. |
| `B0-CONTRACT-002_OUTSIDE_FROZEN_DOMAIN` | A world, outcome, action or dimension is outside the declared contract. |
| `B0-CONTRACT-003_UNKNOWN_TIMEOUT` | Timeout is UNKNOWN, not an observation or UNSAT. |
| `B0-CONTRACT-004_UNKNOWN_RESOURCE_EXHAUSTED` | Resource exhaustion is UNKNOWN, not an observation or UNSAT. |
| `B0-CONTRACT-005_INFEASIBLE_SEPARATE_FROM_COST` | Feasibility failed and must not be encoded as high cost. |
| `B0-CONTRACT-006_UNAUTHORIZED_COMPONENT` | B1+, LLM, Planner, M3*, connector or experiment code was requested. |

## 7. Exit and next gate

B0 is review-ready only when all three schemas validate, all three artifacts
replay their canonical hashes, Kernel regressions stay green, and the diff
contains no runtime/LLM/training/experiment implementation. Completion of
those checks does not approve the draft semantics.

Any B1–B9 work requires a new explicit user authorization identifying the
slice, approved contracts, editable paths, fixtures and stop condition.
