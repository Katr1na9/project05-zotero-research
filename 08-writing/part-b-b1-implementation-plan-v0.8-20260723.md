# Part B B1 federation Schemas implementation plan v0.8

Status: **B1 APPROVED / MERGED — SI-002 DECISION IMPLEMENTED LOCALLY,
PENDING HUMAN REVIEW**

```text
Authorized slice: B1_FEDERATION_SCHEMAS
Execution authority: NO
Federation runtime / real connectors / downloads: NOT AUTHORIZED
B2–B9: CLOSED
LLM / Planner / M3*: NOT AUTHORIZED
Part A CERTIFIED_STOP semantics: UNCHANGED
Push / PR: NOT AUTHORIZED
```

## 1. Purpose

B1 turns the PB-SI-002 normative map's federation entry into reviewable
contracts without opening a data path. It freezes a finite semantic-family
registry, pointer and epistemic-field rules, open/closed-world declarations,
adapter projection examples and fail-closed error codes.

It does not download data, select a real connector, implement an adapter or run
a federation. The two examples are deliberately abstract and structurally
different so conformance is not confused with one source shape.

## 2. Source and ownership hierarchy

1. The user's explicit B1 authorization on `2026-07-23`.
2. The normative v0.8 B0–B9 map approved under PB-SI-002.
3. Frozen Part A Kernel Claim IR and policy authority.
4. B0 contracts and hashes, which B1 may bind but not modify.
5. B1 contracts and examples, which have no execution authority.

The Kernel retains admission and certification authority. Candidate Compiler
restrictions remain unchanged. B1 does not connect an LLM or grant protected
field ownership to an adapter.

## 3. Exact deliverables

| Artifact | Purpose |
|---|---|
| `schemas/part-b-federation-contract.schema.json` | Finite semantic-family registry and open/closed-world declarations. |
| `schemas/part-b-adapter-conformance.schema.json` | Pointer-preserving Claim IR envelope and adapter invariants. |
| `schemas/part-b-b1-manifest.schema.json` | Contract-only authority and B2–B9 closure. |
| `configs/part-b-federation-contract-v0.8.yaml` | Two abstract registered-family examples. |
| `configs/part-b-adapter-conformance-v0.8.yaml` | Two structurally different non-executable projections. |
| `configs/part-b-b1-manifest-v0.8.yaml` | Hash bindings and explicit absence of runtime authority. |
| `contracts/part-b-b1-boundary-v0.8.md` | Human-readable B1 scope and world-semantics boundary. |
| `contracts/part-b-b1-adapter-conformance-v0.8.md` | Projection invariants and error contract. |
| `src/scope/part-b-b1-spec-issues.md` | Unresolved runtime/interface questions. |
| `tests/unit/test_part_b_b1_contracts.py` | Schema, hash and authority contract tests. |
| `tests/unit/test_part_b_b1_adapter_conformance.py` | Pointer, epistemic and world-boundary tests. |

The only modified existing file is the Kernel authority status record.

## 4. Contract decisions

### 4.1 Finite family registry

Every artifact enumerates its families; no wildcard family or predicate is
permitted. Registrations are versioned and unique. Unknown family, predicate
or schema version fails closed with an explicit error.

### 4.2 Pointer preservation

Input and projected source ID, record ID, content hash and range must match.
Range kind and half-open semantics remain explicit. B1 provides no resolver.

### 4.3 Epistemic separation

`modality`, `truth_status`, `epistemic_role` and
`certification_authority` remain separate. Adapter examples have no
certification authority and cannot produce admission, promotion, system state
or `CERTIFIED_STOP`.

### 4.4 World assumptions

Open-world zero-hit remains unknown. Closed-bounded absence requires an
explicit scope, time window, snapshot identity, completeness conditions and
absence semantics. Schema validity is not proof that those conditions hold.

## 5. RED → GREEN method

The two test modules were created before any B1 artifact. The initial targeted
run failed with two `FileNotFoundError` results for the missing federation and
adapter-conformance Schemas, establishing the planned RED state.

GREEN requires:

```text
python -m unittest tests.unit.test_part_b_b1_contracts tests.unit.test_part_b_b1_adapter_conformance -v
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
git diff --check
```

A final path audit must contain exactly the approved 13-file whitelist and no
behavioral changes under Part A, runtime, LLM, training, connector or
`09-experiments` paths.

## 6. Exit gate

Passing tests establishes internal Schema/example consistency only. It does
not establish connector support, source completeness, external validity,
performance, certification or cost superiority.

After validation, work stops for human review. B2–B9, LLM, real connectors,
downloads, stochastic execution, cost instrumentation, Planner/M3*, push and
PR remain closed unless separately authorized.

## 7. Implementation verification — 2026-07-23

Canonical artifact bindings:

```text
Federation contract:
sha256:6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d

Adapter-conformance contract:
sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a

B1 manifest:
sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e
```

Verification at the local review tip:

```text
Initial RED: 2 expected FileNotFoundError results for missing B1 Schemas
B1 contract tests: 17/17 PASS
Full repository regression: 155/155 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Exact 13-file allowlist audit: PASS
```

No B0 artifact or Part A implementation file changed. The pre-existing
untracked workspace directories were left untouched and are not B1
deliverables.

## 8. PB-B1-SI-002 ownership decision — 2026-07-23

The separately authorized `B1_SI002_RANGE_SEMANTICS_DECISION_ONLY` slice
closes PB-B1-SI-002 as `CLOSED — APPROVED`.

The normative decision is:

```text
range_semantics owner: CONFORMANCE_ENVELOPE_ONLY
Kernel Claim IR change: NONE
byte_or_row_range inference: FORBIDDEN
missing conformance contract: FAIL_CLOSED
Candidate Compiler pointer/range ownership: NONE
production adapter authority: NONE
```

The full rule and error codes are frozen in
`contracts/part-b-b1-range-semantics-v0.8.md`. The test contract verifies that
Kernel Claim IR still rejects `range_semantics`, the B1 envelope still requires
it, Candidate Compiler still forbids `pointer`, and all three approved B1
artifact hashes remain unchanged.

Closing field ownership does not implement or authorize storage of a
claim-to-envelope binding. Production adapter use still requires a separate
runtime authorization and resolution of the remaining open issues. B2–B9,
LLM, Part A changes and `CERTIFIED_STOP` expansion remain closed.

Final local verification for this decision-only slice:

```text
B1 targeted tests: 18/18 PASS
Full repository tests: 156/156 PASS
compileall: PASS
git diff --check: PASS
Exact seven-file allowlist audit: PASS
Frozen B1 hashes unchanged: PASS
```
