# Part B B1 federation boundary contract v0.8

Status: **IMPLEMENTED — PENDING HUMAN REVIEW**

- Contract ID: `part-b-b1-boundary-v0.8`
- Authorized slice: `B1_FEDERATION_SCHEMAS`
- Authorization date: `2026-07-23`
- Execution authority: **none**
- Runtime authority: **none**
- Next default action: **stop after B1 review**

## 1. Normative boundary

B1 freezes only the representation of a finite semantic-family federation and
the conformance obligations of a future adapter. It does not implement an
adapter, connector, federation runtime, retrieval path, source client or data
loader. The two examples are abstract contract fixtures; neither names nor
selects a real source.

The machine-readable boundary is
`configs/part-b-b1-manifest-v0.8.yaml`. Its authorized slice is exactly
`B1_FEDERATION_SCHEMAS`, its execution authority is false, and B2–B9 remain
closed.

LLM components, training, prompts, models and inference are outside B1.
Planner/M3*, stochastic observation execution, cost instrumentation,
experiments and broad connectors are also outside B1.

## 2. Finite federation domain

Every B1 artifact enumerates a finite set of registered semantic families.
Each registration has a unique `family_id`, a semantic version, one or more
versioned source-schema identifiers, a finite predicate allowlist, and an
explicit world-semantics declaration.

The example registry contains two structurally different abstract families:
an execution-event row family and a reported-fragment family. Their presence
proves only that one contract can represent distinct shapes. It is not evidence
of connector support, real-data coverage or external validity. Adding a family,
source schema or predicate requires a new reviewed artifact and hash.

Unknown family, predicate or schema version is an explicit fail-closed error.
An implementation may not silently discard, coerce or reinterpret it.

## 3. Pointer and provenance contract

A conforming projection requires:

1. stable source identity;
2. stable record identity;
3. SHA-256 content identity;
4. a bounded row or byte range; and
5. explicit half-open range semantics.

The projected pointer must reproduce the input provenance exactly. An adapter
may not invent, erase or silently rewrite a source ID, record ID, content hash
or range. B1 defines this comparison contract but supplies no pointer resolver
or runtime validator.

The ownership question was closed by the approved
`part-b-b1-range-semantics-v0.8.md` decision. The existing Kernel Claim IR
continues to store `byte_or_row_range` without a `range_semantics` field.
`range_semantics` belongs only to the versioned conformance envelope.

The Claim IR range pair is opaque: units and endpoint convention must never be
inferred from its values or surrounding claim fields. Without a matching
conformance contract, a future adapter must fail closed under
`B1-RANGE-001_CONFORMANCE_CONTRACT_REQUIRED`. Closing the ownership issue
provides no production adapter, resolver, admission or certification
authority.

## 4. Epistemic separation and authority

`modality`, `truth_status`, `epistemic_role` and
`certification_authority` are four separate fields with separate meanings.
An adapter projection cannot merge them into a single confidence or epistemic
state.

The examples preserve their declared modality and role while leaving truth
unassessed. Their `certification_authority.allowed` value is always false.
Only the already-governed Kernel policy outside the adapter may later evaluate
admission or certification authority. Adapter conformance cannot admit,
promote, issue a level certificate or declare `CERTIFIED_STOP`.

## 5. Open-world and closed-bounded semantics

For `OPEN_WORLD`, zero hits mean `UNKNOWN_NOT_ABSENCE`. No absence claim or
world elimination follows.

For `CLOSED_BOUNDED`, zero hits may be interpreted only under an explicit
completeness contract containing all of:

- scope;
- half-open time window;
- snapshot identity;
- completeness conditions; and
- explicit absence semantics.

The declaration is not self-proving. B1 validates its shape only; no code in
this slice verifies that a snapshot is actually complete.

## 6. Identity binding

Cross-family entity IDs require an explicit namespace, source identifier,
canonical identifier and binding rule. A namespace collision fails closed.
B1 provides examples and validation rules, not entity-resolution logic.

## 7. Authority statement

A valid Schema, example or canonical hash establishes artifact identity and
internal contract consistency only. It establishes no runtime correctness,
source coverage, external validity, completeness fact, performance or
certification result. It cannot extend Part A `CERTIFIED_STOP`.

Completion of B1 stops at human review. B2–B9, LLM, real connectors, downloads,
random execution, cost collection, Planner/M3* and push/PR require separate
explicit authorization.
