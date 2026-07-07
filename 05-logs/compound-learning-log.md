# 全局复利日志：科研版

### 2026-07-06：AFA 综述成为新主线理论基座，"取证规划"从直觉升格为 POMDP 实例化

- 来源：`A Survey on Active Feature Acquisition Strategies`（Aronsson et al., arXiv:2502.11067 v2，已全文精读）。
- 内容：AFA 把"逐步花成本获取特征、何时停止并预测"统一形式化为 POMDP；短视 CMI 贪心是最强 baseline；非自适应近似 Q^NA 可借子模性拿贪心保证；熵目标不是自适应子模的，唯一适配的自适应子模目标是 EC²；MCTS 在线规划在 AFA 中未被充分利用。
- 为什么有复利：
  - Project05-B 的每个部件都能在 AFA 语言里找到对应物和现成方法族：价值估计=CMI 类目标、粒度门控=广义停止决策、证据分组取证=grouped acquisition、非对称归因损失=misclassification cost 进 ℓ、缺失感知评测=von Kleist 线。
  - "为什么不是直接套 AFA"的四点差异（结构化对齐状态、粒度格决策、训练假设崩塌、开放观测空间）就是论文的贡献清单。
  - benchmark 教训直接可用：先证明场景确实需要非短视，否则短视贪心就够——实验必须含这组对照。
- 下次如何复用：
  - 方法章以 AFA-POMDP 记号开场，再逐条写推广；
  - baseline 固定包含：随机、固定顺序、短视 CMI 贪心、熵阈值停止；
  - 写作时引用 schütz2025afabench 的"短视经常打赢非短视"来预防审稿人质疑复杂度。
- 关联文件：`02-literature-notes/2025-Aronsson-AFA-Survey.md`；`03-ideas/topic-rq-brief-v2-20260706.md`

### 2026-07-05：2026 H1 不是空白，Project05 要从“融合”转到“充分性/拒答”

- 来源：TTPrint、CTI-Thinker、OpenSec、Minerva、High-Precision APT Malware Attribution、Synthetic APTs、ARCANE。
- 内容：2026 年上半年已经有人推进 evidence-grounded TTP、LLM+KG+GraphRAG attack reasoning、CTI RLVR、IR agent calibration、OOS/abstention malware attribution、TTP mimicry 和 Bayesian longitudinal attribution。
- 为什么有复利：
  - 这批文献把 Project05 的边界进一步钉牢：单纯 `多源证据融合 + LLM APT attribution` 太宽，容易撞 AURA / CTI-Thinker / TAA-EPLMR / APT-MMF。
  - 真正有空间的是 `evidence availability profile -> sufficiency scoring -> adaptive granularity -> refusal/abstention -> evidence-grounded explanation`。
  - 评估指标应包括 EGAR、over-attribution rate、correct abstention、selective accuracy、OOS rejection、confidence calibration，而不是只看 actor accuracy。
- 下次如何复用：
  - 写专利时围绕“证据门控流程”和“拒答/降级触发条件”组织权利要求。
  - 写论文时把 TTPrint/CTI-Thinker/Minerva 放在上游 CTI 结构化与 LLM 能力增强，把 OpenSec/High-Precision/ARCANE/Synthetic APTs 放在可信归因与拒答动机。

## 目的

记录那些会越用越值钱的积累：术语表、方法框架、写作句式、实验设计经验、代码复用、数据集线索。

## 记录格式

### YYYY-MM-DD：标题

- 来源：
- 内容：
- 为什么有复利：
- 下次如何复用：
- 关联文件：

## 记录

### 2026-06-30：威胁归因阅读主线

- 来源：核心文献筛选与阅读顺序讨论。
- 内容：先读综述建立地图，再读 AttacKG/EXTRACTOR/Kairos/TechniqueRAG 进入方法。
- 为什么有复利：后续每篇论文都可以归入“归因层级、证据来源、方法模块、评价指标”四个维度。
- 下次如何复用：做论文笔记时强制填写这四项。
- 关联文件：`06-templates/paper-intensive-reading-template.md`

### 2026-06-30：威胁归因的两层沉淀框架

