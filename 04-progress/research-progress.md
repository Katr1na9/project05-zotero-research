# Research Progress

## 2026-07-06：APTChaser / GAPT / MLDSJ 补查与撞题修正

- 新增 `02-literature-notes/2025-Zhang-APTChaser-Attack-Technique-Modeling.md`：确认 APTChaser 已覆盖 `LLM + attack technique schema/profile + APT attribution`，禁止 Project05 把“LLM 细化 TTP 后归因”作为主创新。
- 重写 `02-literature-notes/2024-Chen-GAPT-Temporal-Relation-Embeddings.md`：当前只作为二级引用风险项保留，未找到可独立验证 DOI/全文，不能当作已精读文献。
- 新增 `02-literature-notes/2026-Duan-MLDSJ-Multi-Level-Feature-Joint-Attribution.md`：MLDSJ 直接覆盖 `多层 CTI 特征 + Dempster-Shafer 证据融合 + APT group attribution`，是 Project05 原始宽题的红色风险项。
- 新增 `04-progress/collision-matrix-supplement-20260706.md` 和 `04-progress/workflow-status-supplement-20260706.md`。
- 新增 `07-zotero-exports/zotero-import-candidates-20260706-supplement.ris`，包含 APTChaser、MLDSJ 和 `A Multi-Source Feature Fusion-Based Knowledge Graph for APT Attribution` 三条补充导入记录。
- 当前判断：2026 上半年并非空白；证据融合、KG 归因、LLM 技术建模方向都在推进。Project05 必须继续收窄为“归因粒度门控 / 可拒答解释 / 缺失证据清单”。

## 2026-07-06：APT-ATT 暂未获取情况下继续推进专利主线

- 新增 `04-progress/apt-att-unavailable-risk-note-20260706.md`：明确 APT-ATT 正文未获取是风险保留项，不作为当前主线阻塞项。
- 新增 `04-progress/final-topic-boundary-20260706.md`：将 Project05 推荐方向收束为“证据不完整场景下的 APT 归因可判定性评估、分层降级、拒答控制与 LLM 受控解释”。
- 新增 `08-writing/patent-claims-draft-v0.1-20260706.md`：形成专利权利要求草案 v0.1，核心模块包括证据可用性画像、证据区分度/充分性/冲突评分、归因粒度门控、开放集判断、LLM 受控解释和缺失证据采集建议。
- 当前判断：不再把“多源证据融合 + LLM 辅助归因解释”作为宽泛创新点，而是把“证据不足时系统是否允许输出 actor-level 归因”作为核心技术问题。

## 2026-07-06：二次深度撞题扫描完成

- 新增 `04-progress/deep-collision-scan-20260706.md`。
- 新增高风险材料包括：`CN121887534A`、`CN118802369A`、`TRAIL`、`APT-scope`、`APT-ATT`、`APTChaser`、`Construction of Cyber-attack Attribution Framework Based on LLM`、`Correlation Analysis of APT Attack Organizations Based on Knowledge Graphs` 等。
- 更新判断：Project05 不能再以 IOC/KG/HIN/流量/TTP/LLM 框架归因为核心；可保留空间进一步收缩为“归因粒度门控、可拒答解释、缺失证据生成和证据充分性画像”。
- 继续深扫后新增并精读/风险精读：`CN116467438A`、`CN117560223B`、`CN117786088B`、`CN119766567B`、`HG-CTA`、`AARGS`、`GAPT`、`BAN`。
- `08-writing/patent-claims-draft-v0.1-20260706.md` 已标记为偏宽草案，后续 v0.2 必须围绕“归因粒度门控”重写。

## 2026-07-06：基于新安装 research skills 重塑 workflow

- 新增 `01-sop/project05-skill-driven-workflow-v2.md`。
- 新增 `04-progress/workflow-status-20260706.md`。
- workflow 采用 `nature-literature-pipeline` 的检索/评分/归档思想、`nature-reader` 的全文精读约束、`nature-paper-to-patent` 的 source grounding 和 stage gate、`academic-research-suite` 的 research-to-paper pipeline、`experiment-agent` 的实验设计/验证 gate、`scientific-critical-thinking` 的红线审查框架。
- 当前正式定位：Project05 位于 Stage 6 功能级撞题矩阵，尚未通过 Stage 7 专利尽调 gate，不应继续扩写专利说明书。

## 2026-07-05：2026 H1 撞题补读已纳入

