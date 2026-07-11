# 非短视必要性与 DQN 必要性两级 Gate

冻结协议：`08-writing/nonmyopic-dqn-gate-protocol-v0.1-20260711.md`

## 结论

- Gate A（非短视必要性）：**PASS**
- Gate B（DQN 必要性）：**FAIL**
- 决策：`use_lightweight_nonmyopic_planning_no_dqn`

192 个独立参数环境、10 个配对 seed，共运行 7,680 个 episode。DP 相对冻结 M2 的 success 优势为 `0.6208`，证明结构化非短视冲突存在；但 DP 冷启动 p95 为 `83.9598 ms`、最大展开 `23,892` 状态，均未达到 DQN 复杂度门槛。

## 文件

| 文件 | 内容 |
|---|---|
| `nonmyopic_gate_summary.json` | 两级 Gate 判定与总体指标 |
| `nonmyopic_gate_episodes.csv` | 全部 episode 结果 |
| `nonmyopic_gate_scenario_summary.csv` | scenario × planner 聚合 |
| `nonmyopic_gate_dp_benchmarks.csv` | DP 冷启动耗时和展开状态 |
| `nonmyopic_gate_representative_traces.json` | 深度 1/3 代表轨迹（本地生成） |

本实验只证明人工环境族内的存在性和规划边界，不估计真实事件发生率。
