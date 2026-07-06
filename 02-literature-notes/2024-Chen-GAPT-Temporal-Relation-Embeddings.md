# GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings

## 基本信息

- 题名：GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings
- 作者线索：Chen, Wu, Li
- 年份线索：2024
- 来源线索：IEEE Access 2024, 12, 76532-76545
- 当前状态：二级引用风险项，未检索到可独立验证的 DOI、IEEE 页面或全文。
- 主要来源：2026 年 APT knowledge graph correlation 论文参考文献列表。

## 检索结论

截至 2026-07-06 的本轮检索中，使用以下关键词未能确认独立记录：

```text
"GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings"
+"Graph-based APT Attribution Framework" +"Temporal Relation Embeddings"
+"GAPT" +"APT Attribution" +"IEEE Access"
+"76532" +"76545" +"GAPT"
+site:ieeexplore.ieee.org "Graph-based APT Attribution" "Temporal Relation Embeddings"
+site:dblp.org "GAPT" "APT Attribution"
```

因此，GAPT 不能被当作已经完成精读的正式文献，也不能把它的细节当作已知事实。它目前的用途是：在撞题矩阵中保留“时间关系图归因”这条风险线。

## 可确认的撞题风险

仅从题名可确认，它至少可能覆盖：

1. graph-based APT attribution framework；
2. temporal relation embeddings；
3. 用动态/时序关系增强 APT 组织归因；
4. 图结构归因框架这一宽题名空间。

## 对 Project05 的影响

Project05 不能把“时序关系嵌入提升 APT 归因”当作核心创新。更稳妥的表达是：

- 时间线证据只是证据充分性画像中的一个维度；
- 时间一致性用于判断证据是否足以支撑 actor-level 归因；
- 时间证据不足、冲突或漂移时触发降级归因或拒答；
- LLM 只负责解释为什么当前时间证据不足，而不是直接生成归因结论。

## 风险等级

橙色待证。

原因：题名本身压缩了“图 + 时序关系 + APT attribution”空间，但全文与 DOI 暂未验证，不能上升为红色实证撞题项。
