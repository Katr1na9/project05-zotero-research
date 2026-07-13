# Project05 Experiments

## P0-#1 纠错：打破 `intended_cti_node_ids` 特征泄题（2026-07-10）

审查发现所有案例（C01–C06）的动作 `intended_cti_node_ids`（公开"声称目标"）在 OR 覆盖语义下恰好等于该动作 `recoverable_claim_ids` 实际覆盖的节点集合，等同于把答案键交给 M3a/M3b 规划器，使 M3a 近似 Oracle 等价、M3b 无真实可学习空间。

纠错引入**采集通道可靠性（channel reliability）**机制，把"声称目标（declared）"与"实际恢复（actual）"解耦：

- 每个动作有公开的采集通道（默认由 `action_type` 派生，可用 `acquisition_channel` 覆盖）；不可靠通道即使证据存在也可能零收益。
- 通道是否在线：按 `sha256(case_id|channel|seed)` 的确定性伯努利抽样（可复现、跨平台一致）。可靠性写在各 `case_config.json` 的 `channel_reliability` 里（预登记）。
- 缺省完全向后兼容：未声明 `channel_reliability` 的 config 通道可靠性=1.0，行为不变。

预登记档案：`network_telemetry`（`recover_network_summary`）可靠性 0.5，其余通道 1.0。为保证单通道关键节点仍有可靠恢复路径，给 C02/C04/C05 各补一个更贵的可靠回退动作（`C02-AA-007`、`C04-AA-006`、`C05-AA-006`）。

不变量（通道门控下仍严格成立，见 `tests/test_channel_reliability.py`）：Oracle 仍是成本下界（`regret ≥ 0`），且任一规划器达标时 Oracle 必达标。通道离线导致部分高遮蔽 episode 在预算内不可解，属于预期——这正是"何时应停/降级"论线要测的能力。

细节与预登记见 `../04-progress/p0-1-break-feature-leak-channel-reliability-20260710.md`。`results/` 已于 2026-07-10 按该机制重跑刷新。M4 通道离线正向压力见 `../04-progress/m4-channel-reliability-outage-stress-20260710.md`。显式 STOP/降级见 `../04-progress/m4-explicit-stop-degrade-20260710.md`。真正应停压力见 `../04-progress/m4-should-stop-stress-20260710.md`。部分可达选路压力（负/近负结果）见 `../04-progress/m4-partial-reachability-routing-stress-20260710.md`。

**2026-07-13 当前状态**：C07-C10 四个 G3 主案例中，M2 仍是当前冻结对照内的透明部署锚点；非短视 Gate A 通过而 Gate B 未通过，真实 Depth-2 未达到升级门槛，DQN 因而不进入当前主线。C11 作为独立的 OTRF APT29 G2 压力案例，已补齐 Logistic、XGBoost、AFA-VOI 与 Depth-2 的冻结迁移：XGBoost/Logistic 的平均成功成本为 `3.0667`，低于 M2 的 `3.6667`，而 Depth-2 出现一次成功退化。该排序反转只证明策略收益依赖案例结构与覆盖语义，不构成跨域优势。结果见 `results/c11_extended_policies_v0.1/`，论文口径见 `../08-writing/paper-main-draft-v0.6-c11-policy-transfer-20260713.md`。

## C06 独立留出验证（2026-07-10 重跑）

- 数据：CADETS 2018-04-12，318,821 条窗口事件，29,620 个引用节点全部解析。
- 案例：10/10 个真实 CDM motif，目标与支持上限均为 `G3_campaign`。
- 协议：含通道可靠性门控；585 次运行均保留。
- 总体成功率：M2 `0.5111`，M1 `0.5111`，coverage greedy `0.7111`，M3a `0.9778`，Oracle `1.0000`。
- 结论：当前 M2 仍是负结果；通道门控后 M3a 仍强，但不再与 Oracle 成本等价（见下方 toy 矩阵 regret）。不得将 C06 表述为跨数据集泛化。

结果文件：`results/c06_holdout_results.csv`、`results/c06_holdout_summary.json`。