- 已完成 7 篇 2026 H1 关键文献的下载/抽取/精读登记：TTPrint、CTI-Thinker、OpenSec、Minerva、High-Precision APT Malware Attribution、Synthetic APTs、ARCANE。
- CTI-Thinker 本地下载为 Springer HTML 页面，未获得可抽取 PDF；已按网页全文/元数据纳入。
- 关键判断：`LLM + KG/GraphRAG + CTI attack reasoning`、`evidence-grounded TTP extraction`、`可验证 CTI LLM`、`abstention/OOS attribution` 在 2026 年上半年都有推进。
- Project05 的题目不能停留在泛化的 “多源证据融合 + LLM 辅助 APT 归因解释”；更稳的方向是 `证据不完整 + 开放集/未知 actor + 证据充分性评分 + 分层降级 + 拒答/暂缓归因 + 证据解释`。

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
- [x] 将 `Multi-Step LLM Pipeline for Enhancing TTP Extraction in CTI` 写成精读笔记。
- [x] 将 `Open-CyKG` 写成精读笔记。
- [x] 将 `UNICORN` 写成精读笔记。
- [x] 将 `THREATRACE` 写成精读笔记。
- [x] 将 `PROGRAPHER` 写成精读笔记。
- [x] 将 `APT-MMF` 写成精读笔记。
- [x] 将 `ADAPT it!` 写成精读笔记。
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

### 2026-07-04：Multi-Step LLM Pipeline

- 已沉淀：`Multi-Step LLM Pipeline for Enhancing TTP Extraction in Cyber Threat Intelligence`
- 核心收获：
  - 论文将 TTP 抽取拆为 `Extractor -> Technique Candidate Generator -> Validator` 三阶段。
  - Extractor 将复杂 CTI 文本拆成 atomic threat actions；Candidate Generator 用 ATT&CK procedure embedding 召回 top-k technique；Validator 用 LLM 排序和过滤候选。
  - 作者框架报告 Precision 86.14、Recall 78.76、F1 82.28，优于 TTPXHunter、Finetuned-SecureBERT、AttacKG、LADDER 和单 ChatGPT-4o baseline。
  - Atomic reconstruction prompt 与候选约束对降低 LLM TTP 抽取幻觉有价值。
- 对选题的影响：
  - `CTI -> ATT&CK technique` 已经有成熟的多阶段 LLM + retrieval 方法，不能作为最终创新点。
  - 该 pipeline 可作为文本侧 TTP baseline 或前置模块，后续创新应放在 intent、evidence sufficiency、uncertainty-aware attribution 或 CTI-log alignment。
  - Validator 思想可上移为 technique validator、intent validator、evidence sufficiency validator 和 attribution confidence validator。

### 2026-07-04：Open-CyKG

- 已沉淀：`Open-CyKG: An Open Cyber Threat Intelligence Knowledge Graph`
- 核心收获：
  - Open-CyKG 提供了传统 CTI KG 构建路线：cybersecurity NER 识别实体，attention-based neural OIE 抽取关系三元组，再通过 canonicalization / fusion 构建知识图谱。
  - 它的开放仓库包含 OIE、NER、KG canonicalization notebook 和 Neo4j 可视化流程。
  - 它补齐的是 `CTI 文本 -> 实体/关系三元组 -> CTI KG` 底座，不直接解决 actor attribution、attack intent 或 evidence sufficiency。
- 对选题的影响：
  - CTI KG 可作为 GraphRAG / HybridRAG 的结构化证据源，但 KG 构建本身已经不是足够新的最终创新点。
  - 后续更有价值的是给 KG edge 加上 source sentence、confidence、temporal validity，并与 provenance graph / InfoPath 对齐。
  - Open-CyKG 可和 AttacKG、EXTRACTOR 一起构成 CTI text structuring 相关工作线。

### 2026-07-04：UNICORN

- 已沉淀：`UNICORN: Runtime Provenance-Based Detector for Advanced Persistent Threats`
- 核心收获：
  - UNICORN 将 whole-system provenance graph 流式转换为 graph histogram，再用 HistoSketch 生成固定长度 graph sketch，并用演化式聚类模型做 APT 异常检测。
  - 它针对 APT 的 low-and-slow、zero-day、长期潜伏和模型污染风险设计，不依赖预定义攻击签名。
  - 在 StreamSpot、DARPA TC 和自建 supply-chain APT 场景上表现较强，但输出主要是 graph-level alarm。
- 对选题的影响：
  - Provenance-based APT detection 已经有成熟经典基线，后续创新不宜只做“检测是否异常”。
  - 更稳的 Project05 方向是把异常检测信号转成可解释 evidence chain，再映射到 ATT&CK / intent / attribution confidence。
  - UNICORN 可作为 Kairos、DEPCOMM、THREATRACE、PROGRAPHER 之前的日志侧对比基线。

### 2026-07-05：THREATRACE

- 已沉淀：`THREATRACE: Detecting and Tracing Host-Based Threats in Node Level Through Provenance Graph Learning`
- 核心收获：
  - THREATRACE 将主机威胁检测形式化为 provenance graph 上的 anomalous node detection and tracing。
  - 它用 GraphSAGE 学习 benign node roles，把 node type 作为监督标签，并通过 multi-model framework 缓解节点类别不平衡和隐藏角色差异。
  - 相比 UNICORN 的 graph-level alarm，THREATRACE 能定位异常实体和 2-hop 局部上下文，更接近调查证据。
