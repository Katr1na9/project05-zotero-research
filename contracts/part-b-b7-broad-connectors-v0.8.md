# Part B B7 broad-connector contract v0.8

Status: **B7 CONTRACT ONLY — DESCRIPTORS ARE NOT CONNECTORS**

## 1. Finite descriptor vocabulary

The policy registers four contract-only connector kinds:

```text
SNAPSHOT_TABULAR
SNAPSHOT_DOCUMENT
SNAPSHOT_GRAPH
SNAPSHOT_EVENT_STREAM
```

These values describe input shapes. They do not name products, services,
datasets or transport protocols. A descriptor may declare only schema and
provenance-shape capabilities. It contains no executable location, endpoint,
credential, command, query, payload or download instruction.

## 2. B1-B6 binding

The policy and manifest replay the approved canonical hashes for all frozen
B1-B6 contract artifacts used by B7. These references are read-only. B7 does
not rewrite federation, adapter, stochastic-observation, cost, baseline,
Planner-interface or closed-loop semantics.

A descriptor must use a B1 registered semantic family, version and source
schema, and it must bind the approved B1 adapter-conformance hash. Unknown
families, source schemas or conformance hashes fail closed.

## 3. Description is not authorization

The example source is an abstract contract fixture. Its descriptor states:

```text
source_status=CONTRACT_FIXTURE_ONLY
source_selected=false
execution_authority=false
```

Even a schema-valid descriptor grants no source access. A real source remains
behind the `PB-SI-006` PER-SOURCE SEPARATE AUTHORIZATION gate. The supplied
authorization example is deliberately `NOT_AUTHORIZED`.

## 4. Non-execution boundary

B7 supplies NO CONNECTOR RUNTIME and NO DOWNLOAD. It performs no retrieval,
network access, credential resolution, stochastic sampling, cost capture,
Planner execution or evaluation. `PB-B5-SI-001` remains OPEN.

The evidence level is `CONTRACT_CONSISTENCY_ONLY`: NO EXTERNAL VALIDITY, NO
PERFORMANCE CLAIM, no certificate, no system state and no `CERTIFIED_STOP`.
B8 and B9 remain closed.
