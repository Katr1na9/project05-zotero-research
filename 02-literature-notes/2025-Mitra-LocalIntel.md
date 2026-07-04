# LocalIntel: Generating Organizational Threat Intelligence from Global and Local Cyber Knowledge

## 1. 基本信息

- 英文题名：LocalIntel: Generating Organizational Threat Intelligence from Global and Local Cyber Knowledge
- 中文译名：LocalIntel：融合全局与本地网络知识生成组织级威胁情报
- 作者：Shaswata Mitra; Subash Neupane; Trisha Chakraborty; Sudip Mittal; Aritran Piplai; Manas Gaur; Shahram Rahimi
- 年份：arXiv 初稿 2024；本地 PDF 为 arXiv:2401.10036v2，2025-02-09
- Venue：arXiv
- DOI / arXiv / URL：https://arxiv.org/abs/2401.10036
- Code / Dataset：https://github.com/shaswata09/LocalIntel
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：重点读
- 所属主题：LLM-CTI / RAG / Organizational CTI / Local Knowledge / Contextualization

## 2. 一句话总结

LocalIntel 提出一个组织级威胁情报 contextualization 框架，将公开全局威胁情报与组织本地知识库中的资产、配置、维护计划和历史可信情报结合，生成面向特定组织的影响分析与缓解建议。它对我的选题价值在于说明：威胁情报只有和本地上下文结合才真正可行动，而我的后续方向可以把这里的“本地组织知识”进一步替换或扩展为日志侧 provenance evidence / attack summary graph。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 全局 CTI 如 CVE/NVD/CWE/安全博客通常是 generic knowledge，不能直接告诉某个组织该怎么处置。
  - 组织内部又有本地知识，如资产位置、软件版本、配置、维护计划、DMZ 配置、可信历史 CTI 等。
  - SOC 分析师需要手动把全局威胁和本地环境结合，生成组织特定的威胁情报和缓解策略。
- 这个问题为什么重要？
  - 同一个 CVE 对不同组织影响不同，取决于资产是否存在、版本是否受影响、端口配置、维护状态和业务需求。
  - 没有全局 CTI，EDR/SOC 可能只处理局部告警，忽视更大攻击活动。
  - 没有本地知识，漏洞扫描可能产生大量不必要告警，或者给出错误缓解建议。
  - 组织通常不愿把本地知识交给第三方工具，因此 on-premise contextualization 有现实意义。
- 之前方法哪里不够？
  - Nessus、Nexpose 等工具能提示漏洞，但难以结合私有本地上下文给出准确 counteractions。
  - 传统 CTI extraction 关注从文本抽取实体、关系、TTP，但不关注组织级本地化。
  - 通用 RAG 只检索外部知识，不一定能把本地资产和全局威胁正确对齐。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 它不做 threat actor attribution 或 attack intent recognition。
  - 它做的是 organizational CTI generation，即从全局 CTI 与本地知识生成组织相关的影响和缓解策略。
  - 框架中有 Agent 控制检索/生成流程，但本文核心不是多智能体，而是 global-local knowledge contextualization。
  - 对我的方向而言，它提示可以把“本地知识库”换成“日志溯源证据库”，从而形成 CTI + provenance evidence 的证据增强分析。

## 4. 核心贡献

1. 问题贡献：提出组织级 CTI contextualization 问题，把 generic threat intelligence 转换为 organization-specific CTI。
2. 框架贡献：提出 LocalIntel，由 knowledge retrieval 和 contextualization 两个阶段组成。
3. 融合贡献：将 global threat repository 与 local organizational database 联合检索。
4. 原型贡献：构建本地组织知识库原型和评估数据集。
5. 实验贡献：在 58 个公开威胁场景、5 个组织 wiki 和 326 份组织可信 CTI 报告上评估。
6. 评估贡献：使用 RAGAs、G-EVAL、BERTScore 和 SME 人工评价评估生成质量。

## 5. 方法框架

### 输入

- 数据类型：
  - global threat intelligence：CVE、NVD、CWE、安全博客、第三方报告；
  - local organizational knowledge：组织 wiki、资产配置、软件版本、维护计划、DMZ 配置、历史可信 CTI。
- 输入格式：
  - zero-day threat report；
  - organizational wiki chunks；
  - local trusted CTI reports；
  - API search results。
- 先验知识：
  - 本地资产和配置；
  - 组织维护计划；
  - CVE/NVD 知识；
  - SOC 分析任务需求。

### 输出

- 预测结果：
  - contextualized organizational threat intelligence。
- 图结构：
  - 本文未使用正式知识图谱，但指出 local knowledge database 可替换为 knowledge graph。
- 标签：
  - 无分类标签，输出是组织级情报文本。
- 报告：
  - 包含组织特定影响、风险和 mitigation strategies。
