# AURA: A Multi-Agent Intelligence Framework for Knowledge-Enhanced Cyber Threat Attribution

## 1. 基本信息

- 英文题名：AURA: A Multi-Agent Intelligence Framework for Knowledge-Enhanced Cyber Threat Attribution
- 中文译名：AURA：面向知识增强网络威胁归因的多智能体情报框架
- 作者：Nanda Rani; Sandeep Kumar Shukla
- 年份：2025
- Venue：arXiv preprint
- DOI / arXiv / URL：https://arxiv.org/abs/2506.10175
- 本地 PDF：`../07-zotero-exports/pdfs_20260705/AURA_2025.pdf`
- 本地文本：`../07-zotero-exports/pdf_text_20260705/AURA_2025.txt`
- 阅读日期：2026-07-05
- 阅读优先级：必读
- 所属主题：LLM-APT Attribution / RAG / Multi-Agent / Evidence-Grounded Explanation

## 2. 一句话总结

AURA 是当前最接近 Project05 原始想法的论文之一：它用 RAG + 多智能体把 TTP、IOC、malware、tool、timeline 等威胁情报输入转化为 group-wise / nation-wise attribution，并生成自然语言 justification；但它没有显式 evidence weighting、confidence scoring、evidence sufficiency 或 refusal 机制，这正是 Project05 可以继续切入的位置。

## 3. 研究问题

- 论文要解决什么？
  - APT 归因需要从不完整、异构、非结构化威胁情报中关联行为模式。
  - 传统 rule / shallow pattern / black-box classifier 难以解释“为什么归因到某个 actor”。
  - 作者希望用 agentic RAG 把威胁证据、检索和归因解释组织成一个工作流。
- 为什么重要？
  - 归因不仅是分类问题，还涉及外交、响应、威慑和责任追究。
  - 真实归因经常面对 incomplete evidence trails、adversarial deception 和 overlapping behavioral signatures。
  - 分析员需要的是可追踪的解释，而不是黑盒 label。
- 和 Project05 的关系是什么？
  - 它几乎覆盖了“LLM + RAG + APT attribution explanation”的宽题。
  - 因此 Project05 不能再泛泛写“多源证据融合与 LLM 归因解释”。
  - Project05 必须收窄到 AURA 未做透的部分：证据权重、证据充分性、置信度、拒答、降级归因。

## 4. 核心贡献

1. 提出 AURA，即 Attribution Using Retrieval-Augmented Agents。
2. 将归因工作流拆成多个 agent：query rewriting、knowledge retrieval、decision/context relevance、attribution、justification synthesis。
3. 输入覆盖 TTP、IOC、malware details、adversarial tools、campaign timelines。
4. 使用内部 threat report knowledge base 做检索增强归因，而不是让 LLM 闭卷猜测。
5. 输出 actor attribution 和自然语言 justification。
6. 在 group-wise 和 nation-wise 两层归因粒度上评估 top-1 / top-2。

## 5. 方法框架

### 输入

- 分析员 query；
- 结构化或半结构化 threat artifacts：
  - TTPs；
  - IoCs；
  - malware details；
  - adversarial tools；
  - campaign timelines；
- 威胁报告知识库。

### 输出

- group-wise attribution；
- nation-wise attribution；
- natural language justification；
- top-1 / top-2 candidate。

### 关键模块

| 模块 | 作用 | 对 Project05 的启发 |
|---|---|---|
| Query Rewriting Agent | 改写模糊分析员查询 | 可以改造成 evidence availability profile 生成器 |
| Retrieval Module | 从 threat knowledge base 检索上下文 | 可复用为证据检索层 |
| Decision Agent | 判断检索上下文是否与归因目标相关 | 可扩展为 evidence sufficiency validator |
| Attribution Agent | 基于证据输出 actor | 不能让它自由输出，需加候选约束和拒答 |
| Justification Agent | 生成自然语言解释 | 需加入证据引用、权重和置信度 |
| Memory | 保留多轮上下文 | 可用于调查流程，但不是当前核心创新 |

