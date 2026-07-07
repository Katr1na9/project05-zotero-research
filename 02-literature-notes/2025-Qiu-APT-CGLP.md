# APT-CGLP: Advanced Persistent Threat Hunting via Contrastive Graph-Language Pre-Training

- 作者：Xuebo Qiu, Mingqi Lv, Yimei Zhang, Tieming Chen, Tiantian Zhu, Qijie Song, Shouling Ji
- 来源：arXiv:2511.20290，提交于 2025-11-25
- 状态：**摘要级高风险占位，全文待获取**
- 风险等级：红（对新主线候选 A 的"跨模态对齐"单点）

## 十问速览（基于摘要）

1. 输入是什么：溯源图（provenance graph，来自系统审计日志）+ CTI 报告原文。
2. 输出是什么：APT 狩猎结果（溯源图与 CTI 报告的端到端语义匹配）。
3. 核心模块：对比图-语言预训练（Contrastive Graph-Language Pre-training）；LLM 合成高保真"溯源图-CTI 报告"配对训练数据；多目标训练（对比学习 + 跨模态掩码建模），粗细两级跨模态攻击语义对齐。
4. 是否做证据权重：摘要未见。
5. 是否做不完整证据：摘要提到 prior work 的 information loss 问题，但其解法是绕过图抽取（端到端），不是证据充分性建模。
6. 是否做 open-set / abstention：摘要未见。
7. 是否做 false flag / mimicry：摘要未见。
8. 是否生成缺失证据建议：**否**。
9. LLM 是决策层还是解释层：LLM 用于训练数据合成与 CTI 净化，属于数据层，不是归因决策或解释层。
10. 对 Project05 的红线：**"溯源图与 CTI 报告的端到端跨模态语义对齐/匹配"被覆盖，且明确批判了 POIROT 式两段法（图抽取+图匹配）**。Project05 不能把任何形式的"CTI-溯源跨模态对齐方法"作为主创新。

## 任务边界

威胁狩猎（匹配）为止。四个真实 APT 数据集上对比狩猎 baseline。未延伸到：归因语义、对齐结果的证据充分性、取证规划、闭环。

## 对新主线的含义

APT-CGLP 是对齐基座的最新 SOTA 候选。它把"对齐怎么做"这个问题推进得很深，恰好反衬 Project05 的空间在"对齐之后怎么用"：对齐状态作为证据画像 → 归因粒度可判定性 → 主动取证规划。

## 待办

- 获取全文，重点确认其实验是否含"部分对齐/对齐失败"分析（若有，是候选 B 的重要引用支撑）。
