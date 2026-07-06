# 撞题矩阵补充 - 2026-07-06

本文件补充 `collision-matrix-20260705.md`。目的不是替代主矩阵，而是把本轮新核查的 APTChaser、GAPT、MLDSJ 与新发现的多源特征融合方向单独记录，避免后续误判证据强度。

## 新增/修正条目

| 工作 | 证据状态 | 直接覆盖 | 对 Project05 的影响 |
|---|---|---|---|
| APTChaser | Springer 摘要可验证，全文未获得 | LLM 构建 attack technique schema；细粒度 technique profile；APT attribution-aided decision information | 禁止把“LLM 细化 TTP/attack technique 后做归因”作为主创新 |
| GAPT | 二级引用可见，独立 DOI/全文未验证 | graph-based APT attribution；temporal relation embeddings | 保留为橙色待证风险，不能把时序图嵌入归因作为创新 |
| MLDSJ | 开放全文 HTML 可读 | attack pattern + text + graph topology；DS evidence fusion；APT group attribution | 直接封住“多源/多层证据融合提升 APT 归因”的宽路线 |
| Multi-Source Feature Fusion KG for APT Attribution | IEEE 题名与摘要线索可见，全文未获得 | multi-source feature fusion；knowledge graph；APT attribution | 进一步压缩“多源特征融合 + KG + 归因”路线，需纳入 Zotero 待精读 |

## 更新后的红线

Project05 当前不得再把以下内容作为独立核心：

1. 多源/多层 CTI 特征融合用于 APT group attribution；
2. Dempster-Shafer、Bayesian、weighted averaging 等证据融合提升归因准确率；
3. KG/HIN/GNN/RGCN/temporal embedding 图归因；
4. LLM 构建 attack technique schema / technique profile 后做归因；
5. TTP 粒度细化、TTP 相似度加权或 technique implementation modeling；
6. 单纯置信度、单纯 open-set、单纯 abstention。

## 仍可推进的白区

当前更稳的 Project05 核心应当是：

```text
证据充分性画像
  + actor-specific distinctiveness 判断
  + long-tail / time drift / mimicry / missing-feature 风险检测
  + 归因粒度门控
  + 拒答/降级输出
  + LLM 受控解释与缺失证据清单
```

换句话说，Project05 不是再做一个 attribution model，也不是再做一个 evidence fusion model，而是做 attribution output control：

- 什么时候不能给 actor-level 结论；
- 当前证据最多支持 actor、campaign、technique 还是 unknown；
- 为什么不能支持更细粒度归因；
- 还缺哪些证据才能升级结论。

## 对题名的修正建议

更建议：

> 一种面向证据不完整与攻击者混淆场景的 APT 归因粒度门控与可拒答解释方法

论文题名可写为：

> Evidence-Sufficiency-Gated Attribution Granularity Control for LLM-Assisted APT Analysis under Incomplete and Ambiguous Evidence

不建议再使用：

> 一种基于多源证据融合与大语言模型的高级持续性威胁归因解释方法

原因：MLDSJ、APT-MMF、APT-ATT、APT-scope、TRAIL、AARGS、APTChaser 已经让这个题名过宽且高风险。
