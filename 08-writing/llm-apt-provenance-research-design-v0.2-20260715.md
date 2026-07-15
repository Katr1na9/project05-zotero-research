# Project05 受证据约束的 LLM 辅助 APT 溯源研究设计 v0.2

日期：2026-07-15
状态：根据 Reviewer Report 修订的审阅稿；仅提议授权 Phase 1，尚未授权下载模型或运行正式实验
取代：`llm-apt-provenance-research-design-v0.1-20260715.md`

## 1. 修订结论

v0.2 接受并落实审阅报告的 A 级收束：当前数据与人工条件只足以支持**证据编译 pilot 与机制证明**，不支持同时展开五个研究问题，也不支持把 LLM 立即改写为整个 Project05 的唯一主线。

本设计采用两篇论文、三阶段产品矩阵：

| 产品 | 核心问题 | LLM 位置 | 当前状态 |
|---|---|---|---|
| Paper A | 不完整证据下的调查控制与参数治理 | 不进标题；现有 v1.0 事实保持冻结 | 独立保留 |
| Paper B Phase 1 | 受证据约束的 LLM 编译是否比规则更可靠、比 direct 更少越界 | 核心受测模块 | 本设计唯一拟授权实施 |
| Paper B Phase 2 | 编译错误是否传导到路径与规划 | 次级、条件解锁 | 未授权 |
| Paper B Phase 3 | 受约束 LLM selector 是否有效 | 可选扩展 | 未授权 |

禁止把 Paper B 的设计、未运行模型或未通过 Gate 的结果写入 Paper A 的标题、摘要、贡献或结论。Paper A 可以在 future work 中引用已批准但未完成的接口计划，但不能声称 LLM 增益。

## 2. 当前证据边界

1. C04–C06 有 26 条作者锁定开发 claims；C07–C12 有 32 条作者锁定测试 claims、6 个独立案例。
2. 现有 14 条 pilot 未运行模型，且把 gold `claim_id` 暴露成 `sample_id`，正式实验前必须废止这种身份设计。
3. Round 1 Claim/Intent 人工一致性失败；现有作者 claims 不能直接称为人类共识真值。
4. 当前没有独立 actor/campaign truth，内部 G1–G3 不是 actor accuracy。
5. C07–C12 多个规划器的内部 success 已接近饱和，因此 success 不适合作为端到端主指标。
6. RTX 2080 Ti 11 GB 只能支持受限的 7B 4-bit 路线；量化质量上限必须预声明。

## 3. Phase 1 唯一授权范围

Phase 1 只回答两个主要问题：

### RQ1：受约束证据编译

在相同 context packets 上，通用 LLM 或安全领域 LLM 能否相对冻结规则编译器提高来源约束下的有效输出质量？

### RQ5：受控输出与直接归因

在相同可见证据上，结构化编译加控制约束是否比 `LLM-direct` 更少产生无来源或超过案例支持上限的结论？

Phase 1 不回答：

- LLM 是否提高 actor/campaign attribution accuracy；
- LLM 是否普遍改善最终规划成功率；
- 安全领域模型是否具有普遍领域优势；
- LLM selector 是否优于 M2；
- LLM 是否达到 SOTA。

RQ2 只作为次级、探索性分层：同底座安全领域模型与通用模型的差异必须同时报告污染状态、拒答率和量化限制。RQ3 与 RQ4 不在 Phase 1 运行范围内。

## 4. Phase 1 方法概述

```text
冻结 context packet
    ├─ Rule compiler
    ├─ General LLM compiler ─┐
    ├─ Security LLM compiler ├─> schema / ID / pointer checks ─> Phase 1 score
    └─ Human-author gold ────┘

相同 packet
    ├─ constrained compiler output
    └─ LLM-direct structured conclusion
                         └─> ceiling / citation / human-support audit
```

Phase 1 不接入在线执行器，不改变现有 M2、AFA、XGBoost、Logistic、Depth-2、成本 profile 或冻结案例结果。其目的先证明编译接口和约束机制本身是否成立。

## 5. 数据包与泄漏修复

### 5.1 三类身份分离

- `request_id`：公开请求的随机或内容哈希 ID；
- `candidate_claim_id`：由请求哈希和输出序号派生；
- `gold_claim_id`：只存在于私有评分包。

模型不得看到或复制 `gold_claim_id`。修改 private gold 必须不改变 public request 字节和 SHA-256。

### 5.2 Public/private 物理分包

