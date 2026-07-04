# Beyond RAG for Cyber Threat Intelligence: A Systematic Evaluation of Graph-Based and Agentic Retrieval

## 1. 基本信息

- 英文题名：Beyond RAG for Cyber Threat Intelligence: A Systematic Evaluation of Graph-Based and Agentic Retrieval
- 中文译名：超越 RAG 的网络威胁情报：基于图与智能体式检索的系统评估
- 作者：Dzenan Hamzic; Florian Skopik; Max Landauer; Markus Wurzenberger; Andreas Rauber
- 年份：2026
- Venue：arXiv preprint / Manuscript submitted to ACM，正式会议与 DOI 待核验
- DOI / arXiv / URL：https://arxiv.org/abs/2604.11419
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：重点读
- 所属主题：LLM-CTI / GraphRAG / HybridRAG / Evidence Retrieval / Trustworthy Attribution

## 2. 一句话总结

这篇论文系统比较了语义向量 RAG、GraphRAG、Agentic GraphRAG 和 HybridRAG 在 CTI 问答中的表现，说明图结构确实有助于多跳威胁情报推理，但单纯 GraphRAG 会带来结构性幻觉、拒答失败和延迟不稳定；对我的主线而言，它的价值是为“LLM 增强威胁溯源/归因”提供了证据检索架构和可信失败模式分析。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 在 CTI 场景下，传统向量 RAG 很难回答需要跨实体、跨报告、多跳关系推理的问题。
  - GraphRAG、Agentic GraphRAG、HybridRAG 等新检索范式不断出现，但缺少在同一 CTI 数据、同一模型和同一评价协议下的系统比较。
  - 论文关注的不只是平均答案质量，还包括不可回答问题上的拒答能力、延迟稳定性和高风险失败模式。
- 这个问题为什么重要？
  - 威胁归因和安全调查常需要把 threat actor、malware、vulnerability、campaign、victim、sector 等实体串成证据链。
  - 如果检索系统漏掉关键证据，LLM 可能生成自信但错误的归因解释。
  - 如果图查询失败或图结构不完整，GraphRAG 可能把“没有证据”误当成“可推断答案”，这对高风险 CTI/SOC 决策很危险。
- 之前方法哪里不够？
  - 向量 RAG 擅长局部语义匹配，但不擅长显式关系遍历和多跳聚合。
  - GraphRAG 理论上能做关系推理，但依赖 text-to-Cypher、图 schema 覆盖和查询执行稳定性。
  - Agentic correction 可以修复部分图查询错误，但可能带来延迟和复杂度。
  - 现有论文常提出单一系统，缺少对不同检索架构失败模式的可控比较。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 与威胁归因：它不直接输出 actor attribution，但提供 actor/malware/vulnerability/campaign 关系证据的检索和问答底座。
  - 与攻击链：multi-hop QA 可近似表示攻击链中的关系跳转，例如 actor -> uses malware -> targets sector。
  - 与意图识别：论文没有专门的 intent taxonomy，但 guided analyst-style questions 可作为上层分析任务雏形。
  - 与 CTI/RAG/KG：这是本文核心，重点在 CTI reports -> KG -> graph retrieval / hybrid retrieval。
  - 与 Agent：这里只把 agentic 作为 query repair 机制，而不是完整多智能体安全调查系统；对当前主线应作为检索可靠性模块，而不是研究中心。

## 4. 核心贡献

1. 任务贡献：构建 3,300 个 CTI QA pairs，覆盖 simple、single-hop、multi-hop、guided analyst-style 和 unanswerable 五类问题。
2. 方法比较贡献：在同一 CTI 知识库和同一评价协议下比较 RAG、GRAG、AGRAG、HRAG 四种检索架构。
3. 实验贡献：用五个 LLM 对四类系统进行重复评估，评价答案质量、自动指标、拒答能力和运行时间。
4. 失败模式贡献：指出 GraphRAG 不是无条件升级，图结构会引入 text-to-Cypher 错误、schema gap、结构性幻觉和延迟尖峰。
5. 系统设计贡献：提出可靠 CTI assistant 更适合使用 hybrid graph-text retrieval、bounded query repair 和 explicit abstention mechanism。

