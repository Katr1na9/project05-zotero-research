# LLM 语义建图层 prior-art 调研协议 v0.1

日期：2026-07-17  
状态：`review_complete_for_architecture_decision`  
类型：范围综述 / 新颖性尽调，不是论文结果稿

## 1. 决策问题

Project05 拟研究的完整链路为：

```text
原始日志 + CTI 文本 + provenance 事件
  → LLM 语义对齐 / 编译
  → 带来源回指的可执行溯源图
  → 调查控制器判断可溯源性
  → 在成本约束下规划取证顺序与 STOP
```

本调研要回答：

1. 是否已有工作完整实现上述链路？
2. 是否已有工作完成其中的“多模态安全证据 → 统一 provenance graph”层？
3. 已有 LLM 工作输出的是文本、IOC/TTP、普通知识图谱、攻击图，还是案例级系统溯源图？
4. 输出图是否带原始证据指针、案例/主机/时间锚点和可验证的支持边界？
5. 输出是否实际进入自动调查控制、可溯源性判定、成本约束取证规划或 STOP？
6. 若完整先例不存在，最接近的模型、数据、schema 和开源实现是什么？

## 2. 预注册判定标准

只有同时满足以下六项，才判为“完整先例”：

1. 输入至少覆盖原始/半结构化主机或网络日志与 CTI 文本中的两类；
2. 使用 LLM 或语言模型完成跨来源语义对齐，而非纯规则解析；
3. 输出案例级实体—关系图，并能映射到系统 provenance 节点/边；
4. 每条关键边可回指原始来源或文本 span；
5. 输出图被下游自动调查/溯源控制器实际消费；
6. 下游显式处理取证成本、动作顺序、可溯源性或停止决策中的至少一项。

仅满足 1–4 项的工作判为“LLM 编译层局部先例”；仅做 CTI 知识图谱、日志解析、
攻击图生成或 LLM threat hunting 的工作判为“邻接先例”。

## 3. 检索范围

- 时间：2018-01-01 至 2026-07-17；LLM 重点为 2022 年以后。
- 语言：英文为主，补充可核验中文论文。
- 文献类型：同行评审会议/期刊、arXiv 预印本、正式技术报告；开源仓库仅作实现证据。
- 数据库：OpenAlex、Semantic Scholar、arXiv、Crossref，以及 IEEE、ACM、USENIX、
  NDSS、Springer、Elsevier、AAAI、ACL/EMNLP 等论文官网。

## 4. 核心检索式

### A. 直接交叉

1. `("large language model" OR LLM) AND ("provenance graph" OR "system provenance") AND cybersecurity`
2. `(LLM OR "language model") AND (APT OR "advanced persistent threat") AND provenance`
3. `(LLM OR "foundation model") AND "security log" AND (graph OR provenance)`
4. `(LLM OR "large language model") AND "cyber threat intelligence" AND "knowledge graph"`
5. `(LLM OR "large language model") AND ("attack graph" OR "investigation graph") AND cybersecurity`

### B. 编译层分解

6. `LLM security log parsing semantic normalization entity relation extraction`
7. `LLM CTI entity relation extraction STIX knowledge graph`
8. `LLM provenance graph construction from logs`
9. `LLM telemetry to knowledge graph cybersecurity`
10. `LLM grounded cyber threat intelligence source attribution`

### C. 下游闭环

11. `LLM autonomous cyber investigation evidence acquisition planning cost`
12. `LLM threat hunting provenance graph action planning`
13. `cyber investigation planner provenance graph acquisition cost`
14. `APT investigation graph minimum cost evidence collection`

### D. 已知邻接工作与引文链

15. `SEVENLLM cyber threat intelligence`
16. `AttackKG cyber threat intelligence knowledge graph`
17. `TTP extraction CTI large language model`
18. `provenance graph APT detection investigation DARPA TC`

## 5. 纳入标准

- 明确描述输入、输出和下游用途；
- 能获得摘要，核心候选优先获得全文；
- 对本项目至少覆盖一个关键模块：日志语义化、CTI 结构化、图构建、来源 grounding、
  provenance 映射、自动调查或成本规划；
- 重复预印本与正式版本只保留信息更完整的一版。

## 6. 排除标准

- 仅做恶意软件/告警分类、文本摘要或问答，没有结构化关系输出；
- 仅从既有 ATT&CK/STIX 生成说明，不处理案例证据；
- 仅做普通企业知识图谱，与网络安全调查无关；
- 纯 provenance APT 检测但没有 LLM：只作为下游/历史基线，不算 LLM 先例；
- 仅概念性宣称“可用于调查”，没有实际接口、图或评测；
- 二手博客无法追溯到论文或正式实现。

## 7. 数据抽取字段

每篇候选至少记录：题名、作者、年份、venue、DOI/arXiv、代码、输入模态、输出表示、
是否案例级、是否 provenance、是否来源回指、是否 LLM、是否接下游调查、是否成本规划、
数据集、主要指标、局限、与 Project05 的可复用关系。

## 8. 预定裁决

- `complete_precedent`：六项全部满足，原则上复用/包装，不再宣称新编译层。
- `partial_compiler_precedent`：存在成熟编译层但缺少 Project05 下游闭环，优先复用后集成。
- `fragmented_prior_art`：能力分散在 CTI KG、日志解析、provenance 检测和调查规划中；
  可立项做统一编译层，但创新必须落在跨来源对齐、证据回指或可执行接口。
- `insufficient_evidence`：检索证据不足，不得据此宣称空白。

## 9. 输出物

- `search-results-*.json`：各数据库原始检索结果；
- `screening-matrix.csv`：去重、筛选与排除理由；
- `prior-art-evidence-matrix.csv`：核心论文六项覆盖矩阵；
- `llm-provenance-compiler-prior-art-review-v0.1.md`：可审阅结论稿；
- `figures/prior-art-gap-map.png`：研究版图与缺口图。