```text
public/
  context_packets.jsonl.gz
  public_cti_catalog.json
  input_manifest.json
private/
  observation_gold.jsonl.gz
  audit_sample_manifest.json
  gold_manifest.json
```

推理运行器只接受 `public/` 路径。Scorer 在推理完成后单独读取 `private/`。正式测试运行目录不得包含 private 文件。

### 5.3 Context packets

冻结测试包含：

- 32 个正 packets：每个至少包含一个 observation-only gold claim，并加入同案例、同窗或同 provenance 邻域干扰记录；
- 32 个匹配 null packets：按案例和来源类型匹配，不含可接受的目标 observation claim；
- 合计 64 个测试 packets，嵌套于 6 个案例。

开发集相应包含 26 个正 packets 和 26 个匹配 null packets。负例采用固定 seed 和确定性抽样规则构建，在模型运行前冻结；不得依据模型输出替换负例。

每个正 packet 的 private gold 列出 packet 内所有可接受 observation claims，避免模型从干扰记录提取了另一条真实 claim 却被错误处罚。Null packet 必须通过下述最小人工审计后，才能用于“正确弃权”科学主张。

### 5.4 Atomic pilot 的地位

原 14 条单记录 pilot 只用于模型加载、JSON、显存和 ID 隔离冒烟测试。因为 pointer 已随单记录输入提供，其 pointer exact match 只表示复制成功，不构成来源定位能力。

## 6. Gold 分层与最小人工充分集

### 6.1 G0：机器可验证事实

无需第二标注者即可报告：

- JSON/schema 是否有效；
- request/candidate/gold ID 是否隔离；
- pointer 是否指向 packet 内真实记录；
- artifact/record hash 是否匹配；
- literal entity 是否实际出现在结构化来源字段；
- 输出是否为空、拒答或非法；
- direct 输出的声明粒度是否超过冻结 `support_ceiling`；
- 延迟、显存、tokens 和错误状态。

这些指标只能证明接口完整性和机械约束，不能证明 claim 语义被人类认可，也不能单独支撑“减少幻觉”。

### 6.2 G1：作者锁定 observation gold

G1 只包含来源记录直接可观察的字段：source type、原子 subject–predicate–object、时间/顺序和 pointer。不把 tactic、technique、恶意性、actor、campaign、evidence strength、confidence、hypothesis 或 CTI node link 作为 Phase 1 主 gold。

G1 可用于报告“与冻结 Project05 observation gold 的一致率”，不得称为人类共识真值或普适 APT 溯源准确率。

### 6.3 G2：固定的最小双人来源审计

进入 Paper B 标题和“减少无支撑输出”核心声明之前，必须完成一个固定审计面板：

- 24 个 packets：每个 C07–C12 案例各 2 个正 packet、2 个 null packet；
- 从 64 个冻结 packets 中按固定 seed、案例分层和来源类型分层抽取；
- 四个输出包：Rule compiler、General LLM（compiler claims + structured conclusion）、Security LLM compiler、General LLM-direct；
- 每位标注者评 24 × 4 = 96 个输出；
- 两名来源独立、彼此盲法的标注者；第三人只裁决分歧，不替代首轮一致性；
- 标签：supported、partial、unsupported、unassessable；pointer valid 单列；direct 结论另标是否超过来源支持与案例 ceiling。

沿用既有预注册门槛：weighted/nominal kappa `>=0.70` 为可接受，`>=0.80` 为 strong；U/unassessable 比例不得超过 20%。不得删困难 item、后验改阈值或让作者/LLM 标签代填。

如果 G2 不实施或未过门槛：

- 禁止声称“LLM 减少幻觉/无支撑断言已获人类验证”；
- 禁止把 source-supported improvement 写成标题或核心贡献；
- Phase 1 只能作为接口 pilot，结果措辞降级为“schema、pointer 与作者锁定 observation gold 的一致性”。

## 7. 实验条件

### 7.1 主要条件

1. 冻结规则编译器；
2. `Qwen/Qwen1.5-7B-Chat` 4-bit 通用模型；
3. `Multilingual-Multimodal-NLP/SEVENLLM-Qwen1.5-7B` 4-bit 安全领域模型；
4. G1 作者锁定 observation gold；
5. `LLM-direct`，使用同一可见 packet 并输出结构化结论、引用、声明粒度与弃权。

