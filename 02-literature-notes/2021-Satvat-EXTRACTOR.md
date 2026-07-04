# EXTRACTOR: Extracting Attack Behavior from Threat Reports

## 1. 基本信息

- 英文题名：EXTRACTOR: Extracting Attack Behavior from Threat Reports
- 中文译名：EXTRACTOR：从威胁报告中抽取攻击行为
- 作者：Kiavash Satvat; Rigel Gjomemo; V. N. Venkatakrishnan
- 年份：2021
- Venue：IEEE European Symposium on Security and Privacy, EuroS&P 2021
- DOI / arXiv / URL：10.1109/EuroSP51992.2021.00046 / https://arxiv.org/abs/2104.08618
- 阅读日期：2026-07-01
- 阅读优先级：必读
- 所属主题：CTI Structure / Attack Graph / Provenance Graph / Threat Hunting

## 2. 一句话总结

EXTRACTOR 试图把非结构化 CTI 威胁报告中的攻击行为自动抽取为简洁的 provenance graph，使这些从文本中提取出的攻击图可以直接作为威胁狩猎系统的 query graph 使用。

## 3. 研究问题

- CTI 报告中有大量攻击知识，但这些知识嵌在长文本、博客、白皮书和报告中，难以被自动化安全分析工具使用。
- 现有方法多抽取 IOC 或局部实体，不能完整表达攻击行为的因果、时序和实体关系。
- 安全分析真正需要的是可操作的行为图：哪些进程、文件、注册表、网络对象参与了攻击，它们之间发生了什么系统行为。

## 4. 核心贡献

1. 提出 EXTRACTOR，从自然语言 CTI 报告中自动抽取简洁攻击行为。
2. 将攻击行为表示为 provenance graph，图中节点是系统实体，边是系统调用/行为关系。
3. 针对 CTI 文本的特殊语言问题设计一套 NLP pipeline，包括归一化、指代消解、文本摘要和图生成。
4. 将自动生成的攻击图用于 POIROT threat hunting 系统，验证其可用于真实威胁检测。

## 5. 方法框架

### 输入

- 非结构化 CTI 报告；
- CTI noun dictionary；
- system call synonym dictionary；
- 威胁狩猎系统可用的系统调用/实体语义。

### 输出

- 简洁 provenance graph；
- 图节点：进程、文件、注册表、IP、网络连接等系统实体；
- 图边：write、read、send、receive、connect、fork、exec 等系统行为。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Normalization | 将长句、复杂句转成更容易处理的单动作短句 | CTI 文本预处理很关键 |
| Tokenization | 按换行、编号、项目符号、标题等切分 CTI 长句 | 通用 NLP 分句器不适合 CTI |
| Homogenization | 将 C2/C&C/Command and Control 等同义表达归一 | 术语归一可降低实体碎片化 |
| Passive-to-active Conversion | 将被动句转成主动句 | 有助于确定动作主体和对象 |
| Ellipsis Subject Resolution | 补全省略主语 | CTI 报告常用连续动作描述同一 malware |
| Pronoun Resolution | 将 it/itself 等代词替换为真实实体 | 避免图中出现无意义代词节点 |
| Entity Resolution | 合并同一实体的不同表达 | 提升图结构一致性 |
| Text Summarization | 保留可在审计日志中观测到的攻击行为句 | 过滤背景介绍、作者信息和不可观测描述 |
| Graph Generation | 用 SRL 和系统调用语义生成 provenance graph | 文本到图的核心步骤 |

### 方法流程

```text
CTI 报告
  ↓
Normalization：分句、同义归一、被动转主动
  ↓
Resolution：省略主语、代词、实体消解
  ↓
Text Summarization：过滤非攻击行为文本
  ↓
Semantic Role Labeling + system call mapping
  ↓
Graph Generation：生成 provenance graph
  ↓
Threat Hunting：作为 POIROT query graph
```

## 6. 关键知识点

### CTI 文本的特殊难点

- Verbosity：报告中大量内容不是攻击行为，例如背景、广告、厂商说明。
- 句子过长：CTI 报告常用项目符号、编号和长句描述多个动作。
- 领域术语复杂：C2、C&C、Command and Control 指向同一概念。
- 省略主语：连续动作中常省略 malware/process 主体。
- 指代复杂：it、itself、the malware 等需要映射回真实实体。
- 关系抽取难：只靠 dependency parsing 不够，需要考虑语义角色。

### Provenance graph 的意义

EXTRACTOR 不是只抽取 IOC，而是抽取可以和系统审计日志匹配的行为图。

这类图能表达：

- 进程执行了什么；
- 文件被谁写入或删除；
- 注册表被谁修改；
- 哪个进程连接了 C2；
- 攻击行为之间的因果/信息流方向。

### 与 AttacKG 的区别

