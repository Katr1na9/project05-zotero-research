# CTIConnect: A Benchmark for Retrieval-Augmented LLMs over Heterogeneous Cyber Threat Intelligence

## 1. 基本信息

- 英文题名：CTIConnect: A Benchmark for Retrieval-Augmented LLMs over Heterogeneous Cyber Threat Intelligence
- 中文译名：CTIConnect：面向异构网络威胁情报的检索增强大语言模型基准
- 作者：Yutong Cheng; Yang Liu; Changze Li; Dawn Song; Peng Gao
- 年份：2026
- Venue：本地 PDF 标注为 KDD 2026 / arXiv；会议日期在 2026-08，正式出版状态待核验
- DOI / arXiv / URL：本地 PDF 标注 DOI 为 10.1145/3770855.3817527；arXiv:2510.11974；https://arxiv.org/abs/2510.11974；项目页 cticonnect.github.io
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：LLM-CTI / RAG / Heterogeneous CTI / Knowledge Graph / Benchmark / Evidence Retrieval

## 2. 一句话总结

CTIConnect 提出一个面向异构 CTI 知识源的 RAG benchmark，将 CVE、CWE、CAPEC、MITRE ATT&CK 和厂商威胁报告整合为 1,860 个专家验证 QA，对 Entity Linking、Entity Attribution 和 Multi-Document Synthesis 三类任务评估 LLM 检索增强能力。它对我的选题很关键，因为它说明“大模型 + 威胁情报/溯源融合”的难点不只是生成答案，而是如何跨结构化知识库、非结构化报告和多文档证据进行任务适配式检索与证据利用。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 现有 CTI benchmark 多数是 closed-book 或单报告抽取，没有评估 LLM 在真实 CTI 工作中如何使用外部异构知识源。
  - CTI 知识源高度异构：结构化数据库使用标准化术语，威胁报告使用厂商叙述和别名。
  - 通用 RAG 往往假设语料同质，但 CTI 中存在明显 cross-source semantic gap。
- 这个问题为什么重要？
  - CTI 更新速度快，模型参数记忆无法跟上新漏洞、新攻击活动和新报告。
  - 生产级 CTI 系统必须能在推理时检索 CVE、CWE、CAPEC、ATT&CK 和 threat reports。
  - 如果检索不能跨源对齐，LLM 可能拿不到正确证据，或者拿到证据但不会利用。
- 之前方法哪里不够？
  - CTIBench 主要评估 closed-book LLM 的 CTI 任务能力，缺少 retrieval-augmented setting。
  - SEvenLLM 关注领域指令微调和单报告理解/生成，不评估异构知识源检索。
  - 通用 RAG benchmark 多在同质语料上评测，难以反映 CTI 中结构化数据库和叙述性报告之间的语义差距。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - TAP、CSC、MLA 等多文档综合任务接近 threat actor profiling、campaign reconstruction 和 malware lineage。
  - ATA 和 VCA 对应从报告行为/漏洞描述归因到 ATT&CK technique 或 CWE。
  - 它不直接做系统日志 provenance graph，但提供了 CTI 侧异构检索框架，可与 Kairos/DEPCOMM 的日志证据侧互补。
  - 它把 Agent 暂时放到未来 harness 设计层；当前核心仍是 RAG/KG/检索策略。

## 4. 核心贡献

1. Benchmark 贡献：构建 CTIConnect，整合 5 类异构 CTI 源，覆盖 9 个 CTI 任务。
2. 数据贡献：包含 1,860 个 expert-verified QA pairs，来自 CVE、CWE、CAPEC、MITRE ATT&CK 和 35 个来源的 vendor threat reports。
3. 任务贡献：将 CTI RAG 任务分为 Entity Linking、Entity Attribution、Multi-Document Synthesis 三类。
4. 方法贡献：提出面向不同任务类别的 domain-specific retrieval strategies，而不是单一 vanilla RAG。
5. 评测贡献：在 10 个 LLM 上比较 closed-book、vanilla RAG、domain-specific retrieval，以及 retrieve-then-rerank、IRCoT 等通用检索范式。
6. 发现贡献：证明 cross-source semantic gap 在不同任务中表现不同，性能瓶颈会在 retrieval infrastructure 和 evidence utilization 之间切换。

## 5. 方法框架

### 输入