RQ5 的正式 structured/direct 配对只使用通用 Qwen。SEVENLLM 在 Phase 1 只参加 compiler 对照，避免把领域模型差异与控制架构差异同时展开。Security direct/structured 如需运行，只能作为后续独立诊断，不进入本设计的主分析或 G2 工作量。

正式下载前必须冻结完整 model revision、许可、权重 SHA-256、量化后端和 prompt。模型不可用时停止该条件，不静默替换。

### 7.2 解码与重复

- 主运行：temperature 0、`do_sample=false`、每 packet 每模型一次 first-pass；
- 不允许把 repair 后输出回填为 first-pass；
- 重复一致性只在预注册的 12-packet 面板上做额外 4 次推理，共形成 5 次技术重复；
- 技术重复不增加独立样本量。

### 7.3 Direct 条件的公平性

正式 `LLM-direct` 与 General compiler/structured 条件使用相同 Qwen 模型、packet、量化、最大上下文和解码配置。Direct 输出必须符合单独 schema，显式给出：

- observation claims 与逐条 pointer；
- 当前最高可支持粒度；
- 攻击路径摘要；
- 是否输出 actor/campaign；
- 缺失证据与 abstain 决策。

不能用自由散文难以评分作为 direct 条件的劣势。

### 7.4 Structured 条件

为使 RQ5 不是“自由文本 vs 禁止输出”的不公平比较，使用通用 Qwen 设置同模型两阶段 `LLM-structured`：

1. 模型先生成 candidate claims；
2. 验证器只做预注册的 schema、pointer、hash 和 G1 observation 规则检查；
3. 同一模型只读取通过检查的 claims、显式缺口和 `support_ceiling`，生成与 direct 相同 schema 的结论。

Structured 阶段不能读取原始 packet、被拒收 claim 或 private gold。Direct 与 structured 的最终结论使用同一评分器。G1 检查使用作者锁定规则，因此没有 G2 时只能报告相对 Project05 gold 的机械/作者一致性，不能称为人类验证的 grounding。

## 8. 两项预注册主指标

Phase 1 只设两项科学主指标，其余均为诊断。

### P1：Grounded Packet Success（GPS）

在 G2 审计面板上：

- 正 packet：至少产生一条由来源支持且 pointer 正确的目标 observation claim，并且没有 unsupported claim；
- null packet：正确 abstain，未产生 unsupported claim；
- partial 不计成功，但单列报告；
- 按 packet 计 0/1，先按案例求均值，再做 6 案例 macro 平均。

若 G2 未完成，只能报告 `project_gold_packet_agreement` 作为代理，禁止仍使用 GPS 名称。

### P2：Unsafe Conclusion Rate（UCR）

在 structured 与 direct 的相同 G2 面板上，任一情况发生即记 1：

- 声明粒度高于冻结 `support_ceiling`；
- 输出 actor/campaign 而没有来源支持；
- 最终路径或结论包含 unsupported observation；
- 引用不存在或不支持对应结论的 pointer。

同样先按案例计算，再做 case-macro。没有 G2 时只能报告机器可判定的 `ceiling_violation_rate` 和 `invalid_pointer_rate`，不能称为完整 UCR。

### 8.1 诊断指标

诊断项包括 schema-valid、claim/type/SPO field agreement、pointer exact、correct/false abstention、positive-packet conclusion coverage、partial/unsupported 构成、拒答率、重复一致性、修正字段数、延迟、显存和 tokens。人工修正时间为可选记录，不作为主指标。

## 9. Phase 1 声明 Gate

### 9.1 人工有效性 Gate

进入任何人类 grounding 声明前，G2 必须满足：

- kappa `>=0.70`；
- U/unassessable `<=20%`；
- 无来源不可访问或 A/B 文件不独立问题；
- disagreement 的第三人裁决与首轮一致性分开报告。

### 9.2 “优于规则” Gate

只有同时满足以下条件，才能写“LLM 编译优于规则”：

- 至少一个 LLM 的 case-macro GPS 比 Rule 高至少 0.05；
- 6 个案例中至少 4 个方向不劣；
- 该模型的 unsupported-claim rate 和 invalid-pointer rate 均不高于 Rule；
- 结果不是由拒答全部困难 packet 得到。

未过门槛时如实写成持平、负结果或接口可行性，不改阈值。

### 9.3 “受控优于 direct” Gate

只有同时满足以下条件，才能写控制层减少不安全结论：

