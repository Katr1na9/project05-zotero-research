# 2026 - Minerva

## 基本信息

- 题名：Minerva: Reinforcement Learning with Verifiable Rewards for Cyber Threat Intelligence LLMs
- 作者：Md Tanvirul Alam, Aritran Piplai, Ionut Cardei, Nidhi Rastogi, Peter J. Worth Jr.
- 年份：2026
- 来源：arXiv:2602.00513
- 本地文件：`../07-zotero-exports/pdfs_20260705_round2/Minerva_2026.pdf`

## 一句话总结

Minerva 说明 CTI LLM 已经开始进入 “可验证奖励 + 领域强化学习” 阶段；Project05 不能只说训练一个 CTI LLM，而应把可验证奖励迁移到证据引用、充分性判断、拒答正确性和归因校准上。

## 研究问题

通用 LLM 在 CTI 任务上存在：

- 输出格式不稳定；
- 标识符、CVE、CWE、CAPEC、ATT&CK、threat actor 等规范实体容易错；
- 传统人工偏好奖励难以覆盖细粒度 CTI 正确性。

作者的核心观察是：很多 CTI 输出可以被 deterministic verifier 自动验证，因此适合 RLVR。

## 方法框架

Minerva 包含：

1. 统一的 CTI task/data pipeline；
2. 多类 CTI 训练任务，包括漏洞、检测、procedure、technique、tactic、mitigation、threat actor 等；
3. 可验证奖励函数，对规范标识符、结构化答案和 CTI 概念进行自动评分；
4. MinervaRL：通过自训练生成 verified trajectories，并蒸馏给模型，以缓解 reward sparsity。

## 数据与实验

- 约 32,000 个训练实例；
- 约 1,200 个验证实例；
- 覆盖 16 类训练任务；
- 在 12 个 CTI benchmark 上评估多个 backbone。

主要结果：

- MinervaRL 平均分相比 base model 提升约 15.8 点；
- 相比 GRPO 也有提升；
- 偏好评价包含 writing quality、prompt-evidence use、CTI concept precision；
- threat actor alias 可以通过 verifier 接受等价表达。

## 局限

- 重点是结构化 CTI 输出和领域模型训练，不是 APT 归因证据融合方法；
- verifier 适合规范实体，但 “证据是否足以归因到 actor” 更难验证；
- 没有把 evidence missing、unknown actor、false flag、refusal correctness 作为核心任务；
- RLVR 成本较高，不适合 Project05 初期直接复现为完整训练路线。

## 对 Project05 的影响

Minerva 的价值在于给 Project05 提供 verifier 思路：

1. 证据引用是否真实来自输入；
2. 输出 actor 是否在候选证据中出现或可通过 alias graph 归一；
3. confidence 是否与证据充分性等级一致；
4. 不可归因样本是否正确拒答；
5. 降级输出是否落到 technique / intent / campaign 而非强行 actor。

## 可转化为我的问题

Project05 不需要一开始训练一个完整 CTI LLM。更现实的路线是：

```text

LLM/RAG output
  -> verifier 检查证据引用、实体规范、证据充分性、拒答条件
  -> feedback / rerank / self-correction

```

如果后续从专利转论文，Minerva 可作为 “可验证奖励/可验证 CTI 输出” 的训练与评价背景。

