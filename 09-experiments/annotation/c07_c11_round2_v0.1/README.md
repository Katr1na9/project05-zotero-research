# C07-C11 annotation Round 2 v0.1

状态：prospective locked，等待两名真实独立标注者；当前无人工标签。

- 只向标注者 A 分发 `annotator_A/`，只向 B 分发 `annotator_B/`。
- `public/` 是一致性分析和来源摘录构建器使用的共享盲 ID 视图，不是标注者分发包。
- `admin/` 含负例条件与真实映射，受 `.gitignore` 保护，严禁分发。
- `adjudicator/` 当前为空；只有 A/B 首轮冻结后才允许生成分歧包。
- 前序 `c07_c11_v0.2` 保持只读，Round 2 不覆盖任何旧标签或结果。
- Codebook：`../protocols/c07_c11_round2-codebook-v0.1.md`。
