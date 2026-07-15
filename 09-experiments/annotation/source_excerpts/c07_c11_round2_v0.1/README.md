# C07-C11 Round 2 Claim 来源摘录包 v0.1

状态：`ready_local_canonical_excerpts`；27/27 个呈现指针已解析，不含人工标签。

本包只解析 `../../c07_c11_round2_v0.1/public/claim_items.jsonl` 中**实际呈现**给标注者的 source pointer。它既不读取原始正确指针，也不读取管理员的正/负例条件。因此，故意错误指针仍会得到其所指向记录的真实 canonical excerpt，标注者可以判断“可访问但与当前 claim 无关”，而不会把不可访问误当成负例。

- 可提交文件：`source_excerpt_manifest.json`（生成后写入）。
- 本地摘录：`local/claim_source_excerpts.jsonl`，受 `.gitignore` 保护。
- 构建器：`../../../scripts/build_annotation_round2_source_excerpts.py`。
- 人工标签：始终不由构建器生成，`human_labels_present=false`。

构建命令：

```powershell
python 09-experiments/scripts/build_annotation_round2_source_excerpts.py
```

若同版本输出已存在，构建器会拒绝覆盖；任何重建或协议变化必须使用新的版本目录。