- 数据类型：
  - 结构化 CTI：CVE、CWE、CAPEC、MITRE ATT&CK。
  - 非结构化 CTI：厂商 threat reports。
- 输入格式：
  - QA query；
  - structured KB entries；
  - unstructured report chunks；
  - report clusters；
  - B2F alignments。
- 先验知识：
  - CTI taxonomy；
  - structured cross-source mappings；
  - threat actor aliases；
  - campaign / malware / vulnerability / TTP 关系。

### 输出

- 预测结果：
  - CWE / CVE / CAPEC / ATT&CK technique；
  - actor profile；
  - malware lineage；
  - campaign storyline；
  - report vulnerability 或 behavior attribution。
- 图结构：
  - CSKG-Guided RAG 中构建 cybersecurity knowledge graph，用于多文档检索。
- 标签：
  - 官方 KB links；
  - manual clustering；
  - expert annotations。
- 报告：
  - Multi-Document Synthesis 输出 actor profile、malware evolution、campaign timeline。
- 证据链：
  - 通过 retrieved candidates、claim-level matching 和 LLM-as-a-judge 评估综合任务中的证据支持。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Closed-Book | 不检索，只用模型参数知识回答 | 用作能力下限 |
| Vanilla RAG | 原始 query embedding 后直接检索 top-k | 用作通用 RAG baseline |
| Extract-then-Retrieve (EtR) | 先抽取安全语义并 canonicalize，再检索 | 适合 Entity Linking |
| Decompose-then-Retrieve (DtR) | 将行为描述拆成多个语义行为，再逐项检索 | 适合 Entity Attribution |
| CSKG-Guided RAG | 离线构建 cybersecurity KG，用实体重叠匹配检索多文档 | 适合 Multi-Document Synthesis |
| LLM-as-a-Judge | 对 MDS 输出做 claim-level matching | 可借鉴为证据链评价方式 |
| Temporal Split | 按任务时间切分验证鲁棒性 | 适合 CTI 时效性评估 |

### 方法流程

```text
Heterogeneous CTI sources
  -> Cross-source seed annotation
  -> Template-constrained QA synthesis
  -> LLM-human collaborative curation
  -> Task routing
  -> Retrieval strategy selection
     -> CB / VR / EtR / DtR / CSKG-guided RAG
  -> LLM inference
  -> Automatic matching or LLM judge evaluation
```

## 6. 数据集与实验

- 数据集：
  - CTIConnect benchmark。
- 数据规模：
  - 1,860 expert-verified QA pairs。
  - 5 类 CTI sources：CVE、CWE、CAPEC、MITRE ATT&CK、vendor threat reports。
  - vendor threat reports 来自 35 个来源。
  - 时间跨度覆盖 2008-2025。
- 任务分类与规模：
  - Entity Linking：
    - RCM Root Cause Mapping：290；
    - WIM Weakness Instantiation：308；
    - ATD Attack Technique Derivation：261；
    - ESD Exploitation Surface Discovery：280。
  - Multi-Document Synthesis：
    - TAP Threat Actor Profiling：135；
    - MLA Malware Lineage Analysis：95；
    - CSC Campaign Storyline Construction：111。
  - Entity Attribution：
    - ATA Attack Technique Attribution：160；
    - VCA Vulnerability Catalog Attribution：220。
- 标注方式：
  - structured mappings 依赖官方 KB links；
  - report cluster 依赖 manual clustering；
  - B2F alignment 依赖 expert annotation；
  - benchmark construction 包括 cross-source seed annotation、factually-grounded QA synthesis、LLM-human collaborative curation。
- Baseline / 模型：
  - Open-source：LLaMA-3-405B、LLaMA-3-8B、Phi-4、Qwen-3-235B。
  - Proprietary：GPT-5、GPT-4o、Claude-Sonnet-4、Claude-3.5-Haiku、Gemini-2.5-Pro、Gemini-2.5-Flash。
- 检索配置：
  - CB：Closed-Book；
  - VR：Vanilla RAG；
  - DS：Domain-Specific retrieval。
  - 额外比较 retrieve-then-rerank 和 IRCoT。
- 指标：
  - EL / EA：regex ID extraction 后计算 Precision、Recall、F1。
  - MDS：LLM judge 做 claim-level matching，计算 Precision、Recall、F1。
  - LLM judge 可靠性：human agreement、self-consistency、stylistic-bias check。
