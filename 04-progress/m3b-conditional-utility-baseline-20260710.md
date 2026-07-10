# M3b 条件收益学习 baseline 实验记录

日期：2026-07-10  
状态：已完成最小可运行版

## 1. M3b 要解决什么

M3a 已经证明：只要把 action 与 CTI 缺口节点显式对应起来，M2 的很多失败会被修复。但 M3a 仍然是规则 baseline，它没有学习“在某个 evidence-gap state 下，哪个 action 的实际收益更高”。

M3b 的目标是把 M3a 的表示升级为可监督学习问题：

```text
Input:
  当前 evidence-gap state
  候选 acquisition action
  action 与未匹配 CTI 节点的公开对应关系

Output:
  P(action resolves critical gap node | state, action)
```

本轮先做最小 logistic baseline，不引入 GNN、RL 或大模型。

## 2. 本轮实现

新增脚本：

- `09-experiments/scripts/run_m3b.py`

新增测试：

- `09-experiments/tests/test_run_m3b.py`

脚本功能：

1. 从 C01-C06 case 中枚举 mask condition。
2. 对每个初始 state 枚举全部可用 acquisition action。
3. 生成 state-action counterfactual rows。
4. 使用公开特征训练无依赖 logistic baseline。
5. 输出 train/test rows、prediction 和 metrics。

输出目录：

- `09-experiments/results/m3b_toy_train_real_test/`

## 3. 特征与标签

### 3.1 特征

当前使用的公开特征包括：

- `cost`
- `budget_remaining`
- `cti_node_coverage`
- `cti_edge_coverage`
- `critical_gap_count`
- `intended_node_count`
- `intended_gap_overlap_count`
- `intended_critical_gap_overlap_count`
- `intended_gap_precision`
- `intended_gap_recall`
- `expected_granularity_gain`
- `expected_uncertainty_reduction`
- `expected_over_attribution_risk_reduction`
- `expected_conflict_resolution`
- `expected_coverage_delta`

特征明确不包含：

- hidden claim ids
- `recoverable_claim_ids`
- actual recovered claims
- oracle path

### 3.2 标签

离线训练标签由 counterfactual outcome 生成：

- `label_yield_positive`
- `label_resolves_any_gap_node`
- `label_resolves_critical_gap_node`
- `label_reaches_target_after_action`

本轮主标签：

```text
label_resolves_critical_gap_node
```

## 4. 信息边界测试

新增测试验证：

1. counterfactual row 能正确标记 action 是否解决缺口节点。
2. 修改 `recoverable_claim_ids` 后，feature row 不变化。
3. logistic baseline 能在可分数据上把 positive action 排到 negative action 前面。

全量测试：

```text
Ran 42 tests
OK
```

## 5. 实验设置

训练集：

```text
C01-C03 toy cases
```

测试集：

```text
C04-C06 real DARPA E3 cases
```

主任务：

```text
Predict whether an action resolves at least one critical unmatched CTI node.
```

## 6. 主结果

结果文件：

- `09-experiments/results/m3b_toy_train_real_test/m3b_metrics.json`
- `09-experiments/results/m3b_toy_train_real_test/m3b_test_predictions.csv`

| Split | Rows | Positive rate | Accuracy | Brier | AUROC | AP | Top-1 label hit |
|---|---:|---:|---:|---:|---:|---:|---:|
| Train C01-C03 | 945 | 0.3577 | 1.0000 | 0.0038 | 1.0000 | 1.0000 | 0.8519 |
| Test C04-C06 | 765 | 0.1922 | 1.0000 | 0.0069 | 1.0000 | 1.0000 | 0.7111 |

解释：

- 该结果说明公开 action-gap 特征足以强预测“是否解决关键缺口节点”。
- Top-1 label hit 未达到 1.0，是因为模型每个 state 只选一个 action，而某些 state 中存在多个 positive action，且最佳 action 还需要考虑后续 granularity transition 与预算。

## 7. 特征消融

结果文件：

- `09-experiments/results/m3b_toy_train_real_test/m3b_ablation_metrics.json`

| Feature set | Test AUROC | Test AP | Test Brier | Test top-1 label hit |
|---|---:|---:|---:|---:|
| full | 1.0000 | 1.0000 | 0.0069 | 0.7111 |
| no_gap_compat | 0.8274 | 0.6580 | 0.1089 | 0.4519 |
| expected_effects_only | 0.6528 | 0.4478 | 0.1544 | 0.4519 |

这说明：

1. 只靠 `expected_*` 手写收益不足以预测真实关键缺口收益。
2. 去掉 action-gap compatibility 后，性能明显下降。
3. M3b 的主线应继续围绕“证据缺口图 + action-gap 条件收益”，而不是回到固定 expected gain 排序。

## 8. 当前局限

必须谨慎看待当前结果：

1. `intended_cti_node_ids` 目前是人工补充的公开语义字段。
2. C04-C06 的 action 空间仍然较干净，缺少大量噪声 action、误导 action 和不可用 action。
3. 当前模型预测的是 node-resolution，不是完整 policy success。
4. 因为 C06 已用于前期诊断，它不能作为最终独立 holdout。
5. 结果过强，说明当前标签与 action-gap 特征高度一致，下一步必须增加更复杂的 action space 和新 trace。

## 9. 下一步

### 9.1 M3b-2

把预测目标扩展为多头：

```text
P(action resolves node)
P(action has positive yield)
P(next granularity >= target)
```

### 9.2 M3b policy evaluation

把模型输出接回 planner：

```text
score(action) =
  P(resolve critical node)
  + alpha * P(reach target granularity)
  - beta * cost
```

并与 M3a、M2、coverage greedy、oracle 对比完整 episode success。

### 9.3 新 holdout

必须引入未参与设计的新 trace：

- DARPA TC E5
- OPTC
- 或其他 campaign-level provenance trace

只有新 holdout 上仍能保持收益，M3b 才能升级为论文主实验。

