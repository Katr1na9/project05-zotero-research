# Multi-Step LLM Pipeline for Enhancing TTP Extraction in Cyber Threat Intelligence

## 1. 基本信息

- 英文题名：Multi-Step LLM Pipeline for Enhancing TTP Extraction in Cyber Threat Intelligence
- 中文译名：用于增强网络威胁情报中 TTP 抽取的多步骤大语言模型流水线
- 作者：Hyoung Rok Kim; Donghyeon Lee; Insup Lee; Soohan Lee; Sangjin Lee
- 年份：2025
- Venue：IEEE Access, Vol. 13, pp. 179696-179710
- DOI / arXiv / URL：10.1109/ACCESS.2025.3622350；https://ieeexplore.ieee.org/document/11205489
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：重点读
- 所属主题：LLM-CTI / ATT&CK-KG-RAG / TTP Extraction / Baseline

## 2. 一句话总结

这篇论文提出一个三阶段 LLM + embedding pipeline，用于从非结构化 CTI 文档中抽取 MITRE ATT&CK technique。它先用 LLM 把复杂 CTI 文本拆成单技术对应的 atomic threat actions，再用 embedding 检索 ATT&CK procedure 候选，最后用 LLM Validator 对候选 technique 排序和过滤，最终在 benchmark 上达到 82.28% F1。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 大量 CTI 文档是非结构化文本，而安全运营需要结构化 TTP / ATT&CK technique。
  - 传统 ontology / graph similarity 方法容易丢失上下文或产生低精度匹配。
  - 分类器方法依赖固定标签空间、阈值和训练数据，ATT&CK 更新后维护成本高。
  - 单 LLM 直接生成 technique 容易幻觉和 false positives。
- 这个问题为什么重要？
  - TTP 是 CTI 结构化、攻击链分析、威胁狩猎和后续归因推理的中间层。
  - 如果 TTP 抽取漏标或误标，后续 intent recognition、evidence chain 和 actor attribution 都会受影响。
- 之前方法哪里不够？
  - AttacKG 图模板匹配 recall 高但 precision 低，容易过抽。
  - LADDER 将行为和高层 technique 描述比对，存在语义粒度不匹配。
  - TTPXHunter / SecureBERT 分类器在跨数据集和 ATT&CK 更新场景下需要阈值调整或重训。
  - 单 prompt LLM 对多标签句子处理不足，且缺少候选约束。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 它处于 `CTI 文本 -> ATT&CK technique` 层。
  - 它不做 attack intent、actor attribution、evidence sufficiency 或 provenance evidence 对齐。
  - 对当前 Project05 主线而言，它是 TTP 抽取强基线，进一步证明创新不能停在 technique extraction。

## 4. 核心贡献

1. 方法贡献：提出 `Extractor -> Technique Candidate Generator -> Validator` 三阶段 TTP 抽取流水线。
2. LLM 使用贡献：用 LLM 将复杂 CTI 描述拆成 atomic threat actions，每条动作尽量对应一个 ATT&CK technique。
3. 检索贡献：构建基于 MITRE ATT&CK procedure 的 embedding knowledge base，用语义相似度召回候选 technique。
4. 验证贡献：用 LLM Validator 对候选 technique 进行 likelihood ranking 和过滤，降低单 LLM 直接生成的幻觉。
5. 实验贡献：与 TTPXHunter、Finetuned-SecureBERT、AttacKG、LADDER、ChatGPT-4o 单模型 baseline 比较，报告最高 F1。
6. 可维护性贡献：相较分类器，ATT&CK 更新时只需更新 STIX/knowledge base，不必重新训练完整分类器。

## 5. 方法框架

### 输入

- 数据类型：
  - CTI 文档；
  - malware / adversary behavior description；
  - MITRE ATT&CK STIX knowledge base；
  - ATT&CK procedure examples。
- 输入格式：
  - 原始 CTI 段落或报告；
  - procedure-level threat actions；
  - technique candidate IDs。
