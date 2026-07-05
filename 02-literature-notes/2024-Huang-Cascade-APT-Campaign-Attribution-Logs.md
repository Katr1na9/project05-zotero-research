# 2024 - Cascade APT Campaign Attribution in System Event Logs

## 基本信息

- 题名：A Cascade Approach for APT Campaign Attribution in System Event Logs: Technique Hunting and Subgraph Matching
- 作者：Yi-Ting Huang, Ying-Ren Guo, Guo-Wei Wong, Meng Chang Chen
- 年份：2024
- 来源：arXiv:2410.22602
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/Cascade_APT_Campaign_Attribution_Logs_2024.pdf`

## 一句话总结

这篇把系统事件日志中的 APT campaign attribution 做成 `Technique hunting + subgraph matching` 级联框架，说明日志侧归因也已有方法；Project05 不能把 “日志证据进入归因” 写成泛泛创新。

## 做了什么

方法 SFM 包含两步：

1. 在系统 event logs 中检测恶意行为并映射到 MITRE ATT&CK techniques；
2. 将检测到的 technique 序列/子图与已知 APT campaign attack sequences 匹配，判断最可能的 campaign。

论文评估了 5 个真实 APT campaign。

## 与 Project05 的关系

它覆盖的是：

- provenance / event log 侧；
- campaign-level attribution；
- ATT&CK technique sequence matching；
- subgraph matching。

它没有覆盖：

- actor-level open-set attribution；
- LLM evidence-grounded explanation；
- 多源 evidence availability profile；
- 证据不足时的拒答/降级；
- false flag / TTP mimicry。

## 对选题的影响

Project05 如果纳入日志/provenance，必须避免写成：

> 基于系统日志和 ATT&CK 技术序列的 APT 活动归因方法

更安全的表述是：把日志侧输出作为一个 evidence channel，并判断它是否足以把结论从 campaign / technique 升级到 actor。

