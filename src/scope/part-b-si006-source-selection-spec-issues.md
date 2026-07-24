# PB-SI-006 source-selection issue register

Status: **SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY**.

The approved SI-006 sub-slice establishes a closed local record for
abstract, non-authorized source identifiers. It is limited to
pointer/modality/truth-status/epistemic-role/certification-authority,
open/closed-world semantics and B1 adapter-conformance bindings.

The following remain explicitly denied or open:

```text
source_authorization_authority=false
retrieval_authority=false
download_authority=false
connector_execution_authority=false
holdout release: DENY
stop_authority=NONE
PB-B7-SI-001: OPEN_DEFAULT_DENY
PB-B7-SI-002: OPEN_DEFAULT_DENY
PB-B5-SI-001: EXECUTION_NOT_ESTABLISHED
```

This closure does not authorize a real source, connector runtime, HTTP/API
access, credentials, quarantine, holdout release, Planner execution,
statistical execution, evidence admission, certification or
`CERTIFIED_STOP`. A future real source requires a separate per-source
authorization and a distinct review gate.
