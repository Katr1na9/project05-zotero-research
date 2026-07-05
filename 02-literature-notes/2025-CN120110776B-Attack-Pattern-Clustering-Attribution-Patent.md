# 2025 - Patent: Attack pattern clustering and attribution

## 基本信息

- 专利号：CN120110776B
- 题名：一种针对攻击模式的攻击手法聚类与归因方法
- 来源：https://patents.google.com/patent/CN120110776B/zh
- 本地 HTML：`../07-zotero-exports/pdfs_20260705_round3/CN120110776B_zh.html`

## 一句话总结

该中国授权专利覆盖 LLM/RAG/KG/TTP/attack tree/attention weighting/attack tree matching 的攻击手法聚类与归因路线，是中文专利方向的强红线。

## 已确认机制

公开页面显示该方法涉及：

- 从威胁情报中抽取攻击信息；
- 使用 RAG 生成三元组；
- 与网络安全知识图谱融合；
- 获得 TTP 数据；
- 聚类攻击手法；
- 构建攻击树；
- 使用 attention 分配权重；
- 通过攻击树匹配完成归因。

## 对 Project05 的红线影响

不能 claim：

- LLM/RAG 抽取 TTP 后聚类归因；
- KG 融合后构建 attack tree；
- attention weighting + attack tree matching 做归因；
- 攻击手法聚类与归因。

## 留给 Project05 的空间

Project05 若要写专利，应避开 attack tree clustering/matching，把重点放在：

- evidence missing；
- attribution sufficiency；
- abstention/refusal；
- open-set unknown actor；
- LLM 解释为什么不能归因。

