# Project05 acquisition-cost experimental gate

状态：实验草案；不承载论文或专利表述，不允许进入正式结果。

本目录把原案例文件中的旧 `cost` 与新成本实验完全隔离。原始
`acquisition_actions.json` 和既有结果不改写；所有新成本通过外部 profile
注入，并由 `run_mvp.py` 记录 profile ID、版本和文件 SHA-256。

## 当前产物

`v0.1-draft-20260714/` 覆盖 C01-C12 共 72 个动作，包含：

- `action-cost-inventory.csv`：管理员审计表；保留旧成本和可用测量证据。
- `cost-rating-packet-A.csv`、`cost-rating-packet-B.csv`：独立评分包；顺序不同，
  不含旧成本、真实恢复集合、期望收益或 planner 结果。
- `measured-cost-collection-template.csv`：动作级运营测量模板。
- `rubric-cost-profile-v0.1-draft.json`：E/V/D/A/R 五分量草案；360 个值待真实评分。
- `measured-cost-profile-v0.1-draft.json`：连续实测成本草案；72 个值待测量与归一化。
- `build-manifest.json`：输入与输出 SHA-256、生成时间、随机种子和覆盖计数。

两个 profile 当前均为 `status=draft`、`formal_ready=false`。即使手工传给
运行器也会被拒绝；只有结构完整、动作覆盖精确且明确改为 `frozen` 的 profile
才能运行 rubric/measured 实验。

## 当前测量边界

| 事实 | 可用动作数 | 边界 |
|---|---:|---|
| 案例编译总扫描事件数 | 41/72 | 不是动作级扫描量，只能作背景证据 |
| 可恢复 claim 的命中记录数 | 40/72 | 是产出量，不是扫描成本 |
| 已观察证据时间跨度 | 40/72 | 不是日志保留期限 |
| 动作级扫描字节 | 0/72 | 待实测 |
| 日志保留期 | 0/72 | 待实测或取得来源策略记录 |
| 动作涉及主机数 | 0/72 | 待以实际查询范围记录 |

因此当前数据不足以自动给 D/V/A 打最终分，更不足以推断 E/R。缺失值保持
`null`，不得用动作类型均值、旧成本或 planner 表现回填。

## 旧成本漂移审计

| action type | 动作数 | 旧成本取值 |
|---|---:|---|
| `cti_report_lookup` | 1 | 3 |
| `extend_log_window` | 8 | 2, 3 |
| `human_review` | 8 | 2, 4, 5 |
| `ioc_enrichment` | 3 | 1, 3 |
| `malware_analysis` | 2 | 4 |
| `query_host_subgraph` | 26 | 2, 3, 4 |
| `recover_network_summary` | 13 | 2 |
| `ttp_local_probe` | 11 | 1, 2 |

这张表只证明旧规则存在同类动作漂移，不证明同类动作必须同价。后续评分必须用
动作级 E/V/D/A/R 证据区分“真实运营差异”和“无依据漂移”。

## 分支合并前必须敲定的实验决策

| ID | 待决问题 | 当前边界/可选方案 |
|---|---|---|
| COST-D01 | 正式范围 | C04-C12 为真实案例；C01-C03 是否只作校准/单测，还是进入稳健性矩阵 |
| COST-D02 | 成本带上限 | 标准草案写 `{1..4}`，但旧 C02/C03 `human_review=5`；需决定新 Arm B 为 1-4 还是 1-5 |
| COST-D03 | 分量权重 | 等权只是候选；必须在查看新 profile planner 结果前冻结，且不得据结果反调 |
| COST-D04 | 缩放与舍入 | `s`、上下界及 half-up/连续值方案待定；代码当前只为冻结 rubric 提供确定性 half-up 路径 |
| COST-D05 | 预算可比性 | A/B/C 使用相同绝对预算、归一化预算，或只比较完整 Pareto 前沿，需预先选择 |
| COST-D06 | 评分人员 | 两名独立评分者、培训/试标、排除规则、第三人裁决和解盲时点待定 |
| COST-D07 | D 的动作级测量 | 需记录 records/bytes scanned；案例编译总量不能替代动作扫描量 |
| COST-D08 | V 的测量 | 需取得 retention window 或采集时点压力证据；事件跨度不能替代保留期 |
| COST-D09 | A 的测量 | host 数、域/组织边界、提权/新授权、法务/外部服务如何映射到 0-3 待定 |
| COST-D10 | E/R 的证据 | 人时、工具步骤和系统扰动如何留痕；是否用演练/沙箱测量待定 |
| COST-D11 | Measured 归一化 | analyst time、machine time、bytes、授权和风险的单位、基准、重复数与合成公式待定 |
| COST-D12 | 成本—收益通约 | `lambda` 或效用换算、取值区间和敏感性网格待定 |
| COST-D13 | 稳健性矩阵 | 权重网格、整体缩放、噪声、相邻次序交换和随机种子待定 |
| COST-D14 | 统计单位 | 案例是独立单位；mask/intensity/seed 是配对重复，聚合和区间估计方案待定 |
| COST-D15 | 全策略接入 | `run_mvp.py` 已支持 profile；Logistic/XGBoost/AFA/Depth-2/预算曲线等专用 runner 需在正式重跑前统一接入 |
| COST-D16 | 冻结与重跑 | profile、输入哈希、命令、输出目录及 paired diff 规范敲定后，才触发 C07-C12 全策略矩阵 |

任何一项若影响 planner-visible cost、预算或训练特征，都必须在合并后统一重跑，
不得只运行受益策略或选择性案例。

## 复现命令

生成新草案时必须使用新的空目录：

```powershell
python .\09-experiments\scripts\build_cost_profile_drafts.py `
  --output-dir .\09-experiments\cost_profiles\<new-draft-dir> `
  --created-utc <ISO-8601-UTC>
```

结构和覆盖校验：

```powershell
python .\09-experiments\scripts\validate_cost_profile.py `
  .\09-experiments\cost_profiles\<dir>\rubric-cost-profile.json
```

正式 Gate（草案应失败）：

```powershell
python .\09-experiments\scripts\validate_cost_profile.py `
  .\09-experiments\cost_profiles\<dir>\rubric-cost-profile.json `
  --require-frozen
```

只有 Gate 通过后，才可在新的空结果目录执行：

```powershell
python .\09-experiments\scripts\run_mvp.py `
  --examples-dir <case-root> `
  --cost-regime rubric `
  --cost-profile <frozen-profile.json> `
  --output-dir <new-empty-result-dir>
```
