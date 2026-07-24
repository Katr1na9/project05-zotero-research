# `project05_depth2_public` Claim-ID/IR field projection draft

这是未提交的字段投影合同草稿，状态为
`draft_projection_not_implementation`。它只服务于
`project05_depth2_public`，不发布 schema、不实现编译器、不写 Kernel。

## 允许进入未来规则编译审查的公开字段

- `config`
  - `case_id`
  - `budget_total`
  - `cti_nodes.node_id`
  - `cti_nodes.stage`
  - `cti_nodes.critical`
  - `channel_reliability`
- `state`
  - `case_id`
  - `step_index`
  - `matched_cti_node_ids`
  - `unmatched_cti_node_ids`
  - `matched_cti_edge_ids`
  - `unmatched_cti_edge_ids`
  - `coverage.cti_node_coverage`
  - `coverage.cti_edge_coverage`
  - `coverage.critical_gap_count`
  - `coverage.stage_coverage`
  - `coverage.evidence_type_coverage`
  - `budget.budget_total`
  - `budget.budget_used`
  - `budget.budget_remaining`
  - `remaining_action_ids`
- `action`
  - 公开动作声明、目标、成本、预期证据/阶段及 prospective `expected_effects`
  - `natural_language_request` 仅作为公开动作元数据，不得解析成标签、判决或结果代理

虽然 runtime contract 暴露 `actions_taken` 与
`action_feedback.recovered_count`，本 M0 投影主动排除它们；后者是 realized
recovery outcome，不能进入规则 Claim-ID/IR 编译边界。

## 明确禁止

禁止 labels、class/attack/technique/verdict、`recoverable_claim_ids`、
`hidden_claim_ids`、`required_claim_ids`、oracle、mask membership、random
seed、run identity、realized outcomes，以及任何 private/hidden evidence、
credentials 或 secrets。

`case_id`、CTI node/edge ID、action ID 都只是公开不透明引用，不是 Claim ID。

## 状态语义

- Claim-ID minting：当前 `not_minted`；本草稿不生成 Claim ID。
- Admission：当前 `not_admitted`；不代表进入 Claim IR、训练、source role、lineage、quota 或 credit。
- Kernel：当前 `pending_kernel_schema`；这是阻塞态，不是隐含批准。
- `kernel_ingestion_authorized=false`。

certificate surface 仍为 `vacant`。不发布
`schemas/claim-ir-kernel.schema.json`，不授权 M0/M1/M2 实现或 XGBoost fit。

裁断上限：
`approve_for_separate_metadata_candidate_review_not_source_role`。
