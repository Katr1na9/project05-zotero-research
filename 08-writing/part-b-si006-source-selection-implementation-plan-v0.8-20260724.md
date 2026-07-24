# PB-SI-006 source-selection implementation plan v0.8

## Scope

This local contract slice implements only deterministic source-selection
validation. It contains no connector runtime, network I/O, credentials,
download, quarantine, holdout release, Planner execution or statistical
analysis.

## Approved 15-file boundary

The slice is limited to three closed schemas, three non-executable YAML
examples, two boundary/contract documents, one local selector module, two
spec/authority updates and the two contract/runtime test files. Existing B1
and B7 artifacts are read-only hash bindings.

## Invariants

- Source identifiers are abstract and `NOT_AUTHORIZED`.
- Pointer and range semantics are explicit and preserved exactly.
- `modality`, `truth_status`, `epistemic_role` and
  `certification_authority` are separate.
- Open-world zero hits are `UNKNOWN_NOT_ABSENCE`; closed-world absence
  requires completeness evidence.
- Missing/unknown/malformed fields, non-conformant adapters, real endpoints
  and authority requests fail closed.
- `download_authority=false`, `retrieval_authority=false`,
  `connector_execution_authority=false`, `holdout release: DENY` and
  `stop_authority=NONE`.

## Narrow status

`PB-SI-006 = SELECTION_CONTRACT_ONLY_DOWNLOAD_DENY`. `PB-B7-SI-001`,
`PB-B7-SI-002` and `PB-B5-SI-001` remain OPEN/NOT ESTABLISHED. The slice
does not expand the Kernel ceiling or `CERTIFIED_STOP`.

## Validation

Acceptance requires 16/16 focused tests, full repository regression,
compileall, diff check, canonical hash replay and a porcelain review proving
that only the 15-file allowlist changed.
