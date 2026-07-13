# C07-C11 Claim 来源摘录包 v0.1

状态：`ready_local_canonical_excerpts`；人工标签仍为零。

## 用途

本包为 `../../c07_c11_v0.2/public/claim_items.jsonl` 中的 27 个 Claim item 提供一一对应的原始来源摘录。摘录按 `blind_id` 关联，只用于让两名标注者判断 claim 是否被来源直接、部分或不支持。

## 文件

- `source_excerpt_manifest.json`：可提交的哈希清单，记录 27 个摘录哈希、父来源、窗口哈希和来源 Gate 状态。
- `local/claim_source_excerpts.jsonl`：本地管理员持有的实际摘录；受 `.gitignore` 保护，不进入公开仓库。
- 构建器：`../../../scripts/build_claim_source_excerpts.py`。
- 单条查看器：`../../../scripts/view_claim_source_excerpt.py CLM-001`；只向终端解码，不另写明文文件。

## 重建

要求本机已有 C07-C10 的四个抽取窗口、THEIA/ClearScope 节点表以及 C11 OTRF Host ZIP。原始大文件只用于验证父来源和抽取链，不写入输出。

```powershell
python 09-experiments/scripts/build_claim_source_excerpts.py
```

构建器执行以下约束：

1. 只读取盲标包公开的 `source_pointer`，不读取管理员标签；
2. 每个 pointer 必须且只能命中一个冻结 record；
3. PIDSMaker 摘录保留完整 event edge 及其两个解析节点；
4. OpTC 和 OTRF 摘录保留命中的原始 JSON event；
5. 原始字符串以可逆 UTF-8 hex 写入本地包，避免含攻击命令的研究数据被终端防护误判；查看器按需在终端解码；
6. `excerpt_sha256` 始终对解码后的原始 payload 计算，而不是对编码容器计算；
7. 校验四个抽取窗口和节点表的冻结哈希，不把项目 notes 当作来源证据。

## 分发边界

DARPA/OpTC/PIDSMaker/OTRF 均属于复用第三方数据。公开仓库只保存代码、哈希和来源说明；实际摘录由管理员在确认标注者访问条件后随盲标材料本地提供。该处理不宣称获得新的数据再分发许可。

## 标注启动状态

来源 Gate 已在当前工作站关闭：C07-C11 共 27/27 个 Claim item 均有 canonical excerpt。管理员必须同时提供 `public/claim_items.jsonl` 和本地摘录文件；只提供前者仍不允许启动 Claim 支持度标注。