- 来源：`A survey of cyber threat attribution` 与 `AttacKG`。
- 内容：
  - 综述负责回答“归因到什么层级”：基础设施、恶意软件、campaign、actor、国家/动机。
  - AttacKG 负责回答“如何把 CTI 变成可计算证据”：报告文本、实体、关系、攻击图、ATT&CK 技术、技术知识图谱。
- 为什么有复利：后续所有论文都可以放入“归因层级”和“证据结构化方法”两个坐标系中比较。
- 下次如何复用：读 EXTRACTOR、TechniqueRAG、CTIBench 时，用同一坐标系判断它们解决的是哪一层问题。
- 关联文件：`02-literature-notes/2025-Prasad-Cyber-Threat-Attribution-Survey.md`；`02-literature-notes/2022-Li-AttacKG.md`

### 2026-07-01：CTI 文本攻击图与系统溯源图的桥

- 来源：`EXTRACTOR: Extracting Attack Behavior from Threat Reports`。
- 内容：EXTRACTOR 将 CTI 报告中的自然语言攻击描述抽取为 provenance graph，可作为 threat hunting 系统的 query graph。
- 为什么有复利：
  - 它把“报告里的攻击故事”和“日志里的系统行为”连接起来。
  - 它为后续理解 Kairos、DEPCOMM 这类系统日志/溯源图论文提供了中间层。
  - 它提醒后续选题不能只抽 TTP 标签，还要考虑证据是否能落到可观测行为。
- 下次如何复用：
  - 读 Kairos 时比较：EXTRACTOR 的 graph 来自 CTI 文本，Kairos 的 graph 来自 whole-system audit logs。
  - 做选题时问：我的方法输出是“文本解释”，还是“可匹配的行为证据图”？
- 关联文件：`02-literature-notes/2021-Satvat-EXTRACTOR.md`

### 2026-07-01：日志侧 provenance evidence 进入主线

- 来源：`KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance`。
- 内容：KAIROS 将系统审计日志建模为 whole-system provenance graph，通过 temporal graph learning 发现异常边，再将异常窗口压缩为 compact attack summary graph。
- 为什么有复利：
  - 它补齐了 EXTRACTOR/AttacKG 缺少的真实日志证据侧。
  - 它把“攻击检测”转化为“可调查的攻击摘要图”，适合后续接 ATT&CK 标注、意图识别、证据链生成和归因解释。
  - 它提醒选题要区分三层：底层系统事件、攻击行为图、上层 ATT&CK/意图/归因语义。
- 下次如何复用：
  - 读 DEPCOMM 时重点比较攻击摘要图压缩策略。
  - 读 TechniqueRAG 时考虑：RAG 不只服务 CTI 文本，也可以服务日志摘要图到 ATT&CK 技术的语义标注。
  - 设计选题时优先问：我的方法能否把 LLM 输出落回具体 provenance edge 或 CTI 证据句？
- 关联文件：`02-literature-notes/2024-Cheng-KAIROS.md`

### 2026-07-04：TechniqueRAG 划定 RAG + ATT&CK 的创新边界

- 来源：`TECHNIQUERAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text`。
- 内容：TechniqueRAG 将 ATT&CK technique annotation 拆成 retriever、LLM re-ranker 和 generator 三个模块，用少量 text-technique pairs 实现 CTI 文本到 technique/sub-technique 的标注。
- 为什么有复利：
  - 它明确告诉我们：“用 RAG 做 ATT&CK 标注”本身已经不够新。
  - 它可以作为后续方法的 baseline 或中间模块。
  - 它暴露了真实 CTI 标注的难点：multi-label 漏标、隐式 technique、相似技术混淆、标注不一致。
- 下次如何复用：
  - 设计选题时，把 TechniqueRAG 放在 technique layer；创新要落到 intent layer、evidence chain、uncertainty 或 CTI-log alignment。
  - 做实验时，可复用 technique-level / sub-technique-level Precision、Recall、F1。
  - 写相关工作时，将 AttacKG、TTPXHunter、TechniqueRAG 归为 CTI-to-ATT&CK annotation 线。
- 关联文件：`02-literature-notes/2025-Lekssays-TechniqueRAG.md`

