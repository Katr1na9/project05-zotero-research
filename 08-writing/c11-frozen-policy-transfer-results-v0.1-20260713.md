# C11 冻结策略迁移结果 v0.1

日期：2026-07-13

## 1. 实验问题

在不修改 C11 的 AND 多 Claim 语义、G2 目标、动作空间、预算和 45 个重复条件的前提下，C07-C10 已冻结的学习策略、AFA 适配和公开 Depth-2 是否保持原有相对排序？

一句话结论：**没有。C11 上 Logistic/XGBoost 和 AFA-VOI Myopic 降低了 M2 成本，而 Depth-2 出现成功退化；策略排序与离线分类指标均不能跨场景直接外推。**

## 2. 冻结设计

| 项目 | 约束 |
|---|---|
| 独立单位 | 1 个 OTRF APT29 Day 1 仿真攻击链 |
| 重复测量 | 每策略 45 个 mask/intensity/seed 条件 |
| C11 目标 | `G2_tactic_intent`，`support_ceiling=G2` |
| 覆盖语义 | AND；OR 仅保留为既有乐观敏感性 |
| XGBoost/Logistic 训练 | C01-C06；C11 不进入训练或调参 |
| AFA | 原 Myopic 与 Rollout-H3 目标、horizon=3 |
| Depth-2 | 原 public surrogate、discount=0.8、failure weight=1.0 |
| 信息边界 | 非 Oracle 不读取隐藏 claims 或真实恢复集合 |
| 聚合边界 | C11 单独报告，不与 C07-C10 G3 均值混算 |

三个 XGBoost 模型的 C11 运行哈希与 C07-C10 主评估完全一致。扩展运行中的 Coverage、M2、M3a 和 Oracle 行与 C11 首轮冻结 CSV 逐条件一致，排除了重新采样或模拟器漂移。

## 3. 主要结果

| Planner | Success | Mean cost | Regret | Premature STOP |
|---|---:|---:|---:|---:|
| Oracle | 1.0000 | 3.0000 | 0.0000 | 0.0000 |
| XGBoost | 1.0000 | 3.0667 | 0.0667 | 0.0000 |
| Logistic | 1.0000 | 3.0667 | 0.0667 | 0.0000 |
| Coverage / M1 | 1.0000 | 3.2444 | 0.2444 | 0.0000 |
| AFA-VOI Myopic | 1.0000 | 3.5556 | 0.5556 | 0.0000 |
| M3a | 1.0000 | 3.5556 | 0.5556 | 0.0000 |
| M2 | 1.0000 | 3.6667 | 0.6667 | 0.0000 |
| AFA-VOI Rollout-H3 | 1.0000 | 3.6889 | 0.6889 | 0.0000 |
| Depth-2 Public | 0.9778 | 4.9091 | 1.9318 | 0.0222 |

XGBoost 与 Logistic 相对 M2 均为 10 胜、34 平、1 负，平均成本差为 `-0.6000`。AFA-VOI Myopic 为 8 胜、35 平、2 负，平均差 `-0.1111`；Rollout-H3 为 8 胜、33 平、4 负，平均差 `+0.0222`。Depth-2 有 1 次 success regression；在其余 44 个共同成功条件中，平均比 M2 多 `1.3182` 成本。

## 4. 离线指标与序贯效用不一致

主标签 `label_resolves_critical_gap_node` 的 C11 离线结果为：

| 模型 | AP | AUROC | Top-1 hit |
|---|---:|---:|---:|
| XGBoost | 0.3952 | 0.8303 | 0.4222 |
| Logistic | 0.6322 | 0.8357 | 0.4222 |

Logistic 的 AP 高于 XGBoost，但两者在 45 个序贯条件中采取了等价决策并得到相同成本。这说明 action-level 分类质量不能直接替代闭环 policy utility；论文应继续把序贯结果作为主评价，把分类指标作为诊断。

## 5. 科学解释

本结果加强的是“策略排序依赖任务结构”，不是“XGBoost 成为主模型”。C07-C10 的 OR/单 Claim/G3 场景中，M2 是当前最佳透明锚点；C11 的 AND/多 Claim/G2 场景中，冻结学习器更接近 Oracle，而有限前瞻更差。可能原因包括公开意图粒度、动作成本结构和 AND 状态更新共同改变了排序，但当前只有一个 C11 案例，不能区分这些因素的独立贡献。

## 6. 可写与不可写

可以写：

- 冻结策略排序没有跨封装保持；
- C11 上 XGBoost/Logistic 与一步 AFA 降低了 M2 成本；
- Depth-2 在 C11 出现 success regression；
- 离线分类指标与序贯效用不一致；
- M2 只能称 C07-C10 的透明部署锚点。

不可写：

- XGBoost 在 APT 调查中普遍优于规则；
- 学习器已证明跨域泛化；
- 45 个条件是 45 个独立攻击；
- C11 证明 actor/campaign 归因准确率；
- 当前 AFA 是 NOCTA/WinRegRL 官方复现。

## 7. 剩余门槛

双人盲标仍为 `awaiting_annotations`。本实验关闭了 C11 策略族不完整问题，但没有关闭人工粒度效度、自然 engagement、分析师效用或官方 AFA 复现门槛。