- 对选题的影响：
  - 日志侧证据粒度已经可到 node-level，Project05 后续创新不宜只做异常节点检测。
  - 更有价值的是把 anomalous nodes / local context 聚合成 attack story、InfoPath 或 attack summary graph，并映射到 ATT&CK / intent / evidence sufficiency。
  - THREATRACE 可作为 node-level provenance graph learning baseline。

### 2026-07-05：PROGRAPHER

- 已沉淀：`ProGraPher: An Anomaly Detection System based on Provenance Graph Embedding`
- 核心收获：
  - PROGRAPHER 将 streaming provenance graph 切成 temporal snapshots，用 graph2vec 学习 whole graph embedding，再用 TextRCNN 预测下一个 snapshot embedding。
  - 相比 UNICORN 的 graph-level alarm，PROGRAPHER 通过 Rooted Subgraph 排名把异常 snapshot 映射回 suspicious nodes，进一步降低分析师工作量。
  - 真实 Production EDR 数据上 PROGRAPHER AUC 0.943，显著高于 UNICORN 的 0.542。
- 对选题的影响：
  - PROGRAPHER 可作为 snapshot-level provenance graph embedding baseline。
  - 它证明日志侧 detector 可以输出 key indicators，但还不能自动生成 ATT&CK、intent 或 actor attribution explanation。

### 2026-07-05：APT-MMF

- 已沉淀：`APT-MMF: An advanced persistent threat actor attribution method based on multimodal and multilevel feature fusion`
- 核心收获：
  - APT-MMF 将 APT reports 与 IOC 信息建模为 heterogeneous attributed graph，融合 attribute type、BERT text、Node2vec topology 三类节点特征。
  - 它通过 IOC type-level、metapath-based neighbor node-level、metapath semantic-level 三层 attention 学习 report node 表示并进行 actor classification。
  - 数据集包含 1,300 reports、21 APT groups、24,694 nodes、40,335 relationships；最终 Micro-F1 0.8321、Macro-F1 0.7051。
- 对选题的影响：
  - APT-MMF 是 CTI/IOC graph-based actor attribution 强基线。
  - 它提供了 report-IOC-metapath 的证据组织方式，但仍缺少 unknown actor、false flag、证据不足拒答和日志侧 provenance evidence 对齐。

### 2026-07-05：ADAPT it!

- 已沉淀：`ADAPT it! Automating APT Campaign and Group Attribution by Leveraging and Linking Heterogeneous Files`
- 核心收获：
  - ADAPT 将 APT attribution 拆成 campaign-level Intra-Clustering 和 group-level Inter-Clustering。
  - 它覆盖 executables 与 documents，使用 file-specific、generic、pattern-based 和 infrastructure linking features。
  - 数据集包含 6,134 APT samples、92 groups；campaign reference dataset 包含 230 samples、22 campaigns、17 groups。
  - Reference dataset 上 campaign clustering 对 executables F1 0.91、documents F1 0.92，group attribution F1 0.89。
- 对选题的影响：
  - ADAPT 是样本侧 heterogeneous file-based campaign/group attribution 强基线。
  - 它与 APT-MMF 互补，可共同支撑“报告侧 + 样本侧 + 日志侧”的多源证据融合方向。

## 下一步任务

1. 主线阅读已完成一轮沉淀。
2. 下一步维护 `04-progress/mainline-synthesis-20260705.md`，整理主线收束图：日志侧 evidence、CTI/IOC graph attribution、样本侧 campaign/group attribution、LLM/RAG/KG、可信归因评估。
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
### 2026-07-05：撞题补读 AURA / Guru / AttacKG+ / MM-AttacKG / TAA-EPLMR

- 已沉淀：
  - `AURA: A Multi-Agent Intelligence Framework for Knowledge-Enhanced Cyber Threat Attribution`
  - `On Technique Identification and Threat-Actor Attribution using LLMs and Embedding Models`
  - `AttacKG+: Boosting Attack Knowledge Graph Construction with Large Language Models`
  - `MM-AttacKG: A Multimodal Approach to Attack Graph Construction with Large Language Models`
  - `TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning`，全文待获取。
- 核心收获：
  - AURA 已经把 RAG、多智能体、LLM、APT attribution 和自然语言 justification 结合起来，且输入包括 TTP、IOC、malware、tools、timeline。
  - Guru et al. 已经做了 `CTI -> TTP -> actor ranking`，并证明 TTP-only attribution 噪声高、只能优于随机但不足以自动化高风险归因。
  - AttacKG+ 已经用 LLM 构建文本 attack knowledge graph；MM-AttacKG 进一步把 CTI 图像纳入多模态 attack graph construction。
  - TAA-EPLMR 题名高度接近 Project05 原始 idea，需拿到全文确认是否覆盖 evidence path、confidence、refusal、incomplete evidence ablation。
- 对选题的影响：
  - 不能再把“多源证据融合 + LLM 辅助 APT 归因解释”作为宽题直接推进。
  - 更稳的切口是：面向证据不完整场景的证据充分性感知、置信度校准、分层降级归因与可拒答机制。
  - 方法设计应以 `能不能归因到 actor` 为核心，而不是只追求输出一个 actor label。
