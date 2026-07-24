# PB-SI-006 source-selection contract v0.8

## Contract identity

The contract is a closed, hash-addressed JSON/YAML pair. Its upstream
bindings are read-only:

```text
B1 adapter-conformance:
sha256:f0c3b5fe0a2fa8a1ac9d92a88058223fb12af21bf98f5fe5930d76b662ef7b6a

B7 connector policy:
sha256:43c6270078e03ac1764d16c41871a97a09df3a626c060ceebdecc06682b064c3

B7 manifest:
sha256:28179580dc0e8c4dbc6f1a6cb1d5f0d4939a3ae7466c078e60f20fb16fffac49
```

## Selection record

Every record requires an abstract source pointer, explicit modality,
truth-status, epistemic role, certification authority, world semantics and
adapter conformance. `certification_authority.allowed=false`; a selection
record cannot admit evidence, eliminate worlds, issue a certificate or
change system status.

The example identifier is deliberately abstract and
`source_authorization=NOT_AUTHORIZED`. No HTTP/API endpoint, credential,
dataset download, quarantine or holdout label is present. Selection is a
contract consistency result, not a data-access grant.

Open-world zero hits remain `UNKNOWN_NOT_ABSENCE`. Closed-bounded absence is
allowed only with an independently supplied completeness attestation.
Missing, unknown, malformed or contradictory fields fail closed with stable
`SI006-SELECTION-*` reason codes.

## Authority boundary

```text
source_selection_contract_authority=true
local_selection_evaluation_authority=true
source_authorization_authority=false
retrieval_authority=false
download_authority=false
credential_use_authority=false
connector_execution_authority=false
planner_execution_authority=false
holdout release: DENY
stop_authority=NONE
```

`PB-SI-006` state is
`SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY`. `PB-B7-SI-001` and
`PB-B7-SI-002` remain `OPEN_DEFAULT_DENY`. `PB-B5-SI-001` remains
`EXECUTION_NOT_ESTABLISHED`. This contract grants no real-source
authorization and no `CERTIFIED_STOP` authority.
