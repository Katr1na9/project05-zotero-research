# C11 OTRF APT29 Day 1 第三数据家族接入协议 v0.1

日期：2026-07-12  
状态：**事件读取前预注册**  
源案例：`R08`  
拟编译案例：`C11-otrf-apt29-day1-scranton-nashua`

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Origin Mode: plan
- Origin Date: 2026-07-12
- Verification Status: SOURCE-VERIFIED / EVENT-UNINSPECTED
- Version Label: code_plan_v1

## 1. Experiment Overview

- **Title**: OTRF APT29 Day 1 多通道证据接入与参数锁定评估
- **Objective**: 检验 Project05 的公开接口能否在第三种数据封装上编译跨通道 evidence claims，并在不读取隐藏恢复集合的条件下执行调查控制。
- **Hypothesis H1**: 至少 3 个预锁定关键节点可各恢复 2 条来自不同传感器家族的事件级 claim。
- **Hypothesis H2**: 冻结 M2 在 C11 上可执行且无信息边界或 ceiling violation；不预注册其成本优于其他策略。
- **Hypothesis H3**: AND corroboration 会比 OR 更严格；差异大小是待测结果，不预设方向或显著性。
- **Type**: ETL + deterministic evaluation

## 2. 研究边界

C11 是 APT29 行为仿真数据，不是真实世界中待识别的未知行为体。它用于测试：

- 第三数据家族接入；
- 多 claim 证据组合；
- 信息边界、STOP 与粒度截断；
- 冻结策略的跨封装可执行性。

它不用于证明 actor attribution accuracy，也不进入 M2、M3a、XGBoost、AFA 或 Depth-2 的训练、调权或模型选择。

## 3. 先验锁定

事件归档尚未打开时，依据 APT29 `day1` emulation plan 锁定：

- 主机：`SCRANTON`（主）、`NASHUA`（横向移动目标）。
- 场景：Day 1，步骤 `1.A-10.B`。
- 初始访问与 C2：`1.A-1.B`。
- 快速收集与外传：`2.A-2.B`。
- 隐蔽工具部署与 UAC 绕过：`3.A-3.C`。
- 横向移动：`8.A-8.C`。
- NASHUA 收集与外传：`9.A-9.C`。
- 持久化重触发：`10.A-10.B`，仅作非关键节点；若数据中不可观察，不得替换关键步骤。

源 README 的时间戳存在 `2020-04-29` 与 `2020-05-01` 两种记录。因此首轮使用 `2020-04-29T00:00:00Z` 至 `2020-05-03T00:00:00Z` 的保守分析包络；该包络不是攻击精确时间声明，也不得在看过事件后缩窗以提高命中率。

## 4. 多 claim 冻结规则

主分析使用全局 `node_coverage_semantics = AND`。关键节点必须在案例编译前分配至少两条 claim，并满足：

1. 两条 claim 来自不同传感器家族；
2. 至少一条为主机侧行为证据；
3. 至少一条为独立网络或第二 Windows provider 证据；
4. 同一事件的字段拆分、同一日志行的重复表述不得计为两条 claim。

预锁定关键节点：

| 节点 | 仿真步骤 | 主机侧证据家族 | 第二证据家族 |
|---|---|---|---|
| N01 initial breach + C2 | 1.A-1.B | Sysmon process / PowerShell | Zeek 或 Sysmon network |
| N02 collection + first exfil | 2.A-2.B | PowerShell + file activity | Zeek/C2 flow |
| N03 UAC bypass + HTTPS C2 | 3.A-3.C | registry + process activity | Zeek 或 Sysmon network |
| N04 lateral movement | 8.A-8.C | PowerShell/WinRM/PSExec process | Zeek SMB/DCE-RPC 或目标主机事件 |
| N05 NASHUA collection/exfil | 9.A-9.C | PowerShell + archive/file activity | Zeek/C2 flow |

若某节点只有一个可回查 claim，则该节点在 AND 主分析中保持不覆盖。允许另做 OR 敏感性分析，但 OR 结果不得替代 AND 主结果，也不得据此修改 claim 划分。

## 5. Inputs

| Input | 路径 | 说明 |
|---|---|---|
| Host events | `09-experiments/real_data/otrf_apt29/raw/apt29_evals_day1_manual.zip` | 固定提交中的 Day 1 主机归档 |
| Zeek log | `09-experiments/real_data/otrf_apt29/raw/combined_zeek.log` | Day 1 合并网络日志 |
| Emulation plan | `09-experiments/real_data/otrf_apt29/docs/apt29.xlsx` | 只用于先验步骤与可观察项锁定 |
| Ground truth slice | `09-experiments/real_data/otrf_apt29/ground_truth/R08.json` | 事件读取前冻结的场景边界 |

PCAP 不是首轮必需输入。仅当 Zeek 记录无法提供协议级回指、且补 PCAP 的决策在失败原因登记后作出时，才获取 SCRANTON/NASHUA PCAP；不得先看 PCAP 再改关键节点。

## 6. Expected Outputs

| Output | 路径 | Success Criterion |
|---|---|---|
| 封装检查 | `real_data/otrf_apt29/derived/R08_archive_inventory.json` | ZIP 可读、成员路径安全、文件类型和字节数完整记录 |
| 事件抽取摘要 | `real_data/otrf_apt29/derived/R08_extraction_summary.json` | 解析错误、事件总数、provider/host/time 范围可审计 |
| motif 编译报告 | `real_cases/C11-.../motif_report.json` | 每条 claim 有事件 ID/日志定位；缺失显式保留 |
| C11 配置 | `real_cases/C11-.../case_config.json` | AND 语义；冻结节点；不修改旧模型参数 |
| 冻结评估 | `results/c11_holdout_v0.1/` | 所有方法读取同一公开接口；信息边界测试通过 |

## 7. Gate 与停止规则

| Gate | 通过条件 | 失败处理 |
|---|---|---|
| D1 来源完整性 | 精确字节数与 SHA-256 登记，ZIP 可读 | 停止，不换镜像冒充同源文件 |
| D2 封装可解析 | 无路径穿越；JSON/JSONL 结构可枚举 | 记录不可用，不手工修造事件 |
| D3 多 claim 可识别 | 至少 3 个关键节点各有 2 个独立家族 claim | 报告 Gate 失败；可保留第三家族单 claim 附录，但不关闭多 claim 缺口 |
| D4 信息边界 | 规划器视图不含 `recoverable_claim_ids` 或未来实现 | 停止评估并修复接口 |
| D5 冻结评估 | M2/M3a/XGBoost/AFA/Depth-2 参数不变 | 任何改动产生新开发分支，C11 不再是 holdout |

## 8. Analysis Plan

- **主终点**：D3 多 claim Gate 是否通过，以及 AND 主分析下的内部 success、cost-to-target、premature STOP、ceiling violation。
- **敏感性**：同一冻结 claims 上比较 OR 与 AND；不得重编 claims。
- **对照**：M2 为透明部署锚点；Oracle 仅为评测下界。复杂策略是否胜出不作为数据接入成功标准。
- **统计单位**：C11 是 1 个独立仿真攻击链；mask/seed 是重复条件，不增加独立样本数。
- **负结果**：若 C11 不可编译、AND 不可达或冻结策略失败，均保留为外部效度结果，不换场景抢救。

## 9. LLM 与 Agent 边界

本协议不调用 LLM 或 agent。后续若使用 LLM 辅助 evidence claim 编译，必须在人工规则版本冻结后作为独立离线实验，并逐条验证事件回指；它不能改写 C11 的 ground truth、关键节点或主分析语义。

