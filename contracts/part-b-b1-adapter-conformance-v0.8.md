# Part B B1 adapter-conformance contract v0.8

Status: **IMPLEMENTED — PENDING HUMAN REVIEW**

Authorized slice: `B1_FEDERATION_SCHEMAS`
Execution authority: **none**
B2–B9: **CLOSED**

## 1. Conformance object

`configs/part-b-adapter-conformance-v0.8.yaml` contains deterministic,
non-executable projection examples. Each example binds:

- one registered family and family version;
- one versioned abstract input schema;
- one adapter identity and version;
- an input shape and explicit field map;
- exact input provenance;
- an explicit namespace/entity binding; and
- the expected Claim IR envelope.

The examples are contract fixtures, not datasets. They contain no connector
address, credential, retrieval command, executable sampling instruction or
hidden truth.

## 2. Required invariants

A conforming future adapter must satisfy all of the following:

1. The family, predicate and schema version are registered.
2. Source ID, record ID, content hash and range survive projection exactly.
3. Row/byte range semantics remain explicit and half-open.
4. Entity IDs carry a namespace and a reviewed binding rule.
5. `modality`, `truth_status`, `epistemic_role` and
   `certification_authority` remain separate.
6. Certification authority is policy-gated outside the adapter and cannot be
   self-granted.
7. Open-world zero-hit remains unknown.
8. Closed-bounded absence requires a complete declaration and later proof of
   its conditions.
9. Unknown or conflicting inputs fail with an explicit B1 error code.

No example emits admission state, system state, a certificate or
`CERTIFIED_STOP`.

### 2.1 Range-semantics ownership

The approved `part-b-b1-range-semantics-v0.8.md` contract assigns
`range_semantics` exclusively to the conformance envelope. It is not a Kernel
Claim IR field. `byte_or_row_range` in Claim IR is an opaque source-relative
pair; neither an adapter nor a consumer may infer byte/row units or endpoint
convention from it.

The conformance envelope must carry `ROWS_HALF_OPEN` or `BYTES_HALF_OPEN` and
must remain bound to the exact versioned conformance contract. A missing,
unsupported or mismatched binding fails closed. This decision supplies no
production adapter authority.

## 3. Error contract

| Code | Meaning |
|---|---|
| `B1-FED-001_UNKNOWN_FAMILY` | The semantic family is outside the finite registry. |
| `B1-FED-002_UNKNOWN_PREDICATE` | The predicate is absent from the registered family allowlist. |
| `B1-FED-003_UNKNOWN_SCHEMA_VERSION` | The source or family version is not registered. |
| `B1-FED-004_POINTER_PROVENANCE_MISMATCH` | Projection changed or lost pointer provenance. |
| `B1-FED-005_NAMESPACE_COLLISION` | A namespace/entity binding collides or is ambiguous. |
| `B1-FED-006_AUTHORITY_SELF_GRANT` | An adapter attempted to grant certification authority. |
| `B1-FED-007_OPEN_WORLD_ZERO_HIT` | Open-world zero-hit was treated as absence. |
| `B1-FED-008_CLOSED_WORLD_INCOMPLETE` | A bounded absence claim lacks required completeness facts. |
| `B1-FED-009_UNAUTHORIZED_EXECUTION` | A contract-only artifact was invoked as runtime logic. |

## 4. Ownership boundary

The adapter may propose a structurally conforming envelope only. Kernel-owned
policy remains responsible for admission and any later certification decision.
The Candidate Compiler remains candidate-only under
`contracts/compiler-kernel-boundary-v0.8.md`; B1 does not give an LLM or any
compiler permission to set pointer/range, protected epistemic or authority
fields.

This contract contains no adapter implementation. B2–B9, LLM, real connectors,
downloads, stochastic execution, cost instrumentation, Planner/M3* and all
extensions to `CERTIFIED_STOP` remain unauthorized.
