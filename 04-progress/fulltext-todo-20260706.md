# 待补全文清单 - 2026-07-06

本文件记录当前已纳入 Project05 但暂时难以获取全文的高风险文献。它们不再阻塞主线推进，但在最终定稿专利权利要求、论文题名和实验设计前，需要做二次复核。

## A 级待补：可能影响专利权利要求边界

| 优先级 | 完整标题 | 当前状态 | 为什么重要 | 当前处理 |
|---|---|---|---|---|
| A1 | An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN | 已有题名/摘要线索，正文未得 | 可能覆盖 heterogeneous CTI representation、CTGAN 增强、APT attribution | 作为 APT-ATT 高风险项保留；不再把异构情报表示/数据增强作为创新 |
| A2 | APTChaser: Cyber Threat Attribution via Attack Technique Modeling | Springer 元数据和摘要可验证，正文未得 | 覆盖 LLM 构建 attack technique schema/profile 并服务归因 | 不把 LLM 细化 TTP 或 technique profile 作为主创新 |

## B 级待证：目前只作为二级引用风险项

| 优先级 | 完整标题 | 当前状态 | 为什么重要 | 当前处理 |
|---|---|---|---|---|
| B1 | GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings | 只在 2026 KG 论文参考文献中出现，独立 DOI/全文未验证 | 可能覆盖 temporal relation embedding + graph-based APT attribution | 作为橙色待证风险项保留；不把时序图嵌入归因作为创新 |

## 推进原则

1. 以上四篇不再阻塞 Project05 当前主线。
2. 专利 v0.2 可以推进，但必须避开它们可能覆盖的宽题空间。
3. 最终正式提交前，至少要再查一次：
   - APT-ATT 是否覆盖 evidence weighting、confidence calibration、missing evidence、refusal；
   - APTChaser 是否覆盖 granularity gate 或 refusal；
   - GAPT 是否真实存在且覆盖 temporal evidence sufficiency；
4. 若后续拿到全文，优先更新：
   - `04-progress/collision-matrix-final-20260706.md`
   - `08-writing/patent-claims-draft-v0.2-20260706.md`

## 已从待补转为已获取

| 完整标题 | 当前状态 | 对 Project05 的结论 |
|---|---|---|
| A Multi-Source Feature Fusion-Based Knowledge Graph Construction from Cyber Threat Intelligence to Facilitate APT Attribution in IDS | PDF 已获取，已抽取全文并精读 | 红色风险项。直接覆盖 multi-source feature fusion + HKG + APT attribution，进一步确认 Project05 不能以多源特征融合知识图谱为核心 |
