# 2026 - APTA2D

## 基本信息

- 题名：APTA2D: APT Attribution via Attention-Guided Pruning and 2-D Convolutional Reasoning
- 年份：2026
- 来源：WCCI/IJCNN submission PDF mirror
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/APTA2D_2026.pdf`

## 一句话总结

APTA2D 是知识图谱/图推理式 APT attribution，高风险地覆盖了 “attention + KG + attack chain reconstruction + attribution confidence”；但当前来源像会议投稿 PDF，需谨慎标注其发表状态。

## 做了什么

论文提出 classify-first, reason-second 框架：

1. multi-head attention 对 full graph 做概率剪枝；
2. 在 condensed subgraph 上用 2-D convolutional reasoning；
3. 输出 APT source IP localization；
4. 声称提升 attribution precision，并能 reconstruct attack chain。

## 与 Project05 的关系

危险点：

- KG / graph reasoning + APT attribution 已有人做；
- attention weighting + attribution confidence 已出现；
- attack chain reconstruction 已出现。

未覆盖：

- LLM evidence explanation；
- 证据不完整画像；
- open-set / unknown actor；
- false flag / mimicry；
- 拒答和分层降级。

## 结论

Project05 不应写成 “基于注意力图推理的 APT 归因”。如果引用 APTA2D，应把它作为 graph-attribution baseline 或红线。

