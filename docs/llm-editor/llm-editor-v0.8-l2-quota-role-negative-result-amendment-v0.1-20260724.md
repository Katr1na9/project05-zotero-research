# L2 quota / role / negative-result amendment v0.1（草案）

**状态**：`draft_for_review_not_effective`  
**基线**：`0d8865592fb738855c61c00e3c89efc30fd44634`  
**范围**：只提出设计，不改变现行 quota、effective catalog、source role、credit 或 L2 Gate。

## 核心判断

现行 quota amendment 已明确：`train ≥4 family` 与每族 lineage 下限是 pilot 的操作下限，不是统计功效定理。应保留的硬边界是独立 family/lineage、防伪重复、fail-closed 和“看过模型结果后不得降门槛”。

本草案提出两条证据轨道：

- **A：`metadata_audit_candidate`**  
  只代表身份、bounded 结构和 Gate 地图证据。A 可以进入独立的 audit-only metadata register（若另行授权），但永不自动成为 train 源、永不授 credit。

- **B：`train_eligible_source_candidate`**  
  只有 B 才可能进入 source-role review。它必须在新合同和新审查下闭合 privacy、nested notice、outcome-composition、outcome-blind manifest、lineage independence 等 Gate，并通过现行 quota capacity audit。

A 不计入 B；两个失败/部分表面也不能“半个拼一个”组成 B。

## 负结果轨道

建议允许一个受范围约束的负结果主张：

> 在声明的公开 metadata-search universe 与冻结 privacy/notice/outcome/lineage Gate 下，当前检索路径尚未找到足以支撑注册 train L2 pilot 目标的 B-tier family。

这不是“公开语料普遍不可达”的断言，也不是统计功效、模型质量或现实世界有效性的证明。正式使用前必须记录搜索宇宙、时间、查询、去重规则、分母、候选 disposition 和停止规则。

## 止损

LogChunks 等 metadata-only 候选默认进入 `metadata_stop_loss_hold`。只有在 payload 之前已有可审的、至少四个 label-independent execution/capture groups 证据，并能先验辩护 outcome-blind lineage 与 protected-outcome exclusion 时，才值得新合同、新 authority 的 full audit。

REPROD/PANDAcap 的失败路径不静默重开；Toyota 继续 hold + reject source role；St.Gallen 现有路径不因本草案自动重开。

## 不变项

- 身份 ≠ role ≠ credit ≠ L2。
- 不得降低独立性、隐私、notice、outcome、lineage 或 pointer 规则。
- 不得重试、resume、复用已耗尽执行、写 raw path/notice/member content。
- 不得把 A 证据写入 effective train catalog。
- 当前 Direction 04 仍 vacant，train family 进度仍为 `0/4`。
- 本草案不授权下载、audit、训练、baseline、微调或 catalog mutation。

## 待审问题

1. A-tier 是否使用独立 audit-only register？
2. B-tier 是否要求 pointer binding，还是由未来 B 合同定义严格的 unbound 例外？
3. 负结果主张的公开搜索 universe、分母和停止规则如何冻结？
4. 若将来要改 quota，由谁在模型调用前批准新 amendment？

本草案未提交，现行 quota 与 L2 Gate 继续有效。
