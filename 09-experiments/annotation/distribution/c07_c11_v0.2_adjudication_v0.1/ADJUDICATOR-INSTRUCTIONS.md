# C07-C11 第三人盲裁决说明

状态：仅包含 A/B 首轮分歧项。

1. 只依据 `public/` 中的公开题目填写 `annotations/` 中同名 CSV。
2. 每完成一行，将 `reviewed` 填为 `yes`。
3. 不索取或查看 A/B 标签、管理员 key、recoverable claims、规划结果或论文案例结论。
4. Claim 使用冻结标签 `2_direct`、`1_partial`、`0_unsupported` 或 `U_unassessable`。
5. Intent 允许空集合，多节点以 `|` 分隔，只选择公开候选节点。
6. 本包不含粒度分歧；粒度任务无须填写。
7. 返回 `annotations/claim_annotations.csv` 和 `annotations/intent_annotations.csv`。