- 证据链：
  - 输入中显式给出 retrieved global knowledge 与 retrieved local knowledge；但输出中的每个结论没有严格逐句 citation。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Global Threat Repository | 存放公开 CTI，如 CVE/NVD/CWE/安全报告 | 对应外部威胁知识源 |
| Local Knowledge Database | 存放组织资产、配置、维护、历史 CTI | 可类比本地日志/溯源证据库 |
| Agent Controller | 控制 query generation、query execution、completion generation | 可作为单控制器，不必上升为多智能体 |
| NER-based Query Generation | 从已获取知识中抽取实体生成检索查询 | 可用于 global-local 迭代检索 |
| Global Search | 通过 API 检索 NVD/CVE 等全局知识 | 可扩展到 ATT&CK/CWE/CAPEC |
| Local Search | 用向量库检索组织 wiki 和可信 CTI | 可替换为 provenance graph search |
| Contextualized Generation | LLM 基于 Gi ∪ Li 生成组织级 CTI | 后续可加入证据引用和不确定性 |

### 方法流程

```text
Zero-day / generic threat report Gi
  -> Local search over organizational database L
  -> NER and query generation over Gi ∪ Li
  -> Global search over threat repository G
  -> Iterative local/global retrieval
  -> Consolidated knowledge Gi ∪ Li
  -> LLM contextualized generation
  -> Organization-specific CTI C
```

## 6. 数据集与实验

- 数据集：
  - 58 个 trigger / zero-day generic threat intelligence reports。
  - 5 个组织 wiki，模拟 local knowledge database。
  - 326 份 confidential organizational trusted CTI reports。
  - 58 份 SME 手工生成 ground truth。
- 数据来源：
  - global repository：NVD-CVE API。
  - local database：组织 wiki + 可信 CTI 报告，PII 已匿名化。
- 实验设置：
  - local knowledge 存入 Chroma vector database。
  - chunk size = 1500，overlap = 150。
  - embedding model 使用 text-embedding-ada-002。
  - dense retrieval 使用 Maximal Marginal Relevance。
  - 硬件：Intel i9-12900、RTX 3090Ti 24GB、128GB RAM。
- 模型：
  - proprietary：GPT-3.5-turbo、GPT-4o。
  - open-source：Llama-2-7b-chat、Llama-3.1-8B-Instruct、Mistral-7B-Instruct-v0.2、Mistral-NeMo-Minitron-8B-Base、Qwen1.5-7B-Chat、Prometheus-7B、WestLake-7B-v2、WestSeverus-7B-DPO-v2 等。
- 指标：
  - RAGAs similarity；
  - G-EVAL correctness；
  - BERTScore-F1；
  - human correctness rating；
  - Fleiss Kappa inter-rater agreement。
- 主要结果：
  - Qwen1.5-7B-Chat 表现最好：RAGAs similarity 0.92，G-EVAL correctness 0.78，BERTScore-F1 0.66。
  - GPT-3.5-turbo：0.92 / 0.75 / 0.68。
  - GPT-4o：0.91 / 0.75 / 0.66。
  - Prometheus-7B 的 RAGAs similarity 最高，为 0.93，但 correctness 为 0.71。
  - Mistral-NeMo-Minitron-8B-Base 表现较弱：0.84 / 0.56 / 0.55。
  - 人工评价中 3 位 SME 的 Fleiss Kappa = 0.6477，标准误 0.0767，表示 substantial agreement。
- Case study：
  - Movistar 4G router 案例中，公开 CVE 提到 ADB port 5555，但本地配置显示该组织把相关服务配置到 port 22；如果不结合本地知识，缓解建议会错。
  - 本地维护计划进一步影响缓解策略，例如固件升级窗口与认证服务不可用风险。

## 7. 关键知识点

### 概念

- **Global Threat Repository**：公开威胁知识源，如 CVE、NVD、CWE、安全博客和第三方报告。
- **Local Knowledge Database**：组织内部知识库，包含资产、配置、维护计划、业务需求和可信 CTI。
- **Organizational CTI**：面向特定组织环境生成的威胁情报。
- **Contextualization**：把 generic CTI 翻译到组织本地语境中。
- **Generic Threat Intelligence**：通用威胁情报，对所有组织都适用但不包含本地上下文。
- **Contextualized Completion**：LLM 生成的组织级威胁情报输出。

### 技术路线

- LocalIntel 的核心不是闭卷问答，而是 global-local RAG。
- 它与 CTIConnect 的区别：
  - CTIConnect 关注异构 CTI 源之间的跨源检索和 benchmark；
  - LocalIntel 关注全局威胁知识与组织本地知识的 contextualization。
- 它与我的潜在方向的关系：
  - local organizational knowledge 可替换为 local provenance evidence；
  - organizational impact 可扩展为 attack impact / intent；
  - mitigation strategy 可扩展为 evidence-backed investigation report。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| organizational threat intelligence | 组织级威胁情报 | 本文核心输出 |
