# HG-CTA: A heterogeneous graph-based approach for cyber threat attribution

## 基本信息

- 年份：2024
- 来源：https://dl.acm.org/doi/fullHtml/10.1145/3651671.3651707
- 当前状态：纳入 Project05 二次深扫高风险材料。ACM 页面访问受限，当前基于公开检索摘要做风险精读。

## 它在研究什么

HG-CTA 提出一种基于异构图的 cyber threat attribution 方法，利用 cyber threat intelligence 构建异构图，并在图上进行威胁归因。

公开摘要显示其核心链路为：

```text
Cyber Threat Intelligence
  -> heterogeneous graph
  -> graph-based threat attribution
```

## 对 Project05 的撞题影响

HG-CTA 会压缩：

1. 基于 CTI 构建异构图；
2. 在异构图上做 cyber threat attribution；
3. 多类型实体/关系参与归因；
4. 图结构证据增强威胁行为体判断。

这与 Project05 早期“多源证据融合 + 图结构 + 归因”高度接近。

## Project05 可避让空间

Project05 后续不能写成：

> 使用异构威胁情报图提升归因准确率。

更安全的差异点是：

- 异构图只作为证据来源；
- 归因前先判断证据充分性；
- 证据不足时输出降级或拒答；
- LLM 只解释门控结果；
- 输出缺失证据需求，而不是强制 actor label。

## 风险等级

红色。

它说明“CTI 异构图归因”不是新空间。

