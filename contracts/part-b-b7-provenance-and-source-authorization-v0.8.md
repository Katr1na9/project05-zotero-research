# Part B B7 provenance and source-authorization contract v0.8

Status: **B7 CONTRACT ONLY — DEFAULT DENY**

## 1. Source authorization is independent

Connector description and source authorization are separate artifacts.
The default decision is `DENY`; the only B7 example is
`NOT_AUTHORIZED` with reason
`B7-SOURCE-001_SEPARATE_AUTHORIZATION_REQUIRED`.

Missing, wrong or tampered policy/descriptor bindings fail closed. This
contract does not contain an approved-source example. A future real source
requires PER-SOURCE SEPARATE AUTHORIZATION and a separate human gate under
`PB-SI-006`.

## 2. Exact provenance

The provenance envelope requires:

- source identity;
- record identity;
- content SHA-256;
- explicit row-or-byte range;
- explicit half-open range semantics;
- the approved descriptor and B1 conformance bindings.

Numeric endpoints never imply units or endpoint convention. Pointer
provenance is `PRESERVE_EXACTLY`; the input provenance and projected pointer
must be identical. A connector descriptor cannot obtain pointer ownership.

`modality`, `truth_status`, `epistemic_role` and
`certification_authority` remain separate. The example has
`certification_authority.allowed=false`; neither a descriptor nor a
provenance-valid envelope may self-grant admission, world elimination,
certificate, system-status or `CERTIFIED_STOP` authority.

## 3. World and failure semantics

An open-world zero hit means `UNKNOWN_NOT_ABSENCE`. Closed-bounded absence
requires an independently approved completeness attestation; schema validity
is not a completeness proof.

Timeout, resource exhaustion and connector unavailability are
`UNKNOWN_NO_ZERO_HIT`. Partial results are `UNKNOWN_INCOMPLETE`; parse or
schema failures are rejected as unknown. None of these outcomes is UNSAT,
absence or a complete result.

## 4. Authority boundary

There is NO CONNECTOR RUNTIME, NO DOWNLOAD and no real-source observation.
`PB-B5-SI-001` remains OPEN. Passing this contract proves
`CONTRACT_CONSISTENCY_ONLY`, with NO EXTERNAL VALIDITY and NO PERFORMANCE
CLAIM. B8 and B9 remain closed.
