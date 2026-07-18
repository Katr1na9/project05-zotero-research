# DARPA E3 行为基元实验设计

日期：2026-07-09

## 目标

把已抽取的 R01/R02 DARPA TC E3 事件和节点转换为 Project05 可运行的真实案例，执行 M1、CMI、Oracle 与基线规划器对比。首轮只验证真实证据上的粒度判定、证据恢复成本和停止行为，不引入 LLM、Agent 或多模态分支。

## 实验单位与成功标准

- 独立实验单位是一个攻击案例和一次证据遮蔽条件，不把同一案例的不同随机种子当作独立真实样本。
- R01 是完整链案例，目标是以较低取证成本恢复到 `G3_campaign`。
- R02 是天然不完整案例，正确结果是停在 `G2_tactic_intent`，不得通过不存在的持久化、收集或外传证据强行提升到 G3。
- R01/R02 仅作为开发案例，不用于最终泛化结论。

## 行为基元

每条 `evidence_claim` 表示一个可解释的行为关系，例如：

- 进程执行或加载对象；
- 进程写入、读取或修改文件；
- 进程连接远端 IP；
- 攻击链中的失败行为或数据源未观测状态。

行为基元由确定性规则从 CDM Event/Node 中聚合。每条 claim 必须保存匹配事件数量、首末时间和代表性 Event UUID，能够回指原始事件。数百万条原始 Event 不直接进入模拟器。

## 三层信息边界

1. **案例构建层**：允许依据 DARPA ground truth 定义待验证行为基元和 gold stage，但必须记录哪些规则来自 ground truth。
2. **可见证据层**：只包含当前遮蔽条件下可见的真实 CDM claim。
3. **规划器层**：只能读取可见 claim、action 元数据和当前 alignment state；不得读取隐藏 claim 的实际内容、ground truth 标签或 oracle outcome。

Oracle 可以读取隐藏结果，但只作为成本下界。

## 数据流

```text
events.jsonl + nodes.jsonl
  -> case-specific motif specification
  -> deterministic motif compiler
  -> evidence_claims.json + motif audit report
  -> acquisition_actions.json + case_config.json
  -> mask matrix
  -> M1 / CMI / Oracle / greedy / random
  -> R01 reach-G3 metrics + R02 correct-stop metrics
```

## Acquisition Action

Action 表示可执行查询，而不是任意恢复标签：

- `query_host_subgraph`：围绕进程或文件恢复 provenance 行为；
- `recover_network_summary`：恢复指定端点的 NetFlow 行为；
- `extend_log_window`：恢复当前窄窗之外、宽上下文窗以内的行为；
- `ttp_local_probe`：查询某类本地行为是否存在；
- `human_review`：核验冲突或数据源缺失，不生成虚构正证据。

每条 action 的 `recoverable_claim_ids` 由其查询范围和真实 motif 命中结果确定。普通规划器只能看到预期效果，Oracle 才能使用实际恢复集合。

## 指标

共同指标：

- 最终支持粒度；
- 达到正确粒度的成功率；
- 总取证成本；
- 相对 Oracle 成本遗憾；
- action 命中率；
- 关键证据覆盖率。

R01 额外指标：

- 到达 G3 的成本；
- 完整链关键节点恢复率。

R02 额外指标：

- 正确停在 G2 的比例；
- 无效 action 成本；
- 是否错误生成 G3 支持；
- 对 `not_available` 证据的处理。

## 第一轮范围

- 使用 R01/R02 两个开发案例。
- 使用现有 20%、40%、60% 三档遮蔽和固定随机种子。
- 运行现有规划器与 M1 消融。
- 输出单案例轨迹和分层结果，不把重复运行数量表述为独立样本量。
- 完成后再决定是否扩展 E5、OpTC 或增加 LLM 语义映射。

## 测试

- 微型 CDM fixture 验证 motif 聚合与 Event UUID 回指。
- 测试普通规划器改变隐藏 outcome 后输出不变。
- 测试 R02 不存在的阶段不能被 action 恢复。
- 校验生成的 claim/action/config 交叉引用。
- 完整回归测试后再提交实验结果。
