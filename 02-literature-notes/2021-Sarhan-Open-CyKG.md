# Open-CyKG: An Open Cyber Threat Intelligence Knowledge Graph

## 1. 基本信息

- 英文题名：Open-CyKG: An Open Cyber Threat Intelligence Knowledge Graph
- 中文译名：Open-CyKG：开放网络威胁情报知识图谱
- 作者：Injy Sarhan; Marco Spruit
- 年份：2021
- Venue：Knowledge-Based Systems, Vol. 233, Article 107524
- DOI / arXiv / URL：10.1016/j.knosys.2021.107524；https://github.com/IS5882/Open-CyKG
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：重点读
- 所属主题：ATT&CK-KG-RAG / CTI Structure / Knowledge Graph

> 阅读来源说明：本次沉淀基于 Crossref DOI 元数据、开放 GitHub 仓库 README 与代码目录。ScienceDirect/PDF 全文直连未成功，因此实验细节只记录开放材料中能确认的部分，后续如拿到 PDF 可补全。

## 2. 一句话总结

Open-CyKG 提出一个从非结构化 APT/CTI 报告构建开放网络威胁情报知识图谱的框架。它先用 cybersecurity NER 识别实体，再用 attention-based neural Open Information Extraction 抽取关系三元组，最后通过 canonicalization / fusion 将抽取结果归一并构造成可在 Neo4j 中查询和可视化的 CTI KG。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 大量 CTI/APT 报告以自然语言形式存在，安全分析师难以直接检索、关联和推理。
  - 传统 IoC 列表只能捕获离散实体，不能表达攻击实体之间的关系和攻击链上下文。
  - 需要把非结构化 CTI 转换为可查询、可融合、可视化的知识图谱。
- 这个问题为什么重要？
  - CTI KG 可以支撑威胁狩猎、攻击模式检索、跨报告关联和后续 RAG/GraphRAG。
  - 对 Project05 而言，它补齐了“CTI 文本 -> 开放知识图谱”的底座，不只停留在 ATT&CK technique 标注。
- 之前方法哪里不够？
  - 手工 CTI KG 构建成本高，难以随新报告更新。
  - 只做 NER 或 IOC 抽取不能表达实体关系。
  - 单篇报告中的实体别名、重复关系和表述差异需要 canonicalization。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 它处于 `CTI 文本 -> 实体/关系三元组 -> CTI KG` 层。
  - 它不直接做 actor attribution、attack intent recognition 或 evidence sufficiency。
  - 它可作为后续 CTI RAG / GraphRAG / hybrid retrieval 的结构化知识源。

## 4. 核心贡献

1. 任务贡献：面向 CTI/APT 报告构建开放网络威胁情报知识图谱。
2. 方法贡献：结合 cybersecurity NER 与 neural OIE，从非结构化报告中抽取实体和关系三元组。
3. 图融合贡献：使用 canonicalization / fusion 技术和词向量相似性归一实体与关系。
4. 系统贡献：开放 GitHub 仓库，包含 OIE、NER、KG canonicalization notebook 和 Neo4j 可视化流程。
5. 数据贡献：README 指向 MalwareTextDB / Malware DB、Microsoft Security Bulletins 和 CTI reports 等训练或实验数据来源。

## 5. 方法框架

### 输入

- 数据类型：
  - 非结构化 APT / CTI reports；
  - malware/security text；
  - Microsoft Security Bulletins；
  - cybersecurity NER 数据；
  - OIE 训练数据。
- 输入格式：
  - 自然语言句子和报告段落；
  - 标注实体；
  - OIE relation triples。
- 先验知识：
  - cybersecurity entity types；
  - neural NER；
  - Open Information Extraction；
  - word embeddings / similarity；
  - Neo4j graph database。

### 输出

- 预测结果：
  - CTI 实体；
  - 开放关系三元组。
- 图结构：
  - CTI knowledge graph；
  - Neo4j 图数据库中的节点和边。
- 标签：
  - NER 实体类别；
  - relation triple 中的 subject / predicate / object。