| 维度 | EXTRACTOR | AttacKG |
|---|---|---|
| 目标 | 从 CTI 报告抽取 provenance graph | 从 CTI 报告构建 ATT&CK technique knowledge graph |
| 输出 | 可用于 threat hunting 的 query graph | Technique templates / Technique Knowledge Graph |
| 重点 | 文本攻击行为到系统行为图 | 攻击图到 ATT&CK 技术识别与跨报告聚合 |
| 下游 | 日志图匹配、威胁狩猎 | ATT&CK 技术知识沉淀 |

## 7. 数据集与实验

- 数据来源包括 APT report repository、Microsoft Threat Center、Symantec Security Center、Threat Encyclopedia、Virus Radar 等。
- 文本摘要数据集：8,000 个句子，其中 3,800 个 productive，4,200 个 non-productive。
- 划分：4,800 train，1,600 validation，1,600 test。
- 大规模实验：4,100 个 Microsoft Security Intelligence 报告和 11,600 个 TrendMicro 报告。
- 使用 POIROT 作为威胁狩猎系统，将 EXTRACTOR 自动生成的图作为 query graph 在审计日志 provenance graph 中搜索。

### 主要结果

- 公共 CTI 报告图抽取平均 F1 约 0.93。
- 大规模随机报告评估 precision 0.88，recall 0.93，F1 0.90。
- 句子 verbosity 分类中 BERT F1 约 0.953，优于 CNN 和 LSTM。
- 生成的 graph 能在 POIROT 中成功用于 threat detection，接近人工专家构建 query graph 的作用。

## 8. 优点

- 从 CTI 文本到可执行威胁狩猎图的链条清晰。
- 不停留在 IOC 层，而是抽取系统行为关系。
- 对 CTI 特殊语言问题处理细致，包括分句、同义归一、省略主语、代词消解。
- 与 provenance graph 和 audit log 的安全调查场景连接紧密。

## 9. 局限

- pipeline 强依赖规则、词典和传统 NLP 工具，迁移到新领域或新写作风格可能成本较高。
- 输出图更偏系统调用和审计日志可观测行为，不直接处理 ATT&CK technique、actor attribution 或 attack intent。
- 语义理解有限，复杂跨句推理、隐含意图、反事实和不确定性处理不足。
- 不包含 LLM/RAG 机制，无法动态利用外部知识库或生成解释性报告。

## 10. 对我选题的启发

- EXTRACTOR 可作为“CTI 文本 -> 攻击行为图”的基础文献。
- AttacKG 在 EXTRACTOR 的基础上进一步走向 ATT&CK technique 和 KG；Kairos 则会从真实系统日志/provenance 角度补全另一端。
- 我的选题可以把这条链扩展为：

```text
CTI 文本
  ↓
攻击行为图
  ↓
ATT&CK/TTP 映射
  ↓
RAG/KG 检索证据
  ↓
攻击意图识别
  ↓
证据增强候选归因
```

- 如果后续做 LLM/RAG，可以将 EXTRACTOR 的规则 pipeline 作为被替代或增强的对象，而不是从零构建。

## 11. 可转化的研究问题

1. LLM 能否比 EXTRACTOR 的规则/NLP pipeline 更稳地抽取 CTI 攻击行为图？
2. 如何将 EXTRACTOR 的 provenance graph 与 AttacKG 的 ATT&CK technique graph 对齐？
3. 从 CTI 文本图和系统日志 provenance graph 两端融合，能否提升攻击链证据完整性？
4. 能否在攻击行为图上增加 attack intent 和 attribution evidence 层？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AttacKG | AttacKG 可视为在攻击行为图基础上进一步做 ATT&CK 技术识别和技术知识图谱 |
| Kairos | Kairos 从系统审计日志侧构建 whole-system provenance，用于检测和调查 |
| DEPCOMM | DEPCOMM 关注审计日志图摘要，解决日志图过大的问题 |
| TechniqueRAG | TechniqueRAG 用 RAG 做 ATT&CK technique annotation，可补足 EXTRACTOR 不做 ATT&CK 映射的问题 |

## 13. 论文写作可引用观点

- CTI 报告中的攻击知识常嵌入大量非结构化文本，需要被转化为机器可处理的行为表示。
- 与孤立 IOC 相比，攻击行为图能够表达实体之间的因果和信息流关系。
- CTI 文本结构化的关键困难不是简单实体识别，而是动作主体、对象、时序、因果和跨句指代的恢复。

## 14. 我的批注与疑问

- EXTRACTOR 的图更接近系统行为层，AttacKG 的图更接近 ATT&CK 技术层。两者之间是否可以构建统一的中间表示？
- 如果只做 CTI 文本，是否会缺少真实日志证据？如果融合日志，则数据获取和实验复杂度会增加。
- 后续读 Kairos 时重点比较：文本生成的 provenance graph 和审计日志生成的 provenance graph 是否能对齐。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

