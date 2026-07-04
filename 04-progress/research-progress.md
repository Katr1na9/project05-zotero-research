# Research Progress

## 总体里程碑

| 阶段 | 目标 | 状态 | 产物 |
|---|---|---|---|
| M1 | 建立科研工作区和 Zotero 流程 | 进行中 | project05-zotero |
| M2 | 完成 10 篇核心文献精读 | 进行中 | 精读笔记 |
| M3 | 形成 3 个候选选题 | 延后 | 所有文献读完后由用户手动决策 |
| M4 | 选定 1 个主选题 | 未开始 | 选题论证 |
| M5 | 完成最小实验设计 | 未开始 | 实验方案 |
| M6 | 开题报告初稿 | 未开始 | 开题文档 |

## 当前待办

- [x] 将 `A survey of cyber threat attribution` 写成精读笔记。
- [x] 将 `AttacKG` 写成精读笔记。
- [x] 将 `EXTRACTOR` 写成精读笔记。
- [x] 将 `Kairos` 写成精读笔记。
- [x] 将 `TechniqueRAG` 写成精读笔记。
- [x] 将 `DEPCOMM` 写成精读笔记。
- [x] 将 `CTIBench` 写成精读笔记。
- [x] 将 `Large Language Models are Unreliable for CTI` 写成精读笔记。
- [x] 将 `TTPXHunter` 写成精读笔记。
- [x] 将 `SEvenLLM` 写成精读笔记。
- [x] 将 `CTIConnect` 写成精读笔记。
- [x] 将 `LOCALINTEL` 写成精读笔记。
- [x] 将 `Beyond RAG for CTI` 写成精读笔记。
- [x] 将 `A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools` 写成精读笔记。
- [x] 将 `High Stakes, Low Certainty` 写成精读笔记。
- [x] 整理威胁归因术语表 v0.1。
- [ ] 延后：所有核心/扩展文献读完后，再由用户手动决定是否比较 3 个候选选题。
- [ ] 对候选 idea 做 2024-2026 最新工作新颖性检查。

## 阅读记录

### 2026-06-30

- 已阅览并沉淀：`A survey of cyber threat attribution`
- 已阅览并沉淀：`AttacKG`
- 初步判断：
  - 综述提供威胁归因的层级地图和研究动机。
  - AttacKG 提供 CTI 报告结构化、ATT&CK 技术识别和知识图谱构建的方法抓手。
  - 当前值得推进的路线是：CTI 文本 -> 攻击图/TTP -> ATT&CK KG/RAG -> 攻击意图识别 -> 证据增强候选归因。

### 2026-07-01

- 已沉淀：`EXTRACTOR: Extracting Attack Behavior from Threat Reports`
- 已沉淀：`KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance`
- 核心收获：
  - EXTRACTOR 关注 CTI 报告到 provenance graph 的转换，是 AttacKG 的重要前置基础。
  - 它的输出不是 ATT&CK technique，而是可被 threat hunting 系统使用的 query graph。
  - CTI 文本结构化的关键难点包括长句、领域术语、省略主语、代词指代、实体归一、关系抽取和非攻击行为过滤。
  - KAIROS 关注真实审计日志到 whole-system provenance graph 的构建与异常检测，并把异常边压缩为 compact attack summary graph。
  - KAIROS 的价值不仅是检测，更是把百万级日志边压缩成可调查、可解释的攻击摘要图。
- 对选题的影响：
  - 当前选题路线应明确区分“文本攻击行为图”和“系统审计 provenance graph”。
  - 后续不宜只做 CTI 文本侧 TTP 抽取，应考虑“CTI 文本攻击图 + 日志侧 provenance evidence”的双源证据融合。
  - KAIROS 自身不做 ATT&CK 标注、攻击意图识别或组织归因，这正好留下了向上层语义推理扩展的空间。

## 下一步阅读

### 2026-07-04

- 已沉淀：`TECHNIQUERAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text`
- 核心收获：
  - TechniqueRAG 已经较系统地覆盖“CTI 文本 -> ATT&CK technique/sub-technique 标注”任务。
  - 它使用 retriever、LLM re-ranker、fine-tuned generator 三段式框架，在少量标注样例下提升 technique annotation。
  - 它留下的缺口主要不是“再做一个 RAG 标注器”，而是 technique 之后的 intent layer、证据充分性、不确定性和日志侧 evidence 对齐。
- 对选题的影响：
  - 不能把“RAG 做 ATT&CK 标注”作为独立创新点。
  - 候选选题应向 evidence-grounded intent recognition、CTI-log provenance alignment 或 uncertainty-aware attribution 收窄。

### 2026-07-04：DEPCOMM

- 已沉淀：`DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation`
- 核心收获：
  - DEPCOMM 关注系统审计日志因果分析生成的 dependency graph 过大、难以人工调查的问题。
  - 它通过 process-centric communities、community compression 和 InfoPaths 生成攻击调查摘要。
  - 它和 Kairos 互补：Kairos 更偏异常检测后生成 attack summary graph；DEPCOMM 更偏从 POI 出发压缩 dependency graph。
