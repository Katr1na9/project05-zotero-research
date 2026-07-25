# M1 planner-inputs single-execute activation audit

Status: activated single adapter execute authorized, not executed.

This companion is an audit aid only. The adjacent JSON is the exact authority
object accepted by the fail-closed adapter gate; this Markdown file is not
passed to the adapter.

## Frozen context

- Base commit: `3527457ed5907f584bebaf46a38e65fec9df7a9e`
- Surface: `project05_depth2_public`
- Adapter: `m1a_planner_inputs_v0_1`
- Source class: `planner_experiment_inputs`
- Authority-design SHA-256:
  `ea451a7e709072b9ab5723fc17547d0d55807fe6e24243a77b46c6c8f9f60214`
- Adapter-implementation SHA-256:
  `752072cf0596657a4bf6f9a60af5b667d8476731cb89f04a73544d87d9e07797`

## Exact descriptor

```json
{
  "surface_id": "project05_depth2_public",
  "source_class": "planner_experiment_inputs",
  "adapter_id": "m1a_planner_inputs_v0_1",
  "adapter_version": "0.1.0",
  "opaque_record_reference": "case_public_001",
  "declared_source_fields": [
    "config.case_id",
    "config.budget_total",
    "config.cti_nodes.node_id",
    "config.cti_nodes.stage",
    "config.cti_nodes.critical",
    "config.channel_reliability",
    "state.case_id",
    "state.step_index",
    "state.matched_cti_node_ids",
    "state.unmatched_cti_node_ids",
    "state.matched_cti_edge_ids",
    "state.unmatched_cti_edge_ids",
    "state.coverage.cti_node_coverage",
    "state.coverage.cti_edge_coverage",
    "state.coverage.critical_gap_count",
    "state.coverage.stage_coverage",
    "state.coverage.evidence_type_coverage",
    "state.budget.budget_total",
    "state.budget.budget_used",
    "state.budget.budget_remaining",
    "state.remaining_action_ids",
    "action.action_id",
    "action.case_id",
    "action.action_type",
    "action.acquisition_channel",
    "action.target.target_type",
    "action.target.target_value",
    "action.cost",
    "action.intended_cti_node_ids",
    "action.expected_evidence_types",
    "action.expected_stages",
    "action.expected_effects.expected_granularity_gain",
    "action.expected_effects.expected_uncertainty_reduction",
    "action.expected_effects.expected_over_attribution_risk_reduction",
    "action.expected_effects.expected_conflict_resolution",
    "action.expected_effects.expected_coverage_delta",
    "action.status",
    "action.natural_language_request"
  ]
}
```

Descriptor canonical SHA-256:
`914525488af3c6acf0fea3a069aac374eba83ff9f81b30f3473451ec489091a3`.

## Exact projection source and canonicalization

- Projection path:
  `tests/compiler_contract/fixtures/m0_rule_compiler/m0_valid_public_projection.json`
- Projection file SHA-256:
  `b7cae6b152082c71006c9cf545c1bc2a898a1024649f3ba9f02f26781260625b`
- Projection canonical SHA-256:
  `b9de352618c6b4c27acf828aa555df6c1e29c0c423beaa1c1b5a3d54118842c2`

Both input hashes use the adapter's exact canonicalization:

1. Read the committed UTF-8 JSON and parse it to a JSON value.
2. For the descriptor, use exactly the object printed above; the
   `declared_source_fields` array preserves the 38-entry schema enum order.
3. Serialize with Python `json.dumps` using `ensure_ascii=False`,
   `sort_keys=True`, `separators=(",", ":")`, and `allow_nan=False`.
4. UTF-8 encode the serialized text.
5. Apply SHA-256 and encode the digest as 64 lowercase hexadecimal characters.

No adapter function was called to calculate these hashes. No result file,
key, secret, Claim-ID, Kernel record, admission record, catalog entry, role,
credit, L2 state, registry permanence, M2 fit, or fine-tune was created.
