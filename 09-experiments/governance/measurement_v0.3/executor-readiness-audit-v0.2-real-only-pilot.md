# Project05 executor readiness audit v0.2 — real-only C01–C09 and C02 pilot

Status: **one real, read-only capability pilot validated; formal operational-cost measurement remains blocked**

Scope: canonical C01–C09 real-only cohort. Canonical C10+ is unassigned and sealed; source C13+ remains sealed.

This is experiment-governance evidence, not paper or patent prose.

## What changed from v0.1

The historical v0.1 audit remains unchanged. The governed cohort now excludes the three no-original-data toy cases and contains nine canonical real cases, 50 actions, and seven observed action types. The seeded coverage template therefore contains 150 primary attempts (57 calibration, 93 development), not 216.

One narrow executor has been implemented and exercised as capability evidence only:

- canonical action: `C02-AA-002`;
- preserved source alias: `C05-darpa-e3-cadets/C05-AA-002`;
- action type/target: `query_host_subgraph`, exact file target `/tmp/vUgefal`;
- source inputs: local DARPA E3 CADETS R02 `events.jsonl` and `nodes.jsonl`;
- implementation: `09-experiments/scripts/query_host_subgraph_adapter.py`;
- capability run: `09-experiments/governance/measurement_v0.3/pilots/c02-aa-002-r02-file-one-hop-v0.2/pilot-run.json`.

The pilot consumes an allow-listed invocation only. It rejects `recoverable_claim_ids`, `oracle_effects`, and `hidden_claim_ids`; it does not read legacy scalar cost, expected effects, or ground truth.

## Verified real pilot result

The v0.2 run completed from `2026-07-18T06:36:07.155968Z` to `2026-07-18T06:36:16.037496Z` and recorded:

- 8.8823384 wall seconds; 8.75 CPU seconds; 210,473,890.34105843 RSS byte-seconds;
- 901,652,996 bytes scanned and 807,514 raw JSONL source-line reads;
- primitive-operation boundary: one source line read, including immutable-input integrity scans;
- five exact target events, four seed node UUIDs, 3,002 one-hop event records, and 1,391 resolved node records;
- no analyst time, direct currency, authorization wait, downtime, or evidence perturbation.

The adapter independently recomputed the R02 input SHA-256 values and obtained the frozen cohort values:

- events: `8581dc84eccaaa03df957793fc47ed42159ac58d3e17ab714064c0d39bc2b32d`;
- nodes: `f7c874aaac39260e4c67515f9041876d72b7a54fb0a30e1f9eab11f036d47301`.

The derived artifacts are hash-locked in the pilot run record:

- `subgraph-events.jsonl`: `e57e7fc8a50cf8ee137d056f2425b61dc6bdbb22bd2ddda5cc744834220772d1`;
- `subgraph-nodes.jsonl`: `b05bde9903a053c88b0ae1eb52b8dcc38f5ea79e74c4b7c27401b1b155fe4582`.

## Measurement-schema result and its limit

`build_capability_pilot_measurement_v03.py` converted the run to a v0.3 measurement-shaped record tied to the matching schedule identity (`C02/C02-AA-002`, index 14) only for identity validation. It permanently declares:

- `randomization_deviation.deviation_type = unscheduled_capability_pilot`;
- `initial_state_reset = false`;
- zero formal schedule records and one capability-pilot record.

The resulting batch passes schema validation, source replay, and unit-bearing resource-trace completeness. It deliberately fails schedule compliance, coverage, and execution authorization. Its manifest is therefore `capability_pilot_only_not_formal_schedule_measurement`, never a formal schedule measurement.

## Why the adapter is not marked implemented

This pilot is not a completed `query_host_subgraph` action-type adapter. The real-only ontology contains file, process, host, case, module, and thread targets under that action type; this code supports only one CDM18 file target family. The seven-entry registry stays draft with zero implemented and zero eligible adapters.

The required split/merge condition is now met for the implemented file-target family’s **ordered event-source shard** boundary. The adapter accepts a list of event shards as one logical invocation: it performs three scans over the combined event content (integrity, exact-target seed, one-hop expansion) and only two scans of the shared node source (integrity, resolution). The executable regression test verifies that a merged event file and its two ordered shards conserve bytes scanned, records scanned, primitive operations, observation counts, and both derived-artifact SHA-256 values. This prevents node-source shared overhead from being charged repeatedly merely because storage has been partitioned.

That result does not establish invariance across different target families, independent planner actions, retries, or any later shared setup with nonzero overhead. Those boundaries still need an explicit allocation rule and their own tests.

## Remaining gates

1. Freeze target-family contracts, controlled initial state/reset, and termination/error behavior for every action type.
2. Implement and test retry and nonzero shared-overhead allocation rules, then extend split/merge tests to each additional executable target family.
3. Freeze all seven adapter entries and authorize the seeded 150-attempt schedule.
4. Collect randomized, blocked real measurements; three attempts per action remain coverage/smoke only.
5. Establish statistical sufficiency and separately calibrate/freeze any scalar transformation model.

Until all gates pass, legacy scalar costs remain replay-only; this pilot cannot support a formal cost claim, paper result, or patent assertion.
