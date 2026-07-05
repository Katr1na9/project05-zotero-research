# 2026 - OpenSec

## 基本信息

- 题名：OpenSec: Measuring Incident Response Agent Calibration Under Adversarial Evidence
- 作者：Jarrod Barnes
- 年份：2026
- 来源：arXiv:2601.21083
- 本地文件：`../07-zotero-exports/pdfs_20260705_round2/OpenSec_2026.pdf`

## 一句话总结

OpenSec 把安全智能体的评价从 “能不能检测/处置” 推进到 “证据不够时会不会克制”；这与 Project05 的 refusal / abstention 和 evidence-gated attribution 非常接近，但它研究的是 incident response action，不是 APT actor attribution。

## 研究问题

现有安全 agent benchmark 往往混淆了两个问题：

1. 模型是否能识别威胁；
2. 模型是否应该在当前证据下执行高风险动作。

OpenSec 关心的是 calibration under adversarial evidence：当证据含有诱导、注入或不充分信息时，agent 是否会过早执行 containment 等动作。

## 方法框架

OpenSec 构建了一个 dual-control incident response 环境：

- Agent 需要在多步调查中处理证据；
- 环境中存在 prompt injection / adversarial evidence；
- 评价不只看是否最终识别威胁，还看动作是否 evidence-gated。

关键指标包括：

- TTFC：time-to-first-containment；
- EGAR：evidence-gated action rate；
- blast radius；
- injection violation rate；
- false positive containment。

## 数据与实验

论文评估了多个 frontier model 在标准 episode 下的表现。

重要发现：

- 有的模型可以识别真实威胁，但仍然过早 containment；
- GPT-5.2 在测试中执行 containment 的比例很高，但 false positive containment 也很高；
- Claude Sonnet 4.5 表现出一定 restraint，但仍存在明显误触发；
- 校准缺口主要不在 “能不能发现威胁”，而在 “证据不够时是否忍住不行动”。

## 局限

- 任务是 incident response，不是 threat actor attribution；
- 证据动作是 containment，而不是 attribution label；
- provenance tier / evidence weighting 尚未被系统展开；
- 不直接处理开放集 actor、TTP mimicry 或 false flag attribution。

## 对 Project05 的影响

OpenSec 给了 Project05 一个很强的评价思想：

> 不只问模型能不能归因，而要问模型知不知道什么时候不能归因。

Project05 可以迁移它的思路，定义：

- Evidence-Gated Attribution Rate：只有证据充分时才输出 actor；
- Over-Attribution Rate：证据不足仍输出高置信 actor 的比例；
- Correct Abstention Rate：不可归因样本上正确拒答的比例；
- Attribution Blast Radius：错误高置信归因可能造成的影响范围；
- Injection / false evidence violation rate：被诱导证据误导的比例。

## 可转化为我的问题

OpenSec 支持把 Project05 的核心从 “让 LLM 更会归因” 改成：

```text

让 LLM 在证据充分时给出可解释归因；
在证据不足、冲突、疑似 false flag、候选 actor 难以区分时拒绝高置信归因。

```

这对专利尤其有价值，因为它可以保护一个可执行的证据门控流程，而不是泛泛的 LLM 分析。

