# Part B B6 closed-loop evaluation implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B6_CLOSED_LOOP_EVAL
Authority: Schema / policy / manifest / contracts / tests only
planner_implementation_admission_authority=false
planner_execution_authority=false
evaluation_execution_authority=false
sampling_authority=false
production_capture_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
B7–B9: CLOSED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 18-file allowlist

1. `schemas/part-b-closed-loop-evaluation-policy.schema.json`
2. `schemas/part-b-closed-loop-episode.schema.json`
3. `schemas/part-b-closed-loop-feedback-envelope.schema.json`
4. `schemas/part-b-closed-loop-preregistration.schema.json`
5. `schemas/part-b-b6-manifest.schema.json`
6. `configs/part-b-closed-loop-evaluation-policy-v0.8.yaml`
7. `configs/part-b-closed-loop-episode-example-v0.8.yaml`
8. `configs/part-b-closed-loop-feedback-example-v0.8.yaml`
9. `configs/part-b-closed-loop-preregistration-v0.8.yaml`
10. `configs/part-b-b6-manifest-v0.8.yaml`
11. `contracts/part-b-b6-boundary-v0.8.md`
12. `contracts/part-b-b6-closed-loop-evaluation-v0.8.md`
13. `contracts/part-b-b6-preregistration-envelope-v0.8.md`
14. `src/scope/part-b-b6-spec-issues.md`
15. `tests/unit/test_part_b_b6_contracts.py`
16. `tests/unit/test_part_b_b6_closed_loop_eval.py`
17. `08-writing/part-b-b6-implementation-plan-v0.8-20260723.md`
18. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

No runtime source path is allowed. In particular,
`src/scope/part-b-b5-spec-issues.md`, `src/planner/`, B2 sampling, B3
production capture, baseline execution, connectors, LLM, training and
`09-experiments` are outside the change set.

## 2. RED / GREEN contract

The RED-only gate created the two test files and recorded 22 test methods
failing because all B6 artifacts were absent. After the five Schemas and five
YAML artifacts were added, the interim state was 20/22 PASS; the remaining
two failures were the intentionally absent documentation and issue register.

GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b6_contracts tests.unit.test_part_b_b6_closed_loop_eval -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

Final review must show exactly 18 changed files, no stage/commit/push, and no
forbidden path.

## 3. Frozen identities

```text
Closed-loop evaluation policy:
sha256:f9e225fd0bd90046424183620dc9d20a6e91e9c2f4f24893f62dd2b5f8f9f2b1

Closed-loop episode example:
sha256:25216c85648ae7a54b5a8a909773b0714147b64c2fbd4d8ebb6ac98b931f92a7

Feedback envelope example:
sha256:01077b5bf717dcbc22b1d65a6e1d0653ce753504dd2ee713fd83b8b064d15a36

Closed-loop preregistration:
sha256:1c3177a68178d9f940978979ae2ff4c59646bf14e693e78f6592ab5f70f91aca

B6 manifest:
sha256:eca84c24d8e75c3daedbd0e786921c8b00827e8f4405be92a7517cba0e94936d
```

All B2–B5 artifact identities are replayed exactly and remain unmodified.

## 4. Scientific boundary

B6 specifies a finite `public-state → action-ID-or-null → feedback-reference`
protocol and a preregistration freeze. It does not supply the functions that
create any of those objects. The feedback example is explicitly not executed
and gives no Claim IR, evidence-admission, modality or certification
authority.

`PB-B5-SI-001` remains
`OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`, with
`UNCHANGED_OPEN_FROM_B5`. B6 cannot validate legacy M3*, run a method, rank a
method, scalarize cost or support a performance claim.

The B6 evidence level is `CONTRACT_CONSISTENCY_ONLY`. B7–B9 and every
extension of `CERTIFIED_STOP` remain unauthorized.

## 5. Verification record

```text
Baseline: main @ 02348b809d4b7e7d883ddd02be9ad80deb0204ae
B6 RED: 22/22 failed because approved B6 artifacts were absent
Schema-only checkpoint: Draft 2020-12 validation PASS
Machine-contract interim: 20/22 PASS; remaining two awaited documents
B6 targeted GREEN: 22/22 PASS
Full repository tests: 249/249 PASS
python -m compileall -q src tests: PASS
git diff --check and whitespace scan: PASS
Exact allowlist: 18/18 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```
