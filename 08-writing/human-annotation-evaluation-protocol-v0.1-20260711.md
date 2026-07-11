# Claim、公开意图与可支撑粒度人工标注协议 v0.1

日期：2026-07-11
状态：标注前冻结
案例范围：C07-C10

## 1. 目的

本协议评价三个此前未被独立测量的人工环节：

1. evidence claim 是否被来源记录直接支持，是否存在过度表述；
2. `intended_cti_node_ids` 是否能由动作请求和 CTI 图独立复现；
3. 人工判断的最高可支撑归因粒度是否与当前 G0-G3 规则一致。

标注结果用于评估 schema 和代理粒度的外部效度，不用于回头修改 C07-C10 的冻结规划器结果。

## 2. 标注者与盲法

- 至少两名具备安全日志、CTI 或事件响应知识的独立标注者。
- 两名标注者在第一轮不得讨论；只在一致性计算后进入 adjudication。
- 标注包使用随机 blind ID，不显示案例名称、规划器输出、动作真实恢复集合、Oracle 路径或代码计算粒度。
- intended 标注者不得访问 `recoverable_claim_ids`。
- granularity 标注者只能看到当前可见 claims 和 CTI 图，不能看到被隐藏 claims。
- 第三名裁决者只处理分歧，不替代第一轮独立标签。

## 3. 标注单位与抽样

### 3.1 Claim 支持度

单位为“claim-来源指针对”。C07-C10 全部 claims 入组，不抽样。字段包括规范化 subject-predicate-object、claim type、notes、source pointer 和可用来源摘要。

标签：

- `2_direct`：来源直接支持原子 claim，未越过可观察事实；
- `1_partial`：核心事件存在，但对象、因果、技术或攻击含义有过度表述；
- `0_unsupported`：来源不支持或与 claim 冲突；
- `U_unassessable`：来源不可访问或信息不足。

另标 `source_pointer_valid`：yes/no/unassessable。

### 3.2 公开意图

单位为候选动作。C07-C10 全部非 STOP 动作入组。标注者看到 natural-language request、target、channel 以及全部 CTI 节点定义，选择该动作在执行前“希望补充”的节点集合，可为空或多选。

### 3.3 可支撑粒度

从每个案例的 45 个初始条件中生成全部状态，按可见 claim 集合去重；每案例最多选择 12 个状态，并按代码计算的 G0-G3 仅用于分层抽样，标签本身对标注者隐藏。目标最多 48 个状态。

标注者选择 `G0_unknown`、`G1_technique`、`G2_tactic_intent` 或 `G3_campaign`，并标记阻止进入下一粒度的关键缺口。

## 4. 随机化与版本控制

- 随机种子：`20260711`。
- 三类 item 分别随机排列；blind ID 与真实 ID 的映射仅保存在管理员 key 文件。
- 管理员 key 不提供给标注者，不进入公开标注包。
- 第一轮标签只追加不覆盖；若 codebook 修订，使用新 pilot item 或明确标记 round 2。

## 5. 一致性指标

- claim 支持度：排除 `U` 后计算 quadratic-weighted Cohen's kappa；同时报告原始一致率。
- source pointer validity：Cohen's kappa 与原始一致率。
- intended 多标签：exact-match、每 item Jaccard、micro precision/recall/F1。
- granularity：quadratic-weighted Cohen's kappa、相差不超过一级比例和混淆矩阵。

预登记解释阈值：

- weighted kappa ≥ 0.80：strong；0.70-0.79：acceptable；< 0.70：需修订 codebook；
- intended micro F1 ≥ 0.80 且 mean Jaccard ≥ 0.70：acceptable；
- `U_unassessable` 超过 20%：来源包不足，不能用剩余样本宣称高可靠性。

## 6. 防止伪重复与泄漏

- claims、actions 和 states 是标注 item，不等于独立攻击案例；论文仍报告独立案例数为 4。
- 不能用代码原标签作为“第二标注者”。
- 不能让 LLM 标签冒充人工一致性结果；LLM 可在后续作为单独对照。
- 不能在看到一致性结果后删除困难 item 来提高指标。

## 7. 产物

- packet generator：`09-experiments/scripts/build_annotation_packets.py`
- agreement analyzer：`09-experiments/scripts/analyze_annotation_agreement.py`
- 盲标包：`09-experiments/annotation/c07_c10_v0.1/`
- 结果模板：`08-writing/human-annotation-evaluation-results-template-v0.1-20260711.md`
