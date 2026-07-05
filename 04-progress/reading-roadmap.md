# Reading Roadmap

## 2026-07-05 H1 补读批次状态

本轮已把 2026 年上半年与 Project05 撞题/补强最相关的 7 篇纳入主线精读：

1. TTPrint：evidence-grounded TTP extraction 已经成为强基线。
2. CTI-Thinker：LLM + CTI KG + GraphRAG attack reasoning 已经被推进。
3. OpenSec：安全 agent 评价开始关注证据不充分时的克制和校准。
4. Minerva：CTI LLM 已经进入可验证奖励和 RLVR 阶段。
5. High-Precision APT Malware Attribution：APT 归因已有 open-set / OOS abstention 方向。
6. Synthetic APTs：AI agent 可模仿/收敛 TTP，削弱 TTP-based attribution 假设。
7. ARCANE：跨 campaign Bayesian 证据累积仍可能低置信，支持 evidence sufficiency / refusal 主线。

更新后的主线判断：2026 H1 不是空白。Project05 的安全切口应进一步收窄为 `证据不完整与开放集场景下的证据充分性感知、分层降级归因与可拒答 LLM 归因解释`。

## 目标

用 4 周建立“LLM 增强威胁溯源/攻击归因”的完整主线。CTI 结构化、ATT&CK/TTP、RAG/KG、provenance graph、可信评估都是支撑模块；Agentic AI 暂作为 appendix 补充阅读，不作为当前主线。

## 第一梯队：先读 8 篇，建立主线

| 顺序 | 论文 | 目的 | 状态 |
|---:|---|---|---|
| 1 | A survey of cyber threat attribution: Challenges, techniques, and future directions | 建立威胁归因任务、证据、难点和评价维度 | 已沉淀 |
| 2 | AttacKG: Constructing Technique Knowledge Graph from Cyber Threat Intelligence Reports | 理解 CTI 报告到 ATT&CK 技术知识图谱的桥梁 | 已沉淀 |
| 3 | EXTRACTOR: Extracting Attack Behavior from Threat Reports | 理解自然语言报告如何转成攻击行为结构 | 已沉淀 |
| 4 | Kairos: Practical Intrusion Detection and Investigation using Whole-system Provenance | 建立基于系统日志/溯源图做真实安全调查的意识 | 已沉淀 |
| 5 | DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation | 学习海量审计日志如何压缩为调查相关证据 | 已沉淀 |
| 6 | TechniqueRAG: Retrieval Augmented Generation for Adversarial Technique Annotation in CTI Text | 进入 RAG + ATT&CK 技术标注主线 | 已沉淀 |
| 7 | CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence | 学习 LLM-CTI 任务评测设计 | 已沉淀 |
| 8 | Large Language Models are Unreliable for Cyber Threat Intelligence | 建立幻觉、置信度和证据支撑意识 | 已沉淀 |

## 第二梯队：围绕潜在方法框架精读

| 论文 | 目的 | 状态 |
|---|---|---|
| TTPXHunter | TTP 抽取任务定义、标注与指标 | 已沉淀 |
| Multi-Step LLM Pipeline for Enhancing TTP Extraction in CTI | LLM 多阶段流水线做 TTP 抽取 | 已沉淀 |
| Open-CyKG | CTI 知识图谱底座 | 已沉淀 |
| SEvenLLM | 安全事件/CTI 指令数据集和 benchmark | 已沉淀 |
| CTIConnect | 异构 CTI RAG benchmark | 已沉淀 |
| LOCALINTEL | 组织级 CTI + RAG | 已沉淀 |
| Beyond RAG for CTI | GraphRAG / HybridRAG 检索架构与失败模式 | 已沉淀 |

## 第三梯队：对比方法和背景补齐

| 论文 | 目的 | 状态 |
|---|---|---|
| UNICORN | 经典 provenance graph APT 检测 | 已沉淀 |
| THREATRACE | 图学习做主机威胁追踪 | 已沉淀 |
| PROGRAPHER | provenance graph embedding 对比方法 | 已沉淀 |
| APT-MMF | 自动化 APT actor attribution 代表方法 | 已沉淀 |
| ADAPT it! | 异构文件关联做 APT campaign/group attribution | 已沉淀 |
| A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools | 可信归因/置信度融合 | 已沉淀 |
| High Stakes, Low Certainty | 真实归因证据不可靠性与证据权重 | 已沉淀 |

