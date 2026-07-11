# Project05 XGBoost 动作价值实验结果 v0.1

日期：2026-07-11  
对应协议：`xgboost-action-value-protocol-v0.1-20260711.md`

## 1. 设置

- 训练案例：C01-C06，共 6 个开发案例、1845 条 state-action rows。
- 参数锁定测试：C07-C09，共 3 个案例、720 条 state-action rows。
- 策略回放：135 个配对条件，每个方法 135 个 episode。
- XGBoost：3.2.0，固定 150 rounds、depth 3、eta 0.05、seed 11、单线程 CPU。
- 运行时只读取 16 个公开特征，不读取 hidden claims、`recoverable_claim_ids` 或 Oracle path。

## 2. 主标签分类结果

主标签：`label_resolves_critical_gap_node`。

| 模型 | Test Accuracy | Brier | AUROC | AP | Top-1 positive hit |
|---|---:|---:|---:|---:|---:|
| Logistic M3b | **0.7917** | 0.1250 | **0.9205** | 0.8949 | 0.8296 |
| XGBoost | 0.7861 | **0.1217** | 0.9181 | **0.8953** | **0.8593** |

XGBoost 没有建立 AUROC 或 accuracy 优势；它的有效增量主要是 top-1 动作排序和轻微 Brier/AP 改善。

## 3. 辅助标签

### Positive yield

XGBoost test AUROC/AP 为 `0.8260/0.8442`，高于 Logistic 的 `0.8059/0.8030`；但 top-1 hit 为 `0.8593`，略低于 Logistic 的 `0.8667`。

### One-step reaches target

XGBoost test AUROC/AP 为 `0.9746/0.8897`，高于 Logistic 的 `0.9437/0.7980`，但 Brier 从 Logistic 的 `0.0665` 恶化到 `0.2261`，accuracy 从 `0.9056` 降到 `0.6611`。这说明排序能力提高但概率严重失校准，不能直接作为停止概率。

## 4. 序贯策略结果

| 方法 | Success | Mean cost | Regret vs Oracle | Zero-yield | Ceiling violation |
|---|---:|---:|---:|---:|---:|
| Oracle | 1.0000 | 3.8889 | 0.0000 | 0.0000 | 0.0000 |
| **M2** | **1.0000** | **4.5259** | **0.6370** | 0.2741 | 0.0000 |
| XGBoost | 1.0000 | 4.7556 | 0.8667 | **0.1704** | 0.0000 |
| Logistic M3b | 0.9778 | 4.8561 | 0.9470 | 0.2370 | 0.0000 |
| M3a | 1.0000 | 5.0741 | 1.1852 | 0.5926 | 0.0000 |
| Coverage | 0.9407 | 5.8740 | 2.0472 | 1.1481 | 0.0000 |

XGBoost 相对 Logistic：

- 修复 3 个失败条件，均来自 C09；
- 31 次成功条件成本更低，20 次更高，81 次持平；
- 总体 success 从 97.78% 提升到 100%，mean cost 从 4.8561 降至 4.7556。

XGBoost 相对 M2：

- success 持平；
- 33 次成本更低，59 次更高，43 次持平；
- 总体成本仍高 `0.2297`，regret 高 `0.2297`。

## 5. 案例分解

| 案例 | XGBoost cost | Logistic cost | M2 cost | 结论 |
|---|---:|---:|---:|---|
| C07 | 4.8444 | 4.3333 | 4.3111 | XGBoost 更差 |
| C08 | 4.5556 | 4.9333 | 4.5111 | 优于 Logistic，略差于 M2 |
| C09 | 4.8667 | 5.3333，success 0.9333 | 4.7556 | 修复 Logistic 失败，仍差于 M2 |

## 6. 特征依赖

主模型最重要特征是：

1. `intended_critical_gap_overlap_count`
2. `intended_gap_overlap_count`
3. `intended_gap_precision`
4. `intended_gap_recall`

这些特征来自公开动作意图标注。结果证明 action-gap 表示有预测力，同时也说明模型高度依赖标注质量，不能把性能全部归因于 XGBoost 算法本身。

## 7. DQN Gate

- 已通过：XGBoost 相对 Logistic 有小幅 episode 增益，并修复 C09 的失败。
- 未通过：没有超过 M2；尚未建立真正非短视状态的独立测试；只有 3 个参数锁定测试案例；`reaches_target` 概率失校准。

因此当前不应立即把 DQN 写成已确定主模型。下一步先构造非短视决策诊断集、增加 C10 或训练环境，并区分“动作标签预测”与“长期累计回报学习”。

## 8. 可支持与不可支持

可支持：XGBoost 是比 Logistic 更稳的非线性 learned-policy baseline，在 C09 修复了部分提前停止，并保持零 ceiling violation。

不可支持：XGBoost 全面优于 Logistic、XGBoost 优于 M2、当前结果证明 DQN 必然有效、135 个重复条件等于 135 个独立攻击案例。

## 9. 产物

- Runner：`09-experiments/scripts/run_xgboost.py`
- 模型与 SHA：`09-experiments/results/xgboost_c01_c06_train_c07_c09_test/xgboost_*.json`
- 分类和策略汇总：`xgboost_experiment_summary.json`
- 策略结果：`xgboost_policy_results.csv`
- 压缩轨迹：`xgboost_policy_traces.json.gz`
