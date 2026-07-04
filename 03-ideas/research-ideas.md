# Research Ideas

## 使用说明

所有科研灵感先进入这里，不急着判断对错。每条 idea 至少包含：问题、直觉、可能方法、数据来源、可评估指标、风险、下一步。

## 当前候选 idea

### Idea-20260630-01：基于 RAG + ATT&CK KG 的攻击意图识别

- 问题：现有 TTP 映射通常只识别技术标签，较少进一步推断攻击意图和证据链。
- 直觉：ATT&CK tactic 本身具有意图语义；AttacKG 已能构建 technique-level knowledge graph，但还没有显式 intent layer，可在其上增加攻击意图推断。
- 可能方法：CTI 文本抽取 -> TTP 映射 -> ATT&CK KG/RAG 检索 -> 意图标签生成 -> 证据引用。
- 数据来源：ATT&CK procedure examples、CTI 报告、AttacKG/TTPXHunter/TechniqueRAG 相关数据。
- 可评估指标：TTP F1、意图识别 F1、证据引用准确率、幻觉率。
- 相关文献：AttacKG、EXTRACTOR、TechniqueRAG、CTIBench。
- 风险：意图标签体系需要定义；数据标注成本可能较高。
- 下一步验证：先设计 5-8 个攻击意图类别。
- 状态：重点跟进。

### Idea-20260630-02：面向安全调查的多智能体证据链生成

- 问题：单个 LLM 容易幻觉，安全调查需要可追溯证据链。
- 直觉：将日志检索、TTP 映射、证据验证、报告生成拆成不同 agent，可降低错误扩散。
- 可能方法：Planner Agent + Retriever Agent + ATT&CK Mapper + Evidence Verifier + Report Writer。
- 数据来源：ExCyTIn-Bench、Sentinel 风格日志、公开 CTI 报告。
- 可评估指标：调查问题回答准确率、证据覆盖率、报告可用性、幻觉率。
- 相关文献：ExCyTIn-Bench、Cognitive SOC、CyLens。
- 风险：系统实现复杂，硕士周期内要控制规模。
- 下一步验证：先做单文档 CTI investigation agent，不碰真实日志。
- 状态：待验证。

### Idea-20260630-03：可信 LLM 威胁归因的置信度校准

- 问题：LLM 在 CTI 任务中可能过度自信，归因结论需要表达不确定性。
- 直觉：结合 evidence score、retrieval score、TTP similarity、LLM self-consistency 可形成候选归因置信度。
- 可能方法：候选 actor 检索 -> 证据打分 -> opinion pool/校准模型 -> 输出置信度。
- 数据来源：CTI reports、ATT&CK groups、APT-MMF/ADAPT it! 对比。
- 可评估指标：Brier score、ECE、top-k actor accuracy、证据充分性。
- 相关文献：LLMs are Unreliable for CTI、Opinion Pools、High Stakes Low Certainty。
- 风险：actor-level ground truth 不稳定。
- 下一步验证：限制为公开报告中已标注 actor 的小规模数据集。
- 状态：待验证。

### Idea-20260630-04：Technique Knowledge Graph + Intent Layer

- 问题：AttacKG 构建了 technique knowledge graph，但主要停留在 ATT&CK technique 识别，没有进一步表达攻击意图。
- 直觉：可以在 technique graph 上增加 tactic/intent 层，将技术序列映射为攻击阶段目标，例如凭据获取、横向移动、数据收集、外传、破坏。
- 可能方法：复用 ATT&CK tactic 作为弱标签，结合 LLM/RAG 对 CTI 上下文进行意图解释。
- 数据来源：MITRE ATT&CK procedure examples、AttacKG 数据、公开 CTI 报告。
- 可评估指标：intent classification F1、evidence citation accuracy、human evaluation。
- 相关文献：AttacKG、A survey of cyber threat attribution、TechniqueRAG。
- 风险：意图标签体系需要定义清楚，避免过度主观。
- 下一步验证：从 ATT&CK tactics 抽象 6-8 个 intent categories。
- 状态：萌芽。

### Idea-20260701-01：CTI 文本攻击图与日志溯源图的双视角证据融合

