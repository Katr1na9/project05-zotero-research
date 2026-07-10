# C09 OpTC 第三真留出结果

日期：2026-07-10  
案例：`C09-darpa-optc-sysclient0201-0923`  
协议：M3a 权重、STOP 语义和通道先验均在 C07/C08/C09 编译前冻结；本案例未改公式。

## 1. 实验设计

- 真实来源：DARPA OpTC Day1 Plain PowerShell Empire，SysClient0201，2019-09-23 本地 11:23–15:30（UTC `15:23Z`–`19:30Z`）。
- 原始分片：官方 Drive `ecar/evaluation/23Sep19-red/AIA-201-225/AIA-201-225.ecar-last.json.gz`（SHA-256 `FAF181CB…`）；窗口抽取 753,973 / 34,146,068 行。
- 条件：3 种 mask 策略 × 3 个强度 × 5 个 seed = 每个规划器 45 次运行。
- 对比：`oracle_optimal`、`project05_m2`、`project05_m3a_gap_compat`，以及既有基线/消融。
- C09 是第三真留出（相对 C07/C08 的独立 engagement 家族：企业 Windows eCAR），不参与 M3a 调参。

## 2. 主结果

| 规划器 | Success | 平均到达目标成本 | 平均 regret vs Oracle | Ceiling violation |
|---|---:|---:|---:|---:|
| Oracle | 45/45 | 4.1333 | 0.0000 | 0 |
| M2 | 45/45 | 4.7556 | 0.6222 | 0 |
| M3a | 45/45 | 5.2444 | 1.1111 | 0 |

M3a 的 success 与 M2 持平，且没有越过 `G3_campaign` 支持上限。M3a 的平均代价高于 M2（+0.4889），regret 也更大。与 C07/C08 **同向**：**支持跨 engagement 家族管线可复现，不支持 M3a 成本优于 M2**。

## 3. 回退与噪声行为

| 项 | M2 | M3a |
|---|---:|---:|
| 选择廉价网络动作 `C09-AA-001` | 35 | 35 |
| 选择可靠主机回退 `C09-AA-002` | 14 | 14 |
| 选择截屏取证 `C09-AA-004` | 16 | 27 |
| 选择良性 GoogleUpdate 审查 `C09-AA-006` | 0 | 0 |

M3a 未把良性 Google Update 活动当成攻击链缺口；较常先取截屏动作，叠加过宽意图后成本高于 M2。

## 4. 自然缺失（显式保留）

- Mimikatz / `zleazer` 明文口令：窗口内无 `mimikatz`/`sekurlsa` 字符串，未合成 credential claim。
- `news.com` 主机名：C2 claim 以 IP `132.197.158.98:80` 为据。
- 失败的 LSASS 注入：未编造成功注入 claim。
- SysClient0402/0660/DC1 本机链：仅用主主机窗口内的 WMI 引用 claim。

## 5. 事件级可回查 claim

| Claim | Motif | 匹配数 | 首事件 UTC |
|---|---|---:|---|
| C09-EC-001 | powershell → `132.197.158.98:80` | 3762 | 15:24:02Z |
| C09-EC-002 | `Environment\windir` REGISTRY ADD | 1 | 15:25:48Z |
| C09-EC-003 | `Get-Screenshot` SHELL | 1 | 16:51:54Z |
| C09-EC-004 | `SYSCLIENT0402` WMI SHELL | 4 | 17:19:42Z |
| C09-EC-005 | `GoogleUpdate.exe` CREATE（噪声） | 16 | 15:35:00Z |

## 6. 结论与限制

C09 完成第三真留出：企业 Windows eCAR、事件级可回查、自然缺失保留、intended≠OR、信息边界测试通过。与 C07+C08 一起构成“冻结 M3a 在三条异构 holdout 上可跑通、但成本不优于 M2”的配对证据。**禁止**据此回头调 M3a。

## 7. 文件

- `c09-darpa-optc-sysclient0201-0923_mvp_results.csv`
- `c09-darpa-optc-sysclient0201-0923_mvp_summary.json`
- traces JSON 本地生成、已 gitignore
