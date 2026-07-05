# 2026 - TTPrint

## 基本信息

- 题名：TTPRINT: Evidence-Grounded TTP Extraction via Diverge-then-Converge Verification
- 作者：Yutong Cheng, Changze Li, Raihan Sultan Pasha Basuki, Qian Cui, Wei Ding, Peng Gao
- 年份：2026
- 来源：arXiv:2605.25836
- 本地文件：`../07-zotero-exports/pdfs_20260705_round2/TTPrint_2026.pdf`

## 一句话总结

TTPrint 已经把 “从 CTI 报告中抽取 ATT&CK TTP 并绑定原文证据” 做成了强基线；Project05 不能再把 evidence-grounded TTP extraction 当作核心创新，只能把它作为 technique 层证据结构化模块。

## 研究问题

传统 TTP 抽取容易出现两个问题：

1. 为了召回更多 technique，LLM 会提出过宽的候选集合；
2. 为了提高精度，后处理又容易丢掉隐含但真实存在的技术。

作者把问题定义为开放集、多标签、证据约束的 TTP extraction：不仅要识别 technique，还要能定位支持该 technique 的原文证据片段。

## 方法框架

核心是 diverge-then-converge verification：

1. 将 CTI 报告拆成 atomic behaviors；
2. 对每个行为生成较宽的 ATT&CK technique 候选；
3. 对候选 technique 做 deterministic span localization，把候选绑定到报告中的证据窗口；
4. 结合证据窗口和 MITRE 官方定义做 verification；
5. 只保留同时被原文证据和 technique 定义支持的候选。

这个设计的重要点在于：LLM 不是直接裁决 technique，而是先发散候选，再用可定位证据收敛。

## 数据与实验

- 构建/清洗了 TRAM-Clean；
- 构建了 TTPRINT-Bench；
- 在多个 LLM backbone 上测试；
- 重点比较 full pipeline、去掉 evidence-based verification、去掉 evidence grounding 等消融。

主要结果：

- TRAM-Clean macro-F1 约 76.48%；
- TTPRINT-Bench macro-F1 约 87.39%；
- 相比领先基线分别有明显提升；
- 去掉 evidence-based verification 后 F1 大幅下降，说明证据约束是核心贡献。

## 局限

- 它解决的是 CTI 文本到 ATT&CK technique 的证据锚定抽取，不是 actor attribution；
- 证据主要来自公开 CTI 文本，不包含组织内部日志、样本或 provenance evidence；
- 没有解决 “TTP 是否足以支持 actor 归因”；
- 没有 evidence sufficiency、confidence calibration、refusal / abstention 机制。

## 对 Project05 的影响

这篇论文直接压实了 technique layer：

- `CTI text -> atomic behavior -> ATT&CK TTP -> evidence span` 已经是 2026 年强基线；
- Project05 不能写成 “基于 LLM 的证据增强 TTP 抽取方法”；
- 如果要用 ATT&CK/TTP，需要把 TTPrint 放在前置模块或 baseline；
- 真正的创新应上移到：TTP 证据是否足以支持 intent / campaign / actor，证据不充分时如何降级或拒答。

## 可转化为我的问题

可以把 TTPrint 的输出作为 Project05 的文本侧证据单元：

```text

CTI sentence/span -> atomic behavior -> technique candidate -> verified TTP evidence

```

然后继续问：

1. 这些 verified TTP 是否具有 actor 区分度？
2. 是否存在多个 actor 共享同类 TTP？
3. 缺少 malware、infrastructure、timeline、provenance 时，是否应该禁止高置信 actor attribution？
4. LLM 的作用是否应从 “抽 TTP” 转为 “解释证据充分性与缺失证据”？