- 先验知识：
  - MITRE ATT&CK technique / procedure；
  - sentence embedding model；
  - ChatGPT-4o 或其他 LLM。

### 输出

- 预测结果：
  - MITRE ATT&CK main technique IDs。
- 图结构：
  - 无显式图结构。
- 标签：
  - main technique ID；实验不评估 sub-technique。
- 报告：
  - 无完整调查报告。
- 证据链：
  - 原文 threat action -> candidate procedure/technique -> validator ranking，可作为弱证据链。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Extractor | 用 LLM 从 CTI 文本中抽取 attack-relevant sentences，并把多技术句拆成 atomic threat actions | 可作为后续 intent/evidence pipeline 的文本侧预处理 |
| Technique Candidate Generator | 将 extracted action 嵌入到 ATT&CK procedure embedding space，召回 top-k candidate techniques | 用检索约束 LLM 输出，降低开放式生成幻觉 |
| Validator | 用 LLM 对候选 technique 按上下文相关性排序并输出最终 technique IDs | 类似人工验证，可提升 precision |
| MITRE ATT&CK Knowledge Base | 以 STIX/procedure examples 维护候选技术库 | ATT&CK 更新时可替换知识库，不必重训分类器 |
| Ablation Pipeline | 分析 Extractor、Candidate Generator、Validator 各自贡献 | 对后续方法论文的消融设计有参考价值 |

### 方法流程

```text
Raw CTI text
  -> Extractor: split into atomic threat actions
  -> Embed each threat action
  -> Technique Candidate Generator: retrieve top-k similar ATT&CK procedures / technique IDs
  -> Validator: rank and filter candidate techniques
  -> Final MITRE ATT&CK technique IDs
```

## 6. 数据集与实验

- 数据集：
  - 作者构建的 benchmark dataset。
  - 基于 MITRE ATT&CK v15.1，强调文本中的 technique IDs 都被显式标注。
  - evaluation corpus 中包含 77 个 unique techniques。
- 数据规模：
  - 消融中 Extractor 分析使用 46 个 documents。
  - technique candidate coverage 分析中，77 个 unique techniques 中 75 个被候选集覆盖，coverage 为 97.40%。
  - knowledge base 涉及 192 个 main techniques。
- 标注方式：
  - 论文强调其 benchmark 通过合成 TTP-labeled sentences 保证标注完整和一致。
  - 只评价 main technique，不评价 sub-technique。
- Baseline：
  - TTPXHunter；
  - Finetuned-SecureBERT；
  - AttacKG；
  - LADDER；
  - ChatGPT-4o single LLM baseline。
- 指标：
  - Precision；
  - Recall；
  - F1；
  - hit@k；
  - precision@k；
  - FPH，precision@k 与 hit@k 的调和均值；
  - technique coverage。
- 主要结果：
  - TTPXHunter：Precision 70.73，Recall 49.65，F1 58.35。
  - Finetuned-SecureBERT：Precision 65.02，Recall 54.11，F1 59.06。
  - AttacKG：Precision 9.75，Recall 76.36，F1 17.29。
  - LADDER：Precision 48.12，Recall 26.36，F1 34.07。
  - ChatGPT-4o：Precision 57.70，Recall 70.42，F1 70.56。
  - 作者框架：Precision 86.14，Recall 78.76，F1 82.28。
  - Candidate Generator 的 hit@1 为 0.69，hit@5 为 0.86，作者选择 top-5 作为候选集。
- 消融实验：
  - Extractor：
    - Expert Extraction：Precision 80.37，Recall 74.31，F1 77.22。
    - Direct Extraction Prompt：Precision 91.62，Recall 59.93，F1 72.46。
    - Atomic Reconstruction Prompt：Precision 86.14，Recall 78.76，F1 82.28。
  - Candidate Generator：
    - `Extractor + LLM` recall 66.09。
    - `Extractor + Technique Candidate Generator` recall 97.26。
  - Validator：
    - Without Validator：Precision 68.77，Recall 97.26，F1 80.57。
    - Validator non-ranking：Precision 79.60，Recall 68.15，F1 73.43。
    - Validator ranking：Precision 86.14，Recall 78.76，F1 82.28。
