# Project05 executor readiness audit v0.4 — two bounded real-action capabilities

Status: **two target-specific capability pilots verified; formal operational-cost measurement and M3\* re-evaluation remain blocked**

Supersedes: `executor-readiness-audit-v0.3-code-provenance.md` as the current readiness summary only. Earlier audits and pilot artifacts remain immutable historical records.

Scope: canonical real-only C01–C09 cohort. Canonical C10+ and source C13+ remain sealed.

## Readiness summary

- Registry-wide status: seven action-type adapters remain draft, zero are globally implemented, and zero are eligible for formal operational-cost measurement.
- Target-specific executable evidence: two capability pilots across two action types.
- Formal measurement evidence: zero schedule-compliant records.
- Formal coverage: zero of 50 actions; the 150 controlled primary attempts have not been authorized or executed.
- Paper/patent and M3\* performance gates: closed.

The two pilots establish that real resource vectors can be collected without legacy scalar cost or planner-oracle fields. They do not establish a global adapter implementation, statistical sufficiency, a scalar cost transformation, or a method ranking.

## Capability 1 retained from v0.3

- Canonical action: `C02-AA-002`.
- Source alias: `C05-darpa-e3-cadets/C05-AA-002`.
- Action family: bounded CDM18 file-target `query_host_subgraph` for `/tmp/vUgefal` in R02.
- Verified result: 10.3559157 wall seconds, 9.984375 CPU seconds, 244,984,898.89484233 RSS byte-seconds, 901,652,996 bytes scanned, and 807,514 source-line primitive operations.
- Observation: 3,002 event records and 1,391 node records derived from five exact target events and four seed UUIDs.
- Current run record: `pilots/c02-aa-002-r02-file-one-hop-v0.3/pilot-run.json`.

This remains a file-target-only capability and does not make the registry-wide `query_host_subgraph` adapter implemented or eligible.

## Capability 2 added in v0.4

- Canonical action: `C02-AA-003`.
- Source alias: `C05-darpa-e3-cadets/C05-AA-003`.
- Action family: bounded CDM18 case-target `recover_network_summary` for `R02 external endpoints`.
- Executor: `09-experiments/scripts/recover_network_summary_adapter.py`.
- Adapter SHA-256: `a1b76bfa65a1aa41cbcc47c89f58b1859f336796daa2cee34b0ea777656aa275`.
- Run record: `pilots/c02-aa-003-r02-observed-remote-endpoints-v0.1/pilot-run.json`.
- Run-record SHA-256: `277d0a4c0f3f600badca97794a4c71f8c7ca70256aceb1871a5bad35a70f7f5e`.

The executor accepts only the allow-listed case/action/type/target tuple. It rejects `recoverable_claim_ids`, `oracle_effects`, and `hidden_claim_ids`, and it does not consume legacy scalar cost, expected effects, or ground truth.

### Measured execution result

The run completed from `2026-07-18T07:04:10.582957Z` through `2026-07-18T07:04:10.749668Z`.

- Compute: 0.17153010000038194 wall seconds; 0.171875 CPU seconds; 4,061,438.209631577 RSS byte-seconds.
- Data access: 14,101,676 bytes and 33,292 source-line primitive operations. Both equal exactly two reads of the immutable 7,050,838-byte, 16,646-line node source: one integrity scan and one extraction scan.
- Other measured resources: zero analyst seconds, direct currency, authorization wait, downtime, and evidence perturbation; shared setup remains unallocated.
- Input: 1,378 usable `NetFlowObject` records and zero unusable records.
- Output: 143 deterministic remote-endpoint tuples keyed by exact `(remoteAddress, remotePort, ipProtocol)`.
- Missingness: all 1,378 protocol values are absent and remain `null`; 234 local ports are negative/unknown and are not imputed.

The derived endpoint artifact has SHA-256 `947716a20c063a4719a6acb9eda2966b0777c4758760984381e083b26a6a207a`. Independent recomputation matched the adapter, source-input, and derived-output hashes; the 143 output rows aggregate back to exactly 1,378 source objects and 234 unknown local-port occurrences. Ordered node-shard and merged-node fixtures conserve bytes, records, primitive counts, output counts, and output SHA-256.

### Construct status: partial, not successful external classification

R02 has no frozen local-network boundary, and its observed local addresses include publicly routable `128.55.12.x` space. Therefore RFC1918 membership cannot validly distinguish internal from external endpoints. The executor reports all observed remote endpoint tuples and records:

`requested_scope_status = partial_external_classification_unresolved`

`external_endpoint_count = null`

This is an intentional construct safeguard. The pilot establishes executable network-summary acquisition and its resource vector, but it does not establish that `C02-AA-003` successfully returned the requested external-only set. Resource cost and action outcome remain separate.

The other eight real-only `recover_network_summary` actions use process, endpoint, case, or time-window targets. This one case-target pilot does not implement those heterogeneous targets and cannot change the registry entry from `unimplemented`.

## Capability measurement conversion

The converter was extended under tests to preserve the prior subgraph returned-evidence count (4,393) and to map the network-summary observation to 143 returned endpoint tuples. Converter SHA-256: `3fcc3fe07d4c212d6bbceb549d4e5b856b68210ba273ee2c4c95bd40b45227af`.

The new converted record is `capability-pilot--C02--C02-AA-003--schedule-010`. Schedule index 10 is referenced only to validate case/action identity. The record declares `unscheduled_capability_pilot`, `initial_state_reset=false`, and executor `project05-recover-network-summary-r02-case-pilot-v0.1`.

Validation results:

- schema valid: true;
- provenance valid: true;
- resource trace complete: true;
- schedule compliant: false;
- execution authorized: false;
- capability-pilot records in this batch: one;
- formal schedule records in this batch: zero;
- measurement batch ready: false;
- formal measured-cost profile ready: false.

The source measurement SHA-256 is `7c5bb6c15428a4a908c3d492bed3016982937baf6af45d0e51245f24d5030b96`; normalized batch SHA-256 is `6e7b192abe904892398f512ebff8dced68f53b4f31ad1481705b3ee02e0ed9af`; validation report SHA-256 is `9556cf2e78f87e2b549a61c0491eb6d4a4206dd98ff134a94464fba764fdb440`; evaluation manifest SHA-256 is `95fb9ceb9a655bc424b6f451947276d5463e5575d28326de1fd120d59c0a1865`.

## Formal gates remain closed

1. The formal 150-attempt controlled schedule has not been authorized or executed; capability deviations contribute no formal coverage.
2. Initial-state reset, randomization compliance, retry policy, actor/authority mapping, and shared-overhead allocation remain unfrozen for formal execution.
3. Five action types have no real capability pilot, and the two piloted types cover only one target family each.
4. `recover_network_summary` still lacks a frozen, source-independent external/internal boundary for R02 and target-specific semantics for the other real cases.
5. Statistical sufficiency has not been established.
6. No scalar transformation model has been calibrated, validated, or frozen.
7. M3\* has not been rerun under a valid formal measured-cost profile, so no comparison with XGBoost, M2, or M3b is authorized.

No paper result, patent assertion, scalar-cost claim, or cross-method performance claim is authorized by these capability pilots.
