# C07-C09 冻结预算效率实验结果 v0.1

日期：2026-07-11  
对应协议：`c07-c09-budget-efficiency-protocol-v0.1-20260711.md`

## 1. 实验规模

- 独立真实攻击案例：3 个，C07、C08、C09。
- 配对遮蔽条件：135 个，每个案例 45 个。
- 规划器：Coverage、CMI proxy、M1、M2、M3a、Oracle。
- 总运行数：3192。
- M3a 权重未依据 C07-C09 调整。
- 所有方法的 ceiling violation rate 均为 0。

## 2. 紧预算主结果

| 方法 | C* | C*+1 | C*+2 |
|---|---:|---:|---:|
| Coverage | 37.04% | 37.04% | 65.19% |
| CMI proxy | 25.19% | 25.19% | 56.30% |
| M1 | 31.11% | 31.11% | 65.19% |
| **M2** | **66.67%** | **66.67%** | **100.00%** |
| M3a | 50.37% | 50.37% | 90.37% |
| Oracle | 100.00% | 100.00% | 100.00% |

这里的百分比来自 135 个配对重复条件；独立攻击案例仍只有 3 个，不能把 135 当作独立样本量做强统计推断。

## 3. M3a 与 M2 的配对结论

| 预算 | M3a 净胜 | 持平 | M3a 净负 |
|---|---:|---:|---:|
| C* | 0 | 113 | 22 |
| C*+1 | 0 | 113 | 22 |
| C*+2 | 0 | 122 | 13 |

M3a 没有在任何紧预算配对条件上胜过 M2。因此：

1. 不能把 M3a 写成优于 M2 的规划创新。
2. 当前最强可部署规划器是 M2。
3. M3a 可作为一次有价值的负结果：显式 gap compatibility 不等于更好的序列决策，过度依赖公开意图与当前缺口重合会丢失 M2 的成本、重叠和反馈权衡。
4. 不再使用 C07-C09 调整 M3a；若要开发 M4，必须回到独立开发案例，再使用新的未见案例评估。

## 4. 原始预算结果

- C07、C08：所有评估规划器均达到 100%，存在明显天花板效应。
- C09：M2 与 M3a 为 100%；Coverage、CMI、M1 为 82.22%。
- 原始预算只说明方法在宽松预算下最终可达，不能区分紧预算效率。

## 5. 论文主张调整

当前可支持的主张：

- 建立了证据状态、支持粒度和证据采集动作的统一实验表示。
- 建立了保持自然证据缺口的 DARPA E5/OpTC 真实案例评估。
- 提出了按条件计算 Oracle 最小成本并进行配对预算评测的方法。
- M2 在三个未见案例的紧预算描述性实验中优于简单 Coverage、CMI、M1 和 M3a。

当前不可支持的主张：

- M3a 是新的最优规划器。
- 当前结果证明了 LLM 的有效性。
- 135 个遮蔽条件等价于 135 个独立攻击案例。
- 当前结果足以证明对任意 APT 数据集的统计泛化。

## 6. 产物

- 原始结果：`09-experiments/results/c07_c09_budget_efficiency/budget_efficiency_results.csv`
- 汇总：`09-experiments/results/c07_c09_budget_efficiency/budget_efficiency_summary.json`
- 完整运行轨迹：`09-experiments/results/c07_c09_budget_efficiency/budget_efficiency_traces.json.gz`
- 主表：`08-writing/table-budget-efficiency-c07-c09.csv`
- 主图：`08-writing/fig-budget-efficiency-c07-c09.pdf` 与 `.png`
