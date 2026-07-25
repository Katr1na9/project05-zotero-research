# Part B B8 statistical-preregistration contract v0.8

Status: **LOCAL REVIEW — PLAN FROZEN, NOT EXECUTED**

## 1. Outcome-blind freeze

The primary estimand is the paired difference in the case-level success
indicator. Its direction is frozen as `HIGHER_IS_BETTER`, and its smallest
effect size of interest is represented exactly as `1/20`.

The secondary estimand is the componentwise paired difference of the B3
eight-dimensional resource vector:

```text
[T_human, T_wall, T_CPU, M_byte_sec,
 D_scan, N_record, C_money, T_auth]
```

The normative configuration contains each B3 dimension exactly once.
Secondary cost reporting is descriptive and componentwise. Scalarization and
outcome-dependent metric selection are forbidden.

## 2. Error control and population

The plan freezes:

- exact `alpha=1/20` and confidence level `19/20`;
- the primary family and `HOLM_STEP_DOWN` multiplicity procedure;
- `CASE` as the analysis unit;
- inclusion of all preregistered holdout cases;
- the sole predeclared schema-invalid exclusion rule;
- fixed seed `1729`, 10,000 planned resampling iterations and a deterministic
  method-ID tie break; and
- a single fixed analysis with no interim peeking, optional stopping,
  adaptive endpoint selection or adaptive sample size.

These values are contractual parameters only. No resampling, estimation,
hypothesis test or confidence interval is executed by B8.

## 3. Missingness and failures

Outcome-dependent exclusion and imputation are forbidden. Missing values are
not implicit zero and cannot be rewritten as losses. Timeout and resource
exhaustion are `UNKNOWN_NO_RANK`; infeasibility is `SEPARATE_NO_RANK`.

The plan contains no effect estimate, p-value, label, result, ranking or
superiority statement. It supplies NO STATISTICAL EXECUTION and NO
PERFORMANCE CLAIM.

## 4. Authority boundary

This preregistration does not close `PB-SI-006` or `PB-B5-SI-001`. It grants
no source access, Planner execution, statistical execution, B9 claim,
certificate, system state or `CERTIFIED_STOP`.