- 主要结果：
  - domain-specific retrieval 相比 vanilla RAG 最高提升：Entity Linking +35.2%，Entity Attribution +16.0%，Multi-Document Synthesis +11.3%。
  - retrieve-then-rerank 和 IRCoT 只能弥补约 1-5% 的 vanilla-to-domain-specific gap。
  - Entity Linking 更偏 retrieval bottleneck，合适检索后小模型也能接近强模型。
  - Entity Attribution 更依赖模型能力和证据利用，模型规模提升更明显。
  - 时间切分实验中，性能在 older / newer halves 间通常在 ±2% 内，说明结论在 2008-2025 数据上较稳定。
- Robustness：
  - MDS 的 GPT-4 judge 与专家一致性 Cohen's kappa = 0.85。
  - GPT-4 judge 五次独立运行中 108/115 个 claim verdict 完全一致。
  - CSKG 用 GPT-4o-mini 替代 GPT-4o 构建后平均下降约 1.6%，说明较稳健。
- Case study：
  - Magniber ransomware 跨源关联案例：CSKG-Guided RAG 将 2023 SmartScreen bypass、2021 PrintNightmare 和 2017 South Korea targeting 关联起来，揭示单报告不可见的六年操作连续性。

## 7. 关键知识点

### 概念

- **Heterogeneous CTI**：CTI 不是一个同质文本库，而是结构化标准库和非结构化威胁报告共同构成的生态。
- **Cross-source semantic gap**：同一安全行为在不同源中以不同抽象层、术语和叙述表达出现，导致向量检索失效。
- **Entity Linking**：结构化知识库之间的映射，例如 CVE -> CWE、CAPEC -> ATT&CK。
- **Entity Attribution**：从威胁报告中的行为/漏洞描述归因到正式 taxonomy，例如 ATT&CK technique 或 CWE。
- **Multi-Document Synthesis**：跨多篇报告综合 actor profile、malware lineage 或 campaign storyline。
- **Evidence utilization**：模型拿到正确证据后是否能正确使用，而不是只看检索是否命中。

### 技术路线

- CTIConnect 将 RAG 从“一个检索器 + 一个生成器”推进到“按任务路由的 retrieval architecture”。
- 其核心洞察是：不同 CTI 任务的语义鸿沟不同，因此 retrieval strategy 也应不同。
- 对我的研究而言，CTIConnect 提供三个很重要的桥：
  - CTI structured KB 与 unstructured reports 的桥；
  - report-level evidence 与 campaign/actor profiling 的桥；
  - retrieval accuracy 与 evidence utilization 的评价桥。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| heterogeneous CTI | 异构网络威胁情报 |  |
| cross-source semantic gap | 跨源语义鸿沟 | CTIConnect 核心问题 |
| Entity Linking | 实体链接 | structured -> structured |
| Entity Attribution | 实体归因 | unstructured -> structured |
| Multi-Document Synthesis | 多文档综合 | unstructured -> unstructured |
| Extract-then-Retrieve | 先抽取后检索 | EtR |
| Decompose-then-Retrieve | 先分解后检索 | DtR |
| CSKG-Guided RAG | 网络安全知识图谱引导 RAG |  |
| evidence utilization | 证据利用 | 取得证据后能否正确推理 |
| campaign storyline construction | 攻击活动故事线构建 | CSC |

## 8. 优点

- 非常贴近真实 CTI 工作：同时覆盖结构化标准库和厂商报告。
- 比 CTIBench 和 SEvenLLM 更明确地评估 RAG setting。
- 任务分类清晰，能解释为什么不同检索策略适合不同任务。
- 对 LLM-as-a-judge 做了可靠性验证，不是直接相信自动裁判。
- 引入 temporal split，考虑 CTI 的时间演化。
- Magniber case study 很好地说明跨源关联的实战价值。

## 9. 局限

- 本地 PDF 标注为 KDD 2026，正式出版状态需要后续核验。
- 虽然覆盖 heterogeneous CTI，但还没有纳入系统日志、provenance graph、EDR/SOC telemetry。
- 主要评估 QA 形式，不等价于完整攻击调查工作流。
- MDS 依赖 LLM judge，尽管做了验证，仍可能存在裁判模型偏差。
- DS retrieval 是很强的任务定制策略，部署时需要可靠 task routing。
- 对攻击意图识别没有专门标签体系。

