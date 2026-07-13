# C07-C11 独立盲标说明

你将独立完成三类任务：Claim 来源支持度、公开动作意图和可支撑调查粒度。请不要与另一名标注者讨论，也不要索取管理员 key、规划结果或论文案例结论。

## 文件使用

1. `public/` 是待审 item；`annotations/` 是你唯一需要填写的三个 CSV。
2. Claim 任务同时使用 `source/claim_source_excerpts.jsonl`。运行 `python tools/view_source_excerpt.py CLM-001 --input source/claim_source_excerpts.jsonl` 可查看单条来源。
3. `CODEBOOK.md` 给出完整标签定义。项目 notes 只是待审 claim 的上下文，来源判断必须依据 source excerpt。
4. 每完成一行，将 `reviewed` 填为 `yes`。不确定且来源字段不足时使用 codebook 规定的 `U_unassessable`，不要猜测。
5. 不要修改 `public/`、`source/`、`tools/` 或 CSV 表头，不要新增或删除 item。

## Claim 标签

- `2_direct`：来源直接支持完整原子 claim。
- `1_partial`：核心事件存在，但对象、因果、攻击含义、技术映射或范围部分越界。
- `0_unsupported`：来源不支持、冲突或定位到无关记录。
- `U_unassessable`：来源不可访问、损坏或字段不足。

`source_pointer_valid` 使用 `yes`、`no` 或 `unassessable`。

## 提交

只返回 `annotations/` 下三个已填写 CSV。不要返回整个 ZIP，也不要附带 source excerpt。管理员会先做 A/B 一致性计算，再把分歧交给第三名裁决者。
