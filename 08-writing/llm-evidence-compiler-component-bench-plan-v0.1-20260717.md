# Project05 主线 LLM 证据编译层：Component Bench 实施计划 v0.1

日期：2026-07-17  
状态：`plan_frozen_pending_runtime_authorization`  
上游 Gate：WP4 S2/S3 `passed_s2_s3_ready_for_runtime_gate_review`  
候选组件：CTINexus fixed revision `0c688536d85eae72f6055723492b573b0a1ff865`  
当前授权：仅计划与离线合同；不授权获取/安装组件、模型、embedding 或执行 runtime

## 1. 目标与主线位置

本 bench 不把 LLM 变成归因器或 planner。它只验证已知 CTI 编译组件是否能被 Project05 包装为一个有来源约束的语义建图前端：

```text
CTI 文本
→ CTINexus-compatible triplets
→ Project05 same-record source-span recovery
→ schema / pointer / scope / forbidden-conclusion Gate
→ controller_eligible=false target-graph sidecar
```

M3 仍独立处理“是否可溯源、下一取证动作和 STOP”。本阶段不接 M3 controller。

## 2. 可证伪问题

唯一主问题：

> 在不读取 private gold、不运行 C07–C12、且每条边必须回指同一来源记录的条件下，CTI 组件能否稳定生成 Project05 合同可接受的 target-graph sidecar？

失败条件：

- runtime 无法在冻结依赖/硬件中启动；
- 输出不能稳定转换为冻结 triplet contract；
- 大部分 triplet 缺少可解析 pointer；
- same-record surface support 通过率过低；
- actor/campaign/attribution 结论大量越界；
- 只能依靠修改 validation 数据、阈值或合同才能通过。

失败时退回 `interface-only reuse profile`，不影响 M3 或调查控制主线。

## 3. 实验单位与分包

| 阶段 | 来源 | 独立单位 | 用途 |
|---|---|---|---|
| R0 | 无正文 | 代码 revision / wheel hash | 依赖和 import smoke |
| R1 | CTID Blueprints | 1 文档 | unit runtime smoke、错误路径 |
| R2 | MITRE ATT&CK | 1 上游 STIX 文档；内部 procedure 为重复测量 | prompt/adapter 调试，不作主统计 |
| R3 | CISA | 7 独立通告 | held-out component validation，文档宏平均 |

publisher family 不跨角色。MITRE procedure 不论抽取多少条，统计单位始终为一个上游文档。CISA 7 个通告不得用于 prompt、schema 或阈值调整。

## 4. 运行条件

### C0：`EXPLICIT-ABSTAIN`

不运行组件，输出合法空 sidecar。用于验证所有指标不能因“完全不输出”而虚假变好。

### C1：`CTINEXUS-RAW-PROFILE`

只把冻结组件输出转换为 `NormalizedAlignedTripletBundle`，不进入 controller；保存组件 revision、配置、模型、embedding、prompt 和输入 SHA-256。

### C2：`CTINEXUS+PROJECT05-GATE`

在 C1 后应用 Project05 source-span recovery 和机械 Gate。C2 是系统条件；其目标不是提高召回，而是把不能回指、越界或重复的边明确拒绝。

不得新增 `LLM-direct attribution`、selector 或 planner 条件。本 bench 不是新的 Paper B。

## 5. 预注册指标

主要机器指标：

1. `schema_valid_rate`：组件 bundle 是否满足冻结 schema；
2. `source_pointer_resolution_rate`：pointer 是否解析到当前 public record；
3. `same_record_support_rate`：subject/object 是否同时出现在同一最小来源句；
4. `forbidden_conclusion_rejection_rate`：预构造 actor/campaign/attribution 越界项是否全部拒绝；
5. `explicit_abstention_rate`：不能满足合同的文档是否明确弃权。

护栏：

- 同时报告 `accepted_edge_count` 和 `document_with_any_accepted_edge_rate`，防止 C0 以全拒答获得漂亮错误率；
- 所有 validation 指标按 7 个 CISA 文档宏平均；句子、triplet、边只作嵌套重复测量；
- 不报告 extraction recall、semantic F1、hallucination reduction 或人工 grounding，除非以后另建 gold/人工协议；
- 不把 schema-valid 或 surface co-occurrence 写成“语义正确”。

## 6. 冻结顺序与硬停

### Gate R0：代码与环境

需单独批准后才允许：

- 获取 CTINexus 固定 revision 或已钉 SHA-256 的 0.2.1 wheel/sdist；
- 在独立环境安装；
- 只执行 import、CLI help 和无模型 stub；
- 输出完整依赖锁、许可证与磁盘占用。

R0 不授权模型/embedding 下载或网络 API。

### Gate R1：本地模型配置

另行冻结：模型 ID、revision、量化、embedding ID、最大上下文、解码参数、显存/磁盘预算和离线模式。默认禁止付费 API。不得因结果差而临时换更大模型。

### Gate R2：unit smoke

只运行 CTID 1 文档。必须通过：schema、pointer、same-record recovery、actor/campaign reject、无 private/canonical ID、`controller_eligible=false`。失败则不得进入 MITRE/CISA。

### Gate R3：development

从 MITRE procedure 使用种子 `20260717` 做固定、去重、长度分层抽样；只调 adapter/prompt，不形成统计主张。样本表和配置必须在运行前冻结。

### Gate R4：component validation

对 7 个 CISA 文档一次性运行冻结配置。不得看输出后修改 prompt、schema、阈值、来源或文档。任何修改都需要新版本并使旧运行保持可追溯。

## 7. 与 M3 并行的接口纪律

- runtime 输出仅写 `09-experiments/llm_evidence_compiler_mainline/`；
- 不修改 `run_mvp.py`、`run_m3star*.py` 或 `results/m3star_*`；
- sidecar 始终 `controller_eligible=false`；
- 只有 compiler contract 和最终选定 M3 interface 分别冻结后，才写一个版本化 read-only adapter；
- adapter 接线另设 Gate，不能由 component bench 自动授权。

## 8. 人工审计

R0–R4 的合同、hash、pointer、surface support 和越界拒绝均可机器验证，当前不要求双人审计。

若未来论文需要“语义关系正确”“比基线更少无支撑断言”等强主张，至少需要对冻结 validation 输出做独立语义审核；在该协议获批并完成前，相关字段不得进入标题、摘要或贡献。

## 9. 当前请求的最小下一授权

建议下一次只批准 Gate R0：获取/校验 CTINexus 固定代码或钉死的发行包，在隔离环境做无模型 import smoke，并输出依赖锁。仍不授权模型、embedding、训练、正式推理、C07–C12 或 M3 接线。
