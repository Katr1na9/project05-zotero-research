# TECHNIQUERAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text

## 1. 基本信息

- 英文题名：TECHNIQUERAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text
- 中文译名：TechniqueRAG：面向网络威胁情报文本中对抗技术标注的检索增强生成方法
- 作者：Ahmed Lekssays; Utsav Shukla; Husrev Taha Sencar; Md Rizwan Parvez
- 年份：2025
- Venue：Findings of ACL 2025 / arXiv
- DOI / arXiv / URL：10.18653/v1/2025.findings-acl.1076 / arXiv:2505.11988
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：ATT&CK-KG-RAG / LLM-CTI / TTP Annotation

## 2. 一句话总结

TechniqueRAG 解决的是 CTI 文本到 MITRE ATT&CK technique / sub-technique 的自动标注问题。它用 off-the-shelf retriever 召回相似 text-technique 样例，再用 LLM re-ranker 重排候选，最后用微调后的 generator 输出 technique IDs，从而在少量标注数据下提升 ATT&CK 技术标注效果。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 将安全文本或 CTI 片段自动映射到 MITRE ATT&CK technique / sub-technique。
- 这个问题为什么重要？
  - ATT&CK 标注是威胁情报结构化、安全调查、攻击链分析和检测规则生成的关键前置步骤。
  - 手工标注依赖专家知识，耗时且不稳定。
- 之前方法哪里不够？
  - 分类方法需要大量平衡标注数据，难以覆盖 500+ ATT&CK techniques/sub-techniques。
  - 纯 retrieval/ranking 方法容易受语义相似度噪声影响。
  - 纯 LLM 方法存在幻觉、过度生成和细粒度 technique 混淆。
  - 训练专门 retriever 往往需要 hard negatives、denoising data 或大规模任务数据。
- 它和我的方向的关系是什么？
  - 它是“CTI 文本 -> ATT&CK 技术标签”的当前强 baseline。
  - 如果后续做攻击意图识别，TechniqueRAG 解决的是 technique 层；我的潜在创新必须在 intent、evidence grounding、uncertainty 或 CTI-log alignment 上继续向上/向外扩展。

## 4. 核心贡献

1. 提出 TechniqueRAG，将 off-the-shelf retriever、LLM-based re-ranker 和 fine-tuned generator 组合起来做 ATT&CK technique annotation。
2. 设计安全领域 re-ranking prompt，让 LLM 显式分解攻击步骤、识别显式/隐式行为，并区分 technique 与 sub-technique。
3. 在 TRAM、Procedures、Expert 三类数据集上评估，覆盖 single-label 与 multi-label 场景。
4. 通过错误分析指出当前 ATT&CK 标注的主要难点：under-prediction、相似 technique 混淆、隐式技术漏标、类别不平衡和标注不一致。

## 5. 方法框架

### 输入

- 数据类型：安全文本、CTI 句子、攻击行为描述。
- 输入格式：一段 security text `xq`。
- 先验知识：
  - MITRE ATT&CK technique / sub-technique ID 集合；
  - 少量 text-technique 标注样例；
  - retriever 的检索语料；
  - instruction-tuned LLM。

### 输出

- 预测结果：一个或多个 ATT&CK technique / sub-technique IDs。
- 图结构：无显式图结构。
- 标签：MITRE ATT&CK technique/sub-technique。
- 报告：无完整调查报告。
- 证据链：主要通过 retrieved exemplars 和 re-ranker reasoning 间接提供，不是严格证据链。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Retriever | 从标注样例中召回与查询文本相似的 text-technique pairs | 不训练复杂 retriever，降低数据需求 |
| LLM-based Re-ranker | 对召回候选进行安全领域推理式重排 | 显式分解攻击步骤，区分显式行为和隐式行为 |
| Generator | 基于查询文本和重排样例生成 technique IDs | 少量样例微调生成器，缓解纯 LLM 幻觉 |
| Domain Prompt | 指导 LLM 进行 technique/sub-technique 相关性分析 | 可改造成“意图识别 prompt”或“证据充分性 prompt” |

### 方法流程

```text
Security text / CTI sentence
  ↓
Retriever：召回 top-K 相似 text-technique pairs
  ↓
LLM-based re-ranker：按攻击步骤、显式/隐式行为、sub-technique 粒度重排
  ↓
选择 top-k exemplars 拼接为 generator context
  ↓
Fine-tuned generator
  ↓
ATT&CK technique / sub-technique IDs
```

