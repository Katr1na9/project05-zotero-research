# C08 E5 ClearScope 第二真留出结果

日期：2026-07-10  
案例：`C08-darpa-e5-clearscope-0515`  
协议：M3a 权重、STOP 语义和通道先验均在 C07/C08 编译前冻结；本案例未改公式。

## 1. 实验设计

- 真实来源：DARPA TC E5 ClearScope R05，2019-05-15 Appstarter Micro APT Elevate trace（Android）。
- 条件：3 种 mask 策略 × 3 个强度 × 5 个 seed = 每个规划器 45 次运行。
- 对比：`oracle_optimal`、`project05_m2`、`project05_m3a_gap_compat`，以及既有基线/消融。
- C08 是第二真留出（相对 C07 THEIA 的异构 performer），不参与 M3a 调参。

## 2. 主结果

| 规划器 | Success | 平均到达目标成本 | 平均 regret vs Oracle | Ceiling violation |
|---|---:|---:|---:|---:|
| Oracle | 45/45 | 3.8889 | 0.0000 | 0 |
| M2 | 45/45 | 4.5111 | 0.6222 | 0 |
| M3a | 45/45 | 5.0444 | 1.1556 | 0 |

M3a 的 success 与 M2 持平，且没有越过 `G3_campaign` 支持上限。M3a 的平均代价高于 M2（+0.5333），regret 也更大。与 C07 同向：**支持跨 engagement / 异构 performer 管线可复现，不支持 M3a 成本优于 M2**。

## 3. 回退与噪声行为

| 项 | M2 | M3a |
|---|---:|---:|
| 选择廉价网络动作 `C08-AA-001` | 26 次 | 36 次 |
| 选择可靠主机回退 `C08-AA-002` | 21 次 | 15 次 |
| 选择良性 `sl` 驱动审查 `C08-AA-005` | 0 次 | 0 次 |

M3a 未把良性 elevate-driver setup 当作攻击链缺口；较常先试低成本网络通道，叠加过宽意图后成本高于 M2。

## 4. 自然缺失（显式保留）

- 报告 C2 `77.138.117.150:80`：PGDMP netflow 远端地址被 scrub 为 `0`，未合成 IP claim。
- `calllog.db` / `calendar.db` / `mmssms.db`：窗口内无对应文件节点。
- `screencap` claim 的墙钟时间早于 `msm_g711tlaw` elevate，对应报告中提权前失败截屏；图结构为 C2→elevate 与 C2→screencap 分叉，而非 elevate→collection。

## 5. 结论与限制

C08 完成第二真留出：Android ClearScope、事件级可回查、自然缺失保留、intended≠OR、信息边界测试通过。与 C07 一起构成“冻结 M3a 在两条异构 E5 holdout 上可跑通、但成本不优于 M2”的配对证据。下一步若要第三留出，优先 OpTC，且仍不得回头调 M3a。

## 6. 文件

- `c08-darpa-e5-clearscope-0515_mvp_results.csv`
- `c08-darpa-e5-clearscope-0515_mvp_summary.json`
- traces JSON 本地生成、已 gitignore
