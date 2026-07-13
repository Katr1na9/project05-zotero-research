# C07-C11 人工标注来源访问台账 v0.1

> **历史台账。** 2026-07-13 已从本地四个冻结窗口恢复 C07-C10 全部 19 条记录；当前状态见 `human-annotation-source-access-ledger-v0.2-20260713.md`。

日期：2026-07-12
状态：Claim 来源访问 Gate 部分阻塞

## 1. 当前状态

| Artifact | 案例 | Claims | 当前本地精确记录 | Gate |
|---|---|---:|---|---|
| `darpa_e5_R04_pidsmaker_event_table` | C07 | 5 | 不在当前工作区；仅保留 record UUID 与编译说明 | BLOCKED |
| `darpa_e5_R05_pidsmaker_event_table` | C08 | 4 | 不在当前工作区；仅保留 record UUID 与编译说明 | BLOCKED |
| `darpa_optc_R06_sysclient0201_ecar_window` | C09 | 5 | 不在当前工作区；仅保留 event ID 与抽取摘要 | BLOCKED |
| `darpa_optc_R07_sysclient0351_ecar_window` | C10 | 5 | 不在当前工作区；仅保留 event ID 与抽取摘要 | BLOCKED |
| `otrf_apt29_day1_host_events` | C11 | 8 | 本地 Host ZIP 可用；每条 claim 有精确 JSONL line、host/provider/record/EventID | READY_LOCAL |

总计 27 条 claims：8 条当前可直接回查，19 条仍需补来源记录或 canonical excerpts。

### 本机回收扫描依据

- 已在 `D:\Software\Codex\Workplace\workspace` 全目录检索 C07-C10 的代表性 record UUID/event ID；命中仅来自当前 case、motif 和 annotation 文件，没有独立原始记录。
- 已按 PIDSMaker、PGDMP、eCAR、OpTC、event-table、R04-R07、AIA 分片等名称扫描普通文件，未发现候选窗口或导出。
- 已只读检查 `workspace.zip` 的 105,166 个中央目录成员；未发现上述命名的数据候选，未解压或执行归档内容。

因此本台账使用“当前本机未恢复”，而不是断言官方来源永久不可获得。

## 2. Canonical excerpt 最低要求

每条 excerpt 必须：

1. 由原始来源按 record UUID/event ID 精确抽取；
2. 保留判断 claim 所需的原始字段，不把项目 notes 改写成“原始记录”；
3. 记录 source artifact、source hash、抽取脚本/命令、record locator 与 excerpt SHA-256；
4. 对敏感或超大字段只做有记录的最小裁剪；
5. 由测试验证 27 个 pointer 均有且仅有一个 excerpt。

## 3. 启动规则

- C11 的 8 个 Claim items 可以在管理员提供本地只读 ZIP 后进入标注。
- C07-C10 的 19 个 Claim items 在来源 Gate 关闭前不得要求标注者仅凭 notes 给出 direct/partial/unsupported。
- 公开意图和粒度任务不依赖原始记录，可先行开展。
- 若最终无法恢复 C07-C10 来源，必须如实报告 claim 人工效度未完成，而不是用 `U_unassessable` 的高比例包装通过。

## 4. 下一动作

优先寻找此前生成 C07-C10 claims 时使用的本地抽取窗口或 PostgreSQL/event-table 导出。如果无法恢复，再评估重新获取官方源数据的成本；在数据可用前不启动完整 Claim 盲标。