## 6. 数据集与实验

- 数据集：
  - TRAM；
  - MITRE Procedures；
  - Expert split。
- 数据规模：
  - TRAM：约 4,797 texts，193 technique/sub-technique，平均 1.16 labels；
  - Procedures：约 11,723 texts，488 technique/sub-technique，平均 1.00 labels；
  - Expert：约 695 texts，290 technique/sub-technique，平均 1.84 labels；
  - 训练集覆盖约 499 unique techniques，约为 ATT&CK Enterprise 中 637 techniques 的 78%。
- 标注方式：
  - TRAM 和 Procedures 偏 single-label；
  - Expert 来自真实威胁情报报告句子，偏 multi-label。
- Baseline：
  - classification methods；
  - retrieval/ranking methods；
  - zero-shot LLM；
  - CoT/self-reflection prompt；
  - vanilla RAG；
  - prior methods such as AttacKG、LADDER、NCE、Text2TTP、IntelEX。
- 指标：
  - Precision；
  - Recall；
  - F1；
  - technique-level 与 sub-technique-level 分开评价。
- 主要结果：
  - TechniqueRAG 在多个数据集上超过 zero-shot 与普通 prompt/RAG 变体。
  - 在 Procedures 数据上效果最好，因为句子更接近单一 technique 描述。
  - 在 Expert 数据上 recall 较低，原因是 Expert 多为 multi-label，且真实报告中的 technique 往往隐式表达。
- 消融实验：
  - 比较 zero-shot、CoT/reflection、TechniqueRAG 等 domain adaptation 方式。
  - 讨论 re-ranker 对 generator 的误差传播。
- Case study：
  - 论文展示 PowerShell、scheduled task、SSH private key、Monero miner 等例子，说明 RAG 能帮助模型召回正确 technique，但也会引入不相关 technique。

## 7. 关键知识点

### 概念

- ATT&CK technique annotation 是把非结构化安全文本映射为标准化 TTP 标签的任务。
- Technique 与 sub-technique 的细粒度区分是难点，例如 T1059 和 T1059.001。
- 真实 CTI 文本往往是 multi-label，且技术行为可能隐式表达。

### 技术路线

- 不直接训练大型分类器，而是将任务拆成：
  - retrieval；
  - LLM re-ranking；
  - generation。
- 用 LLM 的推理能力提升候选排序，但避免让 LLM 完全开放式生成。
- 用少量标注样例微调 generator，而不是端到端训练整个 RAG 系统。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| adversarial technique annotation | 对抗技术标注 / ATT&CK 技术标注 | 本文核心任务 |
| text-technique pair | 文本-技术标注对 | 检索语料基本单元 |
| re-ranker | 重排序器 | 用 LLM 重新排列候选技术 |
| off-the-shelf retriever | 现成检索器 | 不做领域训练 |
| sub-technique | 子技术 | ATT&CK 层级 |
| under-prediction | 漏标 / 欠预测 | 多标签场景下常见 |

## 8. 优点

- 紧贴 CTI + ATT&CK 主线，是当前 TTP 标注方向的重要 baseline。
- 方法设计现实：不依赖大规模标注数据，也不要求训练复杂 retriever。
- 显式使用 LLM re-ranking，能把安全专家式推理注入检索过程。
- 错误分析很有价值，尤其是 multi-label 漏标、隐式 technique 漏识别和标注不一致。
- 对后续做 RAG/GraphRAG/Agentic RAG 的实验设计有直接参考意义。

## 9. 局限

- 主要输出 ATT&CK technique IDs，不输出攻击意图、攻击阶段解释或归因结论。
- evidence grounding 不够严格；retrieved exemplars 不是原文证据链。
- 对 multi-label Expert 数据 recall 偏弱，说明真实 CTI 复杂句中的隐式行为仍难处理。
- 如果 re-ranker 漏掉关键 technique，generator 会继承错误。
- 只处理文本，不处理日志侧 provenance graph、attack summary graph 或多源证据对齐。

## 10. 对我选题的启发

