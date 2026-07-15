# Project05 安全 Top-4 定位与研究空缺综合

**版本**：v0.1，2026-07-14  
**用途**：为论文 v0.9 的标题、摘要、引言与相关工作提供权威定位。  
**约束**：不改变方法和实验主干；不把 Project05 包装成任何单篇工作的直接增量；不把一般 AFA 综述作为理论底座。

## 1. 结论先行

现有文献中，没有必要也不应强行指定一篇同时完成“威胁报告构图、本地日志对齐、LLM 语义推演、证据不完整下主动补证和结论约束”的单一母文。更准确的论文叙事是：

1. CTI 抽取与查询图匹配工作已经解决“如何把报告转成可搜索行为，以及如何在本地审计图中定位对应活动”。
2. 近五年安全 Top-4 工作持续改进日志侧溯源图的压缩、异常检测、根因定位和攻击故事重建。
3. 最新图—语言和日志—情报工作已经覆盖语义统一、跨模态对齐以及 LLM 辅助数据生成，因而这些不能再作为 Project05 的主创新。
4. 这些系统的共同任务终点仍主要是匹配、检测、摘要、TTP/场景识别或行为体判断。它们通常不公开一个接口来回答：当对齐只有部分成立、采集通道可能失败且预算有限时，下一步应获取哪类证据，何时停止，以及当前证据最多允许输出哪一级调查结论。
5. Project05 因而是一个**对最终归因输出而言的前置决策层、对抽取和对齐而言的后置控制层**。它接收上游产生的部分对齐和证据单元，把它们转换为可更新缺口状态，再执行取证动作选择、反馈更新、STOP 和结论粒度截断。

## 2. 权威文献群

### 2.1 近五年安全 Top-4 主证据

| 完整题名 | Venue / 时间 | 已解决的问题 | 任务终点 | Project05 接续的位置 |
|---|---|---|---|---|
| *DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation* | IEEE S&P 2022 | 将审计日志依赖图划分、压缩并生成 InfoPaths，降低人工调查规模 | 摘要图和关键路径 | 当摘要仍缺关键阶段或证据类型时，决定是否补采及何时停止 |
| *PROGRAPHER: An Anomaly Detection System based on Provenance Graph Embedding* | USENIX Security 2023 | 从长时溯源图发现异常快照并回指可疑节点 | 异常快照、节点指示器 | 将这些输出作为证据单元，而不是把异常分数直接提升为归因结论 |
| *KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance* | IEEE S&P 2024 | 从全系统审计流检测异常边并重建紧凑攻击摘要图 | 告警和攻击摘要图 | 处理摘要图因采集缺失、跨主机缺口或来源失败而不完整的后续控制 |
| *MAGIC: Detecting Advanced Persistent Threats via Masked Graph Representation Learning* | USENIX Security 2024 | 以自监督图表示学习实现批级和实体级 APT 检测 | 异常批次、实体与分数 | 明确其“检测粒度”不等于“可支撑结论粒度”，并决定是否需要更多证据 |
| *High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution* | USENIX Security 2025 | 实证检验 TTP 等高层指标对行为体归因的区分能力 | 证据有效性与高风险归因边界 | 直接支撑“观测到高层行为不等于足以输出 actor”的结论约束动机 |

以上五篇不是 Project05 的“母文”，而是共同证明：安全社区已经能构图、压缩、检测和重建，但**输出是否被证据充分支持**仍需单独建模。

### 2.2 精确对齐先驱与最新红线

| 完整题名 | Venue / 时间 | 对 Project05 的红线或用途 |
|---|---|---|
| *POIROT: Aligning Attack Behavior with Kernel Audit Records for Cyber Threat Hunting* | ACM CCS 2019 | CTI query graph 与本地 provenance graph 对齐已经成立；虽略早于五年窗口，但它是最精确的历史起点 |
| *EXTRACTOR: Extracting Attack Behavior from Threat Reports* | IEEE EuroS&P 2021 | 从非结构化报告自动构造威胁狩猎可用的 provenance query graph 已经成立 |
| *CLIProv: A Contrastive Log-to-Intelligence Multimodal Approach for Threat Detection and Provenance Analysis* | arXiv 2025 | 日志与威胁情报的共享语义空间、TTP 识别和场景重建是上游能力，不是 Project05 新点 |
| *APT-CGLP: Advanced Persistent Threat Hunting via Contrastive Graph-Language Pre-Training* | KDD 2026 accepted / arXiv 2025 | 图—语言粗细粒度对齐、LLM 合成训练对和 CTI 净化已构成最新红线 |
| *Large Language Models are Unreliable for Cyber Threat Intelligence* | ARES 2025 | LLM 在真实长度 CTI 上存在准确性、一致性和校准问题，支持限制其在线决策权限 |

## 3. 撞题矩阵

符号：`是` 表示论文任务接口明确实现；`部分` 表示可间接支持但不是其主要终点；`否` 表示论文没有提供该接口，不能解释为作者声称该问题不重要。

