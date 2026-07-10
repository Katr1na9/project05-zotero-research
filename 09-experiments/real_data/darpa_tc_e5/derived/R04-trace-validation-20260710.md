# R04 E5 THEIA 真实 Trace 验证

日期：2026-07-10  
状态：已完成原始窗口、节点解析和 C07 motif 编译

## 1. 目的与边界

R04 是 C07 真留出的唯一真实来源：DARPA TC Engagement 5 中 `ta1-theia-target-1` 的 Firefox Drakon BinFmt-Elevate 攻击。窗口由 TA5.1 最终报告第 8.6 节先行锁定，再读取 event-level 数据；没有根据事件结果调整窗口或 M3a 参数。

- 本地时间：2019-05-15 `14:48–15:07 EDT`
- UTC：`2019-05-15T18:48:00Z` 至 `2019-05-15T19:07:00Z`
- 目标：`ta1-theia-target-1` / `128.55.12.110` / Ubuntu 12.04
- 原始 archive：`raw/pidsmaker/theia_e5.dump`
- SHA-256：`8072F8F767EC9CE680D359957F4D394DF171BD7EB6604393C2F50FA45BA8D303`

## 2. 可复现抽取

archive 是 PostgreSQL custom archive（`PGDMP 1.16`），包含 `event_table`、`file_node_table`、`netflow_node_table` 与 `subject_node_table`。项目使用 `stream_pgdump_event_window.py` 进行流式解压，不把完整 provenance graph 落盘。

| 项 | 结果 |
|---|---:|
| 全表扫描事件数 | 140,994,662 |
| 锁定窗口事件数 | 256,297 |
| 窗口节点哈希 | 7,043 |
| 已解析节点哈希 | 7,043 / 7,043 |
| 时间戳逆序数 | 48,543 |

`timestamp_rec` 全表并不单调，因此不得在首次超过窗口结束时间后提前停止扫描。

## 3. 报告与 Trace 的对齐

| 报告叙述 | Trace 观察 | 结论 |
|---|---|---|
| Firefox 建立 C2 | Firefox 与 `208.203.20.42:80` 之间有 24 条 `EVENT_RECVFROM`，并有 24 条 `EVENT_SENDTO` | 直接可见 |
| BinFmt-Elevate | `/sbin/modprobe -q -- binfmt-0000` 在 14:50:15 与 14:54:45 EDT 各执行一次 | 直接可见的能力信号；不单独声称已证明 root 转换 |
| 注入 sshd 后写 `sshdlog` | `/usr/sbin/sshd` 在 14:58:19 EDT 打开 `/var/log/sshdlog` | 直接可见的后效痕迹；schema 无专门 injection operation |
| `load_helper.ko`、`read_scan.ko` | 14:54 EDT 观察到两次 `sudo insmod` | 与报告一致的良性活动，保留为 context/decoy 而非攻击证据 |
| 第二个 C2：`189.141.204.211:80` | 本窗口已解析节点中未出现该端点 | 真实证据缺口，不生成伪 claim |

## 4. C07 编译结果

`C07-darpa-e5-theia-0515` 使用五个自动编译的 motif，其中三条是攻击链节点，另两条是良性驱动背景。每条 claim 都保存 `event_uuid` 回指；五条 motif 均已观察到。

1. Firefox 接收 `208.203.20.42:80` 数据。
2. BinFmt handler 执行。
3. `sshd` 打开 `sshdlog`。
4. 良性 `load_helper.ko` 驱动安装。
5. 良性 `read_scan.ko` 驱动安装。

该案例的支持上限固定为 `G3_campaign`。它不声称可由单一 trace 归因到命名攻击者，也不把报告文本中未出现于 trace 的观测量当作可获取证据。

## 5. 产物

- `manifest.json`：来源与 archive 哈希。
- `ground_truth/R04.json`：报告级真值与 trace 验证状态。
- `R04_postgres_catalog.json`：无损 catalog 摘要。
- `R04_extraction_summary.json`：完整窗口抽取摘要。
- `R04_node_resolution_summary.json`：节点解析覆盖率。
- `../../../real_cases/C07-darpa-e5-theia-0515/`：可运行的 C07 三件套与 motif 审计。