- 对选题的影响：
  - 日志侧证据可以不直接输入 LLM，而是先压缩为 InfoPaths / attack summary graph。
  - 后续可考虑把 InfoPaths 映射到 ATT&CK technique、tactic 或 attack intent。

### 2026-07-04：CTIBench

- 已沉淀：`CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence`
- 核心收获：
  - CTIBench 将 LLM-CTI 能力拆成 CTI-MCQ、CTI-RCM、CTI-VSP、CTI-ATE、CTI-TAA 五类任务。
  - CTI-ATE 对应 ATT&CK technique extraction，可与 AttacKG、TechniqueRAG、TTPXHunter 对齐。
  - CTI-TAA 对应 threat actor attribution，是当前最贴近威胁归因主线的 benchmark 子任务。
  - 显式 reasoning prompt 并不能稳定提升 CTI-MCQ 准确率，说明“让模型解释一下”不是可靠 CTI 的充分方案。
- 对选题的影响：
  - CTIBench 可作为实验设计和 baseline 参考，但不能直接作为论文创新点。
  - 后续更有价值的扩展是 evidence-grounded attribution、uncertainty-aware CTI 和 CTI text + provenance evidence 融合评测。

### 2026-07-04：Large Language Models are Unreliable for CTI

- 已沉淀：`Large Language Models are Unreliable for Cyber Threat Intelligence`
- 核心收获：
  - 许多 LLM-CTI 工作在短句或短段落上评估，容易高估模型能力。
  - 该文用 350 篇真实长度 APT 威胁报告评估信息抽取和信息生成。
  - LLM 在真实报告上存在性能不足、重复调用不一致和置信度校准较差的问题。
  - few-shot 和 fine-tuning 不一定提升效果，有时会降低性能或校准。
- 对选题的影响：
  - 后续方法必须评价真实长度报告、consistency、ECE、Brier Score 和证据可靠性。
  - “可信威胁归因”可以落到可度量指标，而不是只写概念。

### 2026-07-04：TTPXHunter

- 已沉淀：`TTPXHunter: Actionable Threat Intelligence Extraction as TTPs from Finished Cyber Threat Reports`
- 核心收获：
  - TTPXHunter 使用 SecureBERT、上下文数据增强、IOC 替换和相关句过滤，从完整威胁报告中抽取 ATT&CK TTP。
  - 它扩展了 TTPHunter 只覆盖常见 50 个 TTP 的限制。
  - 论文报告在增强句子数据集上 F1 为 92.42%，在 149 篇真实报告数据集上 F1 为 97.09%。
- 对选题的影响：
  - TTP extraction 已经是比较成熟的中间层，后续不宜把“抽 TTP”作为最终创新。
  - 更值得推进的是：TTP -> intent、TTP + provenance evidence -> evidence chain、TTP + uncertainty -> trustworthy attribution。

### 2026-07-04：SEvenLLM

- 已沉淀：`SEvenLLM: Benchmarking, Eliciting, and Enhancing Abilities of Large Language Models in Cyber Threat Intelligence`
- 核心收获：
  - SEvenLLM 构建了双语 CTI 指令数据、领域微调模型和 SEvenLLM-Bench。
  - 它覆盖 28 类安全事件任务，包括理解任务和生成任务。
  - Select-Instruct 先选择任务再生成 instruction/answer/thought，比普通 self-instruct 更适合领域数据构造。
- 对选题的影响：
  - SEvenLLM 可作为领域模型和指令数据背景，不应成为当前主创新。
  - 它的 Attack Intent Analysis 任务提示了 intent 方向，但需要更严格的标签、证据和评价设计。

### 2026-07-04：CTIConnect

- 已沉淀：`CTIConnect: A Benchmark for Retrieval-Augmented LLMs over Heterogeneous Cyber Threat Intelligence`
- 核心收获：
  - CTIConnect 将 CVE、CWE、CAPEC、MITRE ATT&CK 和 35 个来源的威胁报告整合为 1,860 个专家验证 QA。
  - 任务分为 Entity Linking、Entity Attribution、Multi-Document Synthesis 三类。
  - 论文指出 CTI 中存在 cross-source semantic gap，通用 vanilla RAG 不足以解决。
  - Domain-specific retrieval 相比 vanilla RAG 在不同任务上最高提升 +35.2%、+16.0%、+11.3%。
- 对选题的影响：
  - 后续不能只说“大模型 + RAG”，必须说明异构源、任务路由、检索策略、证据利用和评价指标。
  - CTIConnect 没有纳入 provenance graph，留下 `CTI + 日志溯源证据融合` 的空间。

### 2026-07-04：LOCALINTEL

- 已沉淀：`LocalIntel: Generating Organizational Threat Intelligence from Global and Local Cyber Knowledge`
- 核心收获：
  - LocalIntel 将公开全局 CTI 与组织本地知识库结合，生成组织级威胁情报。
  - 它的本地知识包括资产配置、软件版本、维护计划、组织 wiki 和可信历史 CTI。
  - 论文证明同一个 CVE 的处置建议会因本地配置不同而改变。
