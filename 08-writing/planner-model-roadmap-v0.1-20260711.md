# Project05 主模型路线 v0.1

日期：2026-07-11  
状态：纠正 LLM/决策模型混淆后的主线

## 1. 核心任务

Project05 的核心不是训练一个文本大模型，而是学习：

```text
Q(s, a) = 当前证据状态 s 下，执行取证动作 a 的预期价值
```

状态包含证据覆盖、关键缺口、边覆盖、当前可支撑粒度、预算和动作反馈；动作包含采集类型、公开目标、通道先验和成本。输出是下一取证动作或 STOP。

## 2. 模型层级

| 阶段 | 模型 | 作用 | 当前状态 |
|---|---|---|---|
| B0 | M2 确定性启发式 | 规则部署基线 | 已完成；当前紧预算最强规则方法 |
| B1 | Logistic Regression M3b | 验证 state-action 特征是否可学习 | 已完成；能学习但未形成稳定策略增益 |
| B2 | **XGBoost** | 学习非线性 state-action value，检验 Logistic 欠拟合 | 已完成；小幅优于 Logistic，未超过 M2 |
| B3 | Random Forest / MLP | XGBoost 的模型族对照 | 随 B2 评估 |
| B3.5 | **Depth-2 / DP 诊断** | 区分非短视需求与 RL 需求 | 已完成；Gate A 通过、Gate B 不通过 |
| B4 | **DQN / Dueling DQN** | 学习多步、非短视、带 STOP 的序贯策略 | 当前不批准；轻量规划仍可承受 |
| 支线 | Qwen / SEvenLLM | 原始文本到 evidence claim 的可选编译器 | 暂停，不是主模型 |

XGBoost、DQN 都不是“大语言模型”。XGBoost 是梯度提升树，DQN 是用神经网络逼近动作价值函数的强化学习方法。

## 3. XGBoost 实验

### 输入

直接复用 M3b 已生成的公开 state-action 特征：成本、剩余预算、节点/边覆盖、关键缺口数、动作目标与缺口重合、通道可靠性和 expected effects。禁止使用 hidden claim、`recoverable_claim_ids` 或 Oracle path。

### 标签

- `label_resolves_critical_gap_node`
- `label_reaches_target_after_action`
- `label_yield_positive`

第一版分别训练二分类模型，不把三个标签混成未经解释的单一分数。

### 对照

- Logistic M3b
- Random Forest
- XGBoost
- M2
- Oracle，只作评测上界

### 指标

AUROC、AP、Brier、校准曲线、top-1 action hit，以及真正重要的下游 episode success、cost-to-target、regret 和 premature stop。

## 4. DQN Gate

只有同时满足以下条件才进入 DQN：

1. XGBoost 在未见案例上优于 Logistic，而不是只记住人工动作字段。
2. 状态转移中确实存在“当前最优不等于全局最优”的非短视案例。
3. 增加独立攻击环境或可辩护的训练模拟器；不能把同一案例的 mask/seed 当作独立环境夸大数据量。
4. reward、STOP、动作 mask 和离线评估协议全部预注册。

两级 Gate 实验已完成：非短视必要性通过，但 DQN 必要性不通过。Depth-2 在多步解锁上不足，DP 相对 Depth-2 的 success 优势为 `0.3448`；然而 DP 冷启动 p95 为 `83.9598 ms`、最大仅展开 `23,892` 状态，未达到 DQN 复杂度阈值。因此当前采用轻量非短视规划，DQN 不作为论文核心。

## 5. DQN 形式化

- state：evidence state 向量或结构化编码。
- action：当前可执行取证动作及 STOP。
- transition：执行动作后，根据通道结果更新 evidence state。
- terminal：达到目标粒度、预算耗尽、不可达或选择 STOP。
- reward：粒度提升和关键缺口消除为正奖励，取证成本、零收益动作、提前错误 STOP 和越级输出为惩罚。

优先比较 DQN、Double DQN 和 Dueling DQN，不直接上 PPO。Dueling DQN 适合存在多个相似取证动作、状态价值与动作优势需要分离的场景。

## 6. 当前准确答案

- 当前规则主方法：M2。
- 当前已经训练的 ML 模型：Logistic Regression M3b。
- 当前学习模型：XGBoost 已完成；相对 Logistic 更稳，但未超过 M2。
- 已批准的序贯增强：轻量 Depth-k / DP / beam planning。
- 当前未批准模型：DQN / Dueling DQN。
- 当前 LLM：没有；Qwen 仅为暂停的语义编译支线候选。
