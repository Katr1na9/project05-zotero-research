# CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence

## 1. 基本信息

- 英文题名：CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence
- 中文译名：CTIBench：面向网络威胁情报的大语言模型评测基准
- 作者：Md Tanvirul Alam; Dipkamal Bhusal; Le Nguyen; Nidhi Rastogi
- 年份：2024
- Venue：NeurIPS 2024 Datasets and Benchmarks Track / arXiv
- DOI / arXiv / URL：arXiv:2406.07599；https://arxiv.org/abs/2406.07599
- Code / Dataset：https://github.com/xashru/cti-bench
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：LLM-CTI / Benchmark / ATT&CK / Threat Actor Attribution / Trustworthy CTI

## 2. 一句话总结

CTIBench 提出了一组用于评测 LLM 网络威胁情报能力的 benchmark，把 CTI 能力拆成知识问答、漏洞根因映射、漏洞严重性预测、ATT&CK 技术抽取和威胁行为体归因五类任务。它对我的价值主要不在于方法创新，而在于给后续论文的实验任务设计、baseline 选择和 LLM-CTI 能力边界分析提供参照。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 现有通用 LLM benchmark 不能衡量模型是否真的能处理 CTI 任务。
  - 现有网络安全 benchmark 常偏向代码安全、漏洞识别或记忆性问答，不能覆盖 CTI 中的理解、推理、问题求解和归因。
  - 因此需要一个面向 CTI 的任务集合，系统评估 LLM 在真实安全情报任务中的能力。
- 这个问题为什么重要？
  - CTI 任务的错误输出可能导致错误防御、错误归因或错误处置，风险高于普通问答。
  - 如果没有标准评测，很难判断 LLM 在 CTI 中到底是理解了证据，还是只是在复述训练语料中的知识。
  - 对后续做 LLM/RAG/Agent 安全调查系统的人来说，benchmark 是实验比较的基础。
- 之前方法哪里不够？
  - GLUE、MMLU、HELM 等通用 benchmark 不覆盖 CTI 任务。
  - 部分网络安全 benchmark 只评估记忆能力、代码安全或窄任务。
  - SEvenLLM 等工作覆盖了实体抽取、关系抽取和摘要，但对实际 CTI 问题求解和复杂归因推理覆盖不足。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - CTI-ATE 直接对应 CTI 文本到 MITRE ATT&CK technique 的抽取。
  - CTI-TAA 直接对应 threat actor attribution，是当前主线中最贴近“威胁归因”的 benchmark 子任务。
  - 它没有做 RAG、Agent 或日志溯源图，但可作为这些方法的评价基准。
  - 它没有显式评估攻击意图识别、证据链充分性、证据 grounding 和不确定性校准，这正是后续选题可以扩展的空间。

## 4. 核心贡献

1. 任务贡献：提出 CTIBench，用五类任务评估 LLM 的 CTI 能力。
2. 数据集贡献：构建 CTI-MCQ、CTI-RCM、CTI-VSP、CTI-ATE、CTI-TAA 五个任务数据集。
3. 评价贡献：将 CTI 能力拆成 memorization、understanding、problem-solving、reasoning 四类认知能力。
4. 归因评价贡献：CTI-TAA 使用威胁报告去除直接 actor/campaign/malware 名称后的文本，让模型基于 TTP 和上下文推断 threat actor。
5. 工程贡献：公开代码和数据集，便于复现实验。
6. 风险意识贡献：强调 LLM 幻觉和误解在 CTI 场景中会产生不可靠情报。

## 5. 方法框架

### 输入

- 数据类型：
  - CTI 知识文本和权威知识库；
  - CVE 漏洞描述；
  - MITRE ATT&CK malware/adversarial behavior 描述；
  - 公开威胁报告。
- 输入格式：
  - 多项选择题；
  - CVE description；
  - threat behavior description；
  - 替换掉直接归因实体后的 threat report。
- 先验知识：
  - MITRE ATT&CK；
  - CWE；
  - CVSS v3.1；
  - NVD；
  - Malpedia；
  - threat actor alias / related group 信息。

### 输出

