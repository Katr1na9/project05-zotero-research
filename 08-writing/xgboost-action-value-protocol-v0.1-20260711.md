# Project05 XGBoost 动作价值实验协议 v0.1

日期：2026-07-11  
状态：预注册，C07-C09 XGBoost 结果生成前冻结

## 1. 研究问题

在不读取隐藏证据、实际可恢复集合或 Oracle 路径的条件下，XGBoost 能否从公开 evidence-state 与 acquisition-action 特征学习非线性动作价值，并在完整序贯回放中优于 Logistic M3b 和规则基线 M2？

## 2. 数据切分

- 训练：C01-C03 toy + C04-C06 DARPA E3，共 6 个开发案例。
- 参数锁定测试：C07 E5 THEIA、C08 E5 ClearScope、C09 OpTC，共 3 个案例。
- 同一案例内的 mask、intensity 和 seed 是重复条件，不作为独立攻击案例。
- C07-C09 的规则结果已经被分析，因此它们不是整个研究层面的完全未见数据；它们只保证未用于 XGBoost 拟合和调参。
- 最终外部泛化结论仍需新增 C10。

## 3. 输入特征

完全复用 `run_m3b.py::FEATURE_COLUMNS` 的 16 个公开特征，包括成本、剩余预算、节点/边覆盖、关键缺口、公开动作意图与缺口重合、通道先验和 expected effects。

禁止输入：

- hidden claim ids；
- `recoverable_claim_ids`；
- actual recovered claims；
- Oracle path / Oracle action；
- 测试集标签或测试集统计产生的参数。

## 4. 标签与模型

主标签：`label_resolves_critical_gap_node`。

辅助标签：

- `label_yield_positive`；
- `label_reaches_target_after_action`。

三个标签分别训练二分类器。序贯策略只使用主标签模型。

冻结 XGBoost 参数：

```json
{
  "objective": "binary:logistic",
  "eval_metric": "logloss",
  "max_depth": 3,
  "eta": 0.05,
  "min_child_weight": 1.0,
  "subsample": 0.8,
  "colsample_bytree": 0.8,
  "lambda": 1.0,
  "alpha": 0.0,
  "seed": 11,
  "nthread": 1
}
```

固定 boosting rounds：150。不得依据 C07-C09 修改。

## 5. 策略回放

对非 STOP 动作：

```text
utility(s,a) = P_XGB(resolve critical gap | s,a) - 0.1 * cost(a)
```

STOP utility 固定为 0。当全部采集动作 utility 不为正时选择 STOP。每一步根据执行反馈重新构造公开 state-action 特征。

## 6. 对照

- Logistic Regression M3b，使用相同训练案例、特征、标签和 cost penalty；
- M2；
- M3a，仅作已冻结规则对照；
- Coverage greedy；
- Oracle，仅作评测上界。

## 7. 指标

静态动作价值：accuracy、Brier、AUROC、AP、top-1 positive-action hit。

序贯主指标：target success、cost-to-target、regret vs Oracle、premature stop、ceiling violation、zero-yield actions。

独立案例数只有 3，主结果作案例级和配对描述，不把 135 个重复条件当作 135 个独立样本做显著性夸大。

## 8. 判定规则

- XGBoost 必须在序贯回放中改善 Logistic 或 M2，不能只依靠更高 AUROC 宣称成功。
- 若 XGBoost 与 Logistic/M2 持平，说明树模型没有提供稳定新增价值，不据此进入 DQN。
- 若测试分类性能高但 episode 性能下降，优先诊断标签与长期目标错位。
- 若 ceiling violation 增加，否定安全性改进主张。
- 只有观察到可复现的非短视失败、并补足训练环境后，才进入 DQN/Dueling DQN。