### 2026-07-04：术语表 v0.1

- 来源：已读核心文献与 project05 工作区规范。
- 内容：按威胁归因、CTI、ATT&CK/TTP、图结构/溯源、PIDS/RAG/KG、LLM Agent、可信评估和实验指标整理统一译法。
- 为什么有复利：
  - 后续读论文、写笔记、做开题报告时不会反复纠结术语。
  - 可以直接改善 Zotero 翻译批注质量，避免 `attribution`、`campaign`、`provenance`、`tactic` 等词被误译。
  - 为后续写“问题定义”和“方法框架”提供稳定词汇表。
- 下次如何复用：
  - 每读一篇新论文，若出现新术语，追加到对应分组。
  - 写作时优先使用术语表译法。
- 关联文件：`08-writing/term-glossary.md`

### 2026-07-04：DEPCOMM 的 InfoPath 作为日志侧证据单位

- 来源：`DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation`。
- 内容：DEPCOMM 从 POI event 出发构建 dependency graph，再用 process-centric community、community compression 和 top-ranked InfoPaths 生成可调查摘要。
- 为什么有复利：
  - 它把“巨大日志图”变成“短路径证据”，适合后续输入 LLM/RAG。
  - 它和 Kairos 构成日志侧两种证据底座：Kairos 是异常驱动 attack summary graph，DEPCOMM 是 POI 驱动 dependency graph summarization。
  - InfoPath 可以作为后续 ATT&CK 标注、攻击意图识别、证据链评价的基本单位。
- 下次如何复用：
  - 读 CTIBench/LLM unreliable 时，用 DEPCOMM 反问：benchmark 是否只测文本问答，还是能测图路径证据？
  - 设计方法时，把 InfoPath 序列化为：`source -> process -> file/socket -> process -> sink`。
- 关联文件：`02-literature-notes/2022-Xu-DEPCOMM.md`

### 2026-07-04：CTIBench 定义 LLM-CTI 评测任务地图

- 来源：`CTIBench: A Benchmark for Evaluating LLMs in Cyber Threat Intelligence`。
- 内容：CTIBench 将 LLM-CTI 评测拆成 CTI-MCQ、CTI-RCM、CTI-VSP、CTI-ATE、CTI-TAA 五类任务，其中 CTI-ATE 对应 ATT&CK 技术抽取，CTI-TAA 对应威胁行为体归因。
- 为什么有复利：
  - 它给后续方法论文提供了实验任务和 baseline 组织方式。
  - 它提醒我们不要只做“能生成解释”的系统，而要定义可度量任务、标签和评价指标。
  - 它暴露了当前 benchmark 缺口：证据 grounding、不确定性、日志侧 provenance evidence 和攻击意图层级仍不足。
- 下次如何复用：
  - 设计实验时，优先把任务写成 `输入 -> 输出 -> 标签 -> 指标 -> 失败模式`。
  - 后续读 LLM unreliable 时，用 CTIBench 五任务框架定位每种失败模式。
  - 若构建硕士论文 benchmark，可从 CTI-TAA 扩展到 `report + evidence -> actor + intent + evidence chain + confidence`。
- 关联文件：`02-literature-notes/2024-Alam-CTIBench.md`

### 2026-07-04：LLM-CTI 可信性必须包含一致性和校准

- 来源：`Large Language Models are Unreliable for Cyber Threat Intelligence`。
- 内容：真实长度 CTI 报告会显著暴露 LLM 的漏抽、误抽、不一致和过度自信问题；few-shot 与 fine-tuning 不一定能解决这些问题。
- 为什么有复利：
  - 它把“可信 LLM 威胁归因”转化为可评价指标：Precision、Recall、F1、confidence interval、ECE、Brier Score。
  - 它提醒后续实验不能只用短句或短段落，否则会高估模型能力。
  - 它为 evidence-grounded / uncertainty-aware / provenance-enhanced 方向提供了强研究动机。
- 下次如何复用：
  - 设计实验时，加入重复运行和校准评价。
  - 读 RAG/Agent 论文时，追问它是否真正改善 consistency 和 calibration。
  - 写开题动机时，用“真实长度报告上的不可靠性”支撑研究必要性。
