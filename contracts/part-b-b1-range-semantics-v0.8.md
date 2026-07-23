# Part B B1 range-semantics ownership decision v0.8

Status: **CLOSED — APPROVED**

- Decision ID: `B1_SI002_RANGE_SEMANTICS_DECISION_ONLY`
- Issue: `PB-B1-SI-002`
- Approval date: `2026-07-23`
- Normative ownership: `CONFORMANCE_ENVELOPE_ONLY`
- Claim IR change: **none**
- Runtime or adapter authority: **none**

## 1. Normative decision

`range_semantics` belongs only to the versioned B1 adapter-conformance
envelope. It is not a Kernel Claim IR field and must not be added to the
Candidate Compiler request or response.

Kernel Claim IR continues to carry `pointer.byte_or_row_range` as an opaque,
source-relative pair. The pair alone does not identify whether its coordinates
are bytes or rows and does not define whether an endpoint is inclusive or
exclusive.

`INFERENCE_FORBIDDEN` is normative: no component may infer units or interval
convention from the numeric values, source name, record name, file extension,
predicate, modality, family or other heuristic.

## 2. Conformance-envelope requirements

The approved B1 conformance envelope requires:

- `source_id`;
- `record_id`;
- `content_hash`;
- `byte_or_row_range`; and
- `range_semantics`, currently one of `ROWS_HALF_OPEN` or
  `BYTES_HALF_OPEN`.

The envelope must be interpreted under the exact versioned conformance
contract that produced it. A future production adapter must retain an
auditable binding between the projected claim and that contract. B1 does not
implement such storage, resolution or runtime validation.

## 3. Fail-closed rules

The decision policy is `FAIL_CLOSED`.

| Code | Condition |
|---|---|
| `B1-RANGE-001_CONFORMANCE_CONTRACT_REQUIRED` | No matching versioned conformance contract is available. |
| `B1-RANGE-002_RANGE_SEMANTICS_MISSING` | The envelope has a range but no explicit semantics. |
| `B1-RANGE-003_RANGE_SEMANTICS_MISMATCH` | Input provenance and projected envelope disagree. |
| `B1-RANGE-004_INFERENCE_FORBIDDEN` | A component attempts to guess units or interval convention. |
| `B1-RANGE-005_UNSUPPORTED_RANGE_SEMANTICS` | The semantics value is outside the frozen contract. |

Any of these conditions blocks conformance. It cannot be converted into an
admission, certification, absence, world-elimination or STOP result.

## 4. Ownership boundary

The adapter-conformance layer owns representation and preservation of
`range_semantics`. Kernel Claim IR owns the durable claim and its existing
pointer identity fields. Kernel admission/certification policy retains all
epistemic authority.

The Candidate Compiler remains candidate-only. `pointer` is a protected field,
so the compiler cannot create, rewrite, infer or remove either the range pair
or its conformance-envelope semantics.

## 5. Frozen artifact identities

This decision does not change any B1 YAML artifact:

```text
Federation:
sha256:6dd5ddb6b9b7c48b0d93fa8fe0637403596435f766f328895265041467bea23d

Adapter conformance:
sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a

B1 manifest:
sha256:cecc07466d0aec0dbc7b4d95127651546ba7eb895f98a56d7e37c6f753850f6e
```

## 6. What closure does not authorize

Closing PB-B1-SI-002 grants no production adapter authority. It does not
authorize a connector, federation runtime, Claim IR migration, Part A
behavioral change, LLM, stochastic execution, cost instrumentation,
Planner/M3*, B2–B9 work or any extension of `CERTIFIED_STOP`.

Production use remains blocked unless a separately authorized runtime can
persist and validate the exact conformance-contract binding and satisfy all
other open B1 issues.