- 问题：EXTRACTOR 从 CTI 文本生成 provenance query graph，Kairos 等方法从系统审计日志生成 whole-system provenance graph，但二者通常分开研究。
- 直觉：如果能将 CTI 文本侧 attack behavior graph 与日志侧 provenance graph 对齐，可以生成更强的证据链，支撑攻击链重构、意图识别和候选归因。
- 可能方法：CTI 文本抽取攻击行为图 -> 日志/数据集中构建 provenance graph 或复用 Kairos attack summary graph -> 图匹配/检索 -> ATT&CK/RAG 解释 -> evidence-backed report。
- 数据来源：EXTRACTOR 论文场景、DARPA TC 数据集、OpTC、Kairos 代码/数据线索和公开 CTI 报告。
- 可评估指标：graph match score、attack step coverage、evidence precision/recall、TTP mapping F1、summary graph coverage。
- 相关文献：EXTRACTOR、Kairos、DEPCOMM、AttacKG。
- 风险：数据和实现复杂度较高，硕士论文需要收窄为小规模 case study。
- 下一步验证：读 DEPCOMM 后比较“异常驱动摘要图”和“图摘要压缩”两种路径，决定是否只做日志摘要图到 ATT&CK/intent 的上层语义映射。
- 状态：重点保留，但需要在 DEPCOMM 后做可行性评估。

### Idea-20260701-02：基于日志攻击摘要图的 ATT&CK 标注与意图识别

- 问题：Kairos 能从审计日志输出 compact attack summary graph，但不直接输出 ATT&CK technique、攻击意图或归因解释。
- 直觉：attack summary graph 是比原始日志更适合 LLM/RAG 处理的中间证据；如果将其映射到 ATT&CK technique/tactic，再推断攻击意图，可以形成“真实日志证据 -> 攻击语义”的论文切入点。
- 可能方法：attack summary graph 序列化 -> RAG 检索 ATT&CK procedure examples / TechniqueRAG 知识 -> technique annotation -> tactic/intent inference -> evidence citation。
- 数据来源：Kairos 支持的 DARPA TC / OpTC 数据、ATT&CK procedure examples、公开 CTI 报告。
- 可评估指标：TTP mapping F1、intent classification F1、evidence citation accuracy、hallucination rate、human usefulness score。
- 相关文献：Kairos、TechniqueRAG、AttacKG、EXTRACTOR、LLMs are Unreliable for CTI。
- 风险：公开数据中的 ground truth 可能只到攻击阶段或攻击边，未必有完整 ATT&CK 标签，需要人工标注小规模 case。
- 下一步验证：读 TechniqueRAG 前先整理 Kairos 摘要图可序列化字段：process、file、socket、event type、timestamp、reconstruction error、information flow。
- 状态：新增长期候选。

### Idea 风险更新：Attack Behavior Intermediate Representation

- 状态：暂不作为独立创新点。
- 原因：AttacKG+ 已经提出 LLM-based attack knowledge graph construction，并将攻击表示为 temporally unfolding event，每个 step 包含 behavior graph、MITRE TTP labels 和 state summary。
- 处理：只能作为相关工作/背景概念。真正创新必须继续往 intent、evidence grounding、uncertainty、CTI-log alignment 或 benchmark 方向找缺口。

## 新颖性风险检查

### 2026-06-30：经典论文只能当地基，选题创新必须用 2024-2026 工作校准

- 判断：`A survey of cyber threat attribution` 和 `AttacKG` 适合作为理论框架和方法地基，但不能直接作为创新点来源。
- 原因：
  - AttacKG 的 CTI -> attack graph -> ATT&CK technique KG 路线已经被后续 TTP extraction、RAG、LLM benchmark、GraphRAG 工作继续推进。
  - 2025-2026 已出现 TechniqueRAG、ExCyTIn-Bench、Beyond RAG for CTI 等更贴近当前热点的工作。
- 选题要求：
  - 每个 idea 必须回答“相比 2024-2026 最新工作，我新增了什么”。
  - 不能只说“用 LLM/RAG 改进 AttacKG”，必须落到更具体的缺口，例如 intent layer、证据链、置信度校准、agentic investigation、unanswerable handling。
- 下一步：为每个候选选题补一列 `latest-work-risk`。
