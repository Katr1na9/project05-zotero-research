# C07-C11 人工标注来源访问台账 v0.2

日期：2026-07-13
状态：Claim 来源访问 Gate 已在当前工作站关闭；人工标签仍为零

## 1. 当前状态

| Artifact | 案例 | Claims | Canonical excerpt | Gate |
|---|---|---:|---|---|
| `darpa_e5_R04_pidsmaker_event_table` | C07 | 5 | event edge + src/dst 解析节点；窗口与节点哈希已复核 | READY_LOCAL |
| `darpa_e5_R05_pidsmaker_event_table` | C08 | 4 | event edge + src/dst 解析节点；窗口与节点哈希已复核 | READY_LOCAL |
| `darpa_optc_R06_sysclient0201_ecar_window` | C09 | 5 | 精确 event ID 对应的原始 eCAR JSON event；窗口哈希已复核 | READY_LOCAL |
| `darpa_optc_R07_sysclient0351_ecar_window` | C10 | 5 | 精确 event ID 对应的原始 eCAR JSON event；窗口哈希已复核 | READY_LOCAL |
| `otrf_apt29_day1_host_events` | C11 | 8 | 精确 JSONL line/RecordNumber 对应的原始 Windows event | READY_LOCAL |

总计 27/27 条 claims 已有一一对应的 canonical excerpt。摘录包绑定 `c07_c11_v0.2` 公开 Claim 文件 SHA-256，不读取管理员 key，也没有产生任何人工标签。

## 2. 可复现链

- 构建器：`09-experiments/scripts/build_claim_source_excerpts.py`
- 单条查看器：`09-experiments/scripts/view_claim_source_excerpt.py`
- 哈希清单：`09-experiments/annotation/source_excerpts/c07_c11_v0.1/source_excerpt_manifest.json`
- 本地 payload：`09-experiments/annotation/source_excerpts/c07_c11_v0.1/local/claim_source_excerpts.jsonl`
- Payload SHA-256：`DF060783831ACF1D961938C5FC4BD208A3AA50C64C7BE38DA33F71128FD7A402`

构建器按公开 `source_pointer` 扫描四个冻结抽取窗口和 C11 Host ZIP。PIDSMaker 保留原始 event edge 与解析节点；OpTC/OTRF 保留命中的原始 JSON event。27 个 blind ID、source pointer 和 excerpt hash 均是一一映射。

## 3. 安全与分发边界

攻击遥测中包含可能触发终端防护的命令字符串。磁盘 payload 对所有原始字符串使用可逆 UTF-8 hex，`excerpt_sha256` 则对解码后的 canonical JSON 计算；查看器只在终端按需解码，不写新的明文文件。

原始遥测和实际 excerpt payload 均不提交 Git。公开仓库只保存构建器、哈希清单和来源说明；管理员确认标注者访问条件后，本地提供 payload。本处理不宣称获得新的第三方数据再分发许可。

## 4. 标注启动规则

1. 公开意图、粒度与 Claim 三类任务均已具备技术启动条件。
2. Claim 标注者必须同时获得公开 Claim item 和本地 source excerpt；只提供项目 notes 仍不合格。
3. A/B 仍须独立盲标；管理员不得以代码、LLM 或 source pointer 映射代填标签。
4. 当前状态仍是 `awaiting_annotations`。Gate 关闭不等于 claims 已获人工验证。

## 5. 下一动作

选择两名具备 CTI/日志分析能力且不参与 case 编译的标注者，分发 A/B 独立包并记录开始时间。两人完成前不运行 calibration，也不查看对方结果。