## 5. 方法框架

### 输入

- 数据类型：
  - CTINexus CTI reports。
  - 由 CTI 报告转换出的 Neo4j property graph。
  - 自动生成并验证的 CTI QA pairs。
- 输入格式：
  - 用户问题。
  - 文本块向量库。
  - Cypher 查询接口。
  - 图节点和边，例如 Malware、ThreatActor、Tool、Victim，以及 uses、targets、exploits 等关系。
- 先验知识：
  - CTI entity schema。
  - 图数据库 schema。
  - few-shot text-to-Cypher examples。

### 输出

- 预测结果：
  - CTI 问题答案。
  - 对不可回答问题的拒答。
- 图结构：
  - Neo4j property graph。
  - Cypher query results。
- 标签：
  - reference answer。
  - question type。
  - query provenance。
- 报告：
  - 不同系统的答案质量、失败模式和运行时间比较。
- 证据链：
  - RAG 返回的文本 evidence chunks。
  - GraphRAG 返回的图路径或查询结果。
  - HybridRAG 同时利用图结果和文本证据。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Semantic RAG | 基于文本 chunk 的向量检索 | 作为最小 baseline |
| GRAG | 将自然语言问题转为 Cypher 查询图数据库 | 适合结构化事实和多跳关系推理 |
| AGRAG | 对失败或不完整的 Cypher 查询做 critique-and-repair | 可借鉴为“有限修复”机制，而非完整 Agent 主线 |
| HRAG | 同时使用图查询和文本检索 | 对威胁归因证据链最有启发，能缓解 schema gap |
| LLM-as-a-Judge | 按 agreement、adequacy、faithfulness、clarity 打分 | 可用于后续评价归因解释质量 |
| Abstention Check | 衡量不可回答问题上是否正确拒答 | 可用于可信归因与证据不足场景 |

### 方法流程

```text
CTINexus CTI reports
  -> LLM text-to-graph extraction
  -> Cypher statements
  -> Neo4j property graph
  -> generate QA pairs from graph queries and guided prompts
  -> initialize four systems: RAG / GRAG / AGRAG / HRAG
  -> answer each question with five LLMs
  -> evaluate by LLM-as-a-Judge + classical metrics + abstention + latency
```

## 6. 数据集与实验

- 数据集：
  - 论文基于 CTINexus reports 抽样构造 CTI QA 数据。
- 数据规模：
  - 3,300 CTI question-answer pairs。
  - 15 sampled reports。
  - 10 repeated runs。
- 问题类型：
  - simple factual lookups。
  - single-hop relational queries。
  - multi-hop relational queries。
  - guided analyst-style synthesis questions。
  - unanswerable cases。
- 标注方式：
  - 从生成的 Cypher queries 派生 QA，保证答案存在于图和对应报告中。
  - guided questions 使用额外 prompt 生成，用于测试分析式综合。
  - unanswerable cases 用于测试拒答和过度自信。
- Baseline：
  - Semantic RAG。
  - Graph-only RAG。
  - Agentic GraphRAG。
  - Hybrid graph-text RAG。
- 指标：
  - LLM-as-a-Judge composite score。
  - agreement、adequacy、faithfulness、clarity。
  - F1、BLEU、ROUGE、BERTScore。
  - correct refusal / unsafe abstention。
  - runtime / latency stability。
- 主要结果：
  - AGRAG 和 HRAG 相比 RAG 有显著平均提升，GRAG 只有边际提升。
  - 在 simple、single-hop、multi-hop 上，图结构显著有利，尤其是 multi-hop。
  - 在 guided analyst-style questions 上，纯图系统表现较差，HRAG 更稳，因为这类问题需要结构化事实和上下文文本综合。
  - 在 unanswerable questions 上，图系统会暴露 schema gap 和拒答失败问题。
  - HRAG 在 multi-hop 问题上相比 vector RAG 的答案质量最高提升约 35%。
  - HRAG 的 near-zero failure rate 最低，论文报告从 GRAG 的 26.7% 降到 HRAG 的 4.8%。
  - 论文报告 HRAG correct refusal 达到 76%，而语义 RAG 为 0%。
  - Graph-only retrieval 可能出现最长 39 分钟的查询修复循环。
  - AGRAG 在某些场景下相对 GRAG 最高可实现 147 倍加速。

