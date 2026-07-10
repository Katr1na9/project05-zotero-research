# C07 E5 THEIA 真留出结果

日期：2026-07-10（含 intended≠OR 合规重标后重跑）  
案例：`C07-darpa-e5-theia-0515`  
协议：M3a 权重、STOP 语义和通道先验均在 C07 编译前冻结；本轮仅按标注规范修正公开 `intended_cti_node_ids`（过宽意图），未改公式权重。

## 1. 实验设计

- 真实来源：DARPA TC E5 THEIA R04，2019-05-15 Firefox Drakon BinFmt-Elevate trace。
- 条件：3 种 mask 策略 × 3 个强度 × 5 个 seed = 每个规划器 45 次运行。
- 对比：`oracle_optimal`、`project05_m2`、`project05_m3a_gap_compat`，以及既有基线/消融。
- C07 是单一真留出，不参与 M3a 公式、动作权重或通道先验调参。

## 2. 主结果（intended≠OR 合规后）

| 规划器 | Success | 平均到达目标成本 | 平均 regret vs Oracle | Ceiling violation |
|---|---:|---:|---:|---:|
| Oracle | 45/45 | 3.6444 | 0.0000 | 0 |
| M2 | 45/45 | 4.3111 | 0.6667 | 0 |
| M3a | 45/45 | 4.9333 | 1.2889 | 0 |

M3a 的 success 与 M2 持平，且没有越过 `G3_campaign` 支持上限。M3a 的平均代价高于 M2（+0.6222），regret 也更大。本案例支持“冻结流程在真实留出上可行”，**不支持**“M3a 在成本上优于 M2”。

相对合规前快照（M3a cost 4.3556 / regret 0.7111），过宽意图使 M3a 更常追逐未恢复的邻接缺口，成本上升——这是信息边界收紧后的预期副作用，不是调参胜利。

## 3. 回退与噪声行为

| 项 | M2 | M3a |
|---|---:|---:|
| 选择廉价网络动作 `C07-AA-001` | 25 次 | 35 次 |
| 选择可靠主机回退 `C07-AA-002` | 22 次 | 16 次 |
| 网络通道离线条件数 / 其中使用回退 | 18 / 16 | 18 / 16 |
| 选择良性驱动审查 `C07-AA-005` | 0 次 | 0 次 |

M3a 未把良性驱动活动当作攻击链缺口；网络通道失效时，当前预算允许其转向可靠主机取证。M3a 较常先试低成本网络通道，叠加过宽意图后成本进一步升高。

## 4. 结论与限制

本结果完成了 C07 真留出这一关键缺口：事件级来源可回查、自然缺失显式保留、信息边界测试通过、`intended≠OR(recoverable)` 合规、规划器不因网络故障而提前停止。

但它仍是一个 E5 THEIA trace。下一步是接入 OpTC 或 E5 第二异构 performer，在不调整 M3a 参数的前提下做第二独立留出，并对 M3a/M2 的 paired regret 做汇总评估。

## 5. 文件

- `c07-darpa-e5-theia-0515_mvp_results.csv`
- `c07-darpa-e5-theia-0515_mvp_summary.json`
- traces JSON 本地生成、已 gitignore
