# Research Dashboard

## 项目定位

研究方向：LLM 增强的威胁溯源 / 攻击归因 / 攻击行为意图感知。RAG、ATT&CK、威胁知识图谱、CTI 和 provenance graph 都是支撑模块；Agentic AI 暂作为后置补充模块。

目标：不是泛泛地做“大模型安全”，而是找到一个可落地、可实验、可写成硕士论文的研究切入点。

## 当前主问题

> LLM 如何增强威胁溯源/攻击归因中的证据理解、攻击链重构、意图识别和归因解释？

## 当前候选方向

| 编号 | 方向 | 简述 | 状态 |
|---|---|---|---|
| T1 | LLM + RAG/KG 支撑归因证据理解 | 用 RAG/KG 为 LLM 提供 TTP、ATT&CK、CVE/CWE、CTI 证据 | 重点跟进 |
| T2 | 多智能体安全调查 | 日志检索、TTP 映射、证据验证、报告生成多 agent 协作 | 后置补充 |
| T3 | 可信 LLM 威胁归因 | 幻觉缓解、置信度校准、证据引用 | 待评估 |
| T4 | CTI + 日志溯源证据融合 | 将 CTI 文本攻击图与 Kairos/DEPCOMM 类日志证据对齐，服务威胁溯源和归因解释 | 重点跟进 |

## 核心文献优先队列

| 优先级 | 论文 | 目的 | 笔记状态 |
|---|---|---|---|
| P0 | A survey of cyber threat attribution | 建立威胁归因大图谱 | 已沉淀 |
| P0 | AttacKG | CTI 到 ATT&CK 技术知识图谱 | 已沉淀 |
| P0 | EXTRACTOR | CTI 到攻击行为图 | 已沉淀 |
| P0 | Kairos | 溯源图与安全调查 | 已沉淀 |
| P0 | DEPCOMM | 系统审计日志图摘要与攻击调查 | 已沉淀 |
| P0 | TechniqueRAG | RAG 做 ATT&CK 技术标注 | 已沉淀 |
| P1 | CTIBench | LLM-CTI 评测 | 已沉淀 |
| P1 | Large Language Models are Unreliable for CTI | 可信与幻觉 | 已沉淀 |
| P1 | TTPXHunter | 完整威胁报告到 ATT&CK TTP 抽取 | 已沉淀 |
| P1 | SEvenLLM | 安全事件指令数据、领域模型与 benchmark | 已沉淀 |
| P1 | CTIConnect | 异构 CTI RAG benchmark | 已沉淀 |
| P1 | LOCALINTEL | 组织级 CTI + 本地知识 RAG | 已沉淀 |
| P1 | Beyond RAG for CTI | GraphRAG / HybridRAG 检索架构与失败模式 | 已沉淀 |
| P1 | A Modular Approach to Automatic Cyber Threat Attribution using Opinion Pools | 模块化可信归因与概率融合 | 已沉淀 |
| P1 | High Stakes, Low Certainty | 勒索软件归因中高层 IoC/TTP 的证据可靠性 | 已沉淀 |

## 本周目标

- [ ] 建立 Zotero 集合和标签规范。
- [x] 完成核心文献第一轮精读：综述、AttacKG、EXTRACTOR、Kairos、TechniqueRAG。
- [x] 整理术语表 v0.1。
- [ ] 延后：所有核心/扩展文献读完后，由你手动决定是否进入 3 个候选硕士论文题目比较。

## 当前阅读路线

详见：[reading-roadmap.md](../04-progress/reading-roadmap.md)

### 下一步任务：2026-07-04

1. 补读 `Multi-Step LLM Pipeline`、`Open-CyKG` 等 CTI 到 ATT&CK/KG 支撑文献。
2. 继续补齐 `UNICORN`、`THREATRACE`、`PROGRAPHER`、`ADAPT it!` 等对比方法。
3. 在所有文献沉淀完成、研究方向初步凝练后，再做截至 2026-07-04 的最新成果/撞题检索。

## 延后决策

| 决策 | 触发条件 | 说明 |
|---|---|---|
| 形成 3 个候选硕士论文题目 | 所有核心/扩展文献完成第一轮沉淀后 | 由你手动决定，Codex 只提供候选方向、证据和可行性矩阵 |

## 当前阻塞

| 日期 | 阻塞 | 影响 | 处理 |
|---|---|---|---|
| 2026-06-30 | Zotero 翻译术语不稳定 | 影响精读效率 | 已改用 Bing，后续考虑 GPT/Gemini prompt |

## 决策记录

| 日期 | 决策 | 理由 |
|---|---|---|
| 2026-06-30 | 建立 project05-zotero 作为科研工作区 | 将 Zotero、文献、选题、日志和论文写作流程集中管理 |
| 2026-07-01 | 将 Kairos 纳入核心主线 | 选题需要同时考虑 CTI 文本侧攻击图和日志侧 provenance evidence |
| 2026-07-04 | 严格按 README/SOP 推进 | 单篇论文必须使用精读模板；批量扫描只能作为预筛索引，不能替代单篇精读笔记 |
| 2026-07-04 | 候选题比较延后 | 先完成术语表和文献沉淀，避免过早收窄方向 |
| 2026-07-04 | 完成术语表 v0.1 | 统一归因、CTI、ATT&CK、溯源图、RAG、Agent、可信评估等术语译法 |
| 2026-07-04 | 将 DEPCOMM 纳入日志侧证据主线 | DEPCOMM 提供 POI 驱动的 dependency graph summarization，与 Kairos 的 attack summary graph 形成互补 |
| 2026-07-04 | 将 CTIBench 纳入评测主线 | CTIBench 提供 LLM-CTI 的五类任务，尤其 CTI-ATE 和 CTI-TAA 可支撑后续实验设计 |
| 2026-07-04 | 将 LLM unreliable 纳入可信评测主线 | 真实长度 CTI 报告上的性能、一致性和置信度校准应成为后续方法评价维度 |
| 2026-07-04 | 将 TTPXHunter 纳入 TTP 抽取基线 | TTP 抽取已较成熟，后续创新应上移到 intent、证据链和可信归因 |
| 2026-07-04 | 将 SEvenLLM 纳入领域模型背景线 | 领域指令数据和 benchmark 很重要，但不能替代证据增强归因方法 |
| 2026-07-04 | 将 Agent 论文后置为 appendix | 当前优先研究大模型与现有威胁溯源/归因/RAG/KG 方法融合，Agent 作为后续新技术扩展补充 |
| 2026-07-04 | 将 CTIConnect 纳入异构 RAG 主线 | CTIConnect 说明 CTI RAG 的关键是跨源语义鸿沟、任务路由、证据检索和证据利用 |
| 2026-07-04 | 将 LocalIntel 纳入组织上下文主线 | LocalIntel 说明全局 CTI 必须结合本地资产、配置和知识，才可生成组织级可行动情报 |
| 2026-07-04 | 将 Beyond RAG for CTI 纳入混合检索主线 | GraphRAG 有助于多跳 CTI 关系检索，但必须处理结构性幻觉、拒答失败和延迟不稳定 |
| 2026-07-04 | 将 Opinion Pools 纳入可信归因主线 | 威胁归因应输出 actor 概率分布，并通过多证据模块融合而不是单一黑盒模型完成 |
| 2026-07-04 | 将 High Stakes 纳入证据可靠性主线 | 勒索软件场景中 TTP/高层 IoC 区分度不足，归因系统必须表达 evidence sufficiency、不确定性和拒答 |