- 关联文件：`02-literature-notes/2025-Mezzi-LLMs-Unreliable-CTI.md`

### 2026-07-04：TTP 抽取已经是中间层强基线

- 来源：`TTPXHunter: Actionable Threat Intelligence Extraction as TTPs from Finished Cyber Threat Reports`。
- 内容：TTPXHunter 从完整 CTI 报告中抽取 ATT&CK TTP，结合 SecureBERT、上下文数据增强、IOC 替换和相关句过滤，并输出 STIX。
- 为什么有复利：
  - 它可以作为后续 CTI -> ATT&CK technique/TTP 的 baseline。
  - 它提醒我们：单纯 TTP 抽取已经比较成熟，创新应继续上移到攻击意图、证据链和归因可信度。
  - IOC replacement 和 report-level aggregation 可直接复用到后续方法设计。
- 下次如何复用：
  - 做方法框架时，把 TTPXHunter 放在 technique layer。
  - 设计实验时，把 TTP-level F1 与 intent-level / attribution-level / evidence-level 指标分开。
  - 写相关工作时，将 AttacKG、TechniqueRAG、TTPXHunter 放在 CTI-to-ATT&CK 主线下比较。
- 关联文件：`02-literature-notes/2024-Rani-TTPXHunter.md`

### 2026-07-04：领域指令模型是背景，不是自动等于选题

- 来源：`SEvenLLM: Benchmarking, Eliciting, and Enhancing Abilities of Large Language Models in Cyber Threat Intelligence`。
- 内容：SEvenLLM 构建双语 CTI 指令数据、28 类安全事件任务、领域模型和 benchmark，说明安全领域 LLM 能力增强需要数据、任务和评测三件套。
- 为什么有复利：
  - 它提供了 Select-Instruct、任务池和专家修正的数据构建流程。
  - 它提醒我们：泛化安全事件任务很宽，不能替代专门的威胁归因/攻击意图/证据链任务。
  - 它可作为后续小型数据集构建方法参考。
- 下次如何复用：
  - 若需要构建数据集，采用 `任务池 -> 自动生成 -> 人工修正 -> 错误率报告`。
  - 写相关工作时，将 SEvenLLM 放在 domain-specific cybersecurity LLM / instruction tuning 类。
  - 对 Attack Intent Analysis 保持关注，但需要重新定义更严格的 intent taxonomy。
- 关联文件：`02-literature-notes/2024-Ji-SEvenLLM.md`

### 2026-07-04：异构 CTI RAG 的关键是跨源语义鸿沟

- 来源：`CTIConnect: A Benchmark for Retrieval-Augmented LLMs over Heterogeneous Cyber Threat Intelligence`。
- 内容：CTIConnect 将结构化 CTI 知识库和非结构化威胁报告整合为 RAG benchmark，证明不同任务需要不同检索策略，通用 vanilla RAG 难以弥合 cross-source semantic gap。
- 为什么有复利：
  - 它把“LLM + RAG + CTI”从泛概念拆成任务路由、异构源检索、证据利用和评价指标。
  - 它提供了 Entity Linking、Entity Attribution、Multi-Document Synthesis 三类任务框架。
  - 它暴露了一个可延展缺口：尚未纳入 provenance graph / InfoPath / attack summary graph。
- 下次如何复用：
  - 设计方法时按任务类型选择 retrieval strategy，而不是统一用向量检索。
  - 设计实验时区分 retrieval accuracy 和 evidence utilization。
  - 后续读 Beyond RAG for CTI 时，与 CTIConnect 的 EtR/DtR/CSKG-Guided RAG 对照。
- 关联文件：`02-literature-notes/2026-Cheng-CTIConnect.md`

### 2026-07-04：组织本地上下文决定 CTI 是否可行动

