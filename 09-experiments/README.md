# Project05 Experiments

本目录用于 Project05 最小可行实验实现。当前已经完成 C01 小样例和 dependency-free MVP 模拟器。

## 当前产物

- `data_schema/evidence_claim.schema.json`
- `data_schema/alignment_state.schema.json`
- `data_schema/acquisition_action.schema.json`
- `examples/C01/case_config.json`
- `examples/C01/evidence_claims.json`
- `examples/C01/acquisition_actions.json`
- `scripts/run_mvp.py`
- `results/c01_mvp_results.csv`
- `results/c01_mvp_summary.json`
- `results/c01_mvp_traces.json`

## 如何运行

在仓库根目录执行：

```powershell
python .\09-experiments\scripts\run_mvp.py
```

脚本只依赖 Python 标准库。默认读取：

```text
09-experiments/examples/C01/
```

并输出：

```text
09-experiments/results/c01_mvp_results.csv
09-experiments/results/c01_mvp_summary.json
09-experiments/results/c01_mvp_traces.json
```

## C01 实验设计

C01 是一个手工构造的 Linux provenance 多阶段入侵小样例：

- 12 条 `evidence_claim`；
- 8 个 `acquisition_action`；
- 3 种遮蔽策略：`random`、`stage`、`discriminative`；
- 每种遮蔽策略 5 个随机种子；
- 5 个策略：`random`、`fixed_order`、`coverage_greedy`、`project05_m1`、`full_evidence`。

G3 campaign-level 判定要求所有 critical CTI 节点被覆盖，因此遮蔽 C2、collection 或 exfiltration 关键证据后，系统必须通过动作恢复证据才能达到目标粒度。

## 当前结果快照

`results/c01_mvp_summary.json` 当前结果：

| Planner | success_rate | mean_cost_to_target | mean_steps_to_target |
|---|---:|---:|---:|
| random | 0.4000 | 5.5000 | 2.1667 |
| fixed_order | 1.0000 | 6.2667 | 2.6667 |
| coverage_greedy | 1.0000 | 3.4000 | 1.4667 |
| project05_m1 | 1.0000 | 3.0000 | 1.4667 |
| full_evidence | 1.0000 | 0.0000 | 0.0000 |

这个结果只说明 C01 toy simulator 可以跑通，并初步显示 cost-aware Project05-M1 比固定顺序和 coverage-greedy 更省成本。它还不能作为论文实验结论，后续需要 C02/C03、更多 mask 强度和更严格统计。

## 与写作文档的关系

- 实验方案：`../08-writing/experiment-plan-v0.1-20260707.md`
- 案例清单：`../08-writing/experiment-case-inventory-v0.1-20260708.md`

## MVP 原则

第一版只提交 schema、配置、小样例和结果表。大型原始日志、PDF、威胁情报全文和中间大体量图数据不进入 GitHub。

## 多案例实验矩阵

2026-07-09 已将模拟器扩展为多案例运行器，并加入：

- C01 Linux provenance；
- C02 FreeBSD audit/provenance；
- C03 Windows process/registry/network；
- `20% / 40% / 60%` 三档 mask intensity；
- `random / stage / discriminative` 三种缺失机制；
- 每种条件 5 个随机种子；
- 分案例、分 mask 条件和总体的统计汇总。

运行完整矩阵：

```powershell
python .\09-experiments\scripts\run_mvp.py `
  --examples-dir .\09-experiments\examples `
  --output-dir .\09-experiments\results
```

版本库保留：

```text
results/all_cases_results.csv
results/all_cases_summary.json
```

`all_cases_traces.json` 约 7.6 MB，由命令在本地生成，不进入 Git。

当前共 3 个独立案例、675 个重复运行。总体结果如下：

| Planner | success_rate | mean_cost_to_target |
|---|---:|---:|
| random | 0.6444 | 4.1034 |
| fixed_order | 1.0000 | 4.8741 |
| coverage_greedy | 1.0000 | 2.9778 |
| project05_m1 | 1.0000 | 2.5926 |
| full_evidence | 1.0000 | 0.0000 |

这些数字只验证多案例 toy 闭环和实验代码，不构成论文有效性结论。不同 mask 和 seed 是同一案例上的重复测量，不能作为额外独立样本。
