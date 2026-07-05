# 2026 - ARCANE Bayesian Cyber Attribution

## 基本信息

- 题名：ARCANE: Cross-Campaign Attacker Re-identification via Passive Beacon Telemetry - A Bayesian Network Framework for Longitudinal Cyber Attribution
- 作者：Abraham Itzhak Weinberg
- 年份：2026
- 来源：arXiv:2604.24644
- 本地文件：`../07-zotero-exports/pdfs_20260705_round2/Bayesian_Network_Cyber_Attribution_2026.pdf`

## 一句话总结

ARCANE 把归因建模为跨 campaign 的 Bayesian belief update，但实验反而显示：即使纵向累积 telemetry，actor fingerprint 的可分性仍可能不足。这为 Project05 的 “证据不足时拒绝高置信归因” 提供了强支撑。

## 研究问题

很多归因系统按单个 incident/campaign 独立处理证据。作者提出问题：

> 如果跨多个 campaign 累积 passive beacon telemetry，是否能显著降低 attribution ambiguity？

## 方法框架

ARCANE 的核心是：

1. 使用 passive beacon telemetry 表示攻击者交互痕迹；
2. 将 behavioral、infrastructural、temporal features 编码为 fingerprint vector；
3. 对每个新 campaign 的 telemetry 与历史 fingerprint 比较；
4. 用 Bayesian belief network 更新候选 actor 的 posterior；
5. 使用 time-decayed confidence 度量跨 campaign 证据累积。

输出形式接近：

```text

attributed actor = a*
posterior = P(A = a*)
high confidence = posterior >= threshold

```

## 数据与实验

由于缺少公开纵向 beacon telemetry 数据，论文使用 synthetic dataset。

关键发现：

- 同一 actor 内部相似性高于不同 actor；
- 但不同高级 actor 的 fingerprint 仍然高度接近；
- 主表中 per-campaign baseline overall accuracy 约 43.2%，ARCANE 约 30.7%；
- confidence plateau 大约在 0.15-0.20，远低于高置信阈值；
- evasion level 对 accuracy 影响不显著，真正瓶颈是 feature separability ceiling。

## 局限

- 数据是合成数据；
- passive beacon telemetry 在真实环境中可获得性有限；
- 不支持 previously unseen actors；
- 没有 LLM explanation，也没有多源 CTI/log/sample 融合。

## 对 Project05 的影响

ARCANE 的价值不在于结果多好，而在于它提醒：

> 多证据累积不必然带来高置信归因。

这正好回应用户最早的疑问：如果多源证据大部分拿不到，多源融合还有什么用？

答案是：融合系统的价值不是永远输出 actor，而是判断当前证据是否真的足够；如果 posterior 或 sufficiency score 卡在低水平，就应该降级或拒答。

## 可转化为我的问题

Project05 可以吸收 ARCANE 的概率表达，但扩展为证据充分性感知：

```text

available evidence -> actor posterior / evidence sufficiency score
if sufficient: actor attribution + evidence-grounded explanation
if insufficient: downgrade / abstain + missing evidence recommendation

```

同时要避免 ARCANE 的问题：

- 不能只靠单一 telemetry；
- 要纳入 evidence distinctiveness；
- 要显式支持 unknown actor；
- 要把低 confidence 变成系统行为，而不是只在结果表里报告。

