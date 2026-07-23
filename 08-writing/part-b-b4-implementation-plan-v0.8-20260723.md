# Part B B4 baseline-preregistration implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B4_BASELINE_PREREG
Authority: Schema / policy / manifest / contracts / tests only
execution_authority=false
sampling_authority=false
planner_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
B5–B9: CLOSED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 15-file allowlist

1. `schemas/part-b-baseline-preregistration.schema.json`
2. `schemas/part-b-baseline-isolation-policy.schema.json`
3. `schemas/part-b-b4-manifest.schema.json`
4. `configs/part-b-baseline-preregistration-v0.8.yaml`
5. `configs/part-b-baseline-isolation-policy-v0.8.yaml`
6. `configs/part-b-b4-manifest-v0.8.yaml`
7. `contracts/part-b-b4-boundary-v0.8.md`
8. `contracts/part-b-b4-baseline-preregistration-v0.8.md`
9. `contracts/part-b-b4-baseline-isolation-v0.8.md`
10. `src/scope/part-b-b0-spec-issues.md`
11. `src/scope/part-b-b4-spec-issues.md`
12. `tests/unit/test_part_b_b4_contracts.py`
13. `tests/unit/test_part_b_b4_baseline_prereg.py`
14. `08-writing/part-b-b4-implementation-plan-v0.8-20260723.md`
15. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

Part A behavior, B2/B3 artifacts and hashes, runtime source, LLM, training,
connectors and `09-experiments` are outside this allowlist.

## 2. RED / GREEN contract

RED recorded 12 tests failing only because B4 artifacts were absent. GREEN
requires:

```text
python -m unittest tests.unit.test_part_b_b4_contracts tests.unit.test_part_b_b4_baseline_prereg -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

The final review must replay all three new hashes, preserve the four frozen
B2/B3 bindings, show exactly 15 changed files and confirm that no file is
staged, committed or pushed.

## 3. Scientific and operational boundary

B4 replaces an informal baseline list with a finite, versioned registry and
explicit isolation rules. It does not prove that any algorithm is correctly
implemented, trained, reproducible, uncontaminated or superior. It provides
no baseline runtime and no B5 Planner adapter.

`ORACLE_EVALUATION_ONLY` is evaluator-only. The legacy
`NO_ACQUISITION` experimental arm is not Part B
`B0_PLANNING_AND_CONTRACTS`. Timeout and resource exhaustion remain unknown;
infeasibility remains separate from cost.

The hard non-authority tokens are `NO_BASELINE_EXECUTION`,
`NO_DATA_ACQUISITION`, `NO_CONNECTOR_DOWNLOAD` and
`NO_STOCHASTIC_SAMPLER`. LLM and `CERTIFIED_STOP` authority are unchanged.

## 4. Local verification record

```text
Baseline: main @ f47c118
B4 RED: 12 tests discovered; failures caused only by absent B4 artifacts
B4 targeted GREEN: 12/12 PASS
Full repository tests: 208/208 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS (tracked changes and all 13 untracked files)
Exact allowlist: 15/15 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```

Provisional local-review artifact identities:

```text
Baseline preregistration:
sha256:c51ab64588441855a7ff8413e32695e4b168d6d2a2089674f2cdcd691959906d

Baseline isolation policy:
sha256:8e95dd5ae4ae87140de815101b26592e97432dbf64541474b8bcdacb386b5c1f

B4 manifest:
sha256:2649b2a9067858d5fe2fa4c2f9d6386408384448910c97ee4eb89f1817893afc
```
