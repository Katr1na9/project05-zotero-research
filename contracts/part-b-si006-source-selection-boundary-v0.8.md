# PB-SI-006 source-selection boundary v0.8

Status: **SI006_SOURCE_SELECTION_CONTRACT_ONLY**.

This slice defines a deterministic, local source-selection record. It does
not select a real dataset, endpoint, credential, connector or holdout. The
only positive outcome is `SELECTED_CONTRACT_ONLY` for an abstract,
`NOT_AUTHORIZED` fixture identifier.

The record keeps the following dimensions separate and explicit:

- `source_pointer`, including source/record identity, content hash, range
  unit and half-open range semantics;
- `modality`, `truth_status`, `epistemic_role` and
  `certification_authority`;
- explicit `OPEN_WORLD` or `CLOSED_BOUNDED` semantics;
- B1 adapter-conformance contract identity and hash.

Pointer/range meaning is not inferred from numeric endpoints. Pointer
ownership remains with the caller and no source-selection result rewrites
modality or provenance.

The source-selection record is not source authorization. In particular,
`download_authority=false`, `retrieval_authority=false`,
`connector_execution_authority=false` and
`source_authorization_authority=false`. `holdout release: DENY` and
`stop_authority=NONE` are invariant. No network, credential, HTTP/API,
download, quarantine, Planner, certificate or `CERTIFIED_STOP` path exists
in this slice.

`PB-SI-006` is narrowed only to
`SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY`. `PB-B7-SI-001` and
`PB-B7-SI-002` remain `OPEN_DEFAULT_DENY`; real-source authorization,
connector runtime and data acquisition require separate future gates.
`PB-B5-SI-001` remains `EXECUTION_NOT_ESTABLISHED`.