## Appendix：Agentic AI 补充阅读

> Agent 可以视为大模型之后的新技术扩展模块。当前先不作为主线推进，等 LLM + 溯源/归因/RAG/KG 文献读完后再集中补读。

| 论文 | 目的 | 状态 |
|---|---|---|
| CyLens | agentic LLM 重构 CTI 生命周期 | 后置补充 |
| ExCyTIn-Bench | 安全调查智能体 benchmark | 后置补充 |
| Cognitive SOC | 多智能体、证据支撑叙事、SOC 报告生成 | 后置补充 |

## 四周阅读路线

### Week 1：威胁归因、攻击链、CTI、溯源图

目标：搞清楚威胁归因、攻击链、CTI、溯源图之间的关系。

阅读顺序：

1. A survey of cyber threat attribution
2. AttacKG
3. EXTRACTOR
4. Kairos
5. DEPCOMM

### Week 2：报告文本到 ATT&CK/TTP/KG/RAG

目标：搞清楚报告文本/情报文本如何变成 ATT&CK、TTP、知识图谱和 RAG 输入。

阅读顺序：

1. TTPXHunter
2. TechniqueRAG
3. Multi-Step LLM Pipeline
4. Open-CyKG

### Week 3：LLM + CTI/RAG/KG 主线

目标：进入“LLM 如何利用 CTI、RAG、知识图谱和可信评测来增强威胁溯源/攻击归因”的主线。

阅读顺序：

1. CTIBench
2. SEvenLLM
3. CTIConnect
4. LOCALINTEL
5. Beyond RAG for CTI

### Week 4：可信归因与对比方法

目标：补齐幻觉、置信度、证据权重和自动化 APT 归因对比方法。

阅读顺序：

1. Large Language Models are Unreliable for CTI
2. A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools
3. High Stakes, Low Certainty
4. APT-MMF
5. ADAPT it!

## 当前下一步

### 2026-07-05

下一篇建议阅读：

1. 主线阅读已完成一轮沉淀。
2. 下一步进入收束整理：维护 `04-progress/mainline-synthesis-20260705.md`，把日志侧 evidence、CTI/IOC graph attribution、样本侧 campaign/group attribution、LLM/RAG/KG、可信归因评估之间的关系图固定下来。
3. 文献沉淀完成并初步凝练方向后，做截至 2026-07-04 的最新成果/撞题检索。

原因：