- 来源：`LocalIntel: Generating Organizational Threat Intelligence from Global and Local Cyber Knowledge`。
- 内容：LocalIntel 将全局 CTI 与组织本地知识库结合，生成组织级威胁情报和缓解策略，说明同一个漏洞在不同本地资产/配置下影响不同。
- 为什么有复利：
  - 它把“外部威胁情报”与“本地环境证据”连接起来。
  - 它提示后续选题可以把 local knowledge 从 wiki 扩展为 provenance graph / InfoPath / attack summary graph。
  - 它为 `CTI + 本地证据 -> 可行动情报` 提供了应用动机。
- 下次如何复用：
  - 设计方法时区分 global CTI、local context、generated organizational intelligence。
  - 设计实验时比较 global-only、local-only、global+local、global+local+provenance evidence。
  - 写研究动机时用它说明为什么不能只做通用 CTI/RAG。
- 关联文件：`02-literature-notes/2025-Mitra-LocalIntel.md`

### 2026-07-04：GraphRAG 不是银弹，混合检索才适合归因证据链

- 来源：`Beyond RAG for Cyber Threat Intelligence: A Systematic Evaluation of Graph-Based and Agentic Retrieval`。
- 内容：论文比较 Semantic RAG、GraphRAG、Agentic GraphRAG 和 HybridRAG，发现图结构能提升多跳 CTI 关系推理，但纯 GraphRAG 会因 schema gap、text-to-Cypher 错误和空查询结果产生结构性幻觉、拒答失败和延迟不稳定。
- 为什么有复利：
  - 它给后续方法设计划定底线：不能把 GraphRAG 当成天然可信的升级。
  - 它说明威胁归因证据链更适合混合检索：文本证据、图证据和本地 provenance evidence 互相校验。
  - 它把“证据不足时拒答”变成可评价任务，而不是写作里的抽象可信性。
- 下次如何复用：
  - 设计实验时加入 unanswerable / insufficient evidence 样本。
  - 方法框架中设置 `graph-text cross-check` 和 `bounded query repair`。
  - 写相关工作时，把它放在 CTI RAG/GraphRAG 评测线，与 CTIConnect、LocalIntel、LLM unreliable 对照。
- 关联文件：`02-literature-notes/2026-Hamzic-Beyond-RAG-CTI.md`

### 2026-07-04：威胁归因应输出概率分布，而不是单一标签

- 来源：`A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools`。
- 内容：论文提出模块化归因架构，每个 attributor 针对一类证据输出候选 actor 的 PMF，再用 opinion pool 或 Pairing Aggregator 融合为最终 actor PMF。
- 为什么有复利：
  - 它给 LLM 增强归因提供了清晰架构：LLM 只是一个 attributor，不能替代全部证据融合。
  - 它把“可信归因”落实为 top-k 候选、概率分布、false-flag 抗性和中间证据解释。
  - 它能把 CTI、ATT&CK/KG、provenance graph、local context 自然接到同一框架中。
- 下次如何复用：
  - 设计方法时使用 `attributor -> PMF -> weighted opinion pool -> final actor PMF`。
  - 设计实验时比较 monolithic LLM attribution 和 modular LLM attribution。
  - 写相关工作时将它作为可信归因/概率融合 baseline。
- 关联文件：`02-literature-notes/2023-Teuwen-Modular-Threat-Attribution-Opinion-Pools.md`

### 2026-07-04：TTP 不是天然可靠的 actor attribution evidence

- 来源：`High Stakes, Low Certainty: Evaluating the Efficacy of High-Level Indicators of Compromise in Ransomware Attribution`。
- 内容：论文用专家访谈和真实勒索软件事件报告显示，TTP/高层 IoC 在 ransomware attribution 中常常太泛、组内不稳定、组间重叠明显；同一 RTA 平均 TTP overlap 只有 0.37，不同 RTA 平均 overlap 仍有 0.21，且 silhouette score 为负值。
- 为什么有复利：
  - 它纠正了“高层 IoC/TTP 一定比低层 IoC 更适合归因”的默认假设。
  - 它把可信归因的重点从“抽到 TTP”推进到“证据是否足以支撑某一级别归因”。
  - 它可直接指导 Opinion Pools 中不同 attributor 的权重设计。
- 下次如何复用：
  - 设计方法时，将 TTP attributor 的输出视为弱证据或中等证据，而不是 actor 结论。
  - 设计实验时加入 TTP overlap、actor cluster separability、evidence sufficiency 和 refusal correctness。
  - 写开题动机时，用它说明为什么需要 uncertainty-aware / evidence-grounded attribution。
