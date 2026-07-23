# Part B B3 cost-instrumentation implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B3_COST_INSTRUMENTATION
Authority: deterministic trace aggregation only
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
B4–B9: CLOSED
CERTIFIED_STOP: UNCHANGED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 15-file allowlist

1. `schemas/part-b-cost-trace.schema.json`
2. `schemas/part-b-cost-instrumentation-policy.schema.json`
3. `schemas/part-b-b3-manifest.schema.json`
4. `configs/part-b-cost-instrumentation-policy-v0.8.yaml`
5. `configs/part-b-b3-manifest-v0.8.yaml`
6. `contracts/part-b-b3-boundary-v0.8.md`
7. `contracts/part-b-b3-cost-instrumentation-v0.8.md`
8. `src/cost/__init__.py`
9. `src/cost/instrumentation.py`
10. `src/scope/part-b-b0-spec-issues.md`
11. `src/scope/part-b-b3-spec-issues.md`
12. `tests/unit/test_part_b_b3_contracts.py`
13. `tests/unit/test_part_b_b3_cost_instrumentation.py`
14. `08-writing/part-b-b3-implementation-plan-v0.8-20260723.md`
15. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

Part A, B1/B2 artifacts and hashes, existing Executor behavior, Claim IR,
Planner/M3*, LLM, training, experiments and connectors are outside the
allowlist.

## 2. RED / GREEN

RED was recorded as missing B3 Schemas and `src.cost`. GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b3_contracts -v
python -m unittest tests.unit.test_part_b_b3_cost_instrumentation -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

The final review must replay both new hashes, preserve the B0 cost-contract
hash, show exactly 15 changed files and confirm no staging/commit/push.

## 3. Scientific boundary

B3 changes subjective single-number cost into an auditable vector generated
from explicit trace events. It does not prove those events came from a real
production connector and does not choose how the vector should be collapsed.
Therefore `UNKNOWN_NOT_ZERO`, `SEPARATE_NOT_HIGH_COST`,
`sampling_authority=false`, `scalarization_authority=false` and
`performance_claim_authority=false` are hard gates. B3 has no
`CERTIFIED_STOP` authority.

## 4. Local verification record

```text
Baseline: PB-SI-003 commit 784df1778ee5619a5b6f27040fdbeb968db344f0
B3 targeted tests: 16/16 PASS
Full repository tests: 196/196 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Exact allowlist: 15/15 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```

Local-review artifact identities:

```text
Cost instrumentation policy:
sha256:c64865166be067da37a6f4f5d745ce8dc0421dc342d88589c9bbce6142eb3278

B3 manifest:
sha256:9403004d25c1428beeb85f04c6d65eeb02759d6881ede67390a2d97f2b9c82fb
```

The frozen B0 cost-contract hash remains
`sha256:b6d36c40f7b52c12733dbe75cbcba6058e952f23d67e2155bd73196f6bcfaf53`.
