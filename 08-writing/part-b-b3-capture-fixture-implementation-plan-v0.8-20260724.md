# Part B B3 production-capture fixture implementation plan v0.8

## Scope

This local contract slice implements only a deterministic synthetic fixture
around the frozen B3 cost trace instrumenter. The approved result is a
wrapper containing the existing eight-dimensional trace and explicit
`FIXTURE_SYNTHETIC` / `NOT_PRODUCTION_MEASUREMENT` provenance.

## Allowlist

The slice is limited to the four fixture schemas, four YAML examples, the
boundary contract, the capture-fixture module, this plan, the B3 fixture
spec-issues file and the two contract/runtime tests.

## Invariants

- Existing B3 policy and trace schema are read-only bindings.
- Events are exact non-negative integers and event order cannot change hashes.
- Missing dimensions are `UNKNOWN_NOT_ZERO`; implicit zero is forbidden.
- Mixed currencies fail closed with no FX.
- No scalarization, performance/superiority claim, execution, holdout or STOP
  authority is emitted.
- `production_adapter_authority=false` and
  `measurement_class=NOT_PRODUCTION_MEASUREMENT` remain explicit.

## Validation

The acceptance gate is 15/15 targeted tests, followed by the repository
regression, compile check, diff check, configuration-hash replay and a
porcelain review. This local implementation does not authorize real
production measurement, B4 or any later queue item.

SI-006, B5 execution, holdout release and `CERTIFIED_STOP` remain closed or
denied. PB-B3-SI-001 remains open for a real adapter; PB-B3-SI-002,
PB-B3-SI-003 and PB-B3-SI-004 remain OPEN.
