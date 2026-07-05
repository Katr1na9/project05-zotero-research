# 2026 - Kitten or Panda?

## 基本信息

- 题名：Kitten or Panda? Measuring the Specificity of Threat Group Behaviors in Public CTI Knowledge Bases
- 作者：Aakanksha Saha, Martina Lindorfer, Juan Caballero
- 年份：2026
- 来源：Asia CCS 2026 / arXiv:2506.10645
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/From_IOCs_to_Group_Profiles_2025.pdf`

## 一句话总结

这篇直接量化了 TTP / software / vulnerability 对 threat group attribution 的区分度不足：只有约 34% 的 ATT&CK groups 有 group-specific techniques，合并多源后很多 group 仍没有特异行为。

## 做了什么

作者系统分析 MITRE ATT&CK 和 Malpedia 中 threat group profiles 的特异性与完整性，关注哪些行为只被单个 group 使用。

关键结果：

- ATT&CK 中只有约 34% 的 groups 有 group-specific techniques；
- ATT&CK 中 group-specific software 比例更高，约 73%；
- 在更广的 Malpedia 数据中，group-specific software 下降到约 24%；
- 合并 ATT&CK 与 Malpedia 后，具有 group-specific behaviors 的 group 仍低于 30%；
- 加入 exploited vulnerabilities 和报告中抽取的额外 techniques 后，仍有约 64% 的 groups 缺少任何 group-specific behavior。

## 与 Project05 的关系

这篇是 Project05 的核心动机文献之一：

- TTP 不是天然高置信 actor evidence；
- 多源证据数量增加不等于区分度足够；
- evidence sufficiency scoring 必须考虑 distinctiveness，而不是只数 evidence item 数量；
- 如果当前证据只包含 generic TTP，应降级或拒答。

## 留给 Project05 的空间

它是测量研究，不是归因系统。它没有做：

- LLM 归因解释；
- 证据充分性门控；
- open-set / unknown actor；
- 多源证据可用性画像；
- 自动降级到 campaign / intent / technique。

## 结论

Project05 应把这篇作为 “为什么需要证据区分度与拒答” 的强支撑，同时避免声称 TTP overlap 可以直接支撑 actor attribution。

