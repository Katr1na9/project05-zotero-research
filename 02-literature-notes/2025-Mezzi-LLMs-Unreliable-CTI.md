# Large Language Models are Unreliable for Cyber Threat Intelligence

## 1. 基本信息

- 英文题名：Large Language Models are Unreliable for Cyber Threat Intelligence
- 中文译名：大语言模型在网络威胁情报中并不可靠
- 作者：Emanuele Mezzi; Fabio Massacci; Katja Tuma
- 年份：2025
- Venue：International Conference on Availability, Reliability and Security, Springer LNCS conference version；arXiv
- DOI / arXiv / URL：10.1007/978-3-032-00627-1_17；https://arxiv.org/abs/2503.23175
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：LLM-CTI / Trustworthy Attribution / Calibration / Consistency / Evidence Reliability

## 2. 一句话总结

这篇论文用 350 篇真实长度 APT 威胁报告评估 LLM 做 CTI 信息抽取和 APT 信息生成的可靠性，发现 LLM 在真实报告上性能不足、输出不一致且置信度校准较差。它对我的选题价值非常高，因为它把“LLM-CTI 不可信”的问题具体化为三类可评价指标：准确性、一致性和校准。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 现有很多 LLM-CTI 工作声称效果很好，但多在句子、短段落或人工切分文本上评估。
  - 真实 CTI 报告很长，包含大量背景、交叉引用、无关 APT、历史攻击向量和模糊描述。
  - 因此需要评估 LLM 在真实长度报告中的抽取性能、一致性和置信度可靠性。
- 这个问题为什么重要？
  - CTI 直接影响补丁管理、攻击面收敛、APT 画像、威胁归因和防御优先级。
  - 如果 LLM 漏掉 CVE、误判攻击向量或错误归因 APT，可能造成真实安全风险。
  - 在没有大量标注数据的 CTI 场景中，系统常会依赖模型置信度，因此 calibration 很关键。
- 之前方法哪里不够？
  - 许多工作使用很短的输入：句子、短段落、甚至短于论文摘要的文本。
  - 只报告 Precision、Recall、F1 等点估计，不看重复调用时是否稳定。
  - 不评估模型是否过度自信或信心不足。
  - 少数工作声称 few-shot / fine-tuning 有提升，但不一定能泛化到真实报告长度。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 信息抽取任务涉及 APT、campaign、CVE、attack vector，是威胁归因和攻击链重构的基础。
  - 信息生成任务从 APT 名称生成国家、目标、标签、CVE、攻击向量，接近 threat actor profiling。
  - 论文没有提出 RAG/Agent 方法，但指出 RAG、多智能体和 CoT 可作为未来改进方向。
  - 它为“可信 LLM 威胁归因”提供直接研究动机：不能只输出答案，还要评估稳定性、置信度和错误代价。

## 4. 核心贡献

1. 任务贡献：把 LLM-CTI 可靠性评估分成 information extraction 和 information generation 两类任务。
2. 数据贡献：使用 350 篇真实长度 APT 威胁报告，而不是短句或短段落。
3. 方法贡献：提出五步评估流程：zero-shot、few-shot、fine-tuning、consistency quantification、confidence calibration。
4. 指标贡献：除 Precision、Recall、F1 外，引入 confidence interval、Expected Calibration Error 和 Brier Score。
5. 经验结论：LLM 在真实报告 CTI 任务上不可靠，few-shot 和 fine-tuning 只部分有效，甚至可能降低效果。
6. 风险贡献：指出不一致和过度自信会影响补丁管理、APT 画像和 CTI 自动化决策。

## 5. 方法框架

### 输入

- 数据类型：
  - 真实 CTI 报告；
  - APT 描述；
  - STIX 结构化 ground truth。
- 输入格式：
  - 单篇非结构化威胁报告；
  - APT 名称和描述。
- 先验知识：
  - APT dataset；
  - STIX；
  - MITRE ATT&CK 中 APT group 信息；
  - prompt engineering 技术。

### 输出

- 信息抽取任务输出：
  - APT；
  - campaign；
  - CVE；
  - attack vector。
- 信息生成任务输出：
  - goals；
  - labels，如 nation-state actor、criminal organization、spy；
  - country；
  - CVE；
  - attack vector。
- 图结构：
  - 论文图示中可形成 CTI KG，但核心实验评价的是实体集合，不是图匹配。
- 标签：
  - STIX ground truth；
  - APT profile ground truth。
- 证据链：
  - 论文不要求模型给出证据句，但通过真实报告长度和 STIX 标签评估抽取可靠性。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Real-size CTI Report Evaluation | 使用完整报告测试模型，而不是短句或段落 | 后续实验必须避免只在短文本上证明有效 |
| Zero-shot Evaluation | 测原始 LLM CTI 能力 | 可作为最低 baseline |
| Few-shot Evaluation | 测少量示例是否改善抽取/生成 | 后续可比较 RAG 是否优于 few-shot |
| Fine-tuning Evaluation | 测微调是否稳定提升 | 提醒小数据微调可能破坏泛化 |
| Consistency Quantification | 多次重复调用并用 CI 衡量波动 | 可转化为归因稳定性指标 |
| Calibration Analysis | 用 ECE 和 Brier Score 衡量置信度可信程度 | 可转化为可信归因/拒答机制指标 |

