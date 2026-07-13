# Claim、公开意图与可支撑粒度人工标注结果模板 v0.2

日期：2026-07-12
当前状态：**等待两名独立标注者；Claim 来源 Gate 已在当前工作站关闭**
禁止事项：不得将代码标签、LLM 标签、空模板或项目 notes 写成人工一致性结果

## 1. 样本与完成度

| 任务 | 计划 item | A 已完成 | B 已完成 | 双人可比 | 已裁决 |
|---|---:|---:|---:|---:|---:|
| Claim 支持度与来源指针 | 27 | 待填 | 待填 | 待填 | 待填 |
| 公开动作意图 | 27 | 待填 | 待填 | 待填 | 待填 |
| 可支撑调查粒度 | 60 | 待填 | 待填 | 待填 | 待填 |

独立案例数为 5，其中 C11 是一个 adversary-emulation 链。上述 114 个 item 不得写成 114 个独立攻击样本。

## 2. 来源访问

- Hash 锚定 canonical excerpts：27/27（C07-C11）
- 待补来源记录：0/27
- Claim 标注是否正式启动：否；技术条件已具备，等待两名独立标注者
- A/B 分发包：已生成并完成隔离检查，尚未交付标注者
- 来源台账版本：`human-annotation-source-access-ledger-v0.2-20260713.md`

## 3. A/B 一致性结果

### Claim 支持度

- Quadratic-weighted Cohen's kappa：待计算
- 原始一致率：待计算
- `U_unassessable` 比例：待计算
- 来源指针 Cohen's kappa：待计算

### 公开动作意图

- Exact match：待计算
- Mean Jaccard：待计算
- Micro precision / recall / F1：待计算

### 可支撑粒度

- Quadratic-weighted Cohen's kappa：待计算
- 相差不超过一级比例：待计算
- 混淆矩阵：待生成

## 4. 人工对工程代理校准

### Claim 编译质量

- `2_direct` 接受率（排除 U）：待计算
- `2_direct + 1_partial` 比例（排除 U）：待计算
- Source pointer 可验证率（排除 unassessable）：待计算

### 公开 intended

- Final-human vs compiled exact match：待计算
- Mean Jaccard：待计算
- Micro precision / recall / F1：待计算

### G0-G3 粒度代理

- Final-human vs compiled weighted kappa：待计算
- Exact match / within-one-level：待计算
- Compiled over-granularity rate：待计算
- Compiled under-granularity rate：待计算
- 混淆矩阵：待生成

## 5. 预注册判定

- A/B weighted kappa >= 0.80：strong；0.70-0.79：acceptable；低于 0.70：修订 codebook 并使用新 pilot。
- Intended micro F1 >= 0.80 且 mean Jaccard >= 0.70：acceptable。
- `U_unassessable` 超过 20%：来源包不足。
- 粒度代理通过：final-human vs compiled weighted kappa >= 0.70，且 compiled over-granularity rate <= 0.10。

## 6. 当前唯一可写结论

已冻结 C07-C11 双人盲标协议、114 个空白标注 item、裁决模板和聚合校准程序；27/27 Claim 来源摘录已经就绪，但截至当前没有任何人工标签，不能声称 claims 或 G0-G3 代理已获人工验证。