- 关联文件：`02-literature-notes/2025-Horst-High-Stakes-Low-Certainty.md`

### 2026-07-04：TTP 抽取已形成多阶段 LLM baseline

- 来源：`Multi-Step LLM Pipeline for Enhancing TTP Extraction in Cyber Threat Intelligence`。
- 内容：论文将 TTP extraction 拆成 `Extractor -> Technique Candidate Generator -> Validator`。Extractor 将 CTI 文本拆成 atomic threat actions，Candidate Generator 用 ATT&CK procedure embedding 召回 top-k technique，Validator 用 LLM 对候选排序和过滤。
- 为什么有复利：
  - 它提供了一个可复用的文本侧 ATT&CK 标注模块。
  - 它说明 TTP 抽取已经不是空白创新点，后续研究要继续上移到 intent、evidence sufficiency、uncertainty 和 attribution。
  - Validator 思想可以迁移为 evidence sufficiency validator 或 attribution confidence validator。
- 下次如何复用：
  - 设计方法时，把该 pipeline 作为 CTI text attributor 或 TTP baseline。
  - 设计消融时比较 no-validator、technique-validator、evidence-validator 的差异。
  - 写相关工作时与 TechniqueRAG、TTPXHunter、AttacKG 放在 CTI-to-ATT&CK extraction 线。
- 关联文件：`02-literature-notes/2025-Kim-Multi-Step-LLM-Pipeline-TTP-Extraction.md`

### 2026-07-04：Open-CyKG 作为 CTI 知识图谱底座

- 来源：`Open-CyKG: An Open Cyber Threat Intelligence Knowledge Graph`。
- 内容：Open-CyKG 将非结构化 CTI/APT 报告通过 `cybersecurity NER -> neural OIE triples -> canonicalization / fusion -> CTI KG -> Neo4j visualization` 转成开放知识图谱。
- 为什么有复利：
  - 它给后续 GraphRAG / HybridRAG 提供了传统 CTI KG 构建 baseline。
  - 它提醒我们 KG 构建不是终点，真正服务归因时还需要 source sentence、confidence、temporal validity 和 evidence sufficiency。
  - 它可以和 AttacKG、EXTRACTOR 一起构成“CTI 文本结构化”相关工作线。
- 下次如何复用：
  - 设计方法时把 CTI KG 视为结构化证据源，而不是归因裁判。
  - 若使用图检索，需要评估 KG edge 是否可追溯到原文证据、是否和 provenance evidence 一致。
  - 写相关工作时，用它说明早期 KG 路线，再引出 LLM/RAG/provenance evidence 融合的必要性。
- 关联文件：`02-literature-notes/2021-Sarhan-Open-CyKG.md`

### 2026-07-04：UNICORN 划定日志侧 APT 检测基线

- 来源：`UNICORN: Runtime Provenance-Based Detector for Advanced Persistent Threats`。
- 内容：UNICORN 将流式 whole-system provenance graph 转成 graph histogram 和固定长度 HistoSketch，再用演化式聚类模型检测 graph-level anomaly。
- 为什么有复利：
  - 它是理解 Kairos、DEPCOMM、THREATRACE、PROGRAPHER 的日志侧前置基线。
  - 它说明底层 APT 异常检测已经很强，Project05 更应关注异常之后的证据链、ATT&CK/intent 语义和归因解释。
  - 它把 low-and-slow APT、模型污染、长期因果上下文和实时开销这几个实验约束放进了同一个框架。
- 下次如何复用：
  - 写相关工作时，将 UNICORN 放在 graph-level provenance-based detection。
  - 设计方法时，把 UNICORN/Kairos 类异常信号视为 local behavioral evidence，而不是最终结论。
  - 设计实验时区分 detection metrics 与 explanation / evidence / attribution metrics。
- 关联文件：`02-literature-notes/2020-Han-UNICORN.md`

### 2026-07-05：THREATRACE 将日志证据推进到节点级

