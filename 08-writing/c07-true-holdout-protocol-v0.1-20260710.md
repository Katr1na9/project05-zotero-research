# C07 真留出协议 v0.1

日期：2026-07-10  
状态：协议锁定；**数据尚未接入**  
前置：`contribution-boundary-and-results-brief-v0.1.md`（M3a 主线已冻结）

## 1. 目的

为 M3a 主线提供**未参与方法设计与调参**的独立案例，使“节点级 action–gap 规划有效”从诊断性证据升级为可写进论文的留出证据。

## 2. 硬约束（什么不算 C07）

| 禁止 | 原因 |
|---|---|
| 再包装 C06 / R03（CADETS 2018-04-12） | 已用于 M2 失败诊断与 M3a 修复验证 |
| 在 C04/C05/C06 上事后调 M3a 权重再宣称改进 | 开发集污染 |
| 仅换 mask seed / 强度 | 不是新攻击 trace |
| 宣称“跨数据集泛化”仅凭 E3 内部另一天 | 最多算同家族内部留出，须在文中降级表述 |

## 3. 候选来源（按优先级）

### P0：DARPA TC Engagement 5（推荐）

- **优先 performer**：THEIA（Linux）或 ClearScope（Android）——与现有 E3 FiveDirections/CADETS **异构**，叙事上强于“E3 另一天”。
- **次选**：E5 CADETS（同 performer 不同 engagement，弱于 THEIA/ClearScope，但仍优于 R03）。
- 需要：官方 ground-truth 报告中的可锁定时间窗、可观察 IOC/进程、可定义的 `support_ceiling`。

### P1：DARPA OpTC

- 选一个公开红队活动日 / 主机子集，构造企业遥测风格证据链（process/logon/network/DNS）。
- 优点：场景更接近企业；缺点：体量大、编译成本高。

### P2（仅工程预演，不写最终 holdout）

- E3 内尚未用于规划器设计的其他 topic（若有）；文中必须标 `development_only` / `same_family`。

## 4. 案例编译清单（与 C04/C05 同构）

冻结目录：`09-experiments/real_cases/C07-<slug>/`

必有文件：

1. `case_config.json` — `target_granularity`、`support_ceiling`、`budget_total`、`channel_reliability`、`cti_nodes/edges`、mask 协议。
2. `evidence_claims.json` — 每条 claim 带回指（Event UUID / 主机遥测主键）；含 `hideable` 标签。
3. `acquisition_actions.json` — 显式 `intended_cti_node_ids`（来自取证请求语义，**禁止**从 `recoverable_claim_ids` 自动复制）；不可靠通道动作 + 至少一条可靠回退（若存在单通道关键节点）。

配套真实数据（Git 外）：

- `09-experiments/real_data/darpa_tc_e5/` 或 `.../optc/`：`manifest.json`、ground_truth、抽取摘要（沿用 E3 manifest 模式）。

## 5. 评估协议（公式冻结后）

1. **冻结**：`m3a_gap_compat_score` 权重、STOP 语义、通道先验表——C07 编译前不再改。
2. **对比规划器**：`oracle_optimal`、`project05_m3a_gap_compat`、`project05_m2`、`coverage_greedy`（可选 `project05_m1`）。
3. **M3b**：可不跑；若跑，仅作冻结对照，不调参。
4. **主指标**：success rate、mean cost to target、cost regret vs Oracle、zero-yield、`correct_stop` / `premature_stop`（若启用 STOP）。
5. **通过线（预登记）**：
   - M3a success ≥ M2 且 regret 不显著差于 Oracle 可行性；
   - 无 ceiling violation；
   - 信息边界测试仍通过（改 `recoverable_claim_ids` 不改变 M3a 选择）。
6. **失败也要写**：若 M3a 在真留出上崩塌，主线需回到表示/动作空间假设，而不是偷偷调权。

## 6. 本机现状与阻塞

| 项 | 状态 |
|---|---|
| E3 R01/R02/R03 原始窗 | 已有管线与摘要；R03=C06，不可作 C07 |
| E5 / OpTC 原始数据 | **未下载、未建 manifest** |
| M3a 公式 | 已冻结于 `run_mvp.py` |

**下一步工程动作（有数据后）**：

1. 选定 E5 ground-truth 中的单一攻击窗 → 写 `real_data/darpa_tc_e5/manifest.json` + `ground_truth/R04.json`（编号可调）。
2. 流式抽取 → motif 编译 → C07 三件套。
3. `python run_mvp.py` 指向 C07；结果写入 `results/c07_holdout_*`。
4. 更新本协议状态为 `evaluated`，并回写贡献边界简报第 4.2 节（删除“尚无真留出”）。

## 7. 临时可做、但不替代 C07 的工作

- 为现有 C01–C06 增加噪声/误导动作，测 M3a 鲁棒性（开发集，只写附录）。
- 专利 v0.3 权利要求按 M3a 骨架起草。
- `intended_cti_node_ids` 的离线 LLM 映射协议草案（标注规范，不进在线效用）。
