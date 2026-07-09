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
- 初始 5 个策略：`random`、`fixed_order`、`coverage_greedy`、`project05_m1`、`full_evidence`；2026-07-09 后增加 Oracle、CMI proxy 和 M1 消融。

G3 campaign-level 判定要求所有 critical CTI 节点被覆盖，因此遮蔽 C2、collection 或 exfiltration 关键证据后，系统必须通过动作恢复证据才能达到目标粒度。

## 已退役的 C01 调试快照

`results/c01_mvp_summary.json` 当前结果：

| Planner | success_rate | mean_cost_to_target | mean_steps_to_target |
|---|---:|---:|---:|
| random | 0.4000 | 5.5000 | 2.1667 |
| fixed_order | 1.0000 | 6.2667 | 2.6667 |
| coverage_greedy | 1.0000 | 3.4000 | 1.4667 |
| project05_m1 | 1.0000 | 3.0000 | 1.4667 |
| full_evidence | 1.0000 | 0.0000 | 0.0000 |

该快照中的 `coverage_greedy` 和 `project05_m1` 在动作评分时读取了真实隐藏证据，存在 Oracle 信息泄漏。它只保留为工程历史，不得用于论文结论；有效结果以 `all_cases_*` 严格版本为准。

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

`all_cases_traces.json` 约 20.5 MB，由命令在本地生成，不进入 Git。

修正信息泄漏后，当前共 3 个独立案例、1620 个重复运行。总体结果如下：

| Planner | success_rate | mean_cost_to_target | mean regret vs Oracle |
|---|---:|---:|---:|
| oracle_optimal | 1.0000 | 2.3778 | 0.0000 |
| project05_m1 | 0.9333 | 3.5714 | 1.1984 |
| m1_no_granularity | 0.9630 | 4.1000 | 1.7385 |
| m1_no_uncertainty | 0.9333 | 3.5714 | 1.1984 |
| m1_no_risk | 0.9333 | 3.5714 | 1.1984 |
| m1_no_coverage | 0.8741 | 3.3390 | 1.0424 |
| m1_no_cost | 0.9333 | 3.9048 | 1.5317 |
| cmi_proxy | 0.7704 | 4.0000 | 1.9423 |
| coverage_greedy | 0.9630 | 4.3077 | 1.9462 |
| random | 0.6444 | 4.1034 | 2.0920 |
| fixed_order | 1.0000 | 4.8741 | 2.4963 |

`cmi_proxy` 只使用动作元数据中的预期不确定性下降，不是真实条件互信息。`m1_no_uncertainty` 和 `m1_no_risk` 与完整 M1 结果相同，说明当前 toy 动作元数据不足以让这两个分量改变动作排序。以上数字仍只验证多案例 toy 协议，不构成论文有效性结论。

## DARPA TC E3 真实数据接入

Phase 0 已固定两个开发案例：

- `R01`：2018-04-11 FiveDirections Firefox/Drakon 完整攻击链，来源 topic 为 `ta1-fivedirections-e3-official-2`；
- `R02`：2018-04-06 CADETS Nginx/Drakon 失败攻击链，来源 topic 为 `ta1-cadets-e3-official`。

清单与 ground-truth slice：

```text
real_data/darpa_tc_e3/manifest.json
real_data/darpa_tc_e3/ground_truth/R01.json
real_data/darpa_tc_e3/ground_truth/R02.json
```

验证：

```powershell
python .\09-experiments\scripts\validate_real_manifest.py
```

当前阶段没有下载大型事件归档。后续只获取 manifest 中锁定的两个 JSON archive，并优先采用流式时间窗扫描；`raw/` 和 `extracted/` 已从 Git 排除。
