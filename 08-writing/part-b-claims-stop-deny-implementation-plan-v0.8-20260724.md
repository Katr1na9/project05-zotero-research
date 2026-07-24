# Part B claims and CERTIFIED_STOP DENY implementation plan v0.8

## Scope

This 15-file local slice implements only a deterministic,
`CLAIMS_STOP_DENY_GATE_ONLY` classifier. The claim ceiling remainder is
`CONTRACT_CONSISTENCY_ONLY`; it grants no scalarization, superiority,
certificate or stop authority.

## Approved boundary

The allowlist contains three closed schemas, three canonically hashed YAML
documents, two boundary contracts, one pure in-memory classifier, two
scope/authority append-only updates, this plan and two unit-test files.

No Part A Kernel file or stop path and no `09-experiments` file is in scope.
Existing frozen artifacts and hashes are unchanged.

## Invariants

- `SCALARIZED_RANKING`, `PERFORMANCE_SUPERIORITY`,
  `CERTIFICATE_ISSUED` and `CERTIFIED_STOP` elevation requests are `DENY`.
- `CERTIFIED_STOP=NOT_AUTHORIZED`; `stop_authority=NONE`.
- No weights, results, certificate payload or system status is emitted.
- Stub, sampler, fixture and admission results are not stopping proof.
- Holdout and SI-006 remain `DENY`; SI-008 remains `NOT_OPENED`; B5
  execution remains `NOT_ESTABLISHED`.
- **PART A KERNEL GAMMA UNCHANGED** and Part A stop semantics are unchanged.
- Future enablement requires **SEPARATE HIGHEST-STRINGENCY AUTHORIZATION**.

## Validation and delivery boundary

Acceptance requires 16/16 focused tests, the full repository regression,
compileall, diff check, three canonical hash replays, an exact 15-file
porcelain review, and confirmation that Part A stop paths and
`09-experiments` have no diff.

Local review does not authorize commit, push, PR or any authority elevation.