- structured 相对 direct 的 case-macro UCR 至少降低 0.05；
- 至少 4/6 案例方向有利；
- structured 的 positive-packet conclusion coverage 不得比 direct 低 0.05 以上，防止仅靠全部拒答降低 UCR；
- 无任何隐藏字段或 private gold 进入 structured 请求。

### 9.4 标题与核心贡献 Gate

Paper B 把“evidence-grounded”“减少无支撑输出”或相近正向措辞放入标题/核心贡献，必须同时通过 9.1、9.2 和 9.3。若失败：

- 可以形成负结果/评测型 pilot 稿；
- LLM 在 Paper A 中继续只是可选接口；
- 不把 Phase 2/3 当作挽救 Phase 1 的事后扩展；
- 不预写任何正向摘要。

## 10. 污染、拒答与量化混淆

### 10.1 污染检查

公开 DARPA、OTRF、CTI 文本可能进入模型训练语料。正式报告必须包含：

1. 模型卡与公开训练数据说明中是否披露相关来源；
2. 无 source payload、只给案例/报告名称时的记忆探针；
3. 对关键原始 UUID、时间戳、命令和局部事件串做 exact/near-exact 复现检查；
4. 分开报告“可能公开文本记忆”与“原始事件语义编译”；
5. 无法证明无污染时，状态写为 `unknown`，不得写“确认无污染”。

记忆探针不进入主模型选择，也不能用测试输出调整 prompt。

### 10.2 拒答与安全对齐

按模型和 packet 类型报告：空输出、显式拒答、错误 abstain、策略性保守和非法格式。RQ2 的领域模型差异必须在排除“一个模型只是更少拒答/更多乱答”后解释。

### 10.3 4-bit 限制

所有结论限定于指定 7B 模型的 4-bit 本地推理，不外推到 FP16、70B 或闭源前沿模型。负结果不能写成“LLM 普遍无效”，正结果也不能写成规模规律。OOM、超时或后端失败不得自动更换更大模型。

## 11. 算力与时间预算

### 11.1 正式推理调用预算

| 项目 | 计算式 | 调用数 |
|---|---:|---:|
| Compiler first-pass | 64 packets × 2 models | 128 |
| General structured conclusion | 64 × 1 model | 64 |
| General direct conclusion | 64 × 1 | 64 |
| 12-packet 一致性面板额外 4 次 | 12 × 4 model-mode conditions × 4 | 192 |
| Phase 1 正式总计 |  | 448 |

Rule 与 gold 不产生 GPU 调用。Atomic pilot 为 14 × 2 = 28 次 compiler 调用。Prompt 开发只使用分层抽取的 12 个开发 packets，最多比较 2 个 prompt 版本；选择规则在看到测试输出前冻结。

Pilot 必须测量 p50/p95 延迟、峰值显存和失败率，并据此给出正式运行预计墙钟时间。若 448 次预计超过 24 GPU 小时，只允许取消作为诊断项的额外一致性面板，保留 256 次正式 first-pass；不得减少 64 个测试 packets 或只跑表现更好的模型。

模型和缓存的磁盘预算上限为 30 GB；输出、manifest 和日志另行记录实际大小。安装依赖和下载权重属于需要单独用户授权的外部状态变更。

## 12. Phase 2：端到端传导（未授权）

Phase 2 只有在 Phase 1 完成并单独审阅后才能设计实施。预先冻结以下原则，避免事后为 LLM 加压：

1. 初始可见证据由 record/packet visibility manifest 决定，在任何 Phase 2 模型输出前生成并记录 SHA-256；
2. 使用现有 C07–C12 配对 mask × intensity × seed 网格，不按 Phase 1 结果新增“更难”遮蔽；
3. 端到端主指标优先级为：路径 macro-F1、over-attribution/UCR、ceiling violation；success 降为诊断项；
4. “实质传导”预定义为 case-macro 路径 F1 绝对变化至少 0.05，且至少 2 个独立案例同方向；或 uniform 成本至少改变 1 个动作且至少 2 个案例同方向；
5. 任何改善声明要求不增加 ceiling violation；
6. `gold-admission diagnostic` 只作错误传播上界，禁止出现在摘要、标题或贡献中。

Phase 2 仍需单独设计文档、用户审阅和实施计划；Phase 1 结果不能自动授权它。

## 13. Phase 3：LLM selector（可选、未授权）

Selector 仅在编译层 Gate 通过且 Phase 2 表明表示差异确有传导后考虑。必须采用交叉条件，区分 compiler 与 selector 的相关错误：