- 报告：
  - 无自动调查报告。
- 证据链：
  - 原文句子 -> 实体识别 -> OIE triple -> canonicalized KG edge。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Cybersecurity NER | 识别 CTI 文本中的安全实体 | 可作为 CTI graph/RAG 的实体入口 |
| Neural OIE | 从句子中抽取开放关系三元组 | 可作为不依赖固定 schema 的关系抽取 baseline |
| Triple labeling | 用 NER 结果辅助标记 OIE 关系三元组 | 让开放三元组更接近安全语义 |
| Canonicalization / Fusion | 归一实体、合并重复节点和关系 | 对 actor alias、malware family、tool name 归一很重要 |
| Neo4j visualization | 查询和可视化 CTI KG | 可作为后续 GraphRAG / analyst interface 原型参考 |

### 方法流程

```text
- 非结构化 CTI/APT 报告
  ↓
- Cybersecurity NER 识别安全实体
  ↓
- Attention-based neural OIE 抽取开放关系三元组
  ↓
- 用实体识别结果标记和约束三元组
  ↓
- Canonicalization / fusion 归一实体与关系
  ↓
- 构建 Open-CyKG 并导入 Neo4j 查询/可视化
```

## 6. 数据集与实验

- 数据集：
  - OIE dataset：README 指向 Malware DB / MalwareTextDB。
  - NER dataset：README 指向 Microsoft Security Bulletins 与 Cyber Threat Intelligence reports。
- 数据规模：
  - 本次开放材料未确认完整规模，需全文或 notebook 进一步核验。
- 标注方式：
  - OIE 与 NER 使用已有数据集/标注资源训练或验证。
- Baseline：
  - 本次开放材料未确认完整 baseline。
- 指标：
  - 本次开放材料未确认完整指标。
- 主要结果：
  - 开放材料确认其产物包括 OIE model、NER model、KG canonicalization notebook 和 Neo4j KG visualization。
- 消融实验：
  - 待全文补充。
- Case study：
  - 待全文补充。

## 7. 关键知识点

### 概念

- Open Information Extraction 适合在 schema 未完全固定的 CTI 文本中抽取关系。
- NER 不只是输出实体列表，也可以帮助 OIE triple 获得安全语义类型。
- Canonicalization 是 CTI KG 的关键步骤，因为同一个 actor、tool、malware、vulnerability 可能有多个别名或表述。
- Neo4j 适合承载 CTI KG 查询和可视化，但不自动解决证据可靠性和归因可信度问题。

### 技术路线

- 传统 CTI KG 路线：

```text
CTI text
  -> NER
  -> OIE triples
  -> canonicalization / fusion
  -> KG
  -> query / visualization
```

- 和 LLM/RAG 结合后的可扩展路线：

```text
CTI KG
  -> entity / relation retrieval
  -> evidence-grounded prompt
  -> uncertainty-aware reasoning
  -> attribution / intent / investigation output
```

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Open Information Extraction | 开放信息抽取 | OIE |
| OIE | 开放信息抽取 | 不限定固定关系 schema |
| relation triple | 关系三元组 | subject-predicate-object |
| canonicalization | 归一化 / 标准化 | CTI KG 中常指实体或关系合并 |
| knowledge graph fusion | 知识图谱融合 | 合并重复和等价信息 |
| Neo4j | Neo4j | 图数据库名，不翻译 |

## 8. 优点

- 框架清楚：NER、OIE、canonicalization、KG visualization 串成完整 CTI KG pipeline。
- 开放仓库有利于复现和二次开发。
- 不强依赖 ATT&CK 固定技术 schema，可以抽取更开放的 CTI 关系。
- 对后续 GraphRAG / HybridRAG 提供结构化知识源参考。

## 9. 局限

- 方法以传统神经 NER/OIE 为主，不是 LLM-native pipeline。
- 开放关系抽取会带来关系噪声、语义粒度不稳定和实体边界错误。
- KG 构建本身不等于威胁归因；它缺少 evidence sufficiency、uncertainty、actor PMF 和 refusal 机制。
- 本次未获取 PDF 全文，实验指标、baseline 和 case study 需要后续补核。