| 工作 | 报告/CTI 构图 | 本地日志/溯源图 | 图文或日志情报对齐 | 主动选择下一证据 | 失败反馈更新 | 显式 STOP | 结论支持上限 |
|---|---:|---:|---:|---:|---:|---:|---:|
| POIROT | 是 | 是 | 图匹配 | 否 | 否 | 否 | 否 |
| EXTRACTOR | 是 | 否 | 为下游生成 query graph | 否 | 否 | 否 | 否 |
| DEPCOMM | 否 | 是 | 否 | 否 | 否 | 否 | 否 |
| PROGRAPHER | 否 | 是 | 否 | 否 | 部分（模型适配） | 否 | 否 |
| KAIROS | 否 | 是 | 否 | 否 | 部分（异常检测反馈） | 否 | 否 |
| MAGIC | 否 | 是 | 否 | 否 | 部分（概念漂移适配） | 否 | 否 |
| CLIProv | 情报文本 | 是 | 是 | 否 | 否 | 否 | 否 |
| APT-CGLP | CTI 文本 | 是 | 是 | 否 | 否 | 否 | 否 |
| Project05 | 接收上游结构化结果 | 接收可回指证据 | 不重新发明对齐器 | **是** | **是** | **是** | **是，但当前为待验证工程代理** |

## 4. 允许写进论文的核心判断

### 4.1 可写

> 近期安全研究已经分别推进了审计图摘要、图异常检测、全系统攻击重建和细粒度证据定位；与此同时，CTI 查询图、日志—情报对齐和图—语言预训练也在持续缩小高层报告与低层事件之间的语义鸿沟。然而，这些方法主要在既定证据表面上优化匹配、检测或重建，尚未共同提供一个面向部分对齐结果的调查控制接口，用于在采集成本、通道失败和信息不可见条件下选择下一证据，并约束最终可声称的调查粒度。

### 4.2 不应写

- 不写“现有 Top-4 工作都存在规则匹配混乱”。文献支持的是表示层、数据质量、可观测性和任务终点不同，而不是所有系统都使用脆弱规则。
- 不写“Project05 解决多源融合”。多源融合、语义统一和图文对齐已有强红线。
- 不写“Project05 提高 APT actor attribution accuracy”。当前实验不测这一终点。
- 不写“LLM 是在线规划器”。LLM 只允许作为可替换的上游语义编译器或受证据引用约束的解释器。
- 不把 Round 1 失败改写成通过，也不在任何正文或图表中展示来源不独立的旧粒度一致性数值。

## 5. 论文故事

建议采用以下五段式开篇，而不重写整篇方法：

1. **能力进展**：CTI 行为抽取、溯源图分析和攻击重建已经成熟到可以产生候选攻击图、摘要路径和 TTP/场景结果。
2. **部署断点**：真实现场的证据来源、模式和可用性并不统一，任何上游对齐器都可能只返回部分结果；“未匹配”不能自动解释为“不存在”。
3. **风险**：若把部分结果直接交给 LLM 或归因器，系统可能把检测/场景相似性误提升为 campaign 或 actor 结论。
4. **本文方法**：在上游对齐与下游结论之间加入可审计调查控制层，将部分对齐转换为缺口状态，选择取证动作，吸收零收益反馈，并通过 STOP 和支持上限限制结论。
5. **证据边界**：本文证明接口可运行、策略排序具有场景依赖性，并永久报告 Round 1 构念复现失败；Claim、Intent 与粒度在通过 Route B Gate 前均不被描述为已验证部署构件。

## 6. LLM 的具体位置

```text
CTI / IOC / audit logs / provenance outputs
                  |
      optional semantic compiler (LLM allowed)
                  |
       versioned claims and source pointers
                  |
       Project05 investigation control
       gap state -> action/STOP -> feedback
                  |
       support-bounded investigation result
                  |
  optional evidence-grounded explanation (LLM allowed)
```

LLM 不读取隐藏恢复集合，不生成 Oracle 路径，不绕过粒度门控，也不把语言流畅性当作证据充分性。Planner-visible 字段一旦因 Round 2 codebook 而变化，C07-C12 的所有策略必须全量重跑。

## 7. 本地精读依据

- `02-literature-notes/2019-Milajerdi-POIROT.md`
- `02-literature-notes/2021-Satvat-EXTRACTOR.md`
- `02-literature-notes/2022-Xu-DEPCOMM.md`
- `02-literature-notes/2023-Yang-PROGRAPHER.md`
- `02-literature-notes/2024-Cheng-KAIROS.md`
- `02-literature-notes/2024-Jia-MAGIC.md`
- `02-literature-notes/2025-Li-CLIProv.md`
- `02-literature-notes/2025-Qiu-APT-CGLP.md`
- `02-literature-notes/2025-Mezzi-LLMs-Unreliable-CTI.md`
- `02-literature-notes/2025-Horst-High-Stakes-Low-Certainty.md`

## 8. Route B 不可破坏条件

1. 粒度旧结果不得展示；重做必须保留独立提交、时间戳、哈希与交接记录。
2. Round 1 负结果永久保留；Round 2 只能称为“修订构念后的新验证”。
3. Claim、Intent 未通过 Round 2 前统一称为“待验证工程字段”。
4. 任一 planner-visible 字段变化后，C07-C12 全策略重跑。
5. 构念 Gate 关闭前不新增 DQN、LLM Agent 或新大数据源。
6. 专利不把人工一致性或“分析师可稳定标注意图”写成技术效果。
