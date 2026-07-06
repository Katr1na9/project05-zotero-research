# Correlation Analysis of APT Attack Organizations Based on Knowledge Graphs

## 基本信息

- 年份：2026
- 期刊：Electronics
- DOI：10.3390/electronics15010087
- 来源：https://www.mdpi.com/2079-9292/15/1/87
- 当前状态：纳入 Project05 二次深扫高风险材料。

## 它在研究什么

该文关注 APT attack organizations 的关联分析。它从威胁报告中抽取实体和关系，构建 APT 知识图谱，并结合结构推理、语义嵌入和时间演化模型进行多级关联分析。

## 方法核心

公开信息显示，其方法包括：

```text
APT ontology
  -> 威胁报告实体/关系抽取
  -> 实体归一化
  -> Neo4j APT KG
  -> 显式结构推理
  -> TransE / RotatE 语义嵌入
  -> T-GCN 时间演化
  -> APT organization correlation
```

## 对 Project05 的撞题影响

它压缩：

1. APT KG 构建；
2. APT 组织多级关联分析；
3. KG embedding 用于 APT 组织关系推理；
4. 时间演化建模；
5. sector-oriented threat analysis。

Project05 不能把“APT KG + 组织关联 + 时间演化”写成主创新。

## Project05 可避让空间

该工作偏向“发现组织关系/关联”，而 Project05 应强调：

- 证据不足时不能输出强组织结论；
- 组织关联只能作为候选证据；
- 需要证据充分性评分和归因粒度门控；
- 高冲突或低区分度证据触发降级或拒答。

## 精读结论

这篇 2026 工作进一步证明：APT KG 已经从“构建”推进到“组织关联分析”。Project05 后续不能再把 KG 相关能力放在权利要求主语位置，只能把 KG 作为证据通道。

