# Part B B5 planner-admission evidence contract v0.8

## 1. Identity evidence

The implementation identity binds five canonical descriptors:

1. the authorized source path and baseline commit;
2. the dependency lock;
3. the empty non-trained parameter manifest;
4. allowed and forbidden feature provenance;
5. the deterministic admission-record runtime conformance contract.

Each descriptor is hashed independently with canonical sort-key JSON. The
identity document then receives its own canonical document hash. These are
actual replayable hashes, not values that merely resemble SHA-256.

The identity names only
`part_b_b5_planner_admission_skeleton_v0.8`. It does not identify, wrap or
admit the legacy `project05_m3star_h3_dual`, whose status remains
`NOT_ADMITTED_UNVERIFIED`.

## 2. Required evidence slots

The evidence document contains exactly:

```text
dependency
parameter
feature_provenance
runtime_conformance
```

Every slot binds the corresponding identity descriptor hash, records
`CANONICAL_VALUE_HASH_REPLAY`, and fixes
`grants_execution_authority=false`. Missing or extra slots fail closed.

## 3. Deterministic decision order

The local evaluator applies this order:

1. legacy ID → `DENY_NOT_ADMITTED_UNVERIFIED`;
2. unknown ID → `DENY_UNKNOWN_IMPLEMENTATION`;
3. missing/wrong slot set → `DENY_EVIDENCE_INCOMPLETE`;
4. identity/slot hash mismatch → `DENY_EVIDENCE_HASH_MISMATCH`;
5. failed runtime conformance → `DENY_RUNTIME_CONFORMANCE_FAILED`;
6. other unverified slot → `DENY_EVIDENCE_INCOMPLETE`;
7. exact verified skeleton → `ADMITTED_CONFORMANCE_ONLY`.

Identical mappings produce the same `record_id`, reason code, decision and
record hash. The evaluator does not use wall-clock time, randomness, network
state, hidden labels, oracle state, holdout data or historical performance.

## 4. Admission is not execution

The admission record fixes:

```text
admission_scope=INTERFACE_CONFORMANCE_ONLY
planner_execution_authority=false
evaluation_execution_authority=false
holdout_release_authority=false
performance_claim_authority=false
scalarization_authority=false
stop_authority=NONE
```

It has no action ID, action payload, public-state input, cost, scalar score,
rank, metric, superiority claim, certificate, system status or
`CERTIFIED_STOP`. `PB-B5-SI-002`, `PB-B5-SI-003` and `PB-SI-006` therefore
remain open/default deny.
