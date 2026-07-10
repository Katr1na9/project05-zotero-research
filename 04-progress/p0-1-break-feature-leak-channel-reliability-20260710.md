# P0-#1 纠错：打破特征泄题 + 采集通道可靠性（预登记）

日期：2026-07-10
状态：机制与数据已落地；`unittest` 63/63 通过；`results/` 已于同日重跑刷新。

## 1. 问题（被纠正的"偷工减料"）

代码审查发现：所有案例（C01–C06）里，每个 `acquisition_action` 的公开字段 `intended_cti_node_ids`
（"这个动作声称要解决哪些 CTI 节点"）在 OR 覆盖语义下**恰好等于**该动作 `recoverable_claim_ids`
实际能覆盖的节点集合。

后果：

- `m3a_gap_compat_score` 的核心项 `intended ∩ unmatched` 直接读到了"真实待恢复节点"，使 M3a 近似 Oracle 等价。
- M3b 最强特征 `intended_critical_gap_overlap_count` 同样是答案键的函数，模型无需学习即可"命中"。
- schema 里 `intended_cti_node_ids` 的说明写着 "must not encode hidden claim outcomes"，但数据实际违反了它。

即：declared（声称）== actual（实际），没有给学习型策略（M3b / M3b-3 / M4）留下任何真实的可学习空间。

## 2. 纠错思路：declared ≠ actual，差距来自"通道可靠性"

保留 `intended_cti_node_ids` 作为**公开的、可以是错的声称目标**；实际恢复由隐藏的
`recoverable_claim_ids` 决定，并额外受**采集通道是否在线**的门控。这样：

- 一个动作可以"声称"指向某关键节点，但因其采集通道本 episode 离线而**零收益**（declared ≠ actual）。
- 声称目标不再是完美预测器 → M3a 的规则退化为一个会踩坑的朴素基线。
- 通道可靠性可从**历史反馈**推断：静态 M3b 用通道先验、自适应 M3b（M3b-3）用 Beta 后验 —— 这正是项目原定主线，纠错与主线合流。

### 术语固定

- declared target：`intended_cti_node_ids`，公开，规划器可见，允许不准。
- actual recovery：`realized_recovery = recoverable_hidden ∩ (通道在线 ? 全部 : ∅)`，环境真值。
- channel：采集通道 / 数据源。公开字段 `acquisition_channel`，缺省由 `action_type` 派生。

## 3. 预登记：通道映射与可靠性档案（先冻结，后重跑）

动作类型 → 通道映射（`run_mvp.ACTION_TYPE_CHANNELS`）：

| action_type | channel |
| --- | --- |
| extend_log_window | log_retention |
| query_host_subgraph | host_forensics |
| recover_network_summary | network_telemetry |
| ioc_enrichment / infrastructure_history / cti_report_lookup | threat_intel |
| malware_analysis | sample_lab |
| ttp_local_probe | host_probe |
| human_review | analyst |
| other | other |

可靠性档案（写入各 `case_config.json` 的 `channel_reliability`，此处预登记，重跑前不得再调）：

- `network_telemetry`：0.5
- 其余所有通道：1.0（缺省）

选 `network_telemetry` 作为不可靠通道，因为 `recover_network_summary` 动作在多数案例中**便宜且覆盖多个关键节点**，
是 M3a 最容易被诱导选中的动作 —— 让它成为"诱人但不可靠"的陷阱，才能真正区分朴素规则与学习/自适应策略。

### 通道在线的确定性抽样

`channel_is_up(config, channel, seed)`：`p≥1→恒真`，`p≤0→恒假`，否则
`sha256(case_id|channel|seed)` 的前 64 位归一化后与 p 比较。同一 (case, channel, seed) 稳定、跨平台一致、可复现，
且 Oracle 与所有规划器在同一 episode 观测到**相同**的通道状态。

## 4. 可解性保障：给单通道关键节点补可靠回退动作

以下关键节点原本**只能**经 network 恢复，若 network 离线会永久不可解：C04 `N02_c2`(EC-003)、
C05 `N03_c2`(EC-006/008)、C02 `N06_exfil`(EC-009)。为它们各补一个更贵的可靠通道回退动作：

| 新动作 | 通道 | 恢复 | 成本 | 说明 |
| --- | --- | --- | --- | --- |
| C02-AA-007 | host_forensics | C02-EC-009 | 3 | 比便宜的 network 动作(C02-AA-003, cost 2)贵，但不受 network 离线影响 |
| C04-AA-006 | threat_intel | C04-EC-003 | 3 | 同上（对照 C04-AA-002, cost 2） |
| C05-AA-006 | threat_intel | C05-EC-006/008 | 3 | 同上（对照 C05-AA-003, cost 2） |