- 预测结果：
  - MCQ 选项；
  - CWE ID；
  - CVSS v3.1 vector string；
  - MITRE ATT&CK technique IDs；
  - threat actor / malware family attribution。
- 图结构：无正式攻击图，但 CTI-TAA 评价中使用 alias / related actor graph。
- 标签：
  - CWE；
  - CVSS metric；
  - ATT&CK technique ID；
  - threat actor name。
- 报告：模型可给出简短 reasoning，但 benchmark 主要评价最终答案。
- 证据链：弱。论文要求模型解释，但没有系统评估证据引用、证据充分性或证据和结论的一致性。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| CTI-MCQ | 测 CTI 基础知识、标准、ATT&CK、CWE、CAPEC 等知识掌握 | 可作为 LLM-CTI 背景能力测试 |
| CTI-RCM | 从 CVE 描述映射到 CWE 根因类别 | 展示漏洞语义理解与 taxonomy mapping 任务设计 |
| CTI-VSP | 从 CVE 描述预测 CVSS v3.1 vector | 展示结构化安全评分任务设计 |
| CTI-ATE | 从威胁行为描述抽取 ATT&CK technique IDs | 可与 AttacKG、TechniqueRAG、TTPXHunter 对齐 |
| CTI-TAA | 从匿名化威胁报告推断 threat actor | 与威胁归因主线直接相关 |
| Alias Graph Evaluation | 用 alias 和 related group 图判断 correct / related / incorrect | 对归因评价很有价值，可扩展为置信度和证据权重评价 |

### 方法流程

```text
Authoritative CTI sources / NVD / MITRE ATT&CK / vendor reports
  -> Dataset construction
  -> Prompt-based LLM evaluation
  -> Task-specific answer parsing
  -> Accuracy / exact match / related-actor evaluation
  -> Model capability analysis
```

## 6. 数据集与实验

- 数据集：
  - CTI-MCQ：网络威胁情报多项选择题。
  - CTI-RCM：漏洞根因映射。
  - CTI-VSP：漏洞严重性预测。
  - CTI-ATE：攻击技术抽取。
  - CTI-TAA：威胁行为体归因。
- 数据规模：
  - CTI-MCQ：2,500 个问题，其中 1,578 来自 MITRE，750 来自 CWE，40 来自人工收集，32 来自标准和框架。
  - CTI-RCM：NVD 2024 中抽样 1,000 个带 CWE 映射的漏洞。
  - CTI-VSP：同样基于 1,000 个 2024 CVE 描述及其 CVSS v3 strings。
  - CTI-ATE：60 个 malware instances，其中 30 个来自 2024，30 个来自 2024 年之前，覆盖 397 个 unique attack techniques。
  - CTI-TAA：50 篇公开威胁报告，去除 threat actor、campaign、malware 的直接名称。
- 标注方式：
  - CTI-MCQ：GPT-4o 生成候选题，人工验证并修正错误答案、多正确选项和不可回答问题。
  - CTI-RCM / CTI-VSP：使用 NVD 中已有 CWE 和 CVSS 标注。
  - CTI-ATE：使用 MITRE ATT&CK malware/adversarial behavior 关联 technique。
  - CTI-TAA：使用原始报告中的归因实体作为 ground truth，并收集 Malpedia aliases 和 MITRE related groups。
- Baseline / 模型：
  - ChatGPT-4；
  - ChatGPT-3.5；
  - Gemini-1.5；
  - LLAMA3-70B；
  - LLAMA3-8B。
- 指标：
  - MCQ accuracy；
  - CWE mapping correctness；
  - CVSS vector string correctness；
  - ATT&CK technique extraction correctness；
  - CTI-TAA 中 correct / related / incorrect。
- 主要结果：
  - 论文整体结论是：主流 LLM 在 CTI 上有一定能力，但并不稳定，任务难度越接近实际推理和归因，越暴露可靠性问题。
  - CTI-MCQ 中显式 reasoning prompt 并不稳定提升效果，且显著增加 token 成本。
  - 在 reasoning prompt 对照中，ChatGPT-4 从 71.00% 到 71.84%，GPT-3.5 从 54.08% 到 59.16%，Gemini-1.5 基本持平，LLAMA3-70B 基本持平，LLAMA3-8B 反而下降。
  - 这说明“让模型先推理再回答”不是 CTI 可靠性的充分解决方案。
