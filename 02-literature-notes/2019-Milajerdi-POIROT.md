# POIROT: Aligning Attack Behavior with Kernel Audit Records for Cyber Threat Hunting

## 1. 基本信息

- 英文题名：POIROT: Aligning Attack Behavior with Kernel Audit Records for Cyber Threat Hunting
- 中文译名：POIROT：面向网络威胁狩猎的攻击行为与内核审计记录对齐
- 作者：Sadegh M. Milajerdi, Birhanu Eshete, Rigel Gjomemo, V. N. Venkatakrishnan
- 年份：2019
- Venue：ACM CCS 2019
- DOI / arXiv / URL：https://doi.org/10.1145/3319535.3363217；https://arxiv.org/abs/1910.00056
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：必读
- 所属主题：CTI-provenance alignment / Threat hunting / Graph matching
- 阅读状态：arXiv 正文级精读；重点服务 Project05 撞题边界

## 2. 一句话总结

POIROT 是 CTI 查询图与本地 provenance graph 对齐的奠基工作：它把威胁狩猎形式化为不精确图模式匹配，用 CTI 中 IOC 及其关系构造 query graph，再在内核审计日志生成的 provenance graph 中寻找攻击活动。

## 3. 研究问题

- CTI 中通常不只有孤立 IOC，还包含 IOC 之间的因果或行为关系；传统搜索常忽略这些关系。
- 低层审计日志规模巨大，攻击步骤隐藏在海量正常行为中，需要一种能把高层 CTI 行为模式落到本地日志图上的方法。
- 核心问题不是“归因到哪个组织”，而是“已知 CTI 攻击行为是否发生在本地系统中，以及发生在哪里”。

## 4. 核心贡献

1. 将 CTI correlation 转换为 query graph，将 kernel audit log 转换为 provenance graph，并提出两者之间的不精确图对齐。
2. 设计 similarity metric 来评估 query graph 与 provenance graph 中候选子图的匹配程度。
3. 在真实公开 incident report 和 DARPA adversarial engagement 场景上验证，能在百万级节点图中定位攻击。

## 5. 方法框架

### 输入

- CTI 报告中的 IOC、observable、实体关系。
- Linux / FreeBSD / Windows 等系统的 kernel audit records。

### 输出

- 与 CTI query graph 对齐的本地攻击子图。
- 匹配分数和候选攻击路径。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| CTI query graph 构造 | 把 CTI 关系结构化为图 | 证明“CTI 结构化为图”不是新点 |
| Provenance graph 构造 | 从 kernel audit records 建本地因果图 | 可作为上游证据状态来源 |
| Inexact graph pattern matching | 允许攻击行为与 CTI 模式不完全一致 | 是后续 DeepHunter/MEGR-APT/APT-CGLP 的谱系起点 |

### 方法流程

```text
CTI report
  -> IOC / relationship extraction
  -> query graph
kernel audit records
  -> provenance graph
query graph + provenance graph
  -> inexact graph pattern matching
  -> suspicious aligned subgraph
```

## 6. 数据集与实验

- 数据：公开 incident reports，以及 DARPA Transparent Computing adversarial engagement。
- 平台：Linux、FreeBSD、Windows。
- 指标：能否定位攻击、查询时间、图规模适应能力、匹配质量。
- 结果要点：论文声称可在包含百万级节点的大图中几分钟内定位攻击。

## 7. 关键知识点

### 概念

- Query graph：由 CTI 中 IOC 与关系构成的攻击行为模式图。
- Provenance graph：由审计日志构成的系统实体因果图。
- Inexact graph pattern matching：允许候选子图与查询图不完全同构的近似匹配。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| cyber threat hunting | 网络威胁狩猎 | 安全运营语境 |
| kernel audit records | 内核审计记录 | 系统审计日志 |
| provenance graph | 溯源图 / provenance 图 | 项目内保留 provenance graph |
| query graph | 查询图 | CTI 行为模板 |

## 8. 优点

- 开创了 CTI relation 到 provenance graph 匹配的主线。
- 把 IOC 关系用于狩猎，而不是只做 IOC keyword search。
- 强调现实日志规模和跨平台审计记录。

## 9. 局限

- 依赖 CTI 中能够抽取出相对清晰的 query graph。
- 图匹配与启发式 similarity 仍可能受日志缺失、行为变体、CTI 粒度不一致影响。
- 终点是威胁狩猎和攻击定位，不处理归因粒度、证据充分性、主动取证规划。

## 10. 对我选题的启发

- 直接红线：不能把“从 CTI 图到本地日志图的对齐/匹配”作为 Project05 主创新。
- 可作为上游：Project05 可以把 POIROT 式匹配结果抽象成 evidence alignment state。
- 可作为 baseline：在实验中可把 POIROT 风格对齐器视为“静态查询图匹配”基线。
- 留出的空间：对齐之后如何判断证据足够支持哪个归因粒度，以及下一步该取什么证据，POIROT 没做。

## 11. 可转化的研究问题

1. 当 query graph 只部分匹配 provenance graph 时，系统应输出检测结论，还是降级为“不足以支持更高粒度归因”？
2. 如何把 POIROT 的匹配分数拆解为可解释证据状态，而不是单一 hunting score？
3. 如何基于当前匹配缺口规划下一步日志、样本、网络、CTI 证据获取？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| DeepHunter | 用 GNN 表征学习增强 POIROT 式 graph matching 的鲁棒性 |
| MEGR-APT | 解决 POIROT/DeepHunter 在大规模图上的内存和效率问题 |
| CLIProv | 从结构图匹配转向日志序列与威胁情报语义对齐 |
| APT-CGLP | 端到端 provenance graph 与 CTI report 的图语言预训练 |

## 13. 论文写作可引用句式

- 现有 threat hunting 工作已经能够把 CTI 中的攻击行为关系对齐到本地 provenance graph，但其输出主要服务攻击定位，而非证据充分性判定和取证动作规划。

## 14. 我的批注与疑问

- POIROT 是必须引用的“起点文献”。只要论文里提 CTI-local evidence alignment，就绕不开它。
- 我们应该避免在权利要求里写成“构建 CTI 查询图并与审计日志图匹配”，这会直接撞上 POIROT 谱系。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

