# LO2v2 index acquisition result v0.1

日期：2026-07-23  
Authority base：`1d5209fcc628a6f027d924cee368b27fbcdc0ce6`  
状态：`verified_exact_size_and_md5_hard_stopped`

## 结果

唯一一次 `lo2v2_index_json` initial attempt 成功并已耗尽。

| 检查 | 结果 |
|---|---|
| Launcher invocations | `1` |
| curl exit code | `0` |
| Expected bytes | `31,028,530` |
| Actual bytes | `31,028,530` |
| Exact size | 通过 |
| Expected MD5 | `2efcff67820ba1df40fae362919271eb` |
| Actual MD5 | `2efcff67820ba1df40fae362919271eb` |
| MD5 | 通过 |
| Verified | `true` |
| Attempts remaining | `0` |

没有 retry、resume、range、换源、换 revision、换对象或 mirror substitution。

## 内容访问状态

- `json_opened=false`
- `json_read=false`
- `json_parsed=false`
- `json_validated=false`
- `audit_started=false`

没有读取或持久化 raw JSON、字段、值、run ID、test/task name、path、timestamp 或其他 payload 内容。

## 科学边界

本结果只证明本地对象与 Zenodo revision 4 发布的 `LO2v2_index.json` 在 exact size 和 MD5 上一致。

它不证明：

- 115 个 runs 唯一、完整或统计独立；
- correct/error 与 initialization leakage 已隔离；
- LO2v1 与 LO2v2 不重叠；
- index 是 Candidate Claim IR evidence；
- pointer 可绑定 runtime logs、metrics 或 traces；
- source role、train admission 或 L2 Gate 已通过。

Family、lineage、sample、quota credit 仍全部为 `0`。

## 终态

acquisition 已进入成功终态，唯一 attempt 已耗尽。禁止自动 retry 或 resume。

在新的 reader 与 privacy/notice/schema/manifest/lineage/label-isolation/v1-v2-overlap/protected-overlap/pointer 合同及独立执行授权之前，不得打开或解析 JSON，也不得下载其他 LO2v2 对象。

