# PANDAcap RR Exact Bounded Acquisition Contract v0.1

**状态：`frozen_contract_only_download_not_authorized`**

本合同只冻结 `eurosec2020-pandacap-rr.zip` 的唯一 artifact identity、官方 URL、exact bytes、MD5、写入上限、失败停机规则和后续 reader/privacy/manifest Gate。

本合同不授权 HTTP 请求、下载、续传、创建或调用 launcher、打开 archive、读取 payload、改变 source role 或通过 L2。

Authority base：`c0135e4201988366509b525ed0d572b5e0503f53`

## 1. 唯一 frozen target

来源记录：

| 字段 | 冻结值 |
|---|---|
| Zenodo record | `3759652` |
| Revision | `4` |
| DOI | `10.5281/zenodo.3759652` |
| Concept DOI | `10.5281/zenodo.3759651` |
| Version | `1.0` |
| Record-scope license | CC-BY-4.0 |

唯一目标：

| 字段 | 冻结值 |
|---|---|
| Target ID | `pandacap_eurosec2020_rr_archive` |
| Source key | `eurosec2020-pandacap-rr.zip` |
| Evidence surface | PANDA full-system record/replay traces |
| Exact bytes | `14,897,472,844` |
| Write ceiling | `14,897,472,844` |
| MD5 | `1624d475a6bb337451f0ce201fb17456` |
| Frozen URL | `https://zenodo.org/api/records/3759652/files/eurosec2020-pandacap-rr.zip/content` |
| Future local root | `datasets/llm/local_audit_cache/pandacap-bounded-v0.1/raw` |
| Future relative path | `eurosec2020-pandacap-rr.zip` |
| Download authorized now | **false** |

最大 archive 数为 1；最大 persisted payload 为 `14,897,472,844` bytes。未列对象数与未列 payload bytes 上限均为 0。

## 2. 默认排除对象

| 对象 | Bytes | 当前处置 |
|---|---:|---|
| `eurosec2020-pandacap-qcow.zip` | 6,429,700,473 | excluded / not authorized |
| `eurosec2020-pandacap-pcap.zip` | 1,106,321,401 | excluded / not authorized |
| `ubuntu16-planb-kernelinfo.conf` | 1,572 | supporting metadata only |
| Academic Torrents / mirrors / individual samples | — | excluded / not authorized |

QCOW、PCAP 与 RR 是同一批 SSH sessions 的不同视图，不能增加 family 或 lineage。QCOW 另有敏感/恶意文件风险，PCAP 另有网络标识和 session content 风险，因此不自动降级或切换到这些对象。

## 3. Future acquisition controls

本合同不执行 acquisition。若未来另行授权：

1. 授权必须点名 `pandacap_eurosec2020_rr_archive`；
2. 最多一次 initial attempt；
3. terminal failure 后不得自动重试；
4. partial object 不得在无新授权时 resume；
5. 只能从 frozen URL 发起，HTTP body 只能写入 frozen local path；
6. 不得换 revision、concept record、mirror、cache、object、byte range 或文件名；
7. 即将超过 `14,897,472,844` bytes 时必须 fail closed；
8. acquisition 阶段不得 open、list、extract 或读取 archive；
9. 完成后先核 exact size，再计算 MD5；
10. exact size 与 MD5 均匹配才可记录 `verified`；
11. 成功或失败都硬停，不得自动进入 reader 或 manifest audit。

`verified` 只表示本地对象与 Zenodo revision 4 发布对象的身份一致，不表示 rights、privacy、manifest、lineage、pointer 或 source role 已通过。

## 4. 后续 reader/privacy/manifest Gate

即使未来 size+MD5 通过，仍必须先停。打开 archive 前另行冻结：

- RRArchive/PANDA reader 名称与版本；
- executable/package identity 与 SHA-256；
- invocation、parser 与 fail-closed 行为；
- central-directory member cap；
- notice token、per-member bytes 与 total bytes；
- 禁止 extract 和持久化 raw member paths/raw notice；
- privacy、secret、malware 与 dual-use 隔离；
- session manifest、duplicate/repeat、reset/reinitialization；
- RR/QCOW/PCAP 同-session binding；
- pointer recoverability；
- protected exact/near exclusion。

Notice 阶段不得读取 ordinary trace/replay content。没有冻结 field allowlist 前，不得让以下内容进入模型可见面：

- credentials 或 secrets；
- attacker commands；
- downloaded payload bytes；
- personal/network identifiers；
- malicious 或 dual-use content；
- labels、hidden answers 或 ground truth。

## 5. Lineage 边界

官方 63 traces 声明仍只是 candidate capture count，不能直接记 63 lineage。不得从以下信息推断独立 lineage：

- 下载成功；
- archive/member 数；
- filename 数；
- 官方 trace 总数；
- RR、QCOW、PCAP 多视图数量。

必须证明至少四个稳定、非空、label-independent session groups，并核 duplicate/repeat 与 reset 条件。一个 SSH session 的所有视图必须留在同一 lineage 和 split。

## 6. Authority posture

| 动作 | 当前授权 |
|---|---|
| 保存本合同 | **是** |
| HTTP request | **否** |
| 创建或调用 launcher | **否** |
| 下载 RR ZIP | **否** |
| Resume partial object | **否** |
| 下载 QCOW / PCAP / mirror | **否** |
| 打开 central directory/member | **否** |
| Reader / nested notice / privacy audit | **否** |
| Manifest / lineage / pointer audit | **否** |
| 写 effective catalog | **否** |
| Source role | **否** |
| Family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| 生成训练样本 | **否** |
| Baseline / 微调 | **否** |
| Kernel / Γ / M3* | **否** |
| L2 Gate | **false** |
| Git push | **否** |

下一步必须获得新的、明确点名 `pandacap_eurosec2020_rr_archive` 的 acquisition execution 授权；本合同本身不产生该权限。