### 方法流程

```text
Real-size CTI reports / APT descriptions
  -> Prompt preparation
  -> Zero-shot evaluation
  -> Few-shot evaluation
  -> Fine-tuning evaluation
  -> Repeated prompting for consistency
  -> Log-probability based confidence estimation
  -> ECE / Brier Score calibration analysis
```

## 6. 数据集与实验

- 数据集：
  - Di Tizio et al. 的 open-source APT dataset。
  - 数据以 STIX 标准结构化，可作为 ground truth。
- 数据规模：
  - 350 篇 CTI reports；
  - 覆盖 86 个 MITRE ATT&CK APT groups；
  - APT groups 来自 2008 到 2020 年至少发动一次 campaign 的组织；
  - 平均报告长度约 3,009 words；
  - 报告来源异构，包括安全厂商报告和安全研究博客。
- 信息抽取实体：
  - APT；
  - campaign；
  - vulnerability / CVE；
  - attack vector。
- 信息生成实体：
  - goals；
  - labels；
  - country；
  - CVE；
  - attack vector。
- Baseline / 模型：
  - OpenAI；
  - Google；
  - Mistral；
  - 具体实验中包括 gpt4o、gemini、mistral。
- 实验设置：
  - zero-shot；
  - few-shot；
  - fine-tuning；
  - 重复 prompt 10 次用于 consistency quantification；
  - 仅 gpt4o 用于 calibration analysis，因为可获得 log probabilities。
- 指标：
  - Precision；
  - Recall；
  - F1；
  - Confidence Interval；
  - Expected Calibration Error；
  - Brier Score。
- 主要结果：
  - 真实长度报告上的 LLM 信息抽取效果显著弱于短文本评估中的乐观结果。
  - 信息抽取中，即使最好的 CVE recall 也只有 0.90，意味着至少 10% 漏洞会被漏掉。
  - campaign recall 可低至 0.72，意味着 28% campaign 被漏掉。
  - attack vector recall 最高约 0.83，最低约 0.74，意味着大量攻击向量会被忽略。
  - few-shot learning 和 fine-tuning 不保证提升，有时会降低性能。
  - 信息生成中，APT label、CVE、attack vector 等实体表现尤其差。例如 APT label 的最低 precision/recall 可到 0.02。
  - LLM 多次回答同一问题会产生性能波动；信息生成任务比信息抽取更不稳定。
  - gpt4o 的 calibration 不理想，few-shot 和 fine-tuning 甚至可能让 ECE / Brier Score 变差。
- Case study：
  - 长报告比短段落更容易诱发 false positives 和 false negatives。
  - 同一个报告重复询问可能给出不同 CVE，影响补丁管理。
  - 高置信错误会让自动 CTI pipeline 接受错误预测；低置信正确会让系统丢弃有价值信息。

## 7. 关键知识点

### 概念

- **Real-size CTI reports**：真实威胁报告通常是几千词级别，包含大量非目标实体、历史上下文和交叉引用。
- **Information extraction**：从报告中抽取 APT、campaign、CVE、attack vector 等结构化实体。
- **Information generation**：从 APT 名称或描述生成画像信息，如国家、目标、标签、CVE 和攻击向量。
- **Consistency quantification**：重复同一输入，观察模型输出和指标是否稳定。
- **Calibration**：模型置信度是否能反映真实正确概率。
- **ECE**：Expected Calibration Error，用于衡量预测置信度和真实准确率之间的偏差。
- **Brier Score**：衡量概率预测质量的评分，越低越好。
- **Overconfidence**：模型对错误答案给出过高置信度。
- **Underconfidence**：模型对正确答案给出过低置信度。

### 技术路线

- 这篇论文的核心不是做一个更好的 CTI 系统，而是建立可靠性评估框架。
- 它从三个角度反驳“LLM 可以直接自动化 CTI”：
  - 真实长度报告上的性能不足；
  - 重复调用输出不一致；
  - 置信度不能可靠代表正确性。
- 它对后续研究的强提示是：任何 LLM/RAG/Agent CTI 方法都必须同时回答：
  - 答案对不对；
  - 多次运行是否稳定；
  - 错时是否知道自己可能错；
  - 证据不足时是否能拒答或降级为候选。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| unreliability | 不可靠性 | LLM-CTI 语境 |
| consistency quantification | 一致性量化 | 重复调用稳定性 |
| calibration | 校准 / 置信度校准 | 置信度与真实正确率是否一致 |
| Expected Calibration Error | 期望校准误差 | ECE |
| Brier Score | Brier 分数 | BS |
| information extraction | 信息抽取 | CTI 报告 -> 实体 |
| information generation | 信息生成 | APT 名称 -> APT 画像 |
| real-size report | 真实长度报告 | 区别于短句/段落 |
| prompt overfitting | prompt 过拟合 | few-shot 示例不能泛化 |
| world closing | 封闭世界约束 | 限定可选实体范围 |

