# C12 生产 SOC 衍生运营数据接入与冻结结果 v0.1

日期：2026-07-13

状态：元数据 Gate、事件源 Gate、case 编译和首次冻结 MVP 评估已完成；仅作为独立 G1 外部压力候选，不并入 C07-C10 或 C11 均值。

## 1. 数据来源与目标

C12 来自 [WitFoo Precinct6 Cybersecurity Dataset](https://huggingface.co/datasets/witfoo/precinct6-cybersecurity)，固定 revision：

`1c0be6c03713af68eb9badc404297a63546bf2b4`

该数据集包含经清洗的生产 SOC 事件和 13,119 个 incident。数据卡明确说明：所有标签均来自 Precinct 自动相关；`Disrupted` / `Resolved` 可作为分析师确认筛选，但不存在独立 actor-attribution ground truth。

C12 的目的不是增加一个“APT actor 正确分类”案例，而是检验：面对生产 SOC 衍生数据、极不均衡通道和厂商相关图投影时，现有调查控制流程能否保持信息边界并正确把结论限制在 G1。

## 2. 两级筛选

### 元数据 Gate

冻结输入：`graph/attack_reports.jsonl`，13,119 条，SHA-256：

`DC6946F50B62E6B3DFC9400EB28F388B374D7DCADA0C436C283AB719A0DE2866`

纳入条件：

- `disposition ∈ {Disrupted, Resolved}`；
- `disposition_category = confirmed-malicious`；
- 至少两个归一化产品家族和两个传感通道；
- 至少 5 个节点、5 条边；
- ATT&CK 映射和模板报告文本不参与纳入或排序。

最终 5/13,119 条通过元数据 Gate。源文件哈希、记录数和 11 个产品标签映射全部通过。

### 事件源 Gate

对前 5 条下载 GraphML，并从 `graph/incidents.jsonl` 的 embedded leads 回取原始清洗事件。事件 Gate 额外要求：

- 至少两个独立原始 stream 通道；
- 产品标签与 stream 通道至少在两个通道上对应；
- 每个 lead 具有 artifact、details、observed_at、node_id 和 product 指针；
- lead 数量与元数据一致。

结果：2/5 条通过。另 3 条虽有 Umbrella/Stealthwatch 产品标签，实际 lead 全来自 `meraki` stream，已判为“标签多源、事件单源”并剔除。

## 3. 主候选与证据边界

主候选：`f10c7270-1228-11ed-99ed-adca11e4059c`，源记录序号 11,888。

| 项目 | 结果 |
|---|---:|
| 分析师状态 | `Disrupted` |
| leads | 119 |
| ASA Firewall | 117 |
| Windows Active Directory | 2 |
| 去重清洗详情 | 93 |
| GraphML 节点/边 | 22 / 49 |
| GraphML 原始遥测边 | 0 |
| GraphML 边类型 | 49 × `INCIDENT_LINK` |

全部 GraphML 边都是厂商相关投影。因此：

- GraphML 只能形成一条 `context` claim；
- 原始可恢复证据必须来自 embedded leads；
- 厂商 `Data Theft`、ATT&CK 映射和 suspicion score 不进入 gold claims；
- `actors` 为空，不存在 actor/campaign 正确性终点；
- structured artifact 与 embedded message 的清洗实体存在不一致，不做跨表示实体拼接；
- vendor `observed_at` 与日志内时钟不一致，不建立跨通道因果顺序。

## 4. C12 case contract

目录：`../09-experiments/real_cases/C12-witfoo-precinct6-f10c7270/`

编译结果：

- 5 条 claims：2 条网络观察、2 条 Windows 4672 观察、1 条厂商相关上下文；
- 4 个动作：ASA 汇总、ASA 定向观察、Windows Security 查询、Precinct 投影审查；
- 每个动作均满足 `intended_cti_node_ids != OR(recoverable_claim_ids)`；
- `N04_actor_campaign_attribution` 保持空 required claims 的自然缺口；
- target 与 support ceiling 均为 `G1_technique`；
- 所有 gold claims 的 `mapped_tactic` / `mapped_technique` 均为空。

这里的 G1 表示“行为/技术层调查结论上限”，不表示已验证 ATT&CK technique ID。

## 5. 首次冻结评估

统计单位：1 个 incident × 3 个 mask 策略 × 3 个强度 × 5 个 seed = 45 个重复条件。45 不是独立攻击数量。

| 策略 | success | correct STOP | mean cost to target |
|---|---:|---:|---:|
| Random | 0.8667 | 0.8667 | 0.8462（仅成功条件） |
| Fixed order | 1.0000 | 1.0000 | 0.9778 |
| Coverage greedy | 1.0000 | 1.0000 | 0.9778 |
| CMI proxy | 1.0000 | 1.0000 | 0.9778 |
| M1 | 1.0000 | 1.0000 | 1.5111 |
| M2 | 1.0000 | 1.0000 | 1.4222 |
| M3a | 1.0000 | 1.0000 | 0.9778 |
| Oracle | 1.0000 | 1.0000 | 0.8889 |

解释：

1. G1 上限使确定性策略都能达到内部目标，C12 不提供“更高成功率”的算法胜场；
2. M2 比 Coverage/CMI/M3a 多 `0.4444` 平均成本，再次否定“一个透明规则在所有案例全局最优”；
3. full-evidence node coverage 为 0.75，但结论仍被 support ceiling 截断在 G1；
4. 该结果支持“正确降级与信息边界可迁移”，不支持 actor/campaign 归因能力。

## 6. 写作决定

### 冻结扩展策略迁移

在不改 C12 case、mask、seed、预算和既有模型参数的条件下，补齐冻结策略族：

| 策略 | success | mean cost | 相对 M2 配对差值 |
|---|---:|---:|---:|
| Oracle | 1.0000 | 0.8889 | -0.5333 |
| Depth-2 Public | 1.0000 | 0.8889 | -0.5333 |
| AFA Rollout-H3 | 1.0000 | 0.9778 | -0.4444 |
| XGBoost | 1.0000 | 0.9778 | -0.4444 |
| Logistic | 1.0000 | 0.9778 | -0.4444 |
| M2 | 1.0000 | 1.4222 | 0 |
| AFA Myopic | 1.0000 | 1.5111 | +0.0889 |

XGBoost 仍只由 C01-C06 的 1,845 rows 训练；三个模型 SHA-256 与 C07-C10 冻结评估完全一致。Depth-2 在 12/45 条件成本更低、33 条持平，未发生 success repair 或 regression。

这个结果说明：非短视在该单 incident 的低粒度目标上能够消除 M2 的额外成本，但不能外推为真实运营中普遍需要非短视规划；同一 C12 内 AFA Myopic 又比 M2 更贵，进一步证明不能按方法家族整体下结论。

C12 可以作为论文补充外部效度案例，表述为：

> 一个来自生产 SOC 的多 stream、分析师已处置 incident，用于验证事件源回指、信息边界和 G1 粒度截断。

不得表述为：

- 新的独立 APT actor benchmark；
- 45 个真实攻击；
- 自然发生攻击链的完整因果重建；
- M2 或任一学习器在真实运营中的普遍性能结论；
- 厂商 ATT&CK/`Data Theft` 标签的独立验证。

在修改论文母本前，应先决定 C12 放正文外部效度小节还是附录，并保持与 C11、C07-C10 分表。
