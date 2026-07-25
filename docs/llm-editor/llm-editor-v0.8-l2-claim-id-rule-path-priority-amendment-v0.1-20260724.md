# Claim-ID 规则优先路径 amendment v0.1（草案）

**状态**：`draft_for_review_not_effective`  
**基线**：`12fddd382f6bd783970093b0d3a91cd10445a844`  
**关联**：A/B 与负结果草案 `llm-editor-v0.8-l2-quota-role-negative-result-amendment-v0.1-20260724`；SI-LLM-001

## 目的

把**主实验是否推进**从「必须先凑齐公开 B 级四族并完成 LLM 微调」上解耦。  
优先交付**确定性规则/脚本**的统一 Claim ID / Claim IR 输出，使规划、证书与 Kernel 对接不再被 family 搜索阻塞。

本草案**不**：降低 B 级 Gate、授 source role、写 effective train catalog、授 credit、授权 Qwen/L2 微调、授权下载，或判定 L2 通过。

## 核心决定

1. **暂缓为非阻断依赖**：公开四族 LLM 微调不再作为 Claim-ID 输出与下游实验的前置条件；未来重开仍需新授权。  
2. **解阻塞目标**：规则编译器能稳定产出可机器检查的 Claim IR 包。  
3. **推进顺序（默认禁止三路同等并行）**：
   - **M0** 纯规则 Claim-ID / IR 编译器（必须先做，实施仍需另行授权）  
   - **M1** 多源 adapter 框架集成（M0 冻结后，实施仍需另行授权）  
   - **M2** 可选：XGBoost 学规则残差（需金标准/裁决合同后另授执行）  
4. **比较**：允许，但只能在冻结的规则基线 + 同一评估包上比；Boost 只报相对规则的增量。

## Schema 先行与 Kernel 边界

M0 先发布版本化的外部 `schemas/claim-ir-kernel.schema.json`。`pending_kernel_schema` 只能是该 schema 内的显式状态值，不是另一套 bridge 协议。

在 SI-LLM-001 shared schema 关闭、且有独立授权前：

- `kernel_ingestion_authorized=false`；
- `effective_kernel_state_write_authorized=false`；
- Claim IR 只能作为外部、可审计的中间产物；
- 本 amendment 不授权 schema 发布、代码实现或 Kernel 写入。

## 为什么是这个顺序

| 路径 | 能否解阻塞 | 现在能否启动 | 角色 |
|---|---|---|---|
| 纯规则 | 能 | M0 后另行授权 | 主路径 |
| 框架集成 | 否（需先有 IR 出口） | M0 后另行授权 | 系统贡献 |
| XGB 残差 | 否（需金标准） | 另授 | 可选对照 |
| Qwen 四族微调 | 否 | 暂缓，重开需新授权 | 未来可选 |

现有 **action-value XGBoost** 不得被改写成 Claim 对齐结果；M2 必须是新任务合同。

M0 首批只覆盖显式 allowlist：`planner_experiment_inputs`、`certificate_experiment_inputs`，以及一条 valid fixture 和一条 authority-leak/invalid fixture。不得把“active surfaces”解释为全仓库覆盖。

## M2 的两种模式

- **工程 smoke test**：只检查接口、确定性和失败处理；不拟合 residual，不作科学增益声明。
- **科学 residual fit**：必须另立 gold/adjudication 合同，冻结 `rules_only` 基线，使用 source/lineage-disjoint 的评估包，并取得一次性 execute authority。金标准包应满足现行 evaluative sample-kind 下限，或由另一个有理由的新 amendment 明确替代。

## 与 A/B、负结果轨道的关系

- A 轨可记录编译输入与 Gate/失败台账；**不产生** train credit。  
- B 轨仍是唯一可能的配额 train 源；本路径**不创造** B。  
- 负结果主线可继续描述 B 供给缺口；同时 M0/M1 推进接口与系统。

## 科学天花板（写进稿件前必守）

- M0/M1 最多支持：「接口可用 / 来源约束编译框架 / 下游不因缺四族而停」。  
- **不支持**：「多元语义对齐已解决」「构念效度已关闭」「LLM/树模型带来对齐增益」（除非 M2 按合同完成）。  
- Codebook / 人工构念修复仍独立必需；本路径不豁免。  
- SI-LLM-001 共享 Claim IR schema 未关闭前，不得把未认证输出当作 Kernel 可认证状态写入。

## 不变项

- 身份 ≠ role ≠ credit ≠ L2  
- 禁半个拼一个；禁 Bypass；禁耗尽重跑；禁静默重开失败 acquisition  
- 不得用模型结果回溯降低配额或 Gate  

## 已作决策与仍待冻结项

已作决策：

1. 先发布版本化外部 schema；`pending_kernel_schema` 是状态值，不是 schema 缺席时的替代协议。
2. M0 首批只做 planner/certificate allowlist 与 valid/invalid fixtures。
3. M2 分为工程 smoke test 与科学 residual fit；后者必须新 gold/adjudication 合同。
4. M0 足以支撑“接口/编译器解阻塞”主张；M1 才支撑“多源 adapter framework”主张。

仍待冻结：

1. planner 与 certificate 的具体实验 ID；
2. 若未来提出 M2 科学拟合，由谁批准 gold/adjudication 合同。

## 当前范围

草案未生效、未授权实现执行、未下载、未写 Kernel、未改 catalog/role/credit/L2。M0/M1/M2 的实际实现或执行均需后续单独授权。  
审阅通过前，仅作设计提案；生效或归档提交需另授。
