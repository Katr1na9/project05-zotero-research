# Part B B8 holdout DENY-audit contract v0.8

## Scope

The local evaluator accepts only a small request record and returns a
reproducible audit record.  `release_holdout`, label access, result access,
data access and statistical execution are all explicit DENY outcomes.
`requested_decision=ALLOW` never changes the release decision.

## Fail-closed rules

- Missing or unknown request fields are denied.
- A caller-supplied binding set must match the frozen B8 hashes exactly.
- The evaluator reads contract/configuration files only; it performs no
  network I/O and never opens a holdout payload.
- The record carries no holdout label, holdout result, statistic, ranking or
  superiority claim.

```text
HOLDOUT_DENY_AUDIT_ONLY
DEFAULT_DECISION=DENY
NO HOLDOUT LABEL
NO HOLDOUT RESULT
NO STATISTICAL EXECUTION
CERTIFIED_STOP=NONE
```

This contract does not close `PB-B8-SI-001`, `PB-B8-SI-002`,
`PB-B8-SI-003` or `PB-B8-SI-004`, and it does not establish `PB-SI-006`
source authorization or `PB-B5-SI-001` Planner execution.