## 7. 关键知识点

### 概念

- **Graph grounding**：用显式图结构约束 LLM 的证据检索和关系推理。
- **Text-to-Cypher**：把自然语言 CTI 问题转换为图数据库查询。
- **Structural hallucination**：系统生成的答案在图查询输出层面看似合理，但由于图 schema 或图覆盖不完整，并不被底层原始报告支持。
- **Safe abstention**：当证据不足时，系统应明确拒答，而不是补全一个看似合理的答案。
- **Hybrid redundancy**：用图查询和文本检索互相补位，降低单一检索管线失效的风险。
- **Failure decorrelation**：不同检索架构失败的问题不完全重合，因此 ensemble 或 routing 有机会降低总体失败率。

### 技术路线

- 论文的关键结论不是“GraphRAG 一定更好”，而是：
  - 图适合结构化事实与多跳关系；
  - 文本适合上下文综合和 schema 外信息；
  - agentic repair 适合修复 text-to-query 错误；
  - hybrid retrieval 更适合高风险 CTI 工作流。
- 对我的主线来说，最佳启发是把图和文本都看作 attribution evidence 的不同载体：
  - CTI 报告句子提供叙事证据；
  - ATT&CK/KG 提供规范化语义证据；
  - provenance graph / InfoPath 提供本地可观测证据；
  - LLM 的任务是组合证据、说明不确定性，而不是凭空归因。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Semantic RAG | 语义 RAG / 向量 RAG | text chunk retrieval |
| GraphRAG | 图 RAG | 保留 GraphRAG 也可以 |
| Agentic GraphRAG | 智能体式 GraphRAG | 本文主要指查询修复 |
| HybridRAG | 混合 RAG | 图查询 + 文本检索 |
| text-to-Cypher | 文本到 Cypher 查询 | 图数据库查询生成 |
| graph grounding | 图 grounding / 图结构锚定 | 用结构化图约束推理 |
| structural hallucination | 结构性幻觉 | 图结构不完整导致的伪支撑 |
| unsafe abstention | 不安全拒答 / 拒答失败 | 证据不足仍然作答 |
| correct refusal | 正确拒答 | 证据不足时拒绝回答 |
| latency instability | 延迟不稳定 | 安全运营场景重要 |

## 8. 优点

- 不是提出单一 RAG 系统，而是在同一环境下比较四类检索架构，结论更适合方法选择。
- 明确评价 CTI assistant 的安全相关失败模式，而不是只看平均 QA 分数。
- 问题类型拆分很有启发：simple、single-hop、multi-hop、guided、unanswerable 可以迁移到后续归因任务设计。
- 对 GraphRAG 的风险判断非常重要：图不是越多越好，结构化系统也会产生新的幻觉。
- HRAG 的设计思路与未来“CTI 文本 + ATT&CK/KG + provenance evidence”多源归因解释高度契合。

## 9. 局限

- 论文使用自动生成 QA，未必完全覆盖真实分析师在威胁归因中的开放式调查问题。
- 数据来自单一 CTINexus 管线和受控图 schema，换成其他 CTI 报告或更稀疏图后结果可能不同。
- 它主要做 CTI 问答，不直接做 threat actor attribution、attack intent recognition 或 attack chain reconstruction。
- 它没有纳入系统审计日志、EDR telemetry、provenance graph 或本地组织上下文。
- Agentic 部分只是 query repair，不等于完整安全调查智能体。
- arXiv 版本的正式 venue 和 DOI 仍待核验，PDF 中 ACM 模板信息存在占位内容。

## 10. 对我选题的启发

- 可以直接借鉴：
  - 四类检索架构对比：RAG、GraphRAG、Agentic GraphRAG、HybridRAG。
  - 按问题类型分析收益，而不是只报告总分。
  - 把 unanswerable / insufficient evidence 作为可信系统必测项目。
  - 将 answer quality 拆为 agreement、adequacy、faithfulness、clarity。
- 可以改进：
  - 把 CTI KG 扩展为 `CTI reports + ATT&CK KG + provenance graph / InfoPath`。
  - 把 QA 扩展为 `evidence -> attack intent / attribution candidate / attribution explanation`。
  - 在归因任务中加入证据覆盖率、证据冲突、置信度校准和拒答能力。
