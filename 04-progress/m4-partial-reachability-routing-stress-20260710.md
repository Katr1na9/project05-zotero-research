# M4：部分可达选路压力测试（2026-07-10）

## 动机

应停压力证明了“真不可达时会停”，但 **M3b 相对 M3a 仍无独立停止优势**。本轮检验唯一还值得做的正向对照：离线后可靠回退仍在（部分关键节点仍可达），预算收紧到刚好够 Oracle 最短可靠路径——浪费一次死通道就买不起回退。

若 M3b 仍打平/更差 → 记负结果，冻结 logistic 层，转写贡献边界。

## 干预（仅评估时）

`outage_plus_tight_budget_keep_fallbacks`：

1. 只保留 `network_telemetry` **已实现离线** 的 seed；
2. **不剥**可靠回退（与 should-stop 相反）；
3. 用 Oracle 在离线实现下的最短成本 `C*` 收紧 `budget_total`（要求 `0 < C* ≤` 原预算，且仍存在“声称能补洞”的死通道动作）。

效果：直走可靠路径仍可达；先烧死通道再走可靠路径则 `remaining < C*` → 不可达。正确行为是避开死通道、走可靠路径（或在浪费后正确认输，但 Oracle 从不浪费）。

## 结果（10 个合格条件，真实案例；几乎全来自 C04）

跳过：`already_at_target=30`，`no_tempting_dead_action=14`（C05/C06 多数离线 seed 已达目标或无诱人死通道）。

| Planner | success | premature_stop | mean_zero_yield | mean_budget |
|---|---:|---:|---:|---:|
| Oracle | **1.00** | 0.00 | **0.00** | 4.90 |
| M2 | 0.20 | 0.80 | 0.90 | 4.40 |
| 自适应 M3b | 0.10 | 0.90 | 1.00 | 4.40 |
| 静态 M3b | 0.10 | 0.90 | 1.00 | 4.50 |
| M3a | **0.00** | **1.00** | 1.00 | 4.30 |
| coverage | 0.00 | 1.00 | 1.10 | 4.20 |

典型失败轨迹：先选便宜死通道 `C04-AA-002`（零收益），再 `STOP`（`premature_stop`）。Oracle 直接走 `C04-AA-005` / `C04-AA-006` 可靠路径。

## 解读

1. **干预有效**：Oracle 成功率 1.0、零零收益动作；对照规划器大量 `premature_stop` + `zero_yield`——预算收紧把“死通道诱惑”变成了硬失败。
2. **M3b 相对 M3a 无实质选路优势**：自适应/静态 M3b 仅 `0.10` vs M3a `0.00`，且两者都近乎全员过早停止；通道先验/反馈在这组紧预算条件下几乎没把规划器推到可靠路径。
3. **与应停压力合读**：会停 ≠ 会选路。当前 logistic M3b 的可写增量仍主要是通道先验特征与反馈机制本身，而非相对 M3a 的稳定成功率优势。
4. **样本窄**：合格条件几乎全在 C04（n=10）。结论按“设计压力下的负/近负结果”写，不外推为全案例泛化。

## 产物

- CLI：`--partial-reachability-stress`
- `results/m3b_reliability_toy_train_real_test/m3b_partial_reachability_stress_*.csv/json`
- 测试：`tests/test_stop_action.py::PartialReachabilityInterventionTests`
- 辅助：`run_mvp.oracle_optimal_plan`（供预算收紧与 Oracle 共用）

## 决策

**冻结在 logistic M3b 上继续加戏。** 下一步应写清贡献边界（信息边界纠错、通道先验、STOP/`justified_degrade`、同质 twin 负对照、本轮部分可达负结果），而不是上 GNN/RL 或再堆同构压力。