### 方法流程

```text
Threat data / analyst query
  -> query rewriting
  -> vector retrieval over threat reports
  -> context relevance decision
  -> attribution agent
  -> justification synthesis
  -> actor + explanation
```

## 6. 数据集与实验

- 知识库来源：
  - Google、CrowdStrike、Kaspersky 等公开威胁分析报告；
  - 共 2,229 篇 threat reports。
- 数据切分：
  - 2,199 篇进入 vector database；
  - 30 篇 post-cutoff reports 作为 held-out test set。
- 测试输入：
  - 用 GPT-4o 从 test reports 抽取 TTP、IOC、malware details、tools、attack timeline，转为 JSON。
- 模型：
  - gpt-4o；
  - gpt-4o-mini；
  - Claude 3.5 Haiku；
  - Claude 3.5 Sonnet。
- 设置：
  - 测试时关闭 web search；
  - 只用内部知识库。
- 指标：
  - group-wise top-1 / top-2 accuracy；
  - nation-wise top-1 / top-2 accuracy；
  - pass@3；
  - justification quality：readability、lexical richness、semantic coherence、fluency、LLM-as-judge。

### 主要结果

- Group-wise attribution：
  - gpt-4o top-1 63.33%，top-2 73.33%；
  - Claude 3.5 Sonnet top-1 53.33%，top-2 66.67%。
- Nation-wise attribution：
  - Claude 3.5 Sonnet top-1 83.33%，top-2 100%；
  - gpt-4o top-1 86.67%，top-2 93.33%。
- 作者强调 top-2 在归因模糊场景有价值，因为多个 actor 可能共享 TTP 或基础设施。

## 7. 局限

- 测试集只有 30 篇报告，规模偏小。
- 使用 proprietary LLM，复现性较弱。
- Justification Agent 只生成文本解释，没有 evidence weighting。
- 没有显式 reasoning chain 或 confidence scoring。
- 没有把 evidence sufficiency、refusal、unknown actor、false flag 作为核心任务。
- 输入虽然声称多源，但主要仍是 CTI-derived structured artifacts，不是日志/provenance 级证据融合。

## 8. 对 Project05 的影响

### 撞掉的方向

- “RAG + 多智能体 + APT 归因解释”不能作为 Project05 主创新。
- “输入 TTP/IOC/malware/tool/timeline，然后 LLM 生成 actor explanation”也不够新。

### 留下的空间

1. Evidence weighting：不同证据类型对归因的贡献不同。
2. Evidence sufficiency：判断证据足以支持 technique、intent、campaign 还是 actor。
3. Confidence scoring：输出 actor probability / confidence，而不是单一 label。
4. Refusal / abstention：证据不足时不强行归因。
5. Adaptive granularity：证据不足时降级到 intent 或 campaign hypothesis。
6. CTI + provenance/log evidence alignment：AURA 没有真正处理日志侧证据。

## 9. 可转化的选题问题

更稳的问题不是：

> 如何用 LLM/RAG 做 APT 归因？

而是：

> 在 AURA 类框架已经能生成归因解释后，如何判断某个解释的证据是否足够、置信度是否可靠，以及何时应该拒绝给出 actor-level attribution？

## 10. 相关工作位置

| 相关文献 | 关系 |
|---|---|
| Guru et al. 2025 | Guru 是 CTI->TTP->actor ranking，AURA 是 RAG/multi-agent 解释框架 |
| APT-MMF | APT-MMF 是 graph classifier，AURA 是 LLM/RAG agent framework |
| CTIConnect | CTIConnect 是异构 CTI RAG benchmark，AURA 是面向归因的具体系统 |
| High Stakes | 支撑 AURA 仍需 evidence sufficiency，因为 TTP/IOC 可能不够区分 actor |
| LLMs Unreliable for CTI | 支撑 AURA 需要 calibration / consistency / confidence |
| TAA-EPLMR | 可能比 AURA 更接近 evidence path + LLM reasoning，需全文确认 |

