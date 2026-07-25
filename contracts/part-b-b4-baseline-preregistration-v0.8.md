# Part B B4 baseline preregistration contract v0.8

Status: **LOCAL REVIEW — IDENTITIES AND INTERFACES ONLY**

## 1. Frozen roster

The following order is normative and finite:

| ID | Intended comparison role | B4 execution state |
|---|---|---|
| `NO_ACQUISITION` | reference-only abstention control | not executable |
| `RANDOM_FEASIBLE` | reference-only seeded random control | unverified / fail closed |
| `COVERAGE_GREEDY` | intended deployable public heuristic | unverified / fail closed |
| `CMI_PROXY` | reference-only information proxy | unverified / fail closed |
| `M1_STATIC_EXPECTED_GAIN` | reference-only legacy static method | unverified / fail closed |
| `M2_TRANSPARENT` | intended deployable transparent method | unverified / fail closed |
| `M3A_GAP_COMPATIBILITY` | reference-only legacy model | unverified / fail closed |
| `LOGISTIC_M3B` | reference-only learned baseline | unverified / fail closed |
| `XGBOOST_ACTION_VALUE` | reference-only learned baseline | unverified / fail closed |
| `AFA_VOI_MYOPIC` | reference-only VOI baseline | unverified / fail closed |
| `AFA_VOI_ROLLOUT_H3` | reference-only rollout baseline | unverified / fail closed |
| `DEPTH2_PUBLIC` | reference-only public search baseline | unverified / fail closed |
| `ORACLE_EVALUATION_ONLY` | evaluator-only comparator | never deployable |

Registration is not validation. In particular, these names do not import
historical code, parameters, feature maps, model files or results, and they do
not close PB-SI-005.

## 2. Common interface declaration

Every row declares:

- method family, contract version and comparison role;
- whether the interface is public-state-only;
- allowed public inputs and evaluator-only inputs;
- action-ID-only output with explicit no-action support;
- forbidden deployment inputs;
- training and tuning requirements;
- implementation verification state;
- randomness mode, seed policy and deterministic tie-break;
- explicit timeout, resource-exhaustion, infeasibility and unknown semantics.

Timeout and resource exhaustion are `UNKNOWN_NO_RANK`, never a loss, UNSAT or
zero cost. Infeasibility is `SEPARATE_NO_ACTION`, never an invented high cost.
An unverified implementation fails closed and cannot silently fall back to a
legacy result.

## 3. Oracle and claim boundary

`ORACLE_EVALUATION_ONLY` may be described for a future evaluator-side regret
or lower-bound comparison. B4 does not implement that comparison. Oracle
state cannot enter candidate/deployment inputs, baseline training, tuning or
deployable ranking.

No roster entry has `performance_claim_authority`. No scalarization, success
claim, cost superiority or global-optimality statement follows from this
contract. `execution_authority=false`, `sampling_authority=false`,
`planner_authority=false` and `stop_authority=NONE`.