- 消融实验：
  - 附录比较了 CTI-MCQ 是否使用 reasoning prompt。
- Case study：
  - CTI-ATE 使用 Janicab 行为描述示例，映射到 Audio Capture、Scheduled Task、Screen Capture、Subvert Trust Controls 等 ATT&CK techniques。
  - CTI-TAA 使用匿名化威胁报告示例，让模型根据 TTP 和上下文做归因。

## 7. 关键知识点

### 概念

- **CTI benchmark**：不是单纯问安全知识，而是用任务集合评估模型在 CTI 中的知识、理解、问题求解和推理能力。
- **CTI-ATE**：attack technique extraction，把威胁行为描述映射到 MITRE ATT&CK technique IDs。
- **CTI-TAA**：threat actor attribution，让模型根据去身份化威胁报告推断攻击者或恶意软件家族。
- **Abductive reasoning**：溯因推理，从不完整证据中寻找最合理解释。威胁归因天然属于这一类推理。
- **Alias graph evaluation**：归因实体有多个别名，直接 exact match 不够，因此需要别名图和关联组织图辅助评价。

### 技术路线

- CTIBench 把 LLM-CTI 评测从“是否懂安全知识”推进到“是否能完成 CTI 实务任务”。
- CTI-ATE 可作为 TechniqueRAG、AttacKG、TTPXHunter 的 benchmark 对齐点。
- CTI-TAA 是当前最接近硕士论文主线的子任务，但它仍主要基于报告文本，没有结合系统日志、provenance graph 或证据链评分。
- 论文中的 alias / related group 图评价可以扩展为：
  - actor-level exact match；
  - related actor match；
  - campaign-level plausibility；
  - evidence-supported attribution；
  - uncertainty-aware attribution。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| benchmark | 基准测试 | 也可译为评测基准 |
| CTI-MCQ | CTI 多项选择题 | Cyber Threat Intelligence Multiple Choice Questions |
| root cause mapping | 根因映射 | CVE -> CWE |
| vulnerability severity prediction | 漏洞严重性预测 | CVE -> CVSS vector |
| attack technique extraction | 攻击技术抽取 | CTI -> ATT&CK technique IDs |
| threat actor attribution | 威胁行为体归因 | CTI-TAA |
| abductive reasoning | 溯因推理 | 从不完整证据推断最佳解释 |
| alias graph | 别名图 | actor 名称归一 |
| related actor | 关联行为体 | 评价中标为 related |

## 8. 优点

- 任务覆盖面比较完整，包含知识、漏洞、ATT&CK 技术、威胁归因。
- CTI-TAA 的设定很有价值：遮蔽直接名称，迫使模型根据 TTP 和上下文推断。
- 公开代码和数据，有利于复现实验。
- 明确指出 LLM 在 CTI 中的 hallucination 和 unreliable intelligence 风险。
- alias / related group graph 评价比简单字符串匹配更贴近真实归因。

## 9. 局限

- CTI-TAA 只有 50 篇报告，规模较小，难以支撑细粒度泛化结论。
- 多数任务仍是单轮 prompt evaluation，没有评估 RAG、Agent、多步调查或工具调用。
- CTI-ATE 只抽 main techniques，不评估 sub-technique 细粒度标注。
- 对 evidence grounding 评价不足：模型的理由是否真的来自输入报告，没有被严格度量。
- 没有结合日志、provenance graph、attack summary graph 或 InfoPath，因此不能评估“从报告到真实系统证据”的调查能力。
- 没有系统评估置信度校准、拒答机制和不确定性表达。

## 10. 对我选题的启发

- 可以直接借鉴：
  - CTI 任务拆分方式；
  - CTI-ATE 和 CTI-TAA 的任务定义；
  - actor alias / related group 图评价；
  - 公开 benchmark + prompt + metrics 的实验组织方式。
