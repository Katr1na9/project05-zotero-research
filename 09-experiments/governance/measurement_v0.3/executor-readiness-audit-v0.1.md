# Project05 action executor readiness audit v0.1

Status: **blocked for operational acquisition-cost measurement**

Scope: C01-C12 only; C13+ remains sealed.

This is an experiment-governance record, not paper or patent prose.

## Finding

The current planner runtime contains an outcome-reveal simulator, not a real evidence-acquisition executor. None of the eight action types currently has a frozen collector/adapter that can emit unit-bearing resource telemetry.

Consequently, the current runtime can support historical planner replay under legacy/uniform cost labels, but it cannot establish real acquisition burden for `extend_log_window`, `query_host_subgraph`, `recover_network_summary`, `ioc_enrichment`, `malware_analysis`, `ttp_local_probe`, `human_review`, or `cti_report_lookup`.

## Code evidence

The relevant path is `09-experiments/scripts/run_mvp.py`:

1. `planner_action_view` correctly hides execution-only `recoverable_claim_ids` from non-oracle planners.
2. `run_episode` resolves the selected public action ID back to the full action object.
3. `channel_is_up` makes a seeded Bernoulli availability decision from case, channel, and seed.
4. `recoverable_hidden` computes `recoverable_claim_ids ∩ hidden_ids`.
5. `run_episode` directly moves that set from hidden to visible state and records an `action_taken` trace.
6. No action-specific subprocess, library collector, remote query, filesystem scan, analyst protocol, termination monitor, or resource sampler is invoked on this path.

Repository-wide search found action-type strings in case compilers, governance builders, and the simulator mapping. It did not find operational implementations of the eight action types. Some dataset-intake utilities separately record bytes or records scanned, but those utilities construct/audit datasets; they are not action adapters and cannot be treated as the execution of all 72 planner actions.

## Governance consequence

- `legacy cost` remains historical replay metadata only.
- Simulator wall time is not evidence-acquisition cost.
- The 216-row v0.3 schedule is a seeded, auditable **template only**. It must not be executed or reported as an operational measurement campaign until adapters are frozen.
- The action ontology records `operational_cost_measurement_eligible=false` and binds this conclusion to the SHA-256 of `run_mvp.py`.
- Missing resource dimensions must remain null and block readiness; they must not be imputed from legacy labels or expert scores.

## Required executor boundary

Each action-type adapter must freeze all of the following before the measurement template becomes executable:

1. actor and authorization boundary;
2. initial-state identifier and reset procedure;
3. precondition evaluator;
4. target-to-invocation parameter mapping;
5. concrete entry point or manual protocol;
6. successful completion, partial completion, failure, cancellation, and timeout criteria;
7. observation schema and state-effect mapping;
8. primitive-operation boundary;
9. retry linkage and cancellation behavior;
10. setup/shared-overhead allocation rule;
11. telemetry for analyst seconds by role, compute wall/CPU seconds, memory byte-seconds, bytes/records scanned, direct currency, authorization wait, downtime, and evidence perturbation;
12. a prohibition on consuming `recoverable_claim_ids`, `oracle_effects`, or any hidden answer-key field.

Only after these contracts are implemented and validated may the schedule move from `template_only` to execution-authorized status.