- 来源：`THREATRACE: Detecting and Tracing Host-Based Threats in Node Level Through Provenance Graph Learning`。
- 内容：THREATRACE 用 GraphSAGE-based multi-model framework 学习 benign node roles，在执行阶段检测不能被高置信分类回自身 node type 的 anomalous nodes，并在其 2-hop 邻域中追踪异常。
- 为什么有复利：
  - 它把日志侧证据从 UNICORN 的 graph-level alarm 推进到 anomalous entity / local context。
  - 它提示 Project05 可以把 `异常节点 + 2-hop context` 作为最小 evidence unit，再进一步生成 attack story、ATT&CK/intent 映射和证据充分性判断。
  - 它也提醒我们 anomaly tracing 仍不等于 attack story reconstruction。
- 下次如何复用：
  - 写相关工作时，将 THREATRACE 放在 node-level provenance graph learning。
  - 设计方法时，把 node-level evidence 与 Kairos edge-level anomaly、DEPCOMM InfoPath 进行粒度对比。
  - 设计实验时分开评价 anomalous node detection、evidence chain construction 和 semantic explanation。
- 关联文件：`02-literature-notes/2022-Wang-THREATRACE.md`

### 2026-07-05：PROGRAPHER 补齐 snapshot-level 图嵌入检测基线

- 来源：`ProGraPher: An Anomaly Detection System based on Provenance Graph Embedding`。
- 内容：PROGRAPHER 将 streaming provenance graph 切成 temporal snapshots，用 graph2vec 学习 whole graph embedding，再用 TextRCNN 根据历史 snapshot sequence 预测下一时刻 embedding。
- 为什么有复利：
  - 它把 UNICORN 式 graph-level alarm 推进到 abnormal snapshot + Rooted Subgraph + suspicious node indicator。
  - 它比单纯整图报警更接近分析师可检查的局部证据，但仍不自动生成 attack story、ATT&CK 语义、攻击意图或 actor attribution 解释。
  - Production EDR 上 AUC 0.943 的结果说明 snapshot-level embedding 在真实日志场景中有参考价值。
- 下次如何复用：
  - 写相关工作时，将 PROGRAPHER 放在 snapshot-level provenance graph embedding / indicator generation。
  - 设计方法时，可把 suspicious RSG/node indicator 视为 LLM 解释层的结构化输入。
- 关联文件：`02-literature-notes/2023-Yang-PROGRAPHER.md`

### 2026-07-05：APT-MMF 补齐 CTI/IOC 图归因强基线

- 来源：`APT-MMF: An advanced persistent threat actor attribution method based on multimodal and multilevel feature fusion`。
- 内容：APT-MMF 将 APT reports 与 IOC 信息构造成 heterogeneous attributed graph，融合 attribute type、BERT text、Node2vec topology 三类特征，并用三层 attention 学习 report node 表示完成 actor classification。
- 为什么有复利：
  - 它把 Project05 的归因侧基线从“文本/TTP 抽取”推进到“报告-IOC-属性-关系-metapath 的结构化 actor attribution”。
  - 它可作为 Opinion Pools 中的 CTI/IOC graph attributor，与 LLM/RAG/provenance attributor 融合。
  - 它暴露出关键缺口：known actor closed-set classification 不能处理 unknown actor、false flag、证据不足和日志侧证据对齐。
- 下次如何复用：
  - 写相关工作时，将 APT-MMF 放在 CTI/IOC graph-based actor attribution。
  - 设计方法时，复用 report-IOC-metapath 作为 CTI 证据组织方式，再接日志侧 evidence 和 LLM 解释层。
- 关联文件：`02-literature-notes/2024-Xiao-APT-MMF.md`

### 2026-07-05：ADAPT it! 补齐样本侧 campaign/group 归因基线

- 来源：`ADAPT it! Automating APT Campaign and Group Attribution by Leveraging and Linking Heterogeneous Files`。
- 内容：ADAPT 将 APT attribution 拆成 campaign-level Intra-Clustering 和 group-level Inter-Clustering，覆盖 executables 与 documents，并用 linking features 将跨 campaign 的样本关联到 threat group。
- 为什么有复利：
  - 它补齐了 APT-MMF 之外的样本侧证据来源：不是报告/IOC 图，而是真实 malicious files 的静态特征和基础设施关联。
  - 它提醒 Project05 必须区分 campaign attribution 与 actor/group attribution，不能直接把所有证据推到 actor label。
  - 它把 shared tools、code reuse、false flags、packing/obfuscation、concept drift 等真实归因难点具体化。