## 8. 优点

- 直接挑战了 LLM-CTI 领域常见的乐观结论。
- 使用真实长度 CTI 报告，实验更接近真实安全调查场景。
- 不只看准确率，还看 consistency 和 calibration，这是可信安全系统必须关注的维度。
- 对 few-shot 和 fine-tuning 的负面结果很有启发：不是简单加示例或微调就能解决 CTI 可靠性。
- 与 CTIBench 互补：CTIBench 给任务地图，这篇给可靠性评价框架。

## 9. 局限

- 只使用一个 APT dataset，尽管它较异构，仍可能限制结论泛化。
- 只评估三个主流模型，模型覆盖有限。
- consistency 只重复 prompt 10 次，受成本限制，置信区间可能不够稳定。
- calibration 主要在 gpt4o 上做，因为需要 log probabilities。
- 没有评估 RAG、GraphRAG、多智能体或 evidence retrieval 是否能缓解问题。
- 仍以实体抽取/生成作为主任务，没有直接评估攻击意图识别、证据链生成或 actor attribution 的完整流程。

## 10. 对我选题的启发

- 可以直接借鉴：
  - 用真实长度威胁报告，而不是句子级或段落级样本；
  - 引入 consistency、ECE、Brier Score；
  - 区分 information extraction 和 information generation；
  - 使用 STIX / ATT&CK / APT profile 作为 ground truth。
- 可以改进：
  - 加入 RAG/KG/provenance evidence 后，比较是否提升性能、一致性和校准。
  - 将“实体抽取”扩展为“攻击意图 + 证据链 + 归因候选”。
  - 建立拒答机制：证据不足或置信度未校准时不强行输出单一 actor。
  - 将 DEPCOMM InfoPaths / Kairos attack summary graph 作为额外证据，看是否降低 false positive / false negative。
- 可以作为 baseline：
  - zero-shot LLM；
  - few-shot LLM；
  - fine-tuned LLM；
  - 这些 baseline 可以和 RAG、KG-enhanced、Agentic workflow 比较。
- 可以用于研究动机：
  - LLM-CTI 的核心问题不是“能不能生成像样的解释”，而是“在真实长度、多噪声、证据不完整场景下是否可靠”。
- 可以用于实验设计：
  - 指标不应只包括 F1，还应包括 consistency width、ECE、Brier Score、evidence precision 和 refusal correctness。

## 11. 可转化的研究问题

1. RAG 或知识图谱是否能提升 LLM 在真实长度 CTI 报告上的抽取/归因一致性，而不只是提升一次性 F1？
2. 如果把 CTI 报告证据和日志侧 InfoPath 结合，能否降低 LLM 对无关上下文的误抽取？
3. 能否设计一个 uncertainty-aware threat attribution pipeline，在证据不足时输出候选集和置信度，而不是单一归因？
4. 能否用 ECE / Brier Score 评价威胁归因系统的置信度，使其适合高风险安全决策？
5. 能否构建一个 evidence-grounded CTI benchmark，要求模型同时输出实体、证据句、ATT&CK technique、攻击意图和置信度？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CTIBench | CTIBench 提供任务集合，这篇提供可靠性评价维度 |
| TechniqueRAG | TechniqueRAG 关注提升 ATT&CK 标注性能；这篇提醒还要评价一致性和校准 |
| AttacKG | AttacKG 做 CTI -> ATT&CK KG；这篇说明真实报告中噪声和长度会影响抽取可靠性 |
| EXTRACTOR | EXTRACTOR 从报告抽取行为图；这篇提示行为图抽取也应检查重复运行稳定性 |
| Kairos | Kairos 提供日志证据侧，可以缓解只依赖 CTI 文本的不可靠问题 |
| DEPCOMM | DEPCOMM 的 InfoPath 可作为短证据单位，可能减少长报告中的无关上下文干扰 |
| Opinion Pools | 后续可把校准和置信度与 opinion pool 归因融合结合 |
| High Stakes, Low Certainty | 都强调高风险安全归因中的低确定性问题 |

## 13. 论文写作可引用句式

- 在真实长度 CTI 报告中，LLM 面临的信息噪声和上下文干扰显著高于句子级或段落级评测。
- 对 CTI 自动化系统而言，单次准确率不足以说明可靠性，还需要评估输出一致性和置信度校准。
- Few-shot learning 和 fine-tuning 并不必然改善 CTI 任务表现，甚至可能损害泛化和校准。
- 高置信错误和低置信正确都会对自动化 CTI pipeline 造成安全风险。

## 14. 我的批注与疑问

- 这篇是当前“可信 LLM 威胁归因”方向的关键地基。
- 它让我更确信：硕士论文不能只做 RAG + ATT&CK 标注，而要把可靠性指标放进方法贡献里。
- 它没有做 RAG/KG/Agent/provenance 融合，这正好留下空间。
- 需要后续检索 2025-2026 是否已有工作把 CTI reliability 与 GraphRAG / Agentic retrieval / evidence grounding 结合。
- 如果未来做实验，应尽量避免只用短文本样本，否则容易重复被这篇论文批评的问题。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
