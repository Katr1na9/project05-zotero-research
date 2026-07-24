# B8 holdout DENY-audit implementation plan v0.8

## Authorized slice

The 14-file local slice contains three closed Draft 2020-12 schemas, three
non-executable YAML examples, two boundary contracts, one deterministic
DENY-only evaluator, a scope issue note, this plan, the authority append and
the two contract/runtime tests.

## Invariants

The evaluator reads only frozen contract/configuration documents.  It does
not access holdout data, labels or results; it has no network, connector,
release, statistical, Planner, certificate or `CERTIFIED_STOP` authority.
Every request is deterministic and every binding mismatch is denied.

## Verification

```text
python -m unittest tests.unit.test_part_b_b8_holdout_deny_audit_contracts tests.unit.test_part_b_b8_holdout_deny_audit_runtime -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

The claim ceiling is `HOLDOUT_DENY_AUDIT_ONLY`; this slice does not close
`PB-B8-SI-001` through `PB-B8-SI-004`, does not release a holdout and does
not authorize execution.