- 你已经读完并沉淀了综述、AttacKG、EXTRACTOR 和 Kairos。
- EXTRACTOR 解决的是从 CTI 文本生成 provenance query graph。
- Kairos 解决的是从真实系统审计日志构建 whole-system provenance，并输出 compact attack summary graph。
- TechniqueRAG 已经说明 RAG + ATT&CK technique annotation 的边界；后续不能只做技术标注，需要继续推进到 intent、evidence grounding 或 uncertainty。
- DEPCOMM 已补齐“系统审计日志图摘要”这一侧，说明日志侧证据需要先经过 process-centric community / InfoPath 压缩，才适合进一步进入 ATT&CK/intent/LLM 语义层。
- CTIBench 已补齐 LLM-CTI 评测侧，说明后续实验不能只看生成文本质量，而要明确任务、标签、评价方式和证据可靠性。
- LLM unreliable 已补齐可信评测侧，说明后续方法至少要考虑真实长度报告、输出一致性和置信度校准。
- TTPXHunter 已补齐 TTP 抽取强基线，说明后续不能只做 CTI -> TTP，而应继续推进到 intent / evidence / attribution。
- SEvenLLM 已补齐领域指令数据与 benchmark 背景，说明“训练一个安全大模型”不是当前最稳的硕士创新点，除非有更专门的证据/意图/归因任务。
- Agent 相关论文先后置到 appendix，当前优先读大模型与 CTI/RAG/KG/溯源证据融合的文献。
- CTIConnect 已补齐异构 CTI RAG 评测，说明后续研究必须面对结构化 KB、非结构化报告和证据利用之间的跨源差距。
- LocalIntel 已补齐组织本地上下文主线，说明 CTI 需要结合本地资产、配置、维护计划或日志证据，才能生成可行动情报。
- Beyond RAG for CTI 已补齐 GraphRAG / HybridRAG 架构比较，说明图结构有助于多跳 CTI 关系推理，但纯 GraphRAG 会引入结构性幻觉、拒答失败和延迟不稳定。
- Opinion Pools 已补齐模块化可信归因主线，说明 LLM/RAG/KG/provenance 都可作为 attributor，最终应融合为 actor PMF 而不是单一黑盒结论。
- High Stakes, Low Certainty 已补齐真实归因证据可靠性，说明 TTP/高层 IoC 不能默认作为强 actor attribution evidence，后续需要 evidence sufficiency、拒答和分层归因。
- Multi-Step LLM Pipeline 已补齐 LLM 多阶段 TTP 抽取基线，说明 technique extraction 已经有成熟的 extractor/candidate/validator 架构，后续创新应继续上移。
- Open-CyKG 已补齐开放 CTI 知识图谱底座，说明传统 `NER -> OIE triples -> canonicalization -> KG` 路线可作为结构化检索源，但不能单独解决可信归因。
- UNICORN 已补齐 runtime provenance-based APT detection 基线，说明日志侧 graph-level anomaly detection 已经较成熟，但仍缺少攻击意图、ATT&CK 语义、证据链和归因解释。
- THREATRACE 已补齐 node-level provenance graph learning 基线，说明异常实体定位比整图告警更接近证据链，但仍不能自动生成 attack story、intent 或 attribution explanation。
- PROGRAPHER 已补齐 snapshot-level provenance graph embedding 基线，说明异常 snapshot 可以通过 Rooted Subgraph 映射回可疑节点，但仍停留在 indicator 层，尚不能自动给出 ATT&CK、intent 或 actor attribution 解释。
- APT-MMF 已补齐 CTI/IOC graph-based actor attribution 基线，说明报告-IOC-属性-关系-metapath 可以支撑已知 actor 分类，但仍缺少 unknown actor、false flag、证据不足拒答和日志侧证据对齐。
- ADAPT it! 已补齐 heterogeneous file-based campaign/group attribution 基线，说明样本侧 linking features 可支撑 campaign 与 group 双层聚类，但仍受混淆、共享工具、false flag、基础设施缺失和证据不足影响。
- 3 个候选硕士论文题目暂不生成，等所有核心/扩展文献完成后由你手动决定。

## 当前主线判断

截至 Kairos，已经形成两条证据链：

```text
CTI 文本侧：EXTRACTOR / AttacKG
  -> 攻击行为图 / ATT&CK 技术图谱

日志证据侧：Kairos
  -> whole-system provenance graph
  -> anomalous time window queue
  -> attack summary graph
```

后续选题不宜只停留在“从文本抽取 TTP”，更值得关注：

1. CTI 文本攻击图与日志侧 provenance graph 的对齐；
2. 基于 attack summary graph 的 ATT&CK technique annotation；
3. 基于真实证据链的攻击意图识别与威胁归因解释；
4. 对 LLM/RAG 输出的证据充分性和不确定性评估。
## 2026-07-05 撞题补读更新

新增纳入并阅读：

1. `AURA`：RAG + multi-agent + LLM 的可解释 APT attribution，已沉淀。
2. `Guru et al. 2025`：CTI -> TTP -> actor ranking 的 LLM/embedding baseline，已沉淀。
3. `AttacKG+`：LLM-based attack knowledge graph construction，已沉淀。
4. `MM-AttacKG`：多模态 CTI image-enhanced attack graph construction，已沉淀。
5. `TAA-EPLMR`：evidence path-enhanced LLM reasoning for threat actor attribution，全文待获取，暂不能算完成全文精读。

更新后的主线判断：

- `RAG + multi-agent + LLM + APT attribution + justification` 已被 AURA 明确覆盖，不能作为 Project05 主创新。
- `CTI -> TTP -> actor ranking` 已被 Guru et al. 覆盖，且其实验说明 TTP-only attribution 噪声大，只适合作为辅助基线。
- `LLM/MLLM 构建文本/多模态 attack graph` 已被 AttacKG+ / MM-AttacKG 覆盖，只能作为证据结构化模块。
- `evidence path + LLM reasoning + actor attribution` 可能已被 TAA-EPLMR 覆盖，需要拿到全文确认。
- 当前最稳方向应收窄为：证据不完整场景下的 evidence sufficiency、confidence calibration、adaptive attribution granularity 和 refusal/abstention。
