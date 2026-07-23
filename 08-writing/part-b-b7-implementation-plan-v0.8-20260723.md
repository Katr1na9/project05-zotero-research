# Part B B7 broad-connectors implementation plan v0.8

Status: **LOCAL REVIEW**

```text
Authorized slice: B7_BROAD_CONNECTORS
Authority: Schema / policy / manifest / contracts / tests only
source_selection_authority=false
source_authorization_authority=false
connector_execution_authority=false
retrieval_authority=false
download_authority=false
credential_use_authority=false
planner_execution_authority=false
sampling_authority=false
evaluation_execution_authority=false
performance_claim_authority=false
stop_authority=NONE
B8-B9: CLOSED
Commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 18-file allowlist

1. `schemas/part-b-connector-contract-policy.schema.json`
2. `schemas/part-b-connector-descriptor.schema.json`
3. `schemas/part-b-source-authorization.schema.json`
4. `schemas/part-b-provenance-envelope.schema.json`
5. `schemas/part-b-b7-manifest.schema.json`
6. `configs/part-b-connector-contract-policy-v0.8.yaml`
7. `configs/part-b-connector-descriptor-example-v0.8.yaml`
8. `configs/part-b-source-authorization-example-v0.8.yaml`
9. `configs/part-b-provenance-envelope-example-v0.8.yaml`
10. `configs/part-b-b7-manifest-v0.8.yaml`
11. `contracts/part-b-b7-boundary-v0.8.md`
12. `contracts/part-b-b7-broad-connectors-v0.8.md`
13. `contracts/part-b-b7-provenance-and-source-authorization-v0.8.md`
14. `src/scope/part-b-b7-spec-issues.md`
15. `tests/unit/test_part_b_b7_contracts.py`
16. `tests/unit/test_part_b_b7_provenance.py`
17. `08-writing/part-b-b7-implementation-plan-v0.8-20260723.md`
18. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

`src/scope/part-b-b0-spec-issues.md`,
`src/scope/part-b-b5-spec-issues.md`, `src/connectors/`, B2 sampling, Planner
execution, real-source access, LLM, training and `09-experiments` are outside
the change set.

## 2. RED / GREEN contract

The RED-only gate created the two test files and recorded 24 test methods
failing solely because B7 artifacts were absent. GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b7_contracts tests.unit.test_part_b_b7_provenance -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

Final review must show exactly 18 changed files, no stage/commit/push and no
forbidden path.

## 3. Frozen B7 identities

```text
Connector contract policy:
sha256:43c6270078e03ac1764d16c41871a97a09df3a626c060ceebdecc06682b064c3

Connector descriptor example:
sha256:bc3f2934eb65868ba5db3ac8a0d8bbff7d766271eece9094c68183ce8919ac22

Source authorization example:
sha256:6576f01963ed07f291a19c8ddcf60dbc9ab5fcde5c7868671b43107db3ca15e0

Provenance envelope example:
sha256:f595cdee0a6c51f7a702e540bab71205f2b28a9701d991c214e28f1af8940ac9

B7 manifest:
sha256:28179580dc0e8c4dbc6f1a6cb1d5f0d4939a3ae7466c078e60f20fb16fffac49
```

All approved B1-B6 artifact identities are replayed exactly and remain
unmodified.

## 4. Scientific and runtime boundary

B7 is CONTRACT ONLY. It supplies a finite descriptor vocabulary, an explicit
default-deny per-source gate and an exact provenance envelope. It supplies NO
CONNECTOR RUNTIME and NO DOWNLOAD. The example source is an abstract fixture,
not a dataset or approved source.

`PB-SI-006` remains open for every real source. `PB-B5-SI-001` remains OPEN
and legacy M3* admission remains NOT ESTABLISHED. Passing B7 establishes only
`CONTRACT_CONSISTENCY_ONLY`: NO EXTERNAL VALIDITY, NO PERFORMANCE CLAIM and no
`CERTIFIED_STOP`. B8 and B9 remain closed.

## 5. Verification record

```text
Baseline: main @ e2802636a2da18460def8fd8158e9dd0f30e7647
B7 RED: 24/24 failed because approved B7 artifacts were absent
B7 targeted GREEN: 24/24 PASS
Full repository tests: 273/273 PASS
python -m compileall -q src tests: PASS
git diff --check and allowlist whitespace scan: PASS
Exact allowlist: 18/18 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```