## 10. 对我选题的启发

- 可以直接借鉴：
  - `NER -> OIE triples -> canonicalization -> CTI KG` 作为 CTI KG 构建 baseline。
  - Neo4j / graph database 作为结构化证据查询层。
  - canonicalization 思想可用于 actor alias、tool alias、malware family、campaign name 归一。
- 可以改进：
  - 用 LLM 或 retrieval-augmented extractor 替代传统 NER/OIE。
  - 给每条 KG edge 加上 source sentence、confidence、time 和 evidence type。
  - 将 CTI KG 与 provenance graph / InfoPath 对齐，而不是只停留在报告知识图谱。
- 可以作为 baseline：
  - CTI KG construction baseline；
  - GraphRAG 结构化知识源 baseline；
  - 和 AttacKG、EXTRACTOR 一起作为 CTI text structuring 相关工作。
- 可以用于研究动机：
  - 早期 CTI KG 说明“报告结构化”已经被研究；Project05 不能只做 KG 构建，而要继续推进到证据融合、意图识别或可信归因。
- 可以用于实验设计：
  - 比较 text-only RAG、CTI-KG RAG、CTI-KG + provenance evidence hybrid retrieval。
  - 评价 KG edge 是否能被追溯到原文证据句。

## 11. 可转化的研究问题

1. 如何把 Open-CyKG 式 CTI KG 与 Kairos/DEPCOMM 式 provenance evidence 对齐，形成可验证的攻击证据链？
2. 如何为 CTI KG 中的实体和关系加入 evidence sufficiency / confidence / temporal validity，使其支持可信归因？
3. LLM 能否作为 KG canonicalization 或 relation validation 模块，提高 CTI KG 的实体归一和关系质量？
4. 面向 actor attribution，CTI KG 中哪些关系类型对 actor PMF 真正有区分度？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AttacKG | AttacKG 更贴近 ATT&CK technique graph alignment；Open-CyKG 更偏开放 CTI KG 构建。 |
| EXTRACTOR | EXTRACTOR 输出可用于 threat hunting 的 provenance query graph；Open-CyKG 输出更通用的 CTI KG。 |
| TechniqueRAG / Multi-Step LLM Pipeline | 它们聚焦 ATT&CK technique extraction；Open-CyKG 聚焦实体关系图谱构建。 |
| CTIConnect | CTIConnect 需要异构知识源和 RAG benchmark；Open-CyKG 可作为结构化 CTI KG 源。 |
| Beyond RAG for CTI | Open-CyKG 提供 GraphRAG 所需的 KG 底座，但也会继承 schema gap 和结构性幻觉风险。 |
| LocalIntel | Open-CyKG 是全局 CTI KG；LocalIntel 强调结合本地组织知识。 |

## 13. 论文写作可引用句式

- Earlier CTI knowledge graph work has shown that unstructured threat reports can be transformed into entity-relation graphs through NER, open information extraction, and graph canonicalization.
- However, constructing a CTI knowledge graph alone does not solve trustworthy attribution, because attribution requires evidence weighting, uncertainty estimation, and the ability to abstain under insufficient evidence.
- Open CTI KG construction can serve as a structured retrieval substrate, while provenance evidence provides the local behavioral grounding needed for investigation and attribution.

## 14. 我的批注与疑问

- Open-CyKG 更像“CTI KG 工程底座”，不是当前硕士论文的最终创新方向。
- 它提醒我：后续如果使用 GraphRAG，需要先问 KG 的边是否可追溯、是否可信、是否与本地日志证据一致。
- 需要补查 PDF 全文中的实验指标和数据规模，避免在正式论文里只引用 README 信息。
- 如果要做 CTI + provenance 融合，Open-CyKG 的 triple 与 provenance graph 的 edge/event 语义粒度可能不一致，需要设计中间 schema。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：4/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是，作为 CTI KG 底座文献进入第二梯队。
