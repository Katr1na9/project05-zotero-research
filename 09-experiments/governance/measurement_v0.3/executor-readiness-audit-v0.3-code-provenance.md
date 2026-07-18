# Project05 executor readiness audit v0.3 — code-provenance-locked C02 capability pilot

Status: **capability pilot verified; formal operational-cost measurement remains blocked**

Supersedes: `executor-readiness-audit-v0.2-real-only-pilot.md` for the current pilot record only. The v0.1 and v0.2 audits remain historical records.

Scope: canonical real-only C01–C09 cohort; canonical C10+ and source C13+ remain sealed.

## Current reproducible pilot

- canonical action: `C02-AA-002`;
- source alias: `C05-darpa-e3-cadets/C05-AA-002`;
- executor: `query_host_subgraph` file-target pilot against `/tmp/vUgefal` in DARPA E3 CADETS R02;
- run record: `09-experiments/governance/measurement_v0.3/pilots/c02-aa-002-r02-file-one-hop-v0.3/pilot-run.json`;
- source code: `09-experiments/scripts/query_host_subgraph_adapter.py`;
- code SHA-256: `58339a149e9c6bd7ad2168d34512cc08c8af3800aa980390e3768d54ade2164d`.

The run record independently locks five artifacts: the adapter source, R02 events input, R02 nodes input, derived event subgraph, and derived node subgraph. A post-run recomputation matched every declared SHA-256.

## Measured capability result

The run completed from `2026-07-18T06:48:54.583661Z` through `2026-07-18T06:49:04.938577Z`.

- Resource vector: 10.3559157 wall seconds; 9.984375 CPU seconds; 244,984,898.89484233 RSS byte-seconds; 901,652,996 bytes scanned; 807,514 source-line primitive operations; zero analyst seconds, authorization wait, direct currency, downtime, and evidence perturbation.
- Observation: five exact target events; four seed UUIDs; 3,002 derived event records and 1,391 derived node records.
- Boundary: the executor accepts only allow-listed case/action/type/target fields and rejects planner-oracle fields (`recoverable_claim_ids`, `oracle_effects`, `hidden_claim_ids`). It does not consume legacy scalar cost, expected effect fields, or ground truth.
- Split/merge: merged and ordered-shard event inputs conserve raw bytes, records, primitive counts, observation counts, and derived event/node SHA-256; nodes are scanned once per logical invocation rather than once per event shard.

## Measurement-status result

The converted measurement batch passes schema validation, provenance replay, and complete unit-bearing resource checks. Its manifest explicitly reports:

`capability_pilot_only_not_formal_schedule_measurement`

It contains one capability-pilot record and zero formal schedule records. The record declares an `unscheduled_capability_pilot` randomization deviation and `initial_state_reset=false`, so it cannot contribute to the three-attempt coverage gate.

## Formal gate remains closed

The following gates remain unsatisfied:

1. 149 scheduled primary attempts are absent, so coverage is incomplete.
2. The pilot is intentionally outside randomized schedule compliance and has no controlled initial-state reset.
3. The seven-type adapter registry remains draft, with zero globally implemented/eligible adapter types; this code only covers the CDM18 file-target family within `query_host_subgraph`.
4. Statistical sufficiency has not been established.
5. No scalar transformation model has been calibrated, validated, or frozen.

Therefore no formal measured-cost profile, paper result, patent assertion, or cross-method performance claim is authorized by this pilot.