- 下次如何复用：
  - 写相关工作时，将 ADAPT 放在 heterogeneous file-based campaign/group attribution。
  - 设计方法时，把 ADAPT 的 linking features 与 APT-MMF 的 report-IOC graph、日志侧 provenance evidence 一起纳入 evidence fusion。
- 关联文件：`02-literature-notes/2024-Saha-ADAPT-it.md`
### 2026-07-05：AURA 说明 LLM/RAG/Agent 归因解释宽题已被覆盖

- 来源：`AURA: A Multi-Agent Intelligence Framework for Knowledge-Enhanced Cyber Threat Attribution`。
- 内容：AURA 用 RAG + 多智能体处理 TTP、IOC、malware、tools、timeline，并输出 group-wise / nation-wise attribution 与自然语言 justification。
- 为什么有复利：
  - 它直接堵住了“LLM + RAG + 多智能体做 APT 归因解释”的宽题。
  - 它的 limitation 明确说当前没有 evidence weighting，也只是未来考虑 confidence scoring。
  - 因此 Project05 应转向 evidence sufficiency、confidence calibration、refusal 和 adaptive attribution granularity。
- 关联文件：`02-literature-notes/2025-Rani-AURA.md`

### 2026-07-05：Guru et al. 划定 CTI->TTP->actor baseline

- 来源：`On Technique Identification and Threat-Actor Attribution using LLMs and Embedding Models`。
- 内容：论文用 GPT-4 和 text-embedding-3-large 从 MITRE actor references 中生成 TTP profile，再用 TTP profile 做 actor ranking；最佳平均 rank 约 7.55/29。
- 为什么有复利：
  - 它证明 TTP-only attribution 可做但很弱，GPT/VE 生成 TTP 与 MITRE ground truth 差异大。
  - 它支撑 Project05 不应把 TTP 抽取和 actor ranking 当最终创新。
  - 后续实验应把 TTP overlap、证据区分度和拒答正确率纳入指标。
- 关联文件：`02-literature-notes/2025-Guru-Technique-Identification-Threat-Actor-Attribution.md`

### 2026-07-05：AttacKG+ / MM-AttacKG 把 LLM 构图主线压实

- 来源：`AttacKG+` 与 `MM-AttacKG`。
- 内容：AttacKG+ 用 LLM 从 CTI 文本构建 behavior graph、MITRE TTP labels、state summary；MM-AttacKG 进一步解析 CTI images 并补充 entity、relation、technique。
- 为什么有复利：
  - 文本/多模态 attack graph construction 已经不是安全的主创新点。
  - 这些工作可作为 Project05 的上游 evidence structuring 模块。
  - 真正可做的是把 attack graph evidence 进一步用于证据充分性判断、归因降级和拒答。
- 关联文件：`02-literature-notes/2024-Zhang-AttacKG-plus.md`，`02-literature-notes/2025-Zhang-MM-AttacKG.md`

### 2026-07-05：TAA-EPLMR 是最高撞题风险论文

- 来源：`TAA-EPLMR: Threat Actor Attribution via Evidence Path-Enhanced Large Language Model Reasoning`。
- 内容：全文未获取，但题名、DOI、Crossref reference list 已确认其组合了 evidence path、LLM reasoning 和 threat actor attribution。
- 为什么有复利：
  - 在全文确认前，Project05 不应使用“evidence path-enhanced LLM attribution”作为最终题名。
  - 如果 TAA-EPLMR 覆盖 confidence/refusal/incomplete evidence，则必须进一步转向 provenance alignment 或 open-set unknown actor。
  - 如果它没有覆盖 evidence sufficiency/refusal，则这正是 Project05 的专利切口。
- 关联文件：`02-literature-notes/2025-Xiao-TAA-EPLMR.md`