- 可以作为 baseline：
  - Semantic RAG。
  - GraphRAG。
  - Agentic query repair。
  - HybridRAG。
- 可以用于研究动机：
  - “GraphRAG 不是银弹”：高风险 CTI/归因系统需要处理结构性幻觉和证据不足。
  - “混合证据检索”比单纯向量检索或单纯图检索更适合安全调查。
- 可以用于实验设计：
  - 问题类型：事实、单跳、多跳、分析式综合、不可回答。
  - 指标：答案正确性、证据忠实性、拒答率、延迟、校准。

## 11. 可转化的研究问题

1. 在威胁归因任务中，HybridRAG 是否比纯向量 RAG 或纯 GraphRAG 更能生成证据充分的 actor attribution explanation？
2. 能否将 `CTI report sentences + ATT&CK KG + provenance InfoPaths` 组织成多源证据图，让 LLM 进行攻击意图识别和归因候选排序？
3. 当 CTI 或日志证据不足时，如何让 LLM 可靠拒绝给出归因结论，并输出缺失证据清单？
4. GraphRAG 在威胁归因中会产生哪些结构性幻觉？这些幻觉是否可以通过原文 evidence grounding 和 graph-text cross-check 缓解？
5. 能否设计一个 attribution-oriented benchmark，覆盖 single-hop evidence、multi-hop attack chain、actor candidate、intent inference 和 unanswerable attribution？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CTIConnect | CTIConnect 关注异构 CTI RAG benchmark；本文进一步比较 GraphRAG、AGRAG、HRAG 的系统取舍 |
| LocalIntel | LocalIntel 引入组织本地知识；本文说明本地知识若结构化为图，也需要 hybrid retrieval 和拒答机制 |
| TechniqueRAG | TechniqueRAG 做 ATT&CK technique annotation；本文可作为更上层 evidence retrieval 架构参考 |
| CTIBench | CTIBench 是 LLM-CTI 能力评测；本文更聚焦 retrieval-augmented CTI QA |
| LLMs are Unreliable for CTI | 本文回应不可靠问题中的 grounding 和拒答，但仍需加入 consistency/calibration |
| Kairos / DEPCOMM | Kairos/DEPCOMM 提供日志侧 provenance evidence；本文提供把图证据和文本证据混合检索的架构依据 |
| AttacKG / EXTRACTOR | AttacKG/EXTRACTOR 负责从 CTI 文本构图；本文评估构图之后如何检索和问答 |

## 13. 论文写作可引用句式

- CTI 问题往往需要跨实体、跨文档和跨时间的多跳证据组合，因此单纯基于 top-k 文本块的向量 RAG 难以支撑高可信威胁归因。
- 图结构可以提升关系型 CTI 问题的检索和推理能力，但图 schema 不完整和 text-to-query 错误会引入新的结构性幻觉。
- 对威胁归因系统而言，可靠性不应只由平均回答分数衡量，还应包括证据不足时的拒答能力、延迟稳定性和失败模式可解释性。
- 混合图文本检索为多源威胁证据融合提供了可行路径，尤其适合同时利用 CTI 报告、ATT&CK 知识和本地 provenance evidence。

## 14. 我的批注与疑问

- 这篇不能把我的方向带偏到“Agent”，因为它的 agentic 只是 GraphRAG 的 query repair。真正值得留下的是 hybrid retrieval、schema gap 和拒答机制。
- 它和 CTIConnect 连在一起后，说明当前前沿已经做到“异构 CTI + RAG/GraphRAG benchmark”。我的创新若继续做 CTI-only RAG，很容易撞题。
- 更有空间的方向仍是：把 CTI/KG 侧证据与 Kairos/DEPCOMM 的 provenance evidence 融合，服务 attack intent / attribution explanation / confidence。
- 后续撞题检索要重点查：CTI GraphRAG、provenance graph RAG、threat attribution RAG、evidence-grounded attribution、uncertainty-aware CTI。
- 如果未来做系统，必须限制 query repair loop，不能让图查询在安全运营场景中无限修复。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是

