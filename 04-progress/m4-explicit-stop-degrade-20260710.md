# M4 后半段：显式 STOP / 降级停止（2026-07-10）

## 本轮改动

1. 每个 episode 自动注入公开零成本动作 `STOP`（`action_type=stop`，通道 `decision`）。
2. 选择 `STOP` 立即结束 episode，接受当前 `supportable_granularity`，不恢复任何 claim。
3. 规划器语义：
   - M3a / M3b / 自适应 M3b：`STOP` 效用 = 0（盈亏平衡）；仅当存在正效用取证动作时才继续。
   - Oracle：在已实现通道状态下若无任何可产出恢复路径，则选 `STOP`。
   - coverage / CMI / M1 / M2：同分时偏好 `STOP`，避免在零增益动作上烧预算。
4. 指标扩展：
   - `explicit_stop`
   - `correct_target_stop` / `correct_degrade_stop` / `correct_stop`
   - `premature_stop`（相对同条件 Oracle 仍可达却提前停）
   - `justified_degrade_stop`（Oracle 也不可达时的显式停止）

## 结果要点

### 正常真实案例回放（135 runs）

| Planner | success | correct_stop | explicit_stop | budget |
|---|---:|---:|---:|---:|
| Oracle | 1.000 | 1.000 | 0.000 | 1.79 |
| 静态/自适应 M3b | 0.985 | 0.985 | 0.015 | 2.00 |
| M3a | 0.978 | 0.978 | 0.022 | 1.90 |
| M2 | 0.800 | 0.800 | 0.200 | 2.85 |
| coverage | 0.756 | 0.756 | 0.244 | 3.16 |

弱规划器开始显式停止；强规划器几乎不需要。

### 通道离线正向压力（54 conditions）

| Planner | success | correct_stop | explicit_stop | budget |
|---|---:|---:|---:|---:|
| Oracle | 1.000 | 1.000 | 0.000 | 1.76 |
| 静态/自适应 M3b | 0.963 | 0.963 | 0.037 | 1.80 |
| M3a | 0.944 | 0.944 | 0.056 | 2.04 |
| M2 | 0.648 | 0.648 | 0.352 | 3.06 |
| coverage | 0.593 | 0.593 | 0.407 | 3.48 |

说明：当前案例在 network 离线时仍有可靠回退路径，故 Oracle 仍恒可达，`justified_degrade_stop` 几乎不出现。STOP 的主要收益是让弱规划器少烧预算，而不是让强策略学会“认输”。

## 产物

- `tests/test_stop_action.py`
- schema 增加 `stop`
- 刷新：`results/all_cases_*`、`results/m3b_reliability_toy_train_real_test/*`

## 下一步

构造**真正应停**的条件：可靠回退成本总和 > 剩余预算，或关键节点无可靠通道替代。那时 `justified_degrade_stop` 才会成为区分 M3b/M3a/Oracle 的主信号。
