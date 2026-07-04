# AttacKG: Constructing Technique Knowledge Graph from Cyber Threat Intelligence Reports

## 1. 基本信息

- 英文题名：AttacKG: Constructing Technique Knowledge Graph from Cyber Threat Intelligence Reports
- 中文译名：AttacKG：从网络威胁情报报告构建攻击技术知识图谱
- 作者：Zhenyuan Li; Jun Zeng; Yan Chen; Zhenkai Liang
- 年份：2022
- Venue：ESORICS 2022
- DOI / arXiv / URL：10.1007/978-3-031-17140-6_29 / https://arxiv.org/abs/2111.07093
- 阅读日期：2026-06-30
- 阅读优先级：必读
- 所属主题：ATT&CK-KG-RAG / CTI Structure / Attack Graph

## 2. 一句话总结

AttacKG 将非结构化 CTI 报告解析为攻击行为图，并通过与 MITRE ATT&CK procedure examples 构建的技术模板进行图对齐，识别攻击技术并跨报告聚合形成 Technique Knowledge Graph。

## 3. 研究问题

- CTI 报告中的自然语言攻击描述如何转成结构化攻击图？
- 如何从攻击图中识别对应的 ATT&CK 技术？
- 如何跨多篇报告聚合同一技术的实现细节，形成可复用知识？

## 4. 核心贡献

1. 提出从 CTI 报告自动构建攻击行为图的方法。
2. 使用 ATT&CK procedure examples 初始化 technique templates。
3. 通过图对齐识别攻击图中的 ATT&CK 技术。
4. 跨报告聚合形成 Technique Knowledge Graph。

## 5. 方法框架

### 输入

- CTI 报告文本；
- MITRE ATT&CK procedure examples；
- IOC、实体、依赖关系等攻击知识。

### 输出

- Attack Graph；
- ATT&CK technique mapping；
- Technique Template；
- Technique Knowledge Graph。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| CTI Parser | 从报告中抽取攻击实体、IOC 和依赖关系 | 可作为 CTI 结构化前处理思路 |
| Attack Graph Builder | 将实体和依赖关系组织为攻击行为图 | 可作为攻击链/证据链中间表示 |
| Technique Template | 表示某个 ATT&CK 技术的典型行为结构 | 可扩展为意图模板或 tactic-level 模板 |
| Graph Alignment | 将报告攻击图与技术模板匹配 | 可作为 RAG/KG 证据匹配基础 |
| TKG Construction | 跨报告聚合同一技术知识 | 可作为威胁知识图谱构建参考 |

### 方法流程

```text
CTI 报告
  ↓
实体/IOC/依赖关系抽取
  ↓
攻击行为图 Attack Graph
  ↓
与 ATT&CK Technique Template 图对齐
  ↓
识别 ATT&CK 技术
  ↓
跨报告聚合 Technique Knowledge Graph
```

## 6. 关键知识点

- IOC 不够，实体之间的关系和攻击链结构更重要。
- ATT&CK technique 可以作为连接 CTI 文本和标准化攻击行为的中间层。
- Procedure examples 可作为构建技术模板的弱监督知识来源。
- 图结构比关键词匹配更适合表达攻击行为。
- 跨报告聚合可以弥补单篇 CTI 报告信息不完整的问题。

## 7. 实验信息

- 使用 MITRE ATT&CK procedure examples 构建 technique templates。
- 使用真实 CTI 报告构建 attack graphs。
- 评价任务包括攻击实体抽取、依赖关系抽取和技术识别。
- 论文报告技术识别 F1 接近 0.8，说明图结构对 TTP 映射有效。

## 8. 优点

- 从非结构化 CTI 到结构化图的流程完整。
- 不只抽取 IOC，而是保留攻击行为关系。
- ATT&CK 知识和真实报告知识结合紧密。
- 很适合作为 KG/RAG/攻击链推理的基础文献。

## 9. 局限

- 主要依赖传统 NLP pipeline，语义推理能力有限。
- 聚焦 ATT&CK technique 识别，不直接做攻击意图识别。
- 缺少 LLM/RAG 机制，无法动态解释或补充上下文。
- 证据置信度和冲突证据处理不足。

## 10. 对我选题的启发

- 可以把 AttacKG 作为“CTI -> 攻击图 -> ATT&CK 技术”的基础路线。
- 我的改进空间可以放在：
  - 用 LLM 改进实体/关系抽取；
  - 用 RAG 检索 ATT&CK 和历史 CTI 证据；
  - 从 technique/tactic 序列进一步推断攻击意图；
  - 为归因输出生成证据链和置信度。

## 11. 可转化的研究问题

1. 能否用 LLM/RAG 替代或增强 AttacKG 的传统 NLP pipeline？
2. 能否在 Technique Knowledge Graph 上增加 intent layer？
3. 能否将 TKG 用于候选威胁行为体归因和证据链生成？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| EXTRACTOR | 更早的 CTI 报告到攻击行为图方法 |
| TTPDrill | 更早的 TTP/威胁动作抽取方法 |
| TechniqueRAG | 可作为 AttacKG 的 RAG 化后续方向 |
| CTIBench | 可作为 LLM-CTI 评测补充 |

## 13. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