- Case study：
  - 4H RAT 示例中，Extractor 将一段 malware 描述拆成多条 threat action，例如 C2 通信、remote shell 等，再交给候选检索和验证。

## 7. 关键知识点

### 概念

- **Atomic threat action**：从 CTI 文本中拆出的、尽量只对应一个 ATT&CK technique 的攻击行为句。
- **Technique Candidate Generator**：基于 procedure embedding 召回候选 ATT&CK technique 的模块。
- **Validator**：对候选 technique 进行上下文判断、排序和过滤的 LLM 模块。
- **hit@k**：top-k 候选中是否包含正确 technique。
- **FPH**：precision@k 与 hit@k 的 harmonic mean，用于选择候选数量 k。

### 技术路线

- 论文使用 LLM 的语义拆解能力，但不让 LLM 完全开放式生成 technique。
- 关键设计是先召回候选，再让 LLM 在候选集合内验证：
  - retrieval 负责 coverage；
  - validator 负责 precision；
  - atomic extraction 负责把多技术文本拆到合适粒度。
- 这条路线和 TechniqueRAG 非常接近：
  - TechniqueRAG 是 retriever + LLM re-ranker + generator；
  - 本文是 LLM extractor + embedding candidate generator + LLM validator。
- 两者共同说明：`CTI -> ATT&CK technique` 已经是成熟且竞争激烈的中间任务。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| threat action | 威胁动作 / 攻击行为句 | 可作为 TTP 映射输入 |
| atomic threat action | 原子威胁动作 | 一条动作尽量对应一个 technique |
| Technique Candidate Generator | 技术候选生成器 | 召回候选 ATT&CK technique |
| Validator | 验证器 | 用 LLM 排序和过滤候选技术 |
| hit@k | Hit@k | top-k 候选覆盖正确标签 |
| procedure embedding | 过程示例嵌入 | ATT&CK procedure examples 的向量表示 |

## 8. 优点

- 模块设计清楚，适合做 baseline 或前置 TTP 抽取模块。
- Atomic reconstruction 很有价值，解决 CTI 句子中多个 technique 混在一起的问题。
- Candidate Generator 用候选约束降低 LLM 直接生成的幻觉。
- Validator ranking prompt 在 precision 和 recall 之间取得较好平衡。
- 与 AttacKG、TTPXHunter、LADDER、单 LLM baseline 均做了比较，实验定位清晰。
- ATT&CK 更新时可更新 knowledge base，维护性优于固定分类器。

## 9. 局限

- 仍然只做 main technique extraction，不做 sub-technique、tactic/intent、actor attribution 或证据充分性判断。
- Benchmark 基于合成 TTP-labeled sentences，和真实长篇 CTI 报告仍有差距。
- 使用 ChatGPT-4o 和 OpenAI embedding，成本、复现性和离线部署存在约束。
- Validator 提升 precision 的同时会删除部分正确 technique，false negatives 仍存在。
- 候选覆盖依赖 ATT&CK procedure examples 的丰富度；低频 technique 如 T1111、T1217 可能漏召回。
- 没有评估 consistency、calibration、unanswerable handling 或 provenance evidence。

## 10. 对我选题的启发

- 可以直接借鉴：
  - `atomic threat action -> candidate retrieval -> validator ranking` 作为文本侧 TTP 抽取模块。
  - 用候选约束缓解 LLM hallucination。
  - 用 hit@k / candidate coverage 分析检索模块是否漏掉可能答案。
  - 用 ranking Validator 模拟专家确认。
- 可以改进：
  - 在 TTP 抽取后增加 tactic / intent layer。
  - 将 Validator 从“选择 technique”扩展为“判断证据是否足以支撑 intent / actor attribution”。
  - 将输入从 CTI 文本扩展为 `CTI text + provenance InfoPath / attack summary graph`。
  - 加入 consistency、calibration 和 refusal correctness。