- 可以直接借鉴：
  - `retriever -> LLM re-ranker -> generator` 三段式架构；
  - 显式分解攻击步骤的 re-ranking prompt；
  - technique-level / sub-technique-level 分层评价；
  - under-prediction、similar technique confusion、annotation inconsistency 的错误分析框架。
- 可以改进：
  - 在 technique annotation 之后增加 tactic / intent layer；
  - 将 retrieved exemplars 替换或扩展为 CTI 原文证据句和 provenance graph 边；
  - 增加 evidence sufficiency 和 confidence calibration；
  - 将输入从 security text 扩展为 `security text + attack summary graph serialization`。
- 可以作为 baseline：
  - 如果我的方法做 ATT&CK 标注，TechniqueRAG 是强 baseline；
  - 如果我的方法做 intent recognition，可把 TechniqueRAG 输出作为中间输入。
- 可以用于研究动机：
  - 当前 RAG 已能较好做 technique annotation，但仍缺少意图层、证据链和不确定性机制。
- 可以用于实验设计：
  - 用 TRAM / Procedures / Expert 数据测试 technique annotation；
  - 自建小规模 intent labels 时，可复用其 text-technique pairs 作为基础。

## 11. 可转化的研究问题

1. 在 TechniqueRAG 输出的 ATT&CK techniques 基础上，如何进一步推断攻击意图，并给出证据句？
2. 如果输入不是 CTI 文本，而是 Kairos/DEPCOMM 产生的 attack summary graph，TechniqueRAG 是否仍能有效做 ATT&CK 标注？
3. 如何判断 RAG 检索到的 technique exemplars 是否足以支撑某个 technique / intent 结论？
4. 如何让模型在 evidence insufficient 时输出低置信度或拒答，而不是强行标注？
5. TechniqueRAG 的 under-prediction 是否可以通过 attack-chain context 或 provenance evidence 缓解？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AttacKG | AttacKG 用 KG alignment 做 technique identification；TechniqueRAG 用 RAG + LLM re-ranking 做 technique annotation |
| TTPXHunter | 都做 TTP/ATT&CK 抽取；TTPXHunter 更偏模型和数据增强，TechniqueRAG 更偏 RAG 架构 |
| EXTRACTOR | EXTRACTOR 输出 provenance graph；TechniqueRAG 输出 ATT&CK technique，可考虑将 EXTRACTOR 图作为输入上下文 |
| Kairos | Kairos 输出日志侧 attack summary graph；TechniqueRAG 可启发如何把摘要图映射到 ATT&CK |
| CTIBench | CTIBench 评测 LLM 的 CTI 能力；TechniqueRAG 是具体方法 |
| Large Language Models are Unreliable for CTI | TechniqueRAG 试图通过检索和样例降低幻觉，但仍需可靠性评价 |
| IntelEX / Text2TTP / NCE / LADDER | TechniqueRAG 的主要对比和前序技术路线 |

## 13. 论文写作可引用句式

- ATT&CK technique annotation 是 CTI 结构化和攻击行为理解的重要前置任务，但现有方法在数据稀缺、细粒度 technique 区分和多标签真实报告场景中仍面临挑战。
- RAG 能缓解开放式 LLM 的幻觉问题，但检索候选的噪声和领域相关性不足仍会影响最终标注质量。
- 将安全领域推理注入 re-ranking 阶段，可以在不训练复杂 retriever 的情况下提升技术标注的领域精度。
- Technique-level annotation 并不等同于 attack intent recognition；后者还需要攻击阶段、上下文证据和不确定性建模。

## 14. 我的批注与疑问

- 这篇论文基本堵住了“我用 RAG 做 ATT&CK 标注”这个简单选题，因此不能把 TechniqueRAG 换个模型复现当创新。
- 但它留下了三个空间：
  - technique -> tactic/intent；
  - text evidence -> evidence chain；
  - CTI text -> provenance graph / attack summary graph 的跨模态输入。
- Expert 数据上 recall 低这一点很有启发：真实威胁报告中的多标签、隐式行为和长上下文，正是意图识别容易出问题的地方。
- 需要后续查重：
  - 是否已有论文专门做 ATT&CK technique 到 attack intent 的 RAG/LLM 推理；
  - 是否已有论文把 provenance graph summary 输入 LLM 做 ATT&CK 标注；
  - 是否已有 benchmark 评估 evidence-grounded intent recognition。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

