# Predicate Projection Contract v0.8

**Status:** implemented under explicit user authorization on `2026-07-22`;
pending human review.

## Purpose

MinDiff compares finite witness variables, while distinguishing actions consume
catalog predicates. A projection therefore needs an auditable binding between
those two namespaces. Before this contract, callers could pass arbitrary
strings such as a test-only predicate that did not exist in the frozen action
catalog.

This contract keeps the choice caller-supplied but removes arbitrary predicate
authority. The caller supplies a mapping from each witness variable to one
frozen catalog `action_id`; the Kernel resolves the predicate only from that
action's declared `observation_model.world_dependencies`.

## Document shape

```yaml
schema_version: "0.8.0"
contract_id: stable-nonempty-id
catalog_id: exact-frozen-catalog-id
catalog_version: exact-frozen-catalog-version
bindings:
  witness_variable: catalog_action_id
```

The Twin instance is
`tests/fixtures/TWIN-COUNTEREXAMPLE-001/predicate_projections.yaml`.

## Validation rules

`PredicateProjectionContract.from_action_catalog(...)` must fail closed unless:

1. contract and action catalog both use `schema_version=0.8.0`;
2. `catalog_id` and `catalog_version` match exactly;
3. every binding variable belongs to the compiled witness-variable set;
4. every bound `action_id` exists exactly once in the catalog;
5. the action has an observation model with exactly one non-empty
   `world_dependencies` entry;
6. resolved predicate strings are unique across bound variables.

MinDiff accepts a `PredicateProjectionContract`, not a raw mapping. An explicit
empty contract is permitted for a recertification comparison that intentionally
reports all differences as unprojected. The contract is immutable after
construction.

## Authority boundary

The contract supplies names only. It does not establish observation truth,
action feasibility, completeness, certification authority, level-complete
coverage, a system state or STOP authority. Catalog binding cannot turn a
heuristic dependency into level certification, and it cannot authorize action
execution.

Changing a projection binding does not change Γ or the action catalog, but a
formal frozen run must version and review the projection document rather than
injecting a new string from test or runtime code.
