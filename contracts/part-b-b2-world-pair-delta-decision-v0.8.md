# Part B PB-SI-003 world-pair / delta decision v0.8

Status: **CLOSED — APPROVED FOR EXACT FINITE DECISION SEMANTICS ONLY**

```text
Authorized slice: B2_SI003_WORLD_PAIR_DELTA_DECISION_ONLY
PB-SI-003: CLOSED — APPROVED (exact finite tables only)
decision_rule_authority=true
execution_authority=false
sampling_authority=false
Estimated-model admission: UNRESOLVED_PB_B2_SI_003
CERTIFIED_STOP authority: NONE
```

## 1. Exact decision

For the frozen finite legal-world domain and current candidate \(q\), define
`support` as **all** legal worlds satisfying \(q\), and `alternative` as
**all** legal worlds satisfying \(\neg q\). These are two non-empty, disjoint
finite partitions when a counterexample exists. The required comparison set
is their complete cross product

\[
R=\{\{w_s,w_a\}:w_s\in support,\;w_a\in alternative\}.
\]

Pairs are unordered, stored once, and encoded in lexicographic orientation.
Self-pairs, duplicates and a caller-selected subset are invalid. `R` must be
frozen and bound by the evaluation-manifest hash before any action outcome is
observed.

The Checker's first support SAT witness and first alternative SAT witness do
not establish these complete partitions. A single witness pair is never
sufficient for the production decision. If the frozen legal-world domain
cannot be completely partitioned, eligibility fails closed.

For an action \(a\), `delta_a` is an exact rational in `[0,1]`, scoped to that
action, with no default. A future executable action catalog must carry
`delta_a` before its catalog hash is computed. The inclusive pair decision is

\[
D_{TV}(P_a(\cdot\mid w_i),P_a(\cdot\mid w_j))\ge\delta_a.
\]

For more than one required pair, the aggregate is
`MINIMUM_TV_WORST_CASE`. Equivalently, the action passes only when every
required pair is covered by its finite observation domain and every pair
meets the inclusive threshold. Empty, missing or out-of-domain pair sets fail
closed and confer no eligibility.

## 2. Why this closes PB-SI-003 narrowly

The decision fixes the previously missing world-pair source, pair
orientation, threshold scope, inclusive comparator and multi-pair
aggregation. It does not modify the three approved B2 hashes. Those artifacts
remain an audit snapshot created while PB-SI-003 was OPEN and their catalog
entries remain non-executable design examples.

The decision artifact itself is not a substitute for the v0.8 requirement
that a production `delta_a` be embedded in a future executable action/catalog
hash. No such catalog currently exists.

JSON Schema alone cannot prove cross-field partition completeness, canonical
pair ordering, `numerator <= denominator` or rational reduction. The approved
artifact's contract tests replay those invariants. Any future executable
catalog requires a separately reviewed runtime validator; it may not infer
validity from Schema success alone.

## 3. Remaining sampler gates

Closing PB-SI-003 does not authorize sampling. At minimum, the following
remain unresolved:

- `UNRESOLVED_PB_B2_SI_002`: generator, seed commitment, trial budget and
  trace reproducibility;
- `UNRESOLVED_PB_B2_SI_003`: estimated-model provenance, calibration,
  uncertainty, drift and empirical acceptance;
- a separately approved executable catalog whose hash binds `delta_a`; and
- a separately approved stochastic executor/request/result contract.

Design-table replay remains algebra over exact rationals. It is not a random
draw, case observation, external-validity result or evidence-admission event.

## 4. Authority boundary

This ruling cannot produce observations, eliminate worlds, admit evidence,
rank Planner/M3* actions, issue a certificate or emit a system status.
`CERTIFIED_STOP` remains limited to the separately approved deterministic
Part A Kernel. LLM, connectors, datasets, training and stochastic runtime are
outside this decision.
