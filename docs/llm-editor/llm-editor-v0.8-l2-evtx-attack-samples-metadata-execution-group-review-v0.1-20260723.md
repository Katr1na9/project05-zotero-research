# EVTX-ATTACK-SAMPLES Metadata-only Execution-group 评审 v0.1

**裁断**：`reject_as_train_replacement_at_metadata_gate`

EVTX-ATTACK-SAMPLES 的 repository identity、GPL-3.0 license、固定 commit 和 Git tree 都能可靠钉死；但当前 revision 没有提供任何可核验的独立 execution/run/capture grouping。因此它不能填补 Liwa 空出的训练 slot，也不应进入下载或 payload audit。

## 核验范围

只读取了以下公开 metadata：

- GitHub repository API；
- 固定 commit `4ceed2f4706daf601c212a8f91c113dd85349a2c`；
- recursive Git tree；
- `README.md`、`LICENSE.GPL`；
- 5 个小型目录 README。

没有下载或打开 278 个 EVTX，也没有读取 `evtx_data.csv`、ATT&CK JSON、日志 TXT、PCAP、ETL 或其他 payload。

## Artifact 层通过的部分

| 项 | 结果 |
|---|---|
| 固定 commit | `4ceed2f4706daf601c212a8f91c113dd85349a2c` |
| Commit signature | verified / valid |
| Tree SHA | `df87756f61c490e20e73b1a6cf2835351e8fd070` |
| Tree truncated | false |
| License | GPL-3.0，`LICENSE.GPL` 已核验 |
| EVTX 文件 | 278 |
| EVTX 总 bytes | 48,717,824 |
| distinct EVTX Git blobs | 277 |

固定 commit 与 blob SHA 足以支持可重复的 artifact identity。不过，278 个文件只有 277 个 distinct blob，已经出现同一内容位于两个路径的情形；这进一步说明 path/file count 不是 execution count。

## 为什么 execution-group Gate 失败

主 README 将仓库定义为“与特定 attack 和 post-exploitation techniques 相关的 Windows event samples 容器”，用途是 DFIR/threat-hunting training 与 detection use-case design。它没有声明：

- 独立 run/capture 的数量；
- run/session ID；
- host 或实验环境边界；
- run 的开始和结束时间；
- 文件到一次执行的 membership；
- 多 provider/view 是否来自同一次执行。

其余公开文档也没有补上这些信息：

- `AutomatedTestingTools/readme.md` 明确说部分结果来自 Atomic Red Team 和 EDR testing scripts；
- malware README 只说未来会放置组合多个 TTP 的 execution traces，没有当前 manifest；
- Command-and-Control README 枚举的是 event IDs 和 telemetry indicators；
- ATT&CK metadata README 关注 tactic/technique analytics；
- Emotet README 指向一个外部 ANY.RUN task。

这说明仓库是混合来源、按 technique/telemetry 组织的样本集合，不是带 source-native run registry 的实验语料。尤其是 Atomic Red Team 引用会与现有 Atomic family 形成 generation/nuisance overlap 风险。

## 不允许的替代计数

下列任何数量都不能当 lineage：

- 278 个 EVTX 文件；
- 277 个 distinct Git blobs；
- tactic/technique 目录数；
- event ID 或 telemetry provider 数；
- Git commits；
- 文件名中看起来像不同攻击的 token。

打开 EVTX 后用 timestamp/host 猜 run 也不合格，因为 curator 没有给出 source-native grouping contract；那会把分析者推断冒充数据来源事实。

## Verdict

| Gate | 结果 |
|---|---|
| Identity/revision | pass |
| Repository license | pass，未来仍需 nested notice audit |
| Immutable tree/blob metadata | pass |
| ≥4 curator-declared execution groups | **fail（verified=0）** |
| Cross-family nuisance independence | fail/high risk |
| Replacement approved | false |
| Download approved | false |
| Quota | 0 |

当前 status 从 `reserve_lineage_independence_unverified` 改为 `metadata_reject_execution_groups_undocumented`。只有 curator 发布新的 immutable revision，并附带至少 4 次独立执行的机器可读 manifest，才可重新进行 metadata-only 评审；不能在本 revision 上先下载再补 provenance。

Liwa replacement slot 继续 vacant。下一步应搜索一个官方 artifact 在 metadata 层已经暴露至少 4 个 source-native run/capture group 的独立 endpoint/provenance family。
