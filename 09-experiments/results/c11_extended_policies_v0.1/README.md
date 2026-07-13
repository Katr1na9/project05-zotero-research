# C11 冻结策略迁移 v0.1

状态：完成并通过结果审计。

本目录把 C07-C10 已冻结的 Logistic、XGBoost、AFA-VOI 和 Depth-2 接入 C11。C11 的 AND 多 Claim 语义、G2 目标、预算、动作、遮蔽条件和通道参数均未改变。C11 是一个 OTRF APT29 仿真攻击链；每个策略的 45 个条件是配对重复测量，不是 45 个独立攻击。

## 冻结约束

- XGBoost/Logistic 只使用 C01-C06 训练，C11 仅用于测试；
- C11 生成的三个 XGBoost 模型文件与 C07-C10 主评估模型 SHA-256 完全一致；
- AFA-VOI 保持 Myopic 与 Rollout-H3 原目标和三步 horizon；
- Depth-2 保持 discount `0.8` 和 failure-cost weight `1.0`；
- 三套扩展运行中的 M2/Oracle 行与 C11 首轮结果逐字段一致；
- 非 Oracle 选择器仍不能读取 `recoverable_claim_ids` 或隐藏 claims。

## 结果

| 策略 | Success | 成功条件均成本 | 相对 M2 配对结果 |
|---|---:|---:|---|
| Oracle | 1.0000 | 3.0000 | 参考 |
| XGBoost | 1.0000 | 3.0667 | 10 胜 / 34 平 / 1 负；均值 -0.6000 |
| Logistic | 1.0000 | 3.0667 | 10 胜 / 34 平 / 1 负；均值 -0.6000 |
| Coverage / M1 | 1.0000 | 3.2444 | 原冻结结果 |
| AFA-VOI Myopic | 1.0000 | 3.5556 | 8 胜 / 35 平 / 2 负；均值 -0.1111 |
| M3a | 1.0000 | 3.5556 | 原冻结结果 |
| M2 | 1.0000 | 3.6667 | 参考 |
| AFA-VOI Rollout-H3 | 1.0000 | 3.6889 | 8 胜 / 33 平 / 4 负；均值 +0.0222 |
| Depth-2 Public | 0.9778 | 4.9091 | 1 次成功退化；共同成功条件均值 +1.3182 |

XGBoost 的主标签离线平均精确率为 `0.3952`，低于 Logistic 的 `0.6322`，但二者的序贯结果完全相同。因此本实验不支持“XGBoost 分类能力更强”或“复杂模型普遍更优”；它只表明冻结学习排序在这一 C11 动作空间上比 M2 更接近 Oracle。

## 复现

```powershell
python 09-experiments/scripts/run_xgboost.py --examples-root 09-experiments/examples --real-cases-root 09-experiments/real_cases --output-dir 09-experiments/results/c11_extended_policies_v0.1/xgboost --test-prefixes C11- --experiment-id project05-xgboost-c01-c06-to-c11-frozen-transfer-v0.1
python 09-experiments/scripts/run_afa_voi_baselines.py --cases-root 09-experiments/real_cases --output-dir 09-experiments/results/c11_extended_policies_v0.1/afa_voi --case-prefixes C11 --experiment-id project05-afa-voi-c11-frozen-transfer-v0.1
python 09-experiments/scripts/run_lightweight_nonmyopic_real.py --cases-root 09-experiments/real_cases --output-dir 09-experiments/results/c11_extended_policies_v0.1/depth2 --case-prefixes C11 --experiment-id project05-depth2-public-c11-frozen-transfer-v0.1
python 09-experiments/scripts/summarize_c11_extended_policies.py
```

权威汇总为 `c11_extended_policy_summary.json`，紧凑表为 `c11_extended_policy_table.csv`。C11 不与 C07-C10 的 G3 结果求总均值。
