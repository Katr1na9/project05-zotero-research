# B8 holdout DENY-audit specification issues

Status: **B8_HOLDOUT_DENY_AUDIT — LOCAL CONTRACT ONLY**

```text
PB-B8-SI-001: OPEN — split commitment is not a validated released split
PB-B8-SI-002: OPEN — holdout data, label and result access are denied
PB-B8-SI-003: OPEN — statistical execution remains unavailable
PB-B8-SI-004: OPEN — no empirical, performance or superiority claim
PB-SI-006: DENY — source selection does not authorize retrieval or download
PB-B5-SI-001: NOT_ESTABLISHED — Planner execution authority is absent
CERTIFIED_STOP: NONE
```

The only local decision is `HOLDOUT_DENY_AUDIT_ONLY`.  The audit binds the
existing B8 policy, preregistration, no-data envelope and manifest by their
declared hashes and fails closed on mismatch.  It never reads labels or
results, never releases a holdout, and performs no statistical execution.
