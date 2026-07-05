# 2026 - Uncovering Vulnerabilities of LLM-Assisted CTI

## 基本信息

- 题名：Uncovering Vulnerabilities of LLM-Assisted Cyber Threat Intelligence
- 作者：Yuqiao Meng, Luoxi Tang, Feiyang Yu, Jinyuan Jia, Guanhua Yan, Ping Yang, Zhaohan Xi
- 年份：2026
- 来源：arXiv:2509.23573
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/Uncovering_Vulnerabilities_LLM_Assisted_CTI_2025.pdf`

## 一句话总结

这篇不是 APT 归因方法论文，但它把 LLM-CTI 的失败根源拆成 spurious correlation、conflicting sources、emerging threat generalization，并明确支持 evidence-sufficiency gate / abstention 这类防御思路；Project05 的 “证据不足时拒答” 不能写得太泛。

## 做了什么

论文研究 LLM-assisted CTI 在真实威胁情报环境中的脆弱性。它认为问题不只是通用 hallucination，而是 CTI 本身具有异构、易变、碎片化、来源冲突和证据交织等属性。

作者提出 human-in-the-loop failure categorization，并将失败归为：

1. spurious correlations from superficial metadata；
2. contradictory knowledge from conflicting sources；
3. constrained generalization to emerging threats。

## 与 Project05 的关系

这篇会压住我们的一般性表述：

- 不能只说 “LLM 归因会幻觉，所以加证据充分性判断”；
- 不能把 evidence-sufficiency gate 当成完全没人提过的概念；
- 必须把 gate 落到 APT actor attribution 的具体输入、评分、降级和拒答动作。

## 留给 Project05 的空间

它没有做完整的 APT 归因系统，也没有：

- 构建 actor/campaign/intent/technique 分层归因；
- 做 open-set / unknown actor 归因；
- 设计多源证据缺失画像；
- 输出专门的 APT 归因拒答解释；
- 给出补充取证建议的闭环流程。

## 结论

这篇应该纳入 Project05 的可信 LLM-CTI 背景线。它提醒我们：Project05 的创新必须具体到 “APT 归因证据门控机制”，而不是泛泛写 “加一个 evidence sufficiency gate”。

