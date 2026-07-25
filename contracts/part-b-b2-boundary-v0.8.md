# Part B B2 stochastic-observation boundary contract v0.8

Status: **APPROVED — CONTRACT ONLY / NO EXECUTION AUTHORITY**

- Authorized slice: `B2_STOCHASTIC_OBSERVATION`
- Authorization date: `2026-07-23`
- `execution_authority=false`
- `sampling_authority=false`
- `PB-SI-003`: **OPEN — BLOCKS STOCHASTIC EXECUTION**
- Next default action: **stop after B2 review**

## 1. Authorized result

B2 freezes only:

- a finite exact stochastic-observation catalog Schema and non-executable
  examples;
- a total-variation representation and replay policy;
- a non-executable simulation boundary;
- a B2 manifest, issue register, contract tests and authority record.

It implements no sampler, random observation runtime, empirical estimator,
connector, executor, recertification path, Planner/M3*, cost collector,
experiment, LLM component, certificate issuer or system-state transition.

## 2. Inherited bindings

The B2 manifest binds the approved B0 and B1 manifests. Catalog entries bind
the approved B1 semantic-family contract hash. These bindings identify the
contracts used by the examples; they do not create runtime or sampling
authority.

B0's observation artifact remains byte-for-value unchanged. B2 does not turn
that design example into an executable action and does not modify Part A
Kernel artifacts.

## 3. Finite exact representation

Every B2 contract example has:

1. a finite, unique world domain;
2. a finite, unique observation-outcome domain;
3. one complete conditional-distribution row per world;
4. one exact rational probability per declared outcome;
5. a normalized row whose probabilities sum exactly to one; and
6. explicitly separate failure channels.

Timeout, resource exhaustion and invalid models are `UNKNOWN`; infeasibility
is separate. None is an observation outcome, an UNSAT proof or a high-cost
surrogate.

## 4. PB-SI-003 remains open

B2 can replay

\[
D_{\mathrm{TV}}(P,Q)=\frac{1}{2}\sum_{o\in O}|P(o)-Q(o)|
\]

for a named design pair. It does not decide:

- which production world pairs must be compared;
- whether a future threshold is per-pair, worst-case or aggregated;
- how multiple comparisons are aggregated; or
- when an estimated observation model is acceptable.

All four fields are machine-recorded as `UNRESOLVED_PB_SI_003`. A missing
approved decision fails closed as `FAIL_CLOSED_NO_SAMPLING`. Closing this B2
contract slice does not close `PB-SI-003`.

## 5. Non-executable simulation boundary

The companion stochastic-observation contract describes the minimum
provenance a future simulation request/result would need. That description is
an interface proposal only. No request can be instantiated, no pseudorandom
draw can be made and no result can enter case evidence, world elimination,
recertification or an experiment while `sampling_authority=false`.

Algebraically replaying a frozen probability table and its registered design
TV in a contract test is validation, not simulation or sampling.

## 6. Authority separation

- Part A deterministic observation and formal-ceiling semantics are unchanged.
- B2 examples have `catalog_ceiling_eligible=false`.
- B2 cannot emit a claim, observation, admission decision, certificate,
  `system_status` or `CERTIFIED_STOP`.
- LLM, Planner/M3*, B3–B9 and production adapter/connector work remain closed.
- A hash establishes artifact identity only, not empirical validity,
  calibration, distinguishability, performance or scientific superiority.

## 7. Stop gate

The B2 contract slice and its three exact hashes were approved on
`2026-07-23`. That approval authorizes only the frozen contract artifacts and
their local commit. Push, PR, stochastic execution and every later Part B slice
still require separate explicit authorization. Execution additionally requires
an approved closure of `PB-SI-003`.

## 8. PB-SI-003 decision addendum — 2026-07-23

The separately authorized decision contract
`part-b-b2-world-pair-delta-decision-v0.8.md` now marks PB-SI-003
`CLOSED — APPROVED FOR EXACT FINITE DECISION SEMANTICS ONLY`.

It partitions all frozen legal worlds by candidate \(q\), freezes the complete
`support × alternative` cross-product before an action outcome, rejects a
single-witness-pair shortcut, uses canonical unordered pairs, and requires an exact rational
per-action `delta_a` bound into a future executable catalog hash, and applies
`MINIMUM_TV_WORST_CASE` with an inclusive `>=` gate.

This addendum does not retroactively make the B2 examples executable. The
original B2 artifact remains the snapshot created while PB-SI-003 was OPEN.
`sampling_authority=false`; estimated-model admission remains
`UNRESOLVED_PB_B2_SI_003`; no observation, certificate or `CERTIFIED_STOP` is
authorized.
