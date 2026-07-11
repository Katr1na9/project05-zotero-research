# Claim、公开意图与可支撑粒度人工标注结果模板 v0.1

日期：2026-07-11
当前状态：**等待两名独立标注者完成首轮标注**
禁止事项：不得将代码标签、LLM 标签或空模板写成人工一致性结果

## 1. 样本与完成度

| 任务 | 计划 item | A 已完成 | B 已完成 | 双人可比 |
|---|---:|---:|---:|---:|
| Claim 支持度与来源指针 | 19 | 待填 | 待填 | 待填 |
| 公开动作意图 | 22 | 待填 | 待填 | 待填 |
| 可支撑归因粒度 | 48 | 待填 | 待填 | 待填 |

独立攻击案例数固定为 4。上述 items 是案例内标注单位，不得写成 89 个独立攻击样本。

## 2. 一致性结果

### 2.1 Claim 支持度

- Quadratic-weighted Cohen's kappa：待计算
- 原始一致率：待计算
- `U_unassessable` 比例：待计算
- 来源指针 Cohen's kappa：待计算

### 2.2 公开动作意图

- Exact match：待计算
- Mean Jaccard：待计算
- Micro precision / recall / F1：待计算

### 2.3 可支撑归因粒度

- Quadratic-weighted Cohen's kappa：待计算
- 相差不超过一级比例：待计算
- 混淆矩阵：待生成

## 3. 预登记解释

- Weighted kappa >= 0.80：strong；0.70-0.79：acceptable；< 0.70：修订 codebook 后使用新 pilot，不删除困难 item。
- 意图 micro F1 >= 0.80 且 mean Jaccard >= 0.70：acceptable。
- `U_unassessable` 超过 20%：来源包不足，不得只用剩余样本宣称高可靠性。

## 4. 当前可写结论

截至生成本模板时，只能写“已冻结双人盲标协议并生成标注包”，不能写“人工一致性良好”“粒度规则得到专家验证”或任何数值结论。
