# M3b-2：学习效用策略回放与诱饵动作负对照（2026-07-10）

## 本轮问题

M3b 已证明状态-动作特征可以预测“动作是否补上关键证据缺口”，但尚未证明该预测器能够改善完整的、序贯的取证决策。因此本轮将训练出的逻辑回归模型接入 episode planner，并在同一批 DARPA TC E3 case-condition 上和规则方法比较。

## 固定实验设计

- 训练：C01-C03 toy cases。
- 测试：C04-C06 DARPA TC E3 real cases。
- 独立分析单位：`case_id + mask_strategy + mask_intensity + seed`；不能把同一 case 的多个 seed 当成独立攻击样本。
- 策略分数：`P(补上关键缺口) - 0.1 * action_cost`。
- 比较对象：coverage greedy、M2、M3a、oracle optimal。
- 运行时策略只读公开状态与候选动作描述；`recoverable_claim_ids` 只在执行动作和离线监督标签中使用。

## M3b-2 主结果

正常动作空间（135 个 matched episodes）下：

| Planner | 成功率 | 达标平均成本 | 平均预算使用 |
|---|---:|---:|---:|
| M3b learned policy | 1.0000 | 1.6519 | 1.6519 |
| M3a gap compatibility | 1.0000 | 1.6519 | 1.6519 |
| M2 | 0.8370 | 1.7876 | 2.6370 |
| coverage greedy | 0.9037 | 2.1803 | 2.7407 |
| oracle | 1.0000 | 1.6519 | 1.6519 |

结论不能夸大：M3b 在当前干净动作空间中复现了 M3a 的选择，而非超过 M3a。原因是 M3b 的最强特征就是 M3a 已显式使用的“动作意图节点与当前关键缺口的重合”。

## 负对照：匹配诱饵动作

为了检验该结论是否只是动作空间过于干净，测试集中的 17 个原始动作被扩展为 30 个候选动作。对每个面向关键 CTI 节点的真实动作，加入一个：

- 公开特征完全一致（成本、动作类型、目标、预期影响、意图节点均相同）；
- 仅 action id 不同；
- 离线真实结果为零，即 `recoverable_claim_ids=[]`。

这不是对 DARPA 原始证据的篡改，而是候选取证接口的可靠性失真负对照。公开信息相同的 twins 在决策前不可辨识，因此它用于识别方法的信息论边界，而不是模拟一个“模型本应猜中”的场景。

| Planner | 成功率 | 达标平均成本 | 平均预算使用 |
|---|---:|---:|---:|
| M3b learned policy | 0.9037 | 2.2131 | 2.6741 |
| M3a gap compatibility | 0.9037 | 2.2131 | 2.6815 |
| M2 | 0.8370 | 1.7876 | 2.6370 |
| coverage greedy | 0.8074 | 2.1101 | 3.2444 |
| oracle | 1.0000 | 1.6519 | 1.6519 |

## 研究含义

1. 当前 M3b-2 的贡献是把 M3a 的缺口匹配信号变成可训练、可校准、可审计的效用估计器；它尚不是独立的性能优势。
2. 当候选动作的公开元数据与真实产出脱钩时，M3a 与 M3b 同时下降，说明仅靠一次性的 action-gap compatibility 无法解决“动作可靠性未知”问题。
3. 下一主线应为 M3b-3 / M4：把动作执行后的 yield feedback 转化为动态可靠性后验（可按动作类型、数据源、目标、时间窗口分层），再用该后验调节下一轮动作效用。这样模型才会拥有 M3a 静态规则没有的可学习增量。

## 可复现入口与产物

```powershell
python 09-experiments\scripts\run_m3b.py `
  --train-dir 09-experiments\examples `
  --test-dir 09-experiments\real_cases `
  --output-dir 09-experiments\results\m3b_policy_toy_train_real_test `
  --label-column label_resolves_critical_gap_node `
  --evaluate-policy --decoy-stress --cost-penalty 0.1
```

- 正常回放：[m3b_policy_results.csv](../09-experiments/results/m3b_policy_toy_train_real_test/m3b_policy_results.csv)
- 正常回放摘要：[m3b_policy_summary.json](../09-experiments/results/m3b_policy_toy_train_real_test/m3b_policy_summary.json)
- 诱饵负对照：[m3b_decoy_stress_results.csv](../09-experiments/results/m3b_policy_toy_train_real_test/m3b_decoy_stress_results.csv)
- 诱饵负对照摘要：[m3b_decoy_stress_summary.json](../09-experiments/results/m3b_policy_toy_train_real_test/m3b_decoy_stress_summary.json)
