# 2025 - APT Attribution Using Deep Reinforcement Learning

## 基本信息

- 题名：Advanced Persistent Threats (APT) Attribution Using Deep Reinforcement Learning
- 作者：Animesh Singh Basnet, Mohamed Chahine Ghanem, Dipo Dunsin, Hamza Kheddar, Wiktor Sowinski-Mydlarz
- 年份：2025
- 来源：ACM Digital Threats: Research and Practice accepted manuscript
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/APT_Attribution_Deep_Reinforcement_Learning_2025.pdf`

## 一句话总结

这篇把 APT malware attribution 建成 DRL 问题，使用 Cuckoo 行为报告和 APT Malware Dataset；它压住 “AI/强化学习做 APT malware attribution” 方向，但没有处理 open-set、拒答和 LLM 解释。

## 做了什么

论文分析 3,500+ malware samples，覆盖 12 个 APT groups，使用 Cuckoo Sandbox 提取行为特征，将 attribution 决策建模为 DRL。

报告结果：

- DRL test accuracy 约 94.12%；
- 优于 SGD、SVC、KNN、MLP、Decision Tree 等传统模型；
- reward 与 attribution accuracy 和 confidence 相关。

## 与 Project05 的关系

它是 malware behavior channel 上的强相关工作。Project05 不能写成：

> 使用强化学习/AI 根据恶意软件行为进行 APT 归因

但可以把它放入 evidence channel / baseline。

## 留给 Project05 的空间

它没有解决：

- out-of-scope actor；
- abstention / refusal；
- evidence sufficiency；
- 多源 evidence availability；
- LLM 自然语言解释；
- 证据缺失时的归因粒度降级。

## 结论

Project05 的方法应把 malware attribution 视为一个候选 attributor，而不是终点。创新仍应落在融合后的 sufficiency gating 与拒答行为。