| Compiler | Selector |
|---|---|
| Rule | M2 |
| Rule | LLM |
| Best frozen LLM | M2 |
| Best frozen LLM | LLM |

Selector 只能读取公开 runtime view，返回公开候选 `action_id`、引用和理由。它不得与 Phase 1 共用结果叙事，也不得为了“增加 LLM 含量”在编译 Gate 失败后启动。

## 14. Phase 1 实施产物

拟实施文件限于：

```text
09-experiments/llm_compiler_v0.2/
  README.md
  experiment_config.json
  prompts/
09-experiments/data_schema/
  llm_context_packet.schema.json
  llm_compiler_result.schema.json
  llm_conclusion_result.schema.json
  llm_run_manifest.schema.json
09-experiments/governance/contracts/
  llm-compiler-contract-v0.2.json
09-experiments/scripts/
  build_llm_evaluation_packets.py
  run_llm_phase1.py
  validate_llm_phase1_output.py
  score_llm_phase1.py
09-experiments/tests/
  test_llm_packet_separation.py
  test_llm_phase1_contract.py
  test_llm_phase1_validation.py
  test_llm_phase1_scoring.py
```

Phase 1 不修改 `run_mvp.py`，不实现 semantic-link planner mode，不实现 selector。原 v0.1 pilot 文件保留为历史，不覆盖。

## 15. 开工前硬顺序

1. 用户批准本 v0.2。
2. 编写并审阅 Phase 1 详细实施计划。
3. 先实现 request/candidate/gold ID 分离、public/private packet builder、schema、stub 和测试。
4. 证明修改 private gold 不改变 request hash，且测试包不暴露 canonical claim ID。
5. 冻结 prompt、G0/G1 scorer、audit-panel seed 和 model config。
6. 只有上述测试全绿后，才单独请求安装推理依赖和下载权重。
7. 先跑 28 次 atomic pilot，验证显存与运行预算。
8. 再运行 64-packet Phase 1；任何测试输出不得回流 prompt。
9. 完成 G2 最小双人审计后，才判定 GPS/UCR 与标题 Gate。
10. 结果先写 Markdown 审阅稿，用户通过后再生成正式文档。

## 16. 非目标

Phase 1 不做：

- selector、DQN、RL 或在线 agent；
- Phase 2 端到端规划改造；
- 多模态图像、原始 PCAP 全文或超长上下文推理；
- LLM 微调；
- actor/campaign accuracy；
- 用另一个 LLM 充当 gold judge；
- 用测试集调整 prompt、阈值或 packet；
- 修改或吞并 Paper A；
- 在 Markdown 审阅前生成 DOCX/PPT/PDF。

## 17. 审阅意见落实矩阵

| 审阅项 | v0.2 处理 |
|---|---|
| M1 / A1 范围过宽 | Phase 1 只做 RQ1+RQ5；RQ2 次级；RQ3/4 未授权 |
| M2 / A2 Gold 冲突 | G0/G1/G2 分层；固定 24-packet、96 项/人双审；门槛写死 |
| M3 端到端饱和 | Phase 2 延后；路径 F1/UCR/ceiling 优先；visibility manifest 冻结 |
| M4 抢 Paper A 叙事 | Paper A/B 产品矩阵与禁止混写规则 |
| M5 领域模型混淆 | 污染状态、记忆探针、拒答分层与同底座限制 |
| M6 硬件现实 | 448 调用预算、24 GPU 小时 Gate、4-bit 限制 |
| A3 主指标过多 | 仅 GPS 与 UCR 两项主指标 |
| A4 ID 泄漏 | Phase 1 第一实现项；通过前不得下载模型 |
| A5 论文隔离 | Paper A 不写 Phase 1 未完成结果 |
| B2 success 不宜主指标 | Phase 2 success 降为诊断 |
| B3 指标瘦身 | 其余字段/系统指标全部降为诊断 |
| Minor 4 修正时间 | 字段数保留，时间可选 |
| Minor 5 相关错误 | Phase 3 预设 2×2 compiler-selector 交叉条件 |
| Minor 6 范围膨胀 | 明确不做多模态图像和原始 PCAP 全文 |

## 18. 审阅判定

v0.2 的批准只意味着：可以开始编写 Phase 1 实施计划，并在计划审阅后实现泄漏修复、stub、规则/两 LLM 编译和 structured/direct 对照。它不授权 Phase 2、Phase 3、模型下载、依赖安装或任何正向论文声明。
