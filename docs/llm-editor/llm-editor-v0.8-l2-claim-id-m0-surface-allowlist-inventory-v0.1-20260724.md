# M0 surface allowlist inventory v0.1 (draft)

本附件是只读盘点，不是实现、schema 发布或 Kernel 写入授权。authority base 为
`9279cbe4b1d05c9d78186cb784b1fd385445c01f`；所依据的 amendment 仍为 draft/非生效状态。

## 建议的首批 M0 surface

唯一建议进入后续单独审查的首批 ID 是：

- `project05_depth2_public`
  - `09-experiments/governance/contracts/planner-runtime-contract-v0.1.json`
  - 依据：已冻结 runtime contract，公开 config/state/action 字段边界，labels 与 hidden/recoverable/required claim 字段不可见，独立统计单位为 `case_or_attack_chain`。

`08-writing/2026-07-09-planner-information-boundary-design.md` 只能作为 supporting protocol，不能直接作为可执行 surface。C12 的 aggregate summary 也只能作为 supporting result evidence，尚未形成可列入 M0 的具体输入字段冻结。

## 明确排除与 vacant

- `project05_xgboost_policy`：现有 action-value XGBoost 与 Claim alignment 分离，不得借此写入 Claim-ID/IR 或 fit XGB。
- `project05_logistic_policy`：虽在 runtime contract 家族列表中，但尚无独立冻结的 Claim-ID/IR input projection。
- C12：45 个 mask/intensity/seed 条件是重复条件，不得冒充独立 Claim-ID surfaces，且不得与其他 holdout 池化。
- certificate surface：保持 vacant。现行 implementation plan 禁止真实 Checker、E_case、certificate、Promote 与 STOP。

## 不变的边界

- `schemas/claim-ir-kernel.schema.json` 不发布。
- `kernel_ingestion_authorized=false`。
- 不授权 M0/M1/M2 实现、XGBoost fit、certificate generation、catalog/role/credit/L2 变更。
- M2 gold/adjudication 仅保留字段 `approver_role_to_freeze: "PI"`，不虚构人名。
- 本附件不授 source role、train admission、lineage credit 或 quota credit。

裁断上限：`approve_for_separate_metadata_candidate_review_not_source_role`。