- 可以作为 baseline：
  - TTP extraction baseline；
  - text-side ATT&CK annotation module；
  - 和 TechniqueRAG、TTPXHunter、AttacKG 放在同一相关工作小节。
- 可以用于研究动机：
  - TTP 抽取已经进入多阶段 LLM + retrieval 的成熟阶段，硕士选题不能只做 technique extraction。
  - 真正缺口应继续上移到 intent、evidence sufficiency、uncertainty-aware attribution 和 CTI-log alignment。
- 可以用于实验设计：
  - 先用该类 pipeline 得到 technique candidate，再评价上层 intent/attribution 是否受 TTP 抽取错误影响。
  - 做 ablation：无 Validator / 有 Validator / evidence sufficiency Validator。

## 11. 可转化的研究问题

1. 能否将 Multi-Step LLM Pipeline 的 Validator 扩展为 evidence sufficiency validator，用于判断 TTP 是否足以支持 intent 或 actor attribution？
2. Atomic threat action 是否可以和 DEPCOMM InfoPath / Kairos attack summary graph 对齐，形成 text-action 与 log-action 的统一中间表示？
3. 当 Candidate Generator 给出的候选 technique 覆盖不足时，系统应如何触发拒答或补充检索？
4. 在 TTP 抽取模块之后，如何构建 `technique -> tactic/intent -> actor PMF` 的分层可信推理？
5. 与 TechniqueRAG 相比，Extractor-first pipeline 是否更适合处理真实长篇 CTI 报告中的多技术句和隐式行为？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| TechniqueRAG | 都是 LLM/RAG 风格的 ATT&CK technique annotation；TechniqueRAG 偏 retriever/re-ranker/generator，本文偏 extractor/candidate/validator |
| TTPXHunter | TTPXHunter 是 SecureBERT 分类器路线，本文显示 LLM + retrieval 在 benchmark 上更强 |
| AttacKG | AttacKG 用图模板匹配，本文指出 similarity/graph 方法可能 recall 高但 precision 低 |
| LADDER | LADDER 做相似度匹配，但存在行为句和 technique 描述的语义粒度不匹配 |
| CTIBench | CTI-ATE 可作为 technique extraction 评测任务地图 |
| LLMs are Unreliable for CTI | 本文用 retrieval/validator 缓解幻觉，但仍未评估真实长度报告、校准和一致性 |
| High Stakes, Low Certainty | 本文抽 TTP，High Stakes 提醒 TTP 不等于可靠 actor attribution evidence |
| Kairos / DEPCOMM | 可将本文的 atomic threat action 思路迁移到日志侧 summary graph / InfoPath 的语义化 |

## 13. 论文写作可引用句式

- 多步骤 LLM 流水线可以通过先抽取原子攻击行为、再召回候选技术、最后验证候选技术的方式提升 ATT&CK technique extraction 的精度与召回。
- 对开放式 LLM 生成进行候选约束，是缓解 TTP 抽取幻觉和 false positives 的有效工程策略。
- TTP 抽取虽然是 CTI 结构化的重要前置任务，但其输出仍停留在 technique layer，不能直接替代攻击意图识别或威胁行为体归因。

## 14. 我的批注与疑问

- 这篇和 TechniqueRAG 基本把“LLM/RAG 做 ATT&CK technique extraction”这条线压得很实了。
- 对我的方向，它更像一个可复用文本侧模块，而不是主创新。
- Atomic threat action 很适合作为统一中间表示的元素，但 `High Stakes` 提醒不能把它直接升级为 actor evidence。
- 需要后续比较：TechniqueRAG 的 retrieved exemplars 与本文的 candidate procedures，哪个更适合后续 evidence citation。
- 如果未来做系统，可把本文 pipeline 的最后一层 Validator 改造成多级：
  - technique validator；
  - intent validator；
  - evidence sufficiency validator；
  - attribution confidence validator。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是，但定位为 TTP extraction baseline，不作为最终创新点
