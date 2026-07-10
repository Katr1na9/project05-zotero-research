# M4 推进：通道级可靠性后验 + 通道离线正向压力（2026-07-10）

## 本轮改动

1. `reliability_group` 从 `action_type|evidence_types` 改为 `acquisition_channel`。
   同通道动作共享 Beta 后验；跨通道不迁移。同质 twin 仍是负对照（公开通道相同）。
2. 新增正向压力实验 `--channel-outage-stress`：只评估 `network_telemetry` **已实现离线** 的 seed。
   公开先验仍为预登记的 0.5；静态策略看不到“本 episode 离线”，自适应策略需靠首次零收益反馈转向可靠通道。

## 结果（真实案例 C04–C06，cost_penalty=0.1）

### 正常动作空间

自适应与静态 M3b 均为成功率 `0.9852`、达标成本 `1.9248`；M3a `0.9778` / `1.7727`；Oracle `1.0000` / `1.7852`。

### 同质 twin 诱饵（负对照，仍成立）

| Planner | 成功率 | 达标成本 |
|---|---:|---:|
| 自适应 M3b | 0.5778 | 1.0128 |
| 静态 M3b | 0.6519 | 1.7045 |
| M3a | 0.8370 | 2.8319 |
| Oracle | 1.0000 | 1.7852 |

公开不可区分时，组级后验仍无法识别真动作。

### 通道离线正向压力（54 个离线条件）

| Planner | 成功率 | 达标成本 | 预算使用 |
|---|---:|---:|---:|
| 自适应 M3b | 0.9630 | 1.5962 | 1.7963 |
| 静态 M3b | 0.9630 | 1.5962 | 1.7963 |
| M3a | 0.9444 | 1.7255 | 2.0370 |
| Oracle | 1.0000 | 1.7593 | 1.7593 |

要点：

- **静态 M3b（含 `channel_prior_reliability`）在离线 seed 上优于 M3a**（成功率更高、成本更低）。
- 自适应 ≈ 静态：先验权重已足够让模型偏好可靠通道，首次反馈未再提供增量。
- 这与同质 twin 负对照形成对照：公开可区分的通道故障下，通道先验有真实增益；完全同质 twin 下没有。

## 产物

- `09-experiments/results/m3b_reliability_toy_train_real_test/m3b_channel_outage_stress_results.csv`
- `09-experiments/results/m3b_reliability_toy_train_real_test/m3b_channel_outage_stress_summary.json`

## 下一步

显式 `stop` / 降级动作：在可靠路径超预算或通道持续失败时，用 `correct_stop` 作为主指标，而不是继续烧预算。
