# Part B B8 holdout DENY-audit boundary v0.8

This slice is `B8_HOLDOUT_DENY_AUDIT` with claim ceiling
`HOLDOUT_DENY_AUDIT_ONLY`.  It audits the preregistered, contract-only
release gate and emits deterministic DENY records.  It is not a holdout
release, data loader, label reader, result reader or statistical runner.

```text
DEFAULT_DECISION=DENY
RELEASE_DECISION=DENY
HOLDOUT_DATA_ACCESS_AUTHORITY=false
HOLDOUT_LABEL_ACCESS_AUTHORITY=false
HOLDOUT_RESULT_ACCESS_AUTHORITY=false
STATISTICAL_ANALYSIS_EXECUTION_AUTHORITY=false
STOP_AUTHORITY=NONE
```

The policy, preregistration, no-data envelope and B8 manifest are read-only
hash bindings.  A binding mismatch is denied.  The audit does not read a
holdout label or holdout result, and performs NO STATISTICAL EXECUTION.

`PB-B8-SI-001` through `PB-B8-SI-004` remain `OPEN`.  `PB-SI-006` remains
`DENY`; `PB-B5-SI-001` remains `NOT_ESTABLISHED`.  No certificate,
`system_status`, performance claim, superiority claim or `CERTIFIED_STOP`
authority is emitted.
