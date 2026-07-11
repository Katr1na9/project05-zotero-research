# C07-C10 轻量非短视规划参数锁定协议 v0.1

日期：2026-07-11
状态：结果读取前冻结
规划器名称：`project05_depth2_public`

## 1. 研究问题

在 C07-C10 的公开状态-动作信息下，两步期望规划能否在不读取隐藏恢复结果的条件下，保持 M2 的目标达成率并降低成功条件取证成本？

本实验是非短视 Gate 的真实 trace 接入测试，不把受控环境中的 DP Oracle 直接移植为部署方法，也不启动 DQN。

## 2. 独立单位与重复测量

- 独立攻击案例：4，分别为 C07、C08、C09、C10。
- 每案例 45 个 mask/seed 条件，每规划器共 180 个 episode。
- mask、intensity 和 seed 是同一攻击案例的重复测量，不得写成 180 个独立样本。
- 参数在读取新规划器 C07-C10 结果之前冻结，不按结果调节。

## 3. 可见信息与禁用信息

规划器可读取：

- 当前 evidence-gap state 的覆盖摘要、剩余预算、已执行动作和反馈；
- 动作的 `intended_cti_node_ids`、`expected_stages`、`expected_evidence_types` 和 `expected_effects`；
- 动作成本、采集通道及 `case_config.channel_reliability` 公开先验。

规划器禁止读取：

- `recoverable_claim_ids`；
- 当前 hidden claim 集合；
- 当前 seed 下真实 channel up/down 实现；
- Oracle 最短路径、未来实际恢复结果或测试标签。

信息边界测试必须证明：仅修改候选动作的 `recoverable_claim_ids` 不得改变 `project05_depth2_public` 的选择。

## 4. 冻结规划公式

对候选第一步动作 (a)，M2 即时效用记为 (u(a,s))。对非 STOP 动作，使用公开通道可靠性 (r_q\in[0,1]) 构造两个代理状态：

- 成功分支：扣除成本、记录动作已执行，以公开 `expected_stages` 和 `expected_evidence_types` 更新覆盖摘要，并记录一次正收益反馈；
- 零收益分支：扣除成本、记录动作已执行，不更新覆盖摘要，并记录一次零收益反馈。

在两个代理状态中分别选择剩余预算内第二步 M2 最大效用 (V_2^+) 和 (V_2^0)。冻结两步评价为：

\[
Q_2(a,s)=u(a,s)+0.8\left[r_q V_2^+ +(1-r_q)V_2^0\right]-(1-r_q)c(a).
\]

STOP 的评价固定为 0，不展开第二步。若候选动作执行后无第二步可用，则相应 (V_2=0)。并列时依次按 STOP、低成本、动作 ID 进行确定性决胜。

超参数在结果前固定：深度 2、折扣系数 0.8、失败成本惩罚系数 1.0。它们来自“有限深度优先、成本显式计入”的设计约束，不依据 C07-C10 网格搜索。

## 5. 对照与指标

主要对照：M2 与 Oracle。辅助对照：冻结 XGBoost、Logistic、M3a 和 Coverage 的既有 C07-C10 结果。

指标：

- success rate；
- 成功条件 mean cost-to-target；
- regret vs Oracle；
- zero-yield；
- premature STOP；
- ceiling violation；
- Depth-2 与 M2 的逐条件 paired cost difference。

## 6. 预登记判据

只有同时满足以下条件，才写“轻量非短视规划改善了真实 trace 成本”：

1. C07-C10 聚合 success 不低于 M2；
2. ceiling violation 和 premature STOP 均不高于 M2；
3. 成功条件 mean cost 至少比 M2 低 0.10；
4. 四个案例中至少三个案例的 mean cost 不高于 M2；
5. paired cost 净胜条件数多于净负条件数。

若只保持成功但成本持平，结论为“真实案例未显示新增价值”；若成功下降或成本上升，结论为负结果。无论结果如何，均不回调本协议参数。

## 7. 产物

- 实现：`09-experiments/scripts/run_lightweight_nonmyopic_real.py`
- 测试：`09-experiments/tests/test_lightweight_nonmyopic_real.py`
- 输出：`09-experiments/results/nonmyopic_real_v0.1/`
- 结果报告：`08-writing/c07-c10-lightweight-nonmyopic-results-v0.1-20260711.md`
