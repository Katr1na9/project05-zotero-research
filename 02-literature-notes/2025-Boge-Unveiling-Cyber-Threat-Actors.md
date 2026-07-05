# 2025 - Unveiling Cyber Threat Actors

## 基本信息

- 题名：Unveiling Cyber Threat Actors: A Hybrid Deep Learning Approach for Behavior-Based Attribution
- 作者：Emirhan Boge, Murat Bilgehan Ertan, Halit Alptekin, Orcun Cetin
- 年份：2025
- 来源：ACM Digital Threats: Research and Practice
- DOI：10.1145/3676284
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/Unveiling_Cyber_Threat_Actors_Behavior_Based_Attribution_2025.pdf`

## 一句话总结

这篇用命令序列做 threat actor soft attribution，说明 “行为序列/命令风格归因” 已经有人做；Project05 不能把行为证据归因写成空白。

## 做了什么

作者使用 34 个 threat actors 的命令序列数据，构建 hybrid transformer + CNN 模型，学习命令序列中的全局和局部上下文。

报告结果：

- high-count dataset F1 约 95.11%；
- medium-count dataset F1 约 93.60%；
- low-count dataset F1 约 88.95%。

论文强调这是 soft attribution，不需要 hard attribution 那种直接证据。

## 与 Project05 的关系

它覆盖：

- behavior-based attribution；
- command sequence attribution；
- soft attribution；
- deep learning actor classification。

但它没有：

- LLM 证据解释；
- evidence sufficiency / refusal；
- open-set actor；
- 多源证据融合；
- 缺失证据画像。

## 对选题的影响

Project05 可以把这种模型视作一个 behavior attributor，但不能把 “行为序列可用于归因” 当创新。我们的区别必须是：当该 attributor 输出低置信、数据稀少或行为可模仿时，系统如何降级或拒答。