- 对选题的影响：
  - “本地上下文”是从 CTI 走向可行动安全决策的关键。
  - 后续可把 LocalIntel 的 local knowledge database 扩展为 provenance graph / InfoPath / attack summary graph。

### 2026-07-04：Beyond RAG for CTI

- 已沉淀：`Beyond RAG for Cyber Threat Intelligence: A Systematic Evaluation of Graph-Based and Agentic Retrieval`
- 核心收获：
  - 论文比较了 Semantic RAG、GraphRAG、Agentic GraphRAG 和 HybridRAG 四类 CTI 检索架构。
  - 图结构有助于 simple、single-hop、multi-hop CTI 问题，尤其适合 actor / malware / vulnerability / campaign 等关系推理。
  - 单纯 GraphRAG 不是可靠升级，会因为 text-to-Cypher 错误、schema gap 和空查询结果产生结构性幻觉。
  - HybridRAG 用图查询和文本检索互补，在 guided analyst-style questions 和拒答场景中更稳。
  - 可信 CTI/归因系统不能只看平均回答质量，还应评价拒答能力、延迟稳定性和灾难性失败模式。
- 对选题的影响：
  - 后续若做 LLM 增强威胁归因，不能只选 vector RAG 或 GraphRAG 单一路线。
  - 更稳的方向是 `CTI 文本证据 + ATT&CK/KG 图证据 + provenance/InfoPath 本地证据` 的混合检索与证据链生成。
  - 需要把 unanswerable / insufficient evidence 作为实验任务，要求模型在证据不足时拒绝归因并指出缺失证据。

### 2026-07-04：Opinion Pools

- 已沉淀：`A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools`
- 核心收获：
  - 论文把威胁归因从单体式黑盒分类改造成模块化架构。
  - 每个 attributor 基于一类证据输出候选 actor 的 PMF，再由 opinion pool 融合。
  - Pairing Aggregator 先对不同特征模块成对使用 logarithmic opinion pool，再用 linear opinion pool 得到最终 PMF。
  - 模拟实验显示模块化方法在 top-k accuracy 和 F-measure 上优于 Linear SVM / XGBoost 等 monolithic baselines，但该实验不能代表真实归因效果。
  - 中间 PMF 可以帮助分析师看到哪些证据支持哪些 actor，并发现可能的 false flag。
- 对选题的影响：
  - LLM 不应被设计成唯一归因裁判，而应作为 CTI/RAG attributor 或 evidence reasoning attributor。
  - 后续方向可采用 `CTI attributor + ATT&CK/KG attributor + provenance attributor + local context attributor -> weighted opinion pool -> actor PMF`。
  - 评价指标应包括 top-k accuracy、calibration、false-flag robustness 和解释性，而不只是 actor label accuracy。

### 2026-07-04：High Stakes, Low Certainty

- 已沉淀：`High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution`
- 核心收获：
  - 论文用 20 位专家访谈和 27 份真实勒索软件事件报告检验高层 IoC/TTP 在勒索软件归因中的有效性。
  - 从业者实际更依赖 ransom note、communication channel、leak site、network IoC 等低层或勒索软件特定证据。
  - TTP 在同一 RTA 内部平均 overlap 只有 0.37，不同 RTA 聚合 TTP 平均 overlap 为 0.21，silhouette score 为负值，说明 TTP 很难形成清晰 actor cluster。
  - RaaS、rebranding、affiliate turnover 和 false flag 会削弱“actor 拥有稳定 TTP 签名”的假设。
- 对选题的影响：
  - TTP/ATT&CK 标注只能作为攻击行为语义层，不能直接当作高置信 actor attribution evidence。
  - Opinion Pools 中的 attributor 权重应考虑证据类型的区分度和可靠性，TTP attributor 不应默认高权重。
  - 后续方法应输出 evidence sufficiency、relative/absolute attribution 层级、actor PMF 和拒答，而不是单一 actor label。

## 下一步任务

1. 补读 `Multi-Step LLM Pipeline`、`Open-CyKG` 等 CTI 到 ATT&CK/KG 支撑文献。
2. 继续补齐 `UNICORN`、`THREATRACE`、`PROGRAPHER`、`ADAPT it!` 等对比方法。
3. 在完成文献沉淀并初步凝练方向后，做截至 2026-07-04 的最新成果/撞题检索。

## 主线校准

- 当前主线：LLM 增强威胁溯源 / 攻击归因。
- 支撑模块：CTI 报告、ATT&CK/TTP、RAG/KG、provenance graph、可信评估。
- 阅读判断标准：每篇论文是否帮助 LLM 更好地理解溯源证据、重构攻击链、识别攻击意图、生成证据增强归因解释，或评估归因可信度。

## 延后事项

- `形成 3 个候选硕士论文题目，并用可行性矩阵比较`：推迟到所有核心/扩展文献读完后，由用户手动决定。
- `Agentic AI / 多智能体安全调查`：后置为 appendix 补充阅读，先完成 LLM 与现有溯源/归因/RAG/KG 主线。

## 周进展模板

### Week YYYY-WW

- 本周目标：
- 本周完成：
- 读完论文：
- 关键收获：
- 新增 idea：
- 遇到问题：
- 下周计划：
