# MLDSJ: a multi-level feature joint attribution method for APT group based on threat intelligence

## 基本信息

- 题名：MLDSJ: a multi-level feature joint attribution method for APT group based on threat intelligence
- 作者：Longxuan Duan, Mi Wen, Yun Xiong
- 期刊：EURASIP Journal on Information Security
- 卷期：2026, article number 2
- 发布日期：2025-12-12
- DOI：10.1186/s13635-025-00222-6
- 来源：https://link.springer.com/article/10.1186/s13635-025-00222-6
- 当前状态：开放全文 HTML 精读；PDF 下载链接本轮返回 HTML，未保留可解析 PDF。

## 它在研究什么

MLDSJ 面向 CTI-based APT group attribution，核心主张是：单一特征无法覆盖 APT 归因所需信息链，多层特征融合可以提升归因性能。

它的管线是：

```text
CTI reports
  -> attack pattern-level features
  -> text-level features
  -> graph topology-level features
  -> three simple MLP classifiers
  -> Dempster-Shafer evidence fusion
  -> final APT group attribution
```

它明确把 Dempster-Shafer 证据理论用于融合三类特征，并通过组合规则给出最终归因结果。

## 实验结果

公开全文显示：

- 数据集：238 public CTI reports，覆盖 12 个 APT actors；
- 总体结果：accuracy 89.9%，recall 86.5%，F1 88.2%；
- 对比对象：SMOBI、Word2Vec、SIMVER，以及 weighted averaging、Bayesian inference、possibility-theory-based fusion；
- 结论：多层特征逐步加入能提升性能，DS 融合在不确定或部分冲突信号下更稳健。

## 它承认的限制

这篇对 Project05 很关键，因为它直接承认证据融合仍然有边界：

1. 长尾数据会让大样本 APT 组的证据质量函数占优，尾部组更容易被误判；
2. 时间漂移会让文本、攻击模式和拓扑证据不一致，从而降低融合置信度；
3. 报告风格、语言差异、缺失特征、攻击者混淆都会增加噪声；
4. 攻击者复用代码、借用 TTP、模仿其他组织，会产生 feature blurring；
5. 多模态融合虽然更鲁棒，但对阈值选择、类别不平衡和计算成本更敏感；
6. 论文明确提到 practical trade-off：unknown rejection 更强，但已知组之间的细粒度归因更弱。

## 撞题判断

MLDSJ 是 Project05 的红色风险项。

它直接封住：

- multi-level CTI feature extraction；
- attack pattern + text + graph topology fusion；
- DS evidence theory for APT group attribution；
- confidence / uncertainty / conflicting evidence 语境下的多源证据融合；
- “多源证据融合提升 APT 归因准确率”这一宽创新。

因此 Project05 不能继续把“多源安全证据自适应融合”作为独立核心创新。

## Project05 可避让空间

MLDSJ 留下的空间不是再做一个证据融合器，而是在融合器之后加一个“归因可判定性控制层”：

```text
已有归因模型输出候选 actor / probability / evidence mass
  -> 证据充分性画像
  -> actor-specific distinctiveness 判断
  -> time drift / mimicry / long-tail risk 检测
  -> 归因粒度门控
  -> actor / campaign / technique / unknown / refusal
  -> LLM 生成受控解释与缺失证据清单
```

尤其是 MLDSJ 的 limitation 可以直接变成 Project05 的问题定义：

> 现有多特征融合方法能提升闭集归因性能，但在长尾、漂移、缺失特征和攻击者模仿下，仍可能把证据不足的样本推向高风险 actor-level 结论。因此需要一个独立于归因模型的证据充分性门控层，决定当前证据最多支持哪一级归因。

## 对专利题名的影响

不能写：

- 多源证据融合；
- 多层特征联合归因；
- 基于 DS 证据理论的 APT 归因；
- CTI 文本、攻击模式与图拓扑融合归因。

可以写：

- 证据充分性画像；
- 归因粒度门控；
- 证据不足场景下的可拒答归因解释；
- 长尾、时间漂移、模仿和缺失特征下的归因可判定性评估。

## 风险等级

红色。

原因：它是 2026 卷开放全文，直接覆盖 Project05 原始宽题中“多源/多层证据融合提升 APT group attribution”的大部分空间。
