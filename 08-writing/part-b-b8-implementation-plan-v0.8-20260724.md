# Part B B8 holdout-analysis implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B8_HOLDOUT_ANALYSIS
Authority: Schema / policy / manifest / contracts / tests only
holdout_preregistration_contract_authority=true
statistical_analysis_contract_authority=true
analysis_envelope_contract_authority=true
holdout_data_access_authority=false
holdout_label_access_authority=false
holdout_result_access_authority=false
statistical_analysis_execution_authority=false
source_selection_authority=false
source_authorization_authority=false
connector_execution_authority=false
planner_execution_authority=false
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
stop_authority=NONE
B9: CLOSED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 18-file allowlist

1. `schemas/part-b-holdout-analysis-policy.schema.json`
2. `schemas/part-b-holdout-preregistration.schema.json`
3. `schemas/part-b-statistical-analysis-plan.schema.json`
4. `schemas/part-b-holdout-analysis-envelope.schema.json`
5. `schemas/part-b-b8-manifest.schema.json`
6. `configs/part-b-holdout-analysis-policy-v0.8.yaml`
7. `configs/part-b-holdout-preregistration-v0.8.yaml`
8. `configs/part-b-statistical-analysis-plan-example-v0.8.yaml`
9. `configs/part-b-holdout-analysis-envelope-example-v0.8.yaml`
10. `configs/part-b-b8-manifest-v0.8.yaml`
11. `contracts/part-b-b8-boundary-v0.8.md`
12. `contracts/part-b-b8-holdout-analysis-v0.8.md`
13. `contracts/part-b-b8-statistical-preregistration-v0.8.md`
14. `src/scope/part-b-b8-spec-issues.md`
15. `tests/unit/test_part_b_b8_contracts.py`
16. `tests/unit/test_part_b_b8_holdout_analysis.py`
17. `08-writing/part-b-b8-implementation-plan-v0.8-20260724.md`
18. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

Part A behavior, existing B0-B7 files and hashes, real data, labels, results,
runtime source, LLM, training, `09-experiments` and B9 are outside the change
set.

## 2. RED / GREEN contract

The RED-only gate created the two test files and recorded 26 test methods
failing solely because B8 artifacts were absent. GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b8_contracts tests.unit.test_part_b_b8_holdout_analysis -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

Final review must show exactly 18 changed files, no stage/commit/push and no
forbidden path.

## 3. Frozen B8 identities

```text
Holdout analysis policy:
sha256:542ed51380c7dc3e5ba1553d3c80b1a55e5ca5b008cb38d3df831fdee828b603

Holdout preregistration:
sha256:6af52503f38ff70fc640d8e1313ce8d7f02cf6f79bf23f5cc2a8b3bf5ba38342

Statistical analysis plan example:
sha256:57e24fd84df55adf44fbcae6c0dbf9248750c0901a6075ad845962c11b5e0627

B8 manifest:
sha256:4e6e4ec552d3a9c20c8c68e76766205cb1b2ecdf6dfbfe95866085e0b56c593b

No-data analysis envelope:
sha256:6126bd2145b1a05c91bf53aa81c599992a787d0dd6a43847f5a67f0bb07a07ed
```

The first three artifacts bind frozen B1-B7 identities. The manifest binds
those three B8 hashes. The envelope binds the manifest, producing an acyclic
hash chain.

## 4. Scientific and runtime boundary

B8 freezes an outcome-blind analysis plan and default-deny release contract.
The split fingerprint is an abstract fixture, not evidence of a real dataset.
No holdout label or result is read, and no statistic is computed.

`PB-SI-006` and `PB-B5-SI-001` remain OPEN. B8 supplies no source,
implementation admission, external validity, ranking, superiority claim,
certificate, system status or `CERTIFIED_STOP`. B9 remains closed.

## 5. Verification record

```text
Baseline: main @ 07f31b089374a7e7022438c833892b85a6506641
B8 RED: 26/26 failed because approved B8 artifacts were absent
B8 targeted GREEN: 26/26 PASS
Full repository tests: 299/299 PASS
python -m compileall -q src tests: PASS
git diff --check and exact allowlist audit: PASS
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```