- 可以改进：
  - 将 CTI-TAA 从“只给威胁报告”扩展为“威胁报告 + ATT&CK KG/RAG + 日志侧 InfoPath/attack summary graph”。
  - 将输出从单一 actor name 扩展为：候选 actor、攻击意图、支持证据、反证、不确定性。
  - 加入 evidence grounding 指标，要求每个归因结论链接到报告句子、ATT&CK technique 或 provenance evidence。
- 可以作为 baseline：
  - 零样本 LLM；
  - few-shot LLM；
  - reasoning prompt；
  - RAG-enhanced LLM；
  - graph/RAG/agent 方法与 CTIBench prompt baseline 对比。
- 可以用于研究动机：
  - 现有 LLM-CTI benchmark 已经证明评测很重要，但还没有充分评测证据链、日志证据和可信归因。
- 可以用于实验设计：
  - 从 CTIBench 中抽 CTI-ATE / CTI-TAA 作为文本侧任务；
  - 另接 Kairos/DEPCOMM 类日志摘要，构造 evidence-grounded attribution benchmark。

## 11. 可转化的研究问题

1. 能否在 CTI-TAA 的基础上加入 evidence grounding，要求 LLM 不仅输出 threat actor，还输出支持该归因的 TTP、报告句子和证据强度？
2. 能否将 CTI-ATE 的 ATT&CK technique 输出进一步提升为 tactic / intent 层级，从而做 attack intent recognition？
3. 能否把 DEPCOMM 的 InfoPaths 或 Kairos 的 attack summary graph 序列化为证据输入，构建 CTI text + provenance evidence 的多源归因评测？
4. 能否设计 uncertainty-aware CTI attribution，让模型在证据不足时输出候选集合、置信度和拒答，而不是强行归因？
5. 能否构建一个小规模硕士可完成 benchmark：`report -> TTP -> intent -> candidate actor -> evidence chain`？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| A survey of cyber threat attribution | CTIBench 的 CTI-TAA 是综述中 actor attribution 层级的 LLM 评测实例 |
| AttacKG | AttacKG 构建 ATT&CK technique KG，CTIBench 的 CTI-ATE 可作为 technique annotation 评测任务 |
| EXTRACTOR | EXTRACTOR 关注 CTI 文本到攻击行为图，CTIBench 没有显式攻击图，可互补 |
| Kairos | Kairos 提供日志侧 attack summary graph，CTIBench 缺少日志侧真实证据 |
| DEPCOMM | DEPCOMM 提供 InfoPath 作为可调查证据，CTIBench 可扩展为 evidence-grounded benchmark |
| TechniqueRAG | TechniqueRAG 是 CTI-ATE 类任务的 RAG 方法代表，CTIBench 可作为评测参照 |
| Large Language Models are Unreliable for CTI | 后者更偏可靠性批判，CTIBench 提供任务框架；两者应一起读 |
| SEvenLLM | SEvenLLM 更偏 CTI 指令和基础抽取/生成，CTIBench 更偏实务任务 benchmark |

## 13. 论文写作可引用句式

- 现有通用大模型评测不能充分反映 CTI 场景中的威胁行为理解、TTP 映射和归因推理能力。
- CTI 任务不仅要求模型记忆安全知识，还要求其在不完整证据下进行溯因推理。
- 威胁行为体归因评价不能只依赖字符串精确匹配，因为同一组织常有多个别名和关联组织。
- 对 LLM-CTI 系统而言，生成正确答案并不足够，结论还需要可追溯证据、置信度和不确定性表达。

## 14. 我的批注与疑问

- CTIBench 对我很重要，但它本身并不是最终选题，更多是实验设计地基。
- CTI-TAA 的思路很接近威胁归因，但规模小、证据评价弱，可以作为扩展点。
- 需要警惕：如果只在 CTIBench 上做 prompt/RAG 小改，很容易变成“工程调参”，硕士论文创新不足。
- 更好的切入是：用 CTIBench 暴露的问题，提出 evidence-grounded / uncertainty-aware / provenance-enhanced 的新任务或方法。
- 后续读 `Large Language Models are Unreliable for CTI` 时，要重点比较它指出的失败模式是否能转化为实验指标。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：3.5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是