回退动作已加入对应 `fixed_action_order`。它们比便宜的 network 动作贵，因此 network 仍是 M3a 的诱人首选；
network 离线时才需绕道更贵的可靠路径 —— 这就是 M3a 退化、学习/自适应策略应胜出的场景。

C01/C03/C06 的关键节点本就有可靠通道替代路径（host/log/ioc），无需新增动作。

## 5. 代码改动

- `scripts/run_mvp.py`
  - 新增 `ACTION_TYPE_CHANNELS`、`acquisition_channel`、`channel_reliability`、`channel_is_up`、`realized_recovery`。
  - `run_episode`：动作实际恢复改为受通道门控；trace 事件记录 `acquisition_channel` 与 `channel_up`（反馈字典结构保持不变）。
  - `select_oracle_optimal_action`：新增 `seed` 参数，搜索与回退分支均按通道门控（Oracle 仍是"给定已实现通道状态下的最优"）。
- `scripts/run_m3b.py`
  - `counterfactual_labels` 新增 `seed`，标签改用 `realized_recovery`（反映通道门控）。
  - `feature_row` 新增公开特征 `channel_prior_reliability`（= 该通道预登记可靠性），并加入 `FEATURE_COLUMNS`。
- `data_schema/acquisition_action.schema.json`
  - 新增可选字段 `acquisition_channel`；重写 `intended_cti_node_ids` 说明为"声称目标，可与实际恢复背离，非答案键"。
- 6 个 `case_config.json` 均新增 `channel_reliability`；C02/C04/C05 各加一个可靠回退动作与 `fixed_action_order` 更新。

向后兼容：任何未声明 `channel_reliability` 的 config（含全部单元测试里手搓的最小 config）通道可靠性=1.0，
`realized_recovery == recoverable_hidden`，行为与纠错前完全一致。

## 6. 不变量与守卫测试

`tests/test_channel_reliability.py`：

- 通道原语：派生/覆盖、缺省可靠性=1.0、`channel_is_up` 确定性且尊重 0/1 极值、0.5 通道在多 seed 上取到两种结果。
- declared≠actual：C01 的 network 动作在离线 seed 下声称非空但实际恢复为空；对应 counterfactual 标签随通道结果翻转；`channel_prior_reliability` 进入特征。
- Oracle 不变量（对全部 6 案例跑 `execute_case`）：
  1. `regret ≥ 0`（Oracle 仍是成本下界）。
  2. 任一非 Oracle 规划器达标 ⇒ Oracle 在该条件下必达标（Oracle 是可行性上界）。
  3. Oracle 至少在部分条件达标（排除整案不可解的退化）。

注意：**不**断言 Oracle 在所有条件达标。通道离线 + 高遮蔽时，可靠路径可能超预算 → 该 episode 对所有人（含 Oracle）都不可解。
这是有意为之，且正是"识别不可解、正确停止/降级"论线要评估的能力，由既有 `correct_stop` / `ceiling_violation` 指标承接。

## 7. 重跑结论（2026-07-10）

1. `python -m unittest discover -s 09-experiments/tests`：63/63 通过。
2. 已重跑并刷新：`c01_mvp_*`、`all_cases_*`、`m3a_toy_cases/`、`m3a_real_cases/`、`c06_holdout_*`、`real_e3_*`、`m3b_toy_train_real_test/`、`m3b_policy_toy_train_real_test/`、`m3b_reliability_toy_train_real_test/`。
3. 现象复核：
   - **符合预期**：toy 矩阵上 Oracle 成功率降至 `0.9778`（通道离线导致部分 episode 不可解）；M3a mean regret vs Oracle 升至 `0.2558`，不再近似等价。
   - **符合预期**：logistic 权重中 `channel_prior_reliability` 为第二强特征（`+1.017`），仅次于 `intended_critical_gap_overlap_count`（`+1.643`）——模型确实学到了“偏好可靠通道”。
   - **部分符合**：真实案例正常回放上静态 M3b 成功率 `0.9852` 略高于 M3a `0.9778`，但达标成本略高（`1.92` vs `1.77`）；尚未形成清晰的成本优势。
   - **负结果保留**：同质 twin 诱饵压力下，自适应 M3b（`0.5778`）仍差于静态 M3b（`0.6519`）与 M3a（`0.8370`）——公开可区分的失败模式仍不足，M4（动态可靠性 + 停止/降级）仍是下一主线。
