# LLM 证据编译层主线融合 M3 / WP3 审阅包

日期：2026-07-17  
状态：`ready_for_user_m3_review`  
范围：第三方组件复核、clean-room 输出适配、开发集 `REUSE-HYBRID` stub  
下一授权：无；审阅通过前不新增 CTI 文本、不运行第三方组件、不下载模型或 embedding

## 1. 结论

WP3 已完成“已知组件能否以来源约束接口接入主线”的工程与信息边界验证，但**尚未完成真实组件性能验证**。

- CTINexus 被选为 aligned-triplet 输出 profile；没有安装或执行其代码；
- OntoLogX 仅作来源图 schema 参照；Matryoshka、TACTIC-KG 与 Auto-Prov 均未复制代码；
- clean-room adapter 能把外部三元组转换成逐边带来源句的 target-graph sidecar；
- sidecar 的所有节点与边默认 `controller_eligible=false`，尚不能直接进入调查控制器；
- C04–C06 的日志/provenance 路径只复用冻结 `RULE-STRONG`；CTI 路径因无 `cti_text` 工件而 3/3 明确弃权；
- 没有运行 C07–C12，没有形成组件、LLM 或端到端增益结论。

因此本轮 Gate 的准确表述是：

> **adapter interface pass；component performance not evaluable。**

## 2. 组件裁决

| 组件 | 固定 revision | 许可 | WP3 裁决 |
|---|---|---|---|
| CTINexus | `0c688536...ff865` | MIT | 选作输出合同；runtime 未授权 |
| OntoLogX | `6ed386e6...16b7f` | MIT | schema / 来源设计参照 |
| Matryoshka | `2ee96934...cd2a` | GPL-3.0 | 算法参照；禁止 vendor |
| Auto-Prov | 仓库 404 | 不可得 | 论文强前作 |
| TACTIC-KG | `5df3b630...ed4d` | 仓库无代码许可 | 论文/接口参照；禁止复制 |

机器可读 catalog 位于 `09-experiments/llm_evidence_compiler_mainline/wp3/component-catalog-v0.1.json`。第三方代码复制量为 0。

## 3. 新接口与 fail-closed 规则

WP3 contracts 独立放在 `wp3/contracts/`，没有改变 M1 冻结的 6 个主 contracts：

1. `NormalizedAlignedTripletBundle`：钉死 component ID、revision、license、request 与三元组来源指针；
2. `SourceGroundedTargetGraphSidecar`：输出 request-scoped 节点/边、支持句、来源指针、拒绝原因和弃权状态。

adapter 只接受当前 public request 中的 `cti_text` record，并在同一 record 内寻找同时包含 subject 与 object 的最短句。以下情况全部 fail closed：

- 未登记组件、revision/license/profile 不一致；
- 当前 catalog 未授权却声称已经执行 component runtime；
- pointer 不存在或指向非 `cti_text`；
- actor/campaign 越级实体或归因关系；
- subject/object 不能落到同一来源句；
- 重复边或重复 triplet ID；
- bundle 含 private/gold/oracle 字段或 canonical claim ID。

机械通过只表示“来源表面可回指”，不表示语义已经由人类验证。

## 4. 开发集 `REUSE-HYBRID` 终态

| 项目 | 结果 |
|---|---:|
| 案例 | C04–C06，共 3 个 |
| 冻结 Rule claims | 26 |
| 冻结 Rule links | 15 |
| 可见 `cti_text` 工件 | 0 |
| CTI adapter 请求 | 3 |
| 明确弃权 | 3 |
| 接受的 CTI 边 | 0 |
| C07–C12 运行数 | 0 |

结果只证明：当 CTI 输入不存在时，混合路线不会伪造 CTI 图边，也不会偷偷调用 runtime。它**不能**证明 CTINexus、OntoLogX、规则组件或 LLM 的抽取质量。

## 5. 验证终态

| 验证 | 结果 |
|---|---|
| Python 编译 | 新增 2 个 scripts 通过 |
| WP3 定向测试 | 12 passed |
| M1–M3 全部 compiler 测试 | 47 passed |
| 全仓库测试 | 491 passed, 6 skipped, 0 failed |
| 模型 / embedding runtime | 未加载 |
| private reference | 未读取 |
| controller payload | 未生成 |

旧主线继承锁仍一致：

| 文件 | SHA-256 |
|---|---|
| `run_mvp.py` | `A7EBCF2739B7CD708011DB378D0F18AF3EB970C6236813BE7F8258D5394A952E` |
| `evidence_claim.schema.json` | `5FCA1B77512C5C966860781214DCB83BEE76CFECA56B9E4AE3B91657D73CA63A` |
| `alignment_state.schema.json` | `462C8E5F657A4467FC4B945FBAB60A2FF86D1D1470DBA8D5C3937F46E14EA61E` |

机器可读终态见 `09-experiments/llm_evidence_compiler_mainline/m3-wp3-readiness.json`。

## 6. 当前不需要双人审计

本轮指标是 contract、pointer、hash、same-record surface、弃权和信息边界，均可机械验证；没有声称 human-validated grounding、减少幻觉或真实语义正确，因此当前不触发双人审计。

双人最小语义审计只有在后续真实自动条件已经产生输出、且论文要采用“语义支持更好/无支撑断言更少”等强措辞时才重新判断。

## 7. M3 审阅问题与下一 Gate

M3 只需判断：

1. 是否接受五个组件的 revision/license/复用边界；
2. 是否接受 clean-room adapter 的 same-record source-span 与 fail-closed 合同；
3. 是否接受开发集结论降级为“接口通过、组件性能不可评估”；
4. 是否批准下一步只制定并冻结一份 **source-licensed CTI text artifact amendment**。

即使第 4 项批准，也只授权 CTI 文本来源、许可、分包、泄漏检查与冻结，不自动授权安装 CTINexus/OntoLogX、下载 Qwen/Llama/embedding、调用外部 API、训练、正式推理或运行 C07–C12。真实 component Gate 仍需之后的独立 runtime 授权。
