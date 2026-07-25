# Part B B5 Planner-interface implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B5_PLANNER_INTERFACE
Authority: Schema / policy / manifest / contracts / tests only
planner_execution_authority=false
evaluation_execution_authority=false
sampling_authority=false
production_capture_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
B6–B9: CLOSED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 19-file allowlist

1. `schemas/part-b-planner-public-state.schema.json`
2. `schemas/part-b-planner-decision.schema.json`
3. `schemas/part-b-planner-interface-policy.schema.json`
4. `schemas/part-b-bounded-evaluation.schema.json`
5. `schemas/part-b-b5-manifest.schema.json`
6. `configs/part-b-planner-public-state-example-v0.8.yaml`
7. `configs/part-b-planner-decision-example-v0.8.yaml`
8. `configs/part-b-planner-interface-policy-v0.8.yaml`
9. `configs/part-b-bounded-evaluation-v0.8.yaml`
10. `configs/part-b-b5-manifest-v0.8.yaml`
11. `contracts/part-b-b5-boundary-v0.8.md`
12. `contracts/part-b-b5-planner-interface-v0.8.md`
13. `contracts/part-b-b5-bounded-evaluation-v0.8.md`
14. `src/scope/part-b-b0-spec-issues.md`
15. `src/scope/part-b-b5-spec-issues.md`
16. `tests/unit/test_part_b_b5_contracts.py`
17. `tests/unit/test_part_b_b5_planner_interface.py`
18. `08-writing/part-b-b5-implementation-plan-v0.8-20260723.md`
19. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

No runtime source path is allowed. In particular, `src/planner/`, B2 sampling,
B3 production capture, baseline execution, connectors, LLM, training and
`09-experiments` are outside this allowlist.

## 2. RED / GREEN contract

RED recorded 19 test methods failing only because B5 artifacts were absent.
GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b5_contracts tests.unit.test_part_b_b5_planner_interface -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

The final review must replay all five new hashes, preserve every frozen B0–B4
hash, show exactly 19 changed files and confirm that no file is staged,
committed or pushed.

## 3. Scientific and operational boundary

B5 replaces an informal future Planner API with closed, versioned public-state
and action-ID-only contracts. It does not prove that any method is implemented
correctly, admitted, executable, reproducible or useful. The approved
implementation list is empty; legacy M3* remains unverified.

Finite evaluation bounds specify future failure semantics only. They do not
run an evaluation. B3 cost remains an unscalarized eight-dimensional vector.
TRAIN/TUNE/EVALUATION/HOLDOUT isolation remains in force.

The evidence level is `CONTRACT_CONSISTENCY_ONLY`, with
`NO_IMPLEMENTATION_VALIDATION`, `NO_PERFORMANCE_VALIDITY` and
`NO_SUPERIORITY_CLAIM`. Those three `NO_*` tokens are explicit denials, not
outputs of an experiment.

B6, B7, B8, B9, LLM, `09-experiments` and `CERTIFIED_STOP` expansion remain
unauthorized.

## 4. Verification record

```text
Baseline: main @ c19640a50de118cde39fe024d739ecc1083ef770
B5 RED: 19 test methods discovered; failures caused only by absent B5 artifacts
Machine-contract interim: 16/19 PASS; remaining three awaited documents
B5 targeted GREEN: 19/19 PASS
Full repository tests: 227/227 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Exact allowlist: 19/19 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```

Provisional local-review artifact identities:

```text
Planner public-state example:
sha256:42efd17661a1335f3c84c2c4efbea4de8107087d099dc987a902d20ded50deae

Planner decision example:
sha256:144cd24c0d6e3906ee31d25cdcc629f20901648d58204ee030f397daca23da6d

Planner interface policy:
sha256:b0c9f9971d13efcfeabb39f829592b9502831ba1b94e8de54e3941ba7dd1c343

Bounded evaluation:
sha256:9c1cae4643b95f7e2c87b6398cd096db1836ca3533cca67a1842dd037ec66858

B5 manifest:
sha256:bbe8bde7e6ab4695fc6a03233a8c45f5d205c77b3bed6f2816a89c8f7616c069
```