| global threat repository | 全局威胁知识库 | 公开 CTI 源 |
| local knowledge database | 本地知识库 | 组织内部私有知识 |
| contextualized CTI | 上下文化 CTI / 组织语境化 CTI |  |
| generic threat intelligence | 通用威胁情报 | 未结合组织环境 |
| contextualized completion | 上下文化生成结果 | 论文公式中的 C |
| local organizational knowledge | 组织本地知识 | Li |
| zero-day trigger | 零日触发报告 | LocalIntel 输入 |

## 8. 优点

- 问题定义清楚：global CTI 必须结合 local context 才能产生可行动情报。
- 案例直观，说明本地配置可能改变缓解建议。
- 框架模块化，可替换全局源、本地源、LLM 和检索方式。
- 同时做了自动指标和 SME 人工评价。
- 对“组织级 CTI”给出了可操作原型。

## 9. 局限

- 数据集较小，只有 58 个场景和 5 个组织 wiki。
- 本地知识库是组织 wiki + trusted CTI reports，未纳入真实 EDR、SIEM、系统审计日志或 provenance graph。
- 输出是自然语言报告，缺少严格的证据引用和可验证结构。
- 使用 RAGAs、G-EVAL、BERTScore 评估，和安全决策正确性之间仍有差距。
- Agent 设计较简单，主要是控制检索和生成，不是复杂多智能体推理。
- 没有专门评估 hallucination、calibration、consistency。

## 10. 对我选题的启发

- 可以直接借鉴：
  - global-local knowledge contextualization 的问题定义；
  - 迭代检索流程；
  - 将外部 CTI 与本地资产/配置结合生成组织级情报；
  - SME 评价和自动指标结合。
- 可以改进：
  - 把 local knowledge database 扩展为 provenance graph、InfoPath、attack summary graph。
  - 输出从自由文本改为：威胁影响、攻击意图、相关资产、证据链、缓解建议、置信度。
  - 加入 evidence citation 和 consistency/calibration 评价。
  - 将 local context 从静态 wiki 扩展到动态日志证据。
- 可以作为 baseline：
  - global CTI only；
  - local knowledge only；
  - global + local vanilla RAG；
  - global + local + provenance evidence。
- 可以用于研究动机：
  - 组织级安全决策依赖本地上下文，通用 CTI 或通用 RAG 不足以形成可行动结论。
- 可以用于实验设计：
  - 构建一个小规模 synthetic organizational environment，包含资产、配置、日志摘要和威胁报告，测试是否能生成 evidence-grounded local CTI。

## 11. 可转化的研究问题

1. 能否将 LocalIntel 的 local knowledge database 替换为 provenance graph / InfoPath，使 CTI contextualization 有真实行为证据支撑？
2. 对同一全局 CVE/ATT&CK TTP，不同本地资产配置如何改变攻击意图和影响判断？
3. 能否构建 `global CTI + local provenance evidence -> organization-specific threat attribution explanation`？
4. LocalIntel 的组织级 CTI 输出能否加入证据引用和置信度，降低 hallucination 风险？
5. 能否设计动态本地知识检索，让系统从 EDR/SIEM/provenance graph 中检索证据，而不是只查 wiki？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CTIConnect | CTIConnect 解决异构 CTI 源 RAG；LocalIntel 解决全局 CTI 与本地组织知识 contextualization |
| TechniqueRAG | TechniqueRAG 面向 ATT&CK 标注；LocalIntel 面向组织级影响和缓解策略 |
| LLM unreliable | LocalIntel 仍需补一致性、校准和幻觉评估 |
| Kairos / DEPCOMM | Kairos/DEPCOMM 可作为 LocalIntel 中 local knowledge 的动态日志证据来源 |
| CTIBench | CTIBench 评测 LLM-CTI 能力；LocalIntel 是面向 SOC 的组织级应用框架 |
| SEvenLLM | SEvenLLM 做领域模型/指令数据；LocalIntel 做具体 global-local CTI 生成 |

## 13. 论文写作可引用句式

- 通用威胁情报只有在结合组织本地资产、配置和运行状态后，才能转化为可行动安全决策。
- 组织级 CTI 生成需要同时检索外部威胁知识和内部本地知识。
- 对 SOC 分析而言，威胁影响和缓解策略取决于本地上下文，而不仅是 CVE 或 ATT&CK 标签本身。

## 14. 我的批注与疑问

- LocalIntel 很适合补充我的“本地证据”意识：威胁情报不是孤立文本，必须落到本地环境。
- 它还没有把 local knowledge 做成 provenance evidence，这正是我可以延展的方向。
- 它的评估仍偏生成文本质量，不够贴近安全因果证据和归因可靠性。
- 如果后续做实验，可以借鉴它的 synthetic local wiki 思路，但最好加入真实或模拟日志图。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是，作为 global-local CTI contextualization 关键背景
