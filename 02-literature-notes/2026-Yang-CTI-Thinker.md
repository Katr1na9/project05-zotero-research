# 2026 - CTI-Thinker

## 基本信息

- 题名：CTI-Thinker: an LLM-driven system for CTI knowledge graph construction and attack reasoning
- 作者：Xiuzhang Yang, Ruijie Zhong, Yuling Chen, Guojun Peng, Di Yao, Chaofan Chen, Chenyang Wang, Dongni Zhang, Yilin Zhou, Zixuan Yang
- 年份：2026
- 来源：Cybersecurity, 9(1), DOI: 10.1186/s42400-025-00505-y
- 本地来源：`../07-zotero-exports/pdfs_20260705_round2/CTI_Thinker_2026_springer_page.html`
- 说明：本轮本地下载到的是 Springer HTML 页面，不是可抽取 PDF；精读依据 Springer 页面与元数据。

## 一句话总结

CTI-Thinker 已经把 LLM、LoRA、CTI knowledge graph、ATT&CK 语义对齐和 GraphRAG attack reasoning 结合起来；Project05 若使用 GraphRAG，必须把创新放在证据充分性、拒答、开放集和多源证据可用性判断上。

## 研究问题

CTI 报告通常存在：

1. 非结构化、片段化；
2. 实体和关系表达不统一；
3. 与 ATT&CK technique 的语义映射不足；
4. 传统信息抽取难以处理跨段依赖、低资源样本和新兴威胁；
5. 下游 attack attribution / intent inference 缺少结构化知识支撑。

## 方法框架

CTI-Thinker 的框架可以概括为：

1. 使用 in-context learning 和 LoRA fine-tuning，从 CTI 文本中抽取 threat entities 与 relations；
2. 使用 vector-based semantic alignment 做实体归一、异构表达统一和知识融合；
3. 构建 CTI knowledge graph，并与 ATT&CK 等外部资源对齐；
4. 使用 GraphRAG，把相关子图和外部知识检索出来，喂给 LLM 完成 tactical-level inference 和 CTI question answering。

它的重点不是 “单次问答”，而是先把 CTI 文本结构化，再把图作为推理上下文。

## 数据与实验

论文报告其在知识图谱构建和 attack reasoning 上优于若干 baseline。公开摘要和页面信息显示：

- 知识图谱构建任务取得较高 F1；
- attack reasoning accuracy 约为 79.66%；
- 系统在 precision、robustness、generalizability 上优于对比方法。

## 局限

- 核心仍是 CTI KG construction 与 attack reasoning，不是证据不完整场景下的 actor attribution；
- GraphRAG 提供推理上下文，但不等于证据充分性判断；
- 没有把 missing evidence profile、refusal correctness、unknown actor 或 false flag 作为核心机制；
- 对组织内部日志、样本和 provenance evidence 的融合仍不是主线。

## 对 Project05 的影响

CTI-Thinker 明确说明：到 2026 年，`LLM + CTI KG + ATT&CK alignment + GraphRAG + attack reasoning` 已经不是空白。

因此 Project05 不能写成：

> 基于知识图谱和大语言模型的 APT 攻击推理方法

更稳妥的差异化应是：

1. 图谱/RAG 只作为证据通道；
2. 系统先判断可用证据类型和缺失证据类型；
3. 对每类证据给出可区分度、可靠性和时效性评估；
4. 当证据不足以支持 actor attribution 时，输出降级结论或拒答；
5. LLM 负责证据链解释、缺失证据说明和补充取证建议，而不是直接拍板 actor。

## 可转化为我的问题

Project05 可以把 CTI-Thinker 放在 related work 的 GraphRAG/KG reasoning 线，并明确区分：

```text

CTI-Thinker: CTI KG + GraphRAG -> attack reasoning
Project05: available evidence profile + sufficiency scoring -> adaptive attribution / refusal / explanation

```

也就是说，GraphRAG 是底座，不是创新终点。

