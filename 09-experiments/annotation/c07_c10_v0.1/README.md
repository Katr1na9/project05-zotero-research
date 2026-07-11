# C07-C10 双人盲标包 v0.1

本目录包含 19 个 claim、22 个公开动作意图和 48 个可支撑粒度状态。A、B 标注者第一轮独立完成，不得交换答案。

## 使用顺序

1. 向两名标注者提供 `public/` 中的三个 JSONL 文件以及各自目录中的三个 CSV。
2. 每完成一行，将 `reviewed` 填为 `yes`。意图节点集允许为空；此时 `selected_node_ids_pipe` 留空，但 `reviewed` 必须为 `yes`。
3. 多节点用 `|` 分隔，例如 `N01_x|N03_y`。
4. Claim 标签仅用 `2_direct`、`1_partial`、`0_unsupported`、`U_unassessable`；来源指针仅用 `yes`、`no`、`unassessable`。
5. 粒度仅用 `G0_unknown`、`G1_technique`、`G2_tactic_intent`、`G3_campaign`。
6. 两人完成后运行：`python 09-experiments/scripts/analyze_annotation_agreement.py 09-experiments/annotation/c07_c10_v0.1`。

`admin/admin_key.json` 只供管理员在一致性计算后追溯真实 item，不提供给首轮标注者。当前 `agreement_results.json` 的状态是 `awaiting_annotations`，不包含任何伪造人工结果。