本目录用于 Project05 最小可行实验实现。当前已经完成 C01 小样例和 dependency-free MVP 模拟器。

## 当前产物

- `data_schema/evidence_claim.schema.json`
- `data_schema/alignment_state.schema.json`
- `data_schema/acquisition_action.schema.json`
- `examples/C01/case_config.json`
- `examples/C01/evidence_claims.json`
- `examples/C01/acquisition_actions.json`
- `scripts/run_mvp.py`
- `scripts/run_m3b.py`
- `scripts/run_xgboost.py`
- `scripts/run_afa_voi_baselines.py`
- `scripts/run_lightweight_nonmyopic_real.py`
- `scripts/summarize_c11_extended_policies.py`
- `requirements-ml.txt`
- `results/c01_mvp_results.csv`
- `results/c01_mvp_summary.json`
- `results/c01_mvp_traces.json`
- `results/xgboost_c01_c06_train_c07_c10_test/`
- `results/c11_holdout_v0.1/`
- `results/c11_or_sensitivity_v0.1/`
- `results/c11_extended_policies_v0.1/`

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

P0-#1 通道可靠性纠错后（2026-07-10 重跑），3 个独立 toy 案例总体结果如下：

| Planner | success_rate | mean_cost_to_target | mean regret vs Oracle |
|---|---:|---:|---:|
| oracle_optimal | 0.9778 | 2.4924 | 0.0000 |
| project05_m3a_gap_compat | 0.9556 | 2.6744 | 0.2558 |
| project05_m1 | 0.8148 | 3.9545 | 1.7000 |
| m1_no_uncertainty | 0.8148 | 3.9545 | 1.7000 |
| m1_no_risk | 0.8148 | 3.9545 | 1.7000 |
| m1_no_cost | 0.8148 | 3.9818 | 1.7273 |
| coverage_greedy | 0.8000 | 4.0648 | 1.9352 |
| project05_m2 | 0.8000 | 3.7315 | 1.4907 |
| m1_no_granularity | 0.8000 | 4.0648 | 1.9352 |
| m1_no_coverage | 0.7704 | 3.7788 | 1.5865 |
| fixed_order | 0.7481 | 4.1584 | 2.0198 |
| cmi_proxy | 0.6000 | 3.5679 | 1.9136 |
| random | 0.5704 | 4.1818 | 2.2857 |

要点：Oracle 成功率不再恒为 1.0（部分 episode 因 `network_telemetry` 离线在预算内不可解）；M3a 相对 Oracle 的 mean regret 升至 `0.2558`，不再近似等价。`cmi_proxy` 只使用动作元数据中的预期不确定性下降，不是真实条件互信息。以上数字仍只验证多案例 toy 协议，不构成论文有效性结论。

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

官方 Google Drive 大文件下载当前被网络连接重置。为避免停滞，已使用 ADAPT E3 的公开上下文构建辅助候选索引：

```text
real_data/darpa_tc_e3/derived/adapt_candidate_index.json
```

该索引命中 FiveDirections `9/9` 和 CADETS `11/11` 个 provider-wide ground-truth process UUID，并保留可执行名、父进程、事件类型和网络端点特征。它不包含事件时间或原始 provenance 边，只用于后续原始 CDM 回查，不能直接作为 R01/R02 的最终证据。

重新生成：

```powershell
python .\09-experiments\scripts\build_adapt_candidate_index.py `
  --adapt-root <adapt-e3-checkout> `
  --source-commit 8fa6b58333d18d4601449298d9028c34370fbdd9 `
  --output .\09-experiments\real_data\darpa_tc_e3\derived\adapt_candidate_index.json
```

### PIDSMaker E3 转储获取

PIDSMaker 提供保留节点 UUID、provenance 边和纳秒时间戳的 PostgreSQL 转储。`cadets_e3` 约 1.4 GB，`fivedirections_e3` 约 3.2 GB，是当前优先真实数据入口。下载需要 Google Drive 只读 OAuth，令牌只通过环境变量传入，不写入仓库或命令参数：

```powershell
$env:PIDSMaker_GOOGLE_ACCESS_TOKEN = '<temporary-readonly-token>'
python .\09-experiments\scripts\download_pidsmaker_dumps.py
Remove-Item Env:PIDSMaker_GOOGLE_ACCESS_TOKEN
```

令牌申请范围必须是 `https://www.googleapis.com/auth/drive.readonly`。也可从 [PIDSMaker 官方 Drive 文件夹](https://drive.google.com/drive/folders/1hqfz8__zVqb3QzBuOI2SxrW4lLIdYqFr) 手动下载，并放入：