## 10. 对我选题的启发

- 可以直接借鉴：
  - 任务路由思想：不同 CTI/溯源任务使用不同检索策略。
  - heterogeneous CTI 源整合方式。
  - evidence utilization 分析。
  - temporal split 和 LLM-as-a-judge reliability check。
- 可以改进：
  - 将 CTIConnect 的 CTI 源扩展到 provenance graph / InfoPath / attack summary graph。
  - 在 TAP / CSC / ATA 任务上加入 attack intent 层。
  - 将 retrieved evidence 从报告/KB 扩展为报告句子 + ATT&CK 节点 + 日志路径。
  - 结合 LLM unreliable 的 consistency/calibration 指标，评估 RAG 是否提升可信度。
- 可以作为 baseline：
  - Vanilla RAG；
  - retrieve-then-rerank；
  - IRCoT；
  - EtR / DtR / CSKG-guided RAG。
- 可以用于研究动机：
  - 仅靠通用 RAG 不足以解决 CTI 跨源语义鸿沟；威胁归因/溯源融合需要结构化干预和证据对齐。
- 可以用于实验设计：
  - 可考虑把未来选题的任务定义为：
    `CTI report + ATT&CK/CVE/CWE/CAPEC + provenance evidence -> intent / actor candidate / evidence chain`

## 11. 可转化的研究问题

1. 能否将 CTIConnect 的 heterogeneous CTI RAG 扩展到 `CTI reports + provenance graph` 的双源证据融合？
2. 对 threat actor profiling 和 campaign storyline construction，加入日志侧 InfoPath 是否能提升 evidence utilization？
3. 不同任务是否应动态选择不同检索策略，例如 TTP 标注用 DtR，归因解释用 CSKG + provenance evidence？
4. 能否设计一个面向攻击意图识别的 `Multi-Source Synthesis` 任务，融合 ATT&CK、CTI 报告和日志摘要？
5. RAG 提升的是 retrieval accuracy，还是也能提升 consistency、calibration 和证据充分性？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CTIBench | CTIBench 是 closed-book CTI benchmark；CTIConnect 是 retrieval-augmented CTI benchmark |
| SEvenLLM | SEvenLLM 是指令微调与单报告任务；CTIConnect 是异构知识源检索 |
| TechniqueRAG | TechniqueRAG 聚焦 ATT&CK technique annotation；CTIConnect 覆盖更广的跨源 RAG 任务 |
| TTPXHunter | TTPXHunter 是 TTP 抽取强基线；CTIConnect 的 ATA/ATD 可评估更广泛 technique attribution |
| LLM unreliable | CTIConnect 解决 retrieval setting；仍应补 consistency 和 calibration 评价 |
| Kairos / DEPCOMM | Kairos/DEPCOMM 是日志侧证据压缩；CTIConnect 可作为 CTI 侧检索架构参考 |
| Beyond RAG for CTI | 后续应比较 CTIConnect 的 DS retrieval 与 GraphRAG/agentic retrieval |

## 13. 论文写作可引用句式

- CTI 的知识生态天然异构，结构化知识库和非结构化威胁报告之间存在显著跨源语义鸿沟。
- 生产级 LLM-CTI 系统不能仅依赖参数化知识，而需要在推理时检索并整合外部知识源。
- 通用 RAG 改进不足以弥合 CTI 跨源语义差距，任务类型决定了检索策略设计。
- 对威胁归因而言，关键不只是检索到证据，还包括模型能否正确利用证据形成可靠结论。

## 14. 我的批注与疑问

- 这篇非常贴合当前调整后的主线：大模型与现有 CTI/KG/RAG 方法融合。
- 它再次证明“我用了 RAG”不是创新，关键是异构源、任务路由、证据利用和评价。
- 它没有加入 provenance graph，正好给我的潜在方向留下空间。
- 后续读 Beyond RAG for CTI 时，要重点比较：GraphRAG 是否比 CTIConnect 的 CSKG-Guided RAG 更适合跨源证据链。
- 最终撞题检索时要核验 CTIConnect、CTINexus、TTPrint 等同组最新工作，避免选题撞上 Peng Gao / Dawn Song 这条线。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
