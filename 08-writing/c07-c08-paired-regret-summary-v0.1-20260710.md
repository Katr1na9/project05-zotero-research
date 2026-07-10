# C07 + C08 + C09 paired regret 汇总（冻结 M3a）

日期：2026-07-10  
状态：三条真留出均已冻结评估。  
约束：未改 `m3a_gap_compat_score` / STOP / 通道先验。

## 1. 设定

| 项 | C07 | C08 | C09 |
|---|---|---|---|
| 来源 | E5 THEIA (Linux) | E5 ClearScope (Android) | OpTC eCAR (Windows) |
| 案例 | `C07-darpa-e5-theia-0515` | `C08-darpa-e5-clearscope-0515` | `C09-darpa-optc-sysclient0201-0923` |
| 条件数/planner | 45 | 45 | 45 |
| 产物 | `results/c07_holdout_m3a/` | `results/c08_holdout_m3a/` | `results/c09_holdout_m3a/` |

## 2. 主表（success / mean cost / regret vs Oracle）

| Planner | C07 success | C07 cost | C07 regret | C08 success | C08 cost | C08 regret | C09 success | C09 cost | C09 regret |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Oracle | 1.0000 | 3.6444 | 0.0000 | 1.0000 | 3.8889 | 0.0000 | 1.0000 | 4.1333 | 0.0000 |
| M2 | 1.0000 | 4.3111 | 0.6667 | 1.0000 | 4.5111 | 0.6222 | 1.0000 | 4.7556 | 0.6222 |
| M3a | 1.0000 | 4.9333 | 1.2889 | 1.0000 | 5.0444 | 1.1556 | 1.0000 | 5.2444 | 1.1111 |

## 3. 配对结论

1. **三源同向**：M3a 与 M2 均满 success、无 ceiling violation；M3a 平均成本均高于 M2。  
2. **可写**：冻结管线在跨 engagement 家族（E5 Linux / E5 Android / OpTC Windows）上可复现。  
3. **不可写**：M3a 成本优于 M2。  
4. `mean(M3a_regret - M2_regret)` across {C07,C08,C09} = `(0.6222 + 0.5333 + 0.4889) / 3 = 0.5481`（符号全为正）。

## 4. 禁止事后改

不得因 C09 结果回头调 `m3a_gap_compat_score`、STOP 语义或通道先验表。