```text
real_data/darpa_tc_e3/raw/pidsmaker/cadets_e3.dump
real_data/darpa_tc_e3/raw/pidsmaker/fivedirections_e3.dump
```

R01/R02 的宽时间窗继续作为上下文抽取窗；PIDSMaker 的窄攻击时间窗只作为标签窗。两者不得合并，否则会把攻击标签提前泄漏给证据规划器。

### 官方 CDM 时间窗抽取结果

官方原始归档已到位，当前不再依赖 PIDSMaker 转储。流式抽取器不会完整解压归档，而是在单次扫描中建立节点 SQLite 索引，并输出宽上下文窗内的 Event 与被引用节点：

```powershell
python .\09-experiments\scripts\extract_cdm_window.py `
  --archive <archive.tar.gz> `
  --case <R01-or-R02.json> `
  --output-dir <ignored-output-directory>
```

结果概况：

| 案例 | 全量 Event | 窗内 Event | 引用节点解析 |
|---|---:|---:|---:|
| R01 FiveDirections | 256,634,196 | 3,617,566 | 278,976 / 278,983 |
| R02 CADETS | 12,915,596 | 258,074 | 16,646 / 16,646 |

大型 `events.jsonl`、`nodes.jsonl` 与 SQLite 索引位于 Git 忽略的 `extracted/`。可提交的计数、SHA-256 与 observable 复核结果位于 `real_data/darpa_tc_e3/derived/R0*_extraction_summary.json`。

R01 中 `firefox.exe` 和三个基础设施 IP 命中，`www.cnpc.com.cn` 未出现在 FiveDirections CDM 中，应作为“提供方未观测”而非正证据。R02 的六个预设 observable 均命中。部分 FiveDirections 导出行末带逗号，抽取器已兼容该格式。

### DARPA E3 真实行为基元首轮实验

R01/R02 已分别编译为 C04/C05，每例包含 8 条具有 Event UUID 回指的真实行为基元。实验包含 2 个开发案例、3 种遮蔽策略、3 档遮蔽强度、5 个重复 seed 和 12 个规划器，共 1,080 次运行。seed 是同一案例的重复运行，不是独立攻击样本。

关键结果：

| 规划器 | 总体正确停止率 | 总体成功成本 | C04 正确停止率 | C04 成功成本 |
|---|---:|---:|---:|---:|
| Oracle optimal | 1.0000 | 1.4444 | 1.0000 | 2.8444 |
| CMI proxy | 1.0000 | 1.5333 | 1.0000 | 3.0222 |
| Project05 M1 | 0.9889 | 2.0112 | 0.9778 | 3.9545 |
| Coverage greedy | 1.0000 | 2.0667 | 1.0000 | 4.0444 |
| Random | 0.7778 | 2.1714 | 0.5556 | 6.0000 |

C04 在 60% 遮蔽下，M1 成功率降至 `0.9333`，而 CMI proxy 保持 `1.0000`。失败发生在 `random/0.6/seed37`：静态 expected-effect 评分先选择了实际恢复为零的 action，随后选择高成本重叠 action，预算耗尽时仍缺初始访问证据。

C05 的 full-evidence 正确停在 G2，全部运行均未越过 support ceiling；但多数状态初始已达到 G2，因此该案例更适合验证停止/降级逻辑，暂时不适合区分规划器优劣。

当前结论是负结果与工程验证并存：真实数据管线有效，但 CMI proxy 在这两个开发案例上暂时优于完整 M1。不得在 C04/C05 上调权后再用同一案例宣称改进，下一轮应在独立 E3/E5/OpTC 案例上评估动态冗余感知评分。
