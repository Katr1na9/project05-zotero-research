# Part B B7 specification issues

Status: **B7 LOCAL REVIEW — CONNECTOR/PROVENANCE CONTRACT ONLY**

```text
Authorized slice: B7_BROAD_CONNECTORS
connector_execution_authority=false
source_authorization_authority=false
download_authority=false
planner_execution_authority=false
evaluation_execution_authority=false
performance_claim_authority=false
stop_authority=NONE
B8-B9=CLOSED
```

## Imported gate: PB-SI-006 — real connector and dataset scope

**State:** `OPEN — BLOCKS CONNECTOR/DATA WORK`.

B7 defines the contract that a future source request must satisfy, but it
does not select or authorize a source. Every real source still requires
PER-SOURCE SEPARATE AUTHORIZATION. A descriptor, semantic-family match,
provenance-valid envelope or passing unit test is never an authorization.

The deny-only fixture records `NOT_AUTHORIZED`. This issue is not closed by
B7 and `src/scope/part-b-b0-spec-issues.md` remains unmodified.

## Imported gate: PB-B5-SI-001 — no Planner implementation admitted

**State:** `OPEN — BLOCKS IMPLEMENTATION ADMISSION AND EXECUTION`.

```text
Legacy M3* implementation admission: NOT ESTABLISHED
Legacy M3* execution authority: NONE
B7 disposition: UNCHANGED_OPEN_FROM_B5
```

B7 does not modify `src/scope/part-b-b5-spec-issues.md`.

## PB-B7-SI-001 — no connector runtime or credential model

**State:** `OPEN — BLOCKS CONNECTOR EXECUTION`.

No client, transport, credential resolver, retry loop, parser, adapter
runtime or `src/connectors/` module is selected or implemented. The connector
descriptor is an inert contract fixture.

## PB-B7-SI-002 — no real source is authorized

**State:** `OPEN — REQUIRES PER-SOURCE SEPARATE AUTHORIZATION`.

The source identifier in the example is explicitly abstract and
not authorized. B7 contains NO CONNECTOR RUNTIME and NO DOWNLOAD. It grants no
network, retrieval, credential or data-acquisition authority.

## PB-B7-SI-003 — provenance validity is not source completeness

**State:** `OPEN — BLOCKS CLOSED-WORLD USE`.

Pointer integrity and schema validity do not prove that a source snapshot is
complete. Open-world zero hit stays unknown. Closed-bounded absence requires
a separately approved completeness attestation.

## PB-B7-SI-004 — production conformance remains unvalidated

**State:** `OPEN — BLOCKS EXTERNAL VALIDITY`.

No production adapter or connector has emitted a B7 object, and no real
record has been checked. The evidence level remains
`CONTRACT_CONSISTENCY_ONLY`: NO EXTERNAL VALIDITY and NO PERFORMANCE CLAIM.

## PB-B7-SI-005 — holdout and final claims remain closed

**State:** `OPEN — DEFERRED TO B8/B9`.

B8 and B9 remain closed. B7 grants no HOLDOUT access, statistical analysis,
superiority claim, certificate, system status or `CERTIFIED_STOP`.
