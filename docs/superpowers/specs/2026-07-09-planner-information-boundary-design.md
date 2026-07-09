# Planner Information Boundary Design

日期：2026-07-09

## 目标

修正当前 toy simulator 中普通规划器读取 `hidden_ids` 的 Oracle 信息泄漏，建立可审计的规划器信息边界，并在同一实验矩阵中加入 Oracle、CMI proxy 和 M1 消融。

## 信息边界

模拟器分为两个角色：

1. **Environment**：持有完整证据、隐藏证据和动作执行后的真实恢复结果。
2. **Planner**：只接收当前可见 `alignment_state` 与公开的动作元数据。

只有 `oracle_optimal` 可以读取 `hidden_ids`。`coverage_greedy`、`project05_m1`、`cmi_proxy` 和所有 M1 消融都不得根据真实隐藏集合计算动作分数。

动作执行仍由 Environment 使用 `recoverable_claim_ids ∩ hidden_ids` 决定真实恢复结果。

## 规划器

### Oracle

`oracle_optimal` 穷举预算内剩余动作组合及其真实恢复结果，选择达到目标粒度的最低成本路径。案例最多 8 个动作，精确搜索规模可控；该结果作为 cost regret 的下界。

### Coverage Greedy

仅使用动作声明的 `expected_coverage_delta / cost` 排序，不查看隐藏证据。

### Project05-M1

使用以下公开信息计算动作价值：

```text
expected_granularity_gain
+ expected_uncertainty_reduction
+ expected_over_attribution_risk_reduction
+ expected_conflict_resolution
+ expected_coverage_delta
- action_cost
```

当前状态用于门控权重：存在关键缺口时，提高覆盖和风险降低项的权重；预算不足的动作由动作掩码排除。

### CMI Proxy

当前三个案例都只有单一正向 campaign 假设，无法从样本估计真正的条件互信息。因此第一版仅实现：

```text
expected_uncertainty_reduction / cost
```

输出名称必须为 `cmi_proxy`，文档不得称其为真实 CMI。真实 CMI 需要在后续引入多候选假设、正负案例和动作结果分布后实现。

## M1 消融

在完整 M1 外增加：

- `m1_no_granularity`
- `m1_no_uncertainty`
- `m1_no_risk`
- `m1_no_coverage`
- `m1_no_cost`

每个变体只移除一个价值项，其他信息边界与动作空间保持一致。

## 实验设计

保持现有：

```text
case × mask strategy × mask intensity × seed
```

每个条件运行所有非 Oracle 与 Oracle 规划器。案例是独立实验单位；mask 和 seed 是案例内重复测量。

主要输出：

- 固定预算成功率
- 达标成本
- 达标步数
- 相对 Oracle 的 cost regret
- Oracle top-1 action hit
- 分案例与分 mask 条件结果
- M1 消融差值

## 结果边界

修正前的 M1/coverage 结果标记为工程调试结果，不用于方法有效性结论。修正后的三个手工案例仍只用于验证协议和代码；只有引入多个真实 attack trace 后，才能进行论文级统计推断。

## 验证要求

- 单元测试证明非 Oracle 规划器在改变 `hidden_ids`、保持公开状态不变时选择不变。
- 单元测试证明 Oracle 在真实恢复集合变化时可以改变选择。
- 所有案例 JSON 引用完整且符合 schema。
- 全矩阵可重复运行，并在结果中记录 planner 和 ablation 名称。
