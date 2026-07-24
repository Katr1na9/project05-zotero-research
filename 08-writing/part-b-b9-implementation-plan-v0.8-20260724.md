# Part B B9 freeze-and-claims implementation plan v0.8

Status: **LOCAL CONTRACT REVIEW**

```text
Authorized slice: B9_FREEZE_AND_CLAIMS
Artifact status: B9_CONTRACT_ONLY
Evidence ceiling: CONTRACT_CONSISTENCY_ONLY
freeze_contract_authority=true
audit_contract_authority=true
claim_boundary_contract_authority=true
execution_authority=false
holdout_release_authority=false
performance_claim_authority=false
certificate_authority=false
stop_authority=NONE
commit / push / PR: NOT AUTHORIZED
```

## 1. Exact 18-file allowlist

1. `schemas/part-b-freeze-and-claims-policy.schema.json`
2. `schemas/part-b-freeze-record.schema.json`
3. `schemas/part-b-claim-boundary.schema.json`
4. `schemas/part-b-freeze-audit.schema.json`
5. `schemas/part-b-b9-manifest.schema.json`
6. `configs/part-b-freeze-and-claims-policy-v0.8.yaml`
7. `configs/part-b-freeze-record-example-v0.8.yaml`
8. `configs/part-b-claim-boundary-example-v0.8.yaml`
9. `configs/part-b-freeze-audit-example-v0.8.yaml`
10. `configs/part-b-b9-manifest-v0.8.yaml`
11. `contracts/part-b-b9-boundary-v0.8.md`
12. `contracts/part-b-b9-freeze-and-claims-v0.8.md`
13. `contracts/part-b-b9-audit-and-claim-boundary-v0.8.md`
14. `src/scope/part-b-b9-spec-issues.md`
15. `tests/unit/test_part_b_b9_contracts.py`
16. `tests/unit/test_part_b_b9_freeze_and_claims.py`
17. `08-writing/part-b-b9-implementation-plan-v0.8-20260724.md`
18. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

B9 must not modify B0–B8 artifacts, hashes, authority decisions or gate
states. `src/` runtime behavior, LLM, training, `09-experiments`, real data
and execution code are forbidden.

## 2. Freeze basis

The freeze record binds the ordered 39-item inventory at:

```text
Baseline commit:
be33ef8906f5c6ca0891d21da11573b9510e941e

Manifest-union identities:
38

Additional B8 holdout envelope:
1
```

All paths and hashes replay from the baseline. B9 is excluded from its own
upstream list.

## 3. Directed B9 identities

```text
Freeze record:
sha256:92182dbe5b58163b35f113831847a6349dba1c1f19cfd3a42a352b52a6a968ab

Freeze/claims policy:
sha256:bd04bac10be6e9b049a700eccf8d7f1e771cec89dbf9f6fce412145f40609999

Claim boundary:
sha256:0ee41ab84b171d7b4789a3b76d7971e15ed3e8f5d6501889b4d486b7e70722a8

B9 manifest:
sha256:6cff911409da42f66b3fef1e25cf555f72f6620f5fd713bdf3bc16bcf50c563e

Freeze audit:
sha256:102c6d1871d89fcbf8a3902f3b26a5e1ac081b578dc220481f6f8b4792e8b8d0
```

The dependency order is upstream → record → policy → claim → manifest →
audit. There is no circular or placeholder binding.

## 4. Claim and gate boundary

Only the four machine-enumerated contract-consistency claims may be allowed.
All empirical, external-validity, performance, optimality, holdout,
statistical, implementation, certificate and STOP claims are denied.

`PB-SI-006`, `PB-B5-SI-001` and `PB-B8-SI-004` remain OPEN. Holdout release
is `OPEN / default DENY`; statistical execution is `OPEN / NOT AUTHORIZED`;
implementation admission is `OPEN / NOT ESTABLISHED`.

## 5. Verification gate

```text
python -m unittest tests.unit.test_part_b_b9_contracts tests.unit.test_part_b_b9_freeze_and_claims -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

GREEN requires 28/28 targeted tests, complete repository regression, exact
canonical hash replay, exactly 18 changed files and no staged/committed/pushed
delivery action.

