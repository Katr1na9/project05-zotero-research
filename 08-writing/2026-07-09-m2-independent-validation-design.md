# M2 动态边际效用与独立验证设计

日期：2026-07-09

## 目标

针对首轮真实实验中 M1 选择零恢复 action 和高成本重叠 action 的缺陷，冻结一个不读取隐藏结果的动态边际效用规划器 M2，并使用独立的 DARPA E3 CADETS 2018-04-12 攻击案例 C06 验证。

## 数据边界

- C04/C05 是开发案例，只用于诊断 M1 缺陷和冻结 M2 公式。
- C06 是留出验证案例，不参与 M2 权重、阈值或规则调整。
- C06 结果产生前不得修改 M2 公式。
- C06 仍是同一 DARPA E3 数据族中的内部留出案例，不等同于跨数据集泛化验证。

## 规划器信息边界

M2 可以读取：

- 当前可见 evidence claim；
- stage coverage 与 evidence-type coverage；
- action 的公开类型、目标、成本、expected effects、expected evidence types 和 expected stages；
- 已执行 action 的公开反馈：恢复数量，不包含恢复前隐藏 claim 内容。

M2 不得读取：

- `hidden_ids`；
- action 的 `recoverable_claim_ids`；
- `oracle_effects`；
- ground-truth stage、实际 action outcome 或未来恢复内容。

只有 `oracle_optimal` 可以使用隐藏结果。

## Action 公开元数据

每个 action 增加 `expected_stages`，表示查询设计上可能补充的攻击阶段。该字段是先验查询语义，不是实际恢复结果。

Action signature 由以下公开字段组成：

- `action_type`；
- `target.target_type` 和 `target.target_value`；
- `expected_evidence_types`；
- `expected_stages`。

## 公开反馈

状态增加 `action_feedback`：

```json
[
  {
    "action_id": "C04-AA-002",
    "action_type": "recover_network_summary",
    "recovered_count": 0
  }
]
```

反馈仅在 action 执行后公开。它不暴露未恢复的 claim 身份。

## 冻结评分公式

对每个候选 action 计算：

- `granularity_gain`：公开 expected granularity gain；
- `uncertainty_reduction`：公开 expected uncertainty reduction；
- `risk_reduction`：公开 expected over-attribution risk reduction；
- `stage_gap`：action expected stages 的平均未覆盖比例；
- `evidence_gap`：action expected evidence types 的平均未覆盖比例；
- `overlap`：与已执行 action signature 的最大 Jaccard 重叠；
- `no_yield_risk`：同 action type 已执行且恢复数量为零的比例；
- `cost_ratio`：action cost / 当前剩余预算。

冻结分数：

```text
M2 =
  2.00 * granularity_gain
  + 1.50 * uncertainty_reduction
  + 1.50 * risk_reduction
  + 1.50 * stage_gap
  + 1.00 * evidence_gap
  - 1.50 * overlap
  - 1.00 * no_yield_risk
  - 0.75 * cost_ratio
```

并列时依次选择：

1. 成本较低；
2. expected stages 较多；
3. `action_id` 字典序较小。

## C06 留出案例

- 来源：`ta1-cadets-e3-official-2.json.tar.gz`
- 场景：2018-04-12 CADETS Nginx Backdoor with Drakon/Micro APT
- 宽上下文窗：2018-04-12 13:30-15:00 America/New_York
- UTC：2018-04-12T17:30:00Z 至 2018-04-12T19:00:00Z
- 攻击行为：Nginx 利用、payload 写入与执行、提权成败、Drakon/Micro APT C2、端口扫描。
- 目标粒度：`G3_campaign`
- 支持上限：`G3_campaign`

C06 motif 规则由真实 CDM 命中生成，但不得根据 M2 输出调整 action expected effects。

## 比较与指标

主要比较：

- M2；
- 冻结 M1；
- CMI proxy；
- coverage greedy；
- Oracle optimal。

指标：

- C06 正确达到 G3 的比例；
- 成功成本；
- 相对 Oracle 成本遗憾；
- 零恢复 action 数；
- 重叠 action 浪费成本；
- 首 action 与 Oracle 一致率；
- ceiling violation。

C04/C05 可以重跑用于机制诊断，但不能作为 M2 独立改进证据。

## 停止规则

- 如果 C06 上 M2 不优于 M1，保留负结果，不修改冻结公式。
- 如果 M2 优于 M1，只能表述为单一同族留出案例上的初步证据。
- 后续仍需 E5 或 OpTC 独立数据验证。

## 测试

- 改变 `hidden_ids` 时 M2 选择不变。
- 改变 `recoverable_claim_ids` 时 M2 选择不变。
- 零恢复反馈提高同类 action 的惩罚。
- 已执行 action 与候选 action 的公开 signature 重叠会降低分数。
- C06 full-evidence 达到 G3。
- 所有普通规划器保持零 ceiling violation，Oracle regret 非负。
