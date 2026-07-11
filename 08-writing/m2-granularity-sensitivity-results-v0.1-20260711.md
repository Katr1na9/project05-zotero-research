# M2 权重与粒度代理敏感性结果 v0.1

日期：2026-07-11
协议：`m2-granularity-sensitivity-protocol-v0.1-20260711.md`
状态：冻结分析结果

## 1. M2 单权重扰动

对八个 M2 权重分别进行 0.75 倍和 1.25 倍 one-at-a-time 扰动。16 个变体在 C07-C10 上均保持 success=1.0000、premature STOP=0 和 ceiling violation=0。

- 13/16 个变体与原始 M2 的平均成本、zero-yield 和首动作完全一致；
- `cost x1.25`、`risk x0.75`、`uncertainty x0.75` 三个变体的首动作一致率均为 0.8778；
- 这三个变体的平均成本从 4.5333 增至 4.5556，平均增加 0.0222；zero-yield 从 0.2667 增至 0.3111；
- 没有变体降低原始 M2 的聚合平均成本。

因此，当前结论对单权重 ±25% 扰动局部稳定，但这不证明原始权重全局最优，也不替代跨案例调参与外部验证。

## 2. G0-G3 阈值

在 Lenient、Default 和 Conservative 三档阈值下，C07-C10 的 M2 与 Oracle 结果完全相同：M2 success=1.0000、mean cost=4.5333；Oracle success=1.0000、mean cost=3.9333。

该不变性来自当前案例结构，而不是阈值已经得到外部验证。四个案例的目标 G3 都要求所有 critical nodes 覆盖；该条件比所测试的 node/edge 数值阈值更严格并实际主导判定。因此只能写“在预登记局部区间内数值阈值不改变当前四例结果”。

## 3. OR/AND 覆盖语义

C07-C10 的每个 CTI 节点都只有一条 required claim，故 OR 与 AND 按定义完全等价。真实留出无法识别两种语义的差异，不能据此声称 OR/AND 鲁棒。

在存在多 claim 节点的 C01-C06 开发案例上，默认阈值下结果为：

| Semantics | M2 success | M2 mean cost* | Oracle success | Oracle mean cost* |
|---|---:|---:|---:|---:|
| OR | 0.8000 | 2.7500 | 0.9889 | 2.1348 |
| AND | 0.4963 | 4.2015 | 0.7333 | 3.8939 |

\* 仅成功 episode。

AND 显著降低可达率并提高成功条件成本，说明 success 会受节点证据组合语义影响。由于这是开发集压力分析，不得外推为真实留出性能；它反而强化了人工校准和多源 corroboration 案例的必要性。

## 4. 论文口径

支持的结论：透明 M2 在当前四例上对局部单权重扰动稳定；当前结果不由 G 阈值的小幅移动驱动。

不支持的结论：G0-G3 已得到专家效度验证；OR 优于 AND；M2 权重全局最优；四个真实案例已覆盖多 claim corroboration。

## 5. 可复现产物

- 语义扩展：`09-experiments/scripts/run_mvp.py`
- 敏感性实现：`09-experiments/scripts/run_m2_sensitivity.py`
- 测试：`09-experiments/tests/test_granularity_semantics.py`、`test_m2_sensitivity.py`
- 结果：`09-experiments/results/m2_sensitivity_v0.1/`
