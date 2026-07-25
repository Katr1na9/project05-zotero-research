# Part B B7 boundary contract v0.8

Status: **B7 CONTRACT ONLY — NO CONNECTOR RUNTIME**

```text
Authorized slice: B7_BROAD_CONNECTORS
connector_contract_authority=true
provenance_contract_authority=true
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
B8-B9=CLOSED
```

## 1. Authorized result

B7 freezes closed JSON Schemas and non-executing examples for connector
descriptors, per-source authorization decisions and provenance envelopes. It
also freezes the policy that relates those objects to the approved B1-B6
contracts. Passing the B7 checks establishes `CONTRACT_CONSISTENCY_ONLY`.

This is a shape and provenance contract. It is not a connector
implementation, source client, credential resolver, downloader, adapter
runtime or dataset registration.

## 2. Per-source gate

`PB-SI-006` remains `OPEN — BLOCKS CONNECTOR/DATA WORK`. Every real source
requires a separate authorization that identifies the source, approved
operations and exact descriptor/policy hashes. The B7 example has decision
`NOT_AUTHORIZED`, empty datasets and empty operations.

There is no implicit authorization by semantic family, connector kind,
descriptor validity, provenance validity or test success. The required rule
is **PER-SOURCE SEPARATE AUTHORIZATION**.

## 3. Runtime exclusions

This slice means:

```text
NO CONNECTOR RUNTIME
NO DOWNLOAD
NO NETWORK ACCESS
NO CREDENTIAL USE
NO REAL SOURCE
NO DATA ACQUISITION
NO PLANNER OR EVALUATION EXECUTION
```

No `src/connectors/`, `09-experiments`, LLM, training, sampling or production
capture path is part of B7.

## 4. Preserved gates

`PB-B5-SI-001` remains OPEN. Planner implementation admission remains
`NOT ESTABLISHED`, and legacy M3* execution authority remains NONE.

B7 does not issue a certificate, write a system state or emit
`CERTIFIED_STOP`. It creates NO EXTERNAL VALIDITY and NO PERFORMANCE CLAIM.
B8 and B9 remain closed.
