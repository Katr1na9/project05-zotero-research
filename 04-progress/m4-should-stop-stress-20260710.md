# M4：真正应停压力测试（2026-07-10）

## 动机

上一轮显式 `STOP` 落地后，通道离线场景里 Oracle 仍恒可达（可靠回退够用），因此 `justified_degrade_stop` 几乎为 0，无法检验“正确认输”。

## 干预（仅评估时）

`outage_plus_strip_reliable_fallbacks`：

1. 只保留 `network_telemetry` **已实现离线** 的 seed；
2. 把该通道动作可恢复的 claim，从**其他通道**动作的 `recoverable_claim_ids` 中剥离（去掉 P0-#1 为可解性加的可靠回退）。

效果：诱人的便宜 network 动作仍在，但离线时关键 claim 无法被可靠通道偷偷补上 → 目标对 Oracle 也不可达 → 正确行为是 `STOP`。

## 结果（54 个离线条件，真实案例）

| Planner | success | correct_stop | explicit_stop | premature | justified_degrade | budget |
|---|---:|---:|---:|---:|---:|---:|
| Oracle | 0.8148 | **1.000** | 0.1852 | 0.000 | **0.1852** | 1.56 |
| 静态 M3b | 0.8148 | **1.000** | 0.1852 | 0.000 | **0.1852** | 2.22 |
| 自适应 M3b | 0.8148 | **1.000** | 0.1852 | 0.000 | **0.1852** | 2.20 |
| M3a | 0.8148 | **1.000** | 0.1852 | 0.000 | **0.1852** | 2.04 |
| M2 | 0.5556 | 0.7407 | 0.4444 | **0.2593** | 0.1852 | 3.24 |
| coverage | 0.5556 | 0.7407 | 0.4444 | **0.2593** | 0.1852 | 3.56 |

要点：

1. **Oracle 不再恒达标**（`0.8148`），约 18.5% 条件为真正应停。
2. **M3a / M3b / Oracle 在 `correct_stop` 与 `justified_degrade_stop` 上对齐**（均为 1.0 / 0.1852）——强规划器学会了在不可达时停。
3. **弱规划器过早停止**：M2/coverage 的 `premature_stop_rate=0.2593`，`correct_stop` 仅 `0.7407`。
4. 可达子集上 Oracle 仍最省预算（`1.56` vs M3a `2.04` / M3b `2.22`）。

## 产物

- CLI：`--should-stop-stress`
- `results/m3b_reliability_toy_train_real_test/m3b_should_stop_stress_*.csv/json`
- 测试：`tests/test_stop_action.py::ShouldStopInterventionTests`

## 解读

STOP 机制在“目标真不可达”时有效，且把弱规划器的过早放弃暴露出来。当前 M3b 相对 M3a 仍无额外正确停止优势（两者都已对齐 Oracle 的停止决策）；M3b 的增量仍主要在通道先验下的成本/选路，而非停止本身。
