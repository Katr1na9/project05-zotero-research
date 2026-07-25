# L2 Endpoint / Provenance 独立执行来源检索 v0.3

**Authority base**：`36db116895879d70e9ac170340cf2b17c7fa3ab4`

**范围**：metadata-only、零下载。本轮没有打开 archive、读取 payload/member、论文全文、模型输出、private gold 或 protected material；没有接触正在获取的 REPROD `dots.zip`；没有重开 KernelDriver、Cuckoo、Liwa、EVTX，也没有推进 CERT/IoT-23 下载。

## 1. 裁断

本轮找到一个可进入下一道“逐族 metadata candidate review”的新方向：

> **PANDAcap SSH Honeypot Dataset**
> `approve_for_separate_metadata_candidate_review_not_source_role`

它还不是 source role，不在 effective catalog，不计 family、lineage、sample 或 quota，也不通过 L2 Gate。

| 方向 | Curator 声明 | Artifact Gate | 本轮裁断 |
|---|---|---|---|
| [PANDAcap](https://zenodo.org/records/3759652) | 63 条 PANDA full-system traces；每个 SSH session 触发一次 30 秒 recording | Zenodo revision 4、version 1.0、CC-BY-4.0；4 个对象均有 bytes+MD5 | **可另开逐族 metadata candidate review** |
| [StreamSpot](https://github.com/sbustreamspot/sbustreamspot-data) | 600 个 scenario graphs | Apache-2.0；固定 commit；`all.tar.gz` 有 Git blob identity | **hold**：graph-ID ranges 编码 scenario，且未声明一 graph 一独立/reset execution |
| [WinMET](https://zenodo.org/records/16414116) | CAPE 生成的 Windows malware execution traces | GPL-3.0-or-later；8 个对象 | **hold**：一执行一 trace manifest、重复策略、标签隔离和 distinctness 未闭合 |

## 2. 为什么 PANDAcap 值得逐族审

### Evidence

1. [Zenodo record 3759652](https://zenodo.org/records/3759652) 和 [Records API](https://zenodo.org/api/records/3759652) 明确声明数据包含 **63 PANDA traces**。
2. 同一官方描述将 capture boundary 写得很清楚：SSH session 开始时，PANDA `recctrl` plugin 启动一次 **30 秒 recording**。
3. [PANDAcap 官方仓库](https://github.com/vusec/pandacap)固定到 `ce3d2590ca79ca5afea2593fefc90b087777ecc3`；其中 dataset 文档 blob `f5daa87d67194c426eed51ad01583ba941cdb3fa` 重复确认 63 traces、session trigger 和三个数据 view。
4. Zenodo revision 4 发布 4 个对象，总计 `22,433,496,290` bytes（约 20.89 GiB），每个对象都有官方 MD5：

| Object | Bytes | MD5 | 语义 |
|---|---:|---|---|
| `eurosec2020-pandacap-rr.zip` | 14,897,472,844 | `1624d475a6bb337451f0ce201fb17456` | 63 条 full-system record/replay traces |
| `eurosec2020-pandacap-qcow.zip` | 6,429,700,473 | `440b9366558fee903ace80677bd41af4` | 同 63 sessions 的 base image + disk deltas |
| `eurosec2020-pandacap-pcap.zip` | 1,106,321,401 | `e3154304a5bc0ada181739c42912e15b` | 从同 63 sessions 提取的 network traces |
| `ubuntu16-planb-kernelinfo.conf` | 1,572 | `0e1a09969f7bc166592c35d19c336ee6` | trace analysis kernel profile |

5. [DataCite](https://api.datacite.org/dois/10.5281/zenodo.3759652) 交叉确认 Dataset 类型、DOI、creator、version、CC-BY-4.0 rights 和 concept DOI。
6. Zenodo 正式把数据标为 EuroSec 2020 论文 [PANDAcap: A Framework for Streamlining Collection of Full-System Traces](https://doi.org/10.1145/3380786.3391396) 的 supplement；Crossref 验证了 ACM venue、作者和日期。

### Inference

- PANDAcap 满足本轮的 metadata threshold：63 个 capture units 不是由行数、文件数、日期、攻击类型或 technique 反推，而是 curator 明确声明的 session-triggered recordings。
- `rr`、`qcow`、`pcap` 是同一批 session 的三种 view；即使未来全部通过，也只能按 session 绑定，不能按 archive 或 sensor view 重复计 lineage。
- 63 仍不是 63 个“已核独立 lineage”。官方 metadata 没有给 VM reset/snapshot、duplicate session policy 或 machine-readable 的一 trace ↔ 一 session manifest。
- 数据来自 live SSH honeypot。full-system replay、disk delta 和 PCAP 可能含 credentials、commands、downloaded payload、personal/network identifiers、secrets 或恶意文件；隐私和 dual-use 风险高于普通日志来源。
- 当前 RRArchive 被官方文档描述为当时的 upcoming format，PANDA support 仍在 WIP。没有 reader 名称、版本、hash、invocation 和 parser，不具备直接 audit 或训练资格。
- 该 family 没有 curator-declared benign/null pool，不能单独修复类别平衡。

### Recommendation

只批准下一道独立 review：

`pandacap_ssh_honeypot_full_system_traces_2020`

下一道 review 应默认只考虑 `eurosec2020-pandacap-rr.zip`；QCOW 和 PCAP 不得自动纳入。即使逐族 review 通过，仍须另开：

1. exact bounded acquisition contract；
2. RRArchive reader/tool amendment；
3. central-directory + nested-notice caps；
4. privacy/secret/malware isolation；
5. session manifest、duplicate/reset 与 multi-view binding；
6. record-level pointer probe；
7. protected exact/near exclusion；
8. 独立 source-role review。

任何一步无法在不读取 label、敏感 session content、QCOW/PCAP payload 或 hidden ground truth 的条件下闭合，都应 fail closed。

## 3. 为什么 StreamSpot 没有晋级

[StreamSpot 官方数据仓库](https://github.com/sbustreamspot/sbustreamspot-data)具备不错的 artifact identity：

- HEAD：`07942da41ae3ba7202b146c758fcf0c30d2cb7b6`
- License：Apache-2.0
- `all.tar.gz`：`87,860,166` bytes
- Git blob SHA-1：`0e987d918cdcb4c53446e3ed73b7697d425955a4`
- README 声明 600 graphs

但官方 README 同时把 graph IDs 划成六个连续 scenario ranges：YouTube、GMail、VGame、drive-by-download attack、Download、CNN。ID range 因而直接编码 scenario。数据还在 preprocessing 中移除了 timestamp、折叠了连续 edge，而 raw flow-graph source 未作为该 immutable artifact 的一部分发布。

所以 StreamSpot 目前只能是 derived-graph hold：

- 不能把 600 graph IDs 自动写成 600 个 label-independent executions；
- 不能把 scenario-coded graph ID 直接暴露给 model/pointer；
- 不具备 raw-to-candidate Claim IR 的源指针与时间归一化能力；
- 需另行证明 graph 对应独立/reset execution，才值得重新评估。

## 4. 搜索边界与未推进项

- KernelDriver/Cuckoo：未重开。
- Liwa：未重开。
- EVTX：未重开。
- CERT/IoT-23：未下载。
- E3/E5/OpTC/OTRF/WitFoo：保持 protected，未作为候选推进。
- AIT-LDS：仍受 same-curator/testbed distinctness 阻塞，未用于本轮填位。
- REPROD：下载任务独立运行；本轮没有读目标、日志、进程或修改 automation。
- PANDAcap 的 Academic Torrents mirrors：未使用；候选身份只钉 Zenodo revision 4。

## 5. Source verification

| Source | 支持内容 | 结论 |
|---|---|---|
| Zenodo record/API | identity、revision、license、4 个 bytes+MD5、63 traces、session trigger、multi-view relationship | **VERIFIED** |
| DataCite DOI API | DOI、Dataset type、creator、version、rights、concept/publication relation | **VERIFIED** |
| Crossref DOI API | ACM EuroSec 2020 论文身份、作者、venue、日期 | **VERIFIED** |
| `vusec/pandacap` repository metadata | curator framework identity、Apache-2.0、固定 HEAD | **VERIFIED** |
| Pinned dataset documentation blob | 63 traces、30 秒 session recording、RR/QCOW/PCAP layout、RRArchive warning | **VERIFIED** |
| StreamSpot official project page | 页面返回 HTTP 403 | **NOT USED** |

没有读取论文全文。Crossref、Zenodo、DataCite 与 pinned curator documentation 已独立闭合 PANDAcap 的身份、artifact 和 capture declaration。作者同时是 framework 与 dataset curator，这是正常的 curator relationship，但不能替代 reset、uniqueness 或 privacy audit。

## 6. Gate

- metadata search：`complete`
- reviewable direction：`pandacap_ssh_honeypot_full_system_traces_2020`
- maximum verdict：`approve_for_separate_metadata_candidate_review_not_source_role`
- effective catalog：`false`
- download / payload audit：`false`
- source role：`false`
- family / lineage / sample / quota credit：`0 / 0 / 0 / 0`
- baseline / fine-tuning / Kernel / M3*：`false`
- CERT/IoT-23 download：`false`
- REPROD mutation：`false`
- L2 Gate：`false`
- git push：`false`

本报告由 AI 辅助完成；所有晋级判断仅使用官方 registry、repository metadata 与 curator documentation，未将 trace/file/archive 数静默改写为已核 lineage。
