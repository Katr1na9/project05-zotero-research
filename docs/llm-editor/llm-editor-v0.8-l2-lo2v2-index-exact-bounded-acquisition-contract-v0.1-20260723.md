# LO2v2 `LO2v2_index.json` exact bounded acquisition contract v0.1

日期：2026-07-23  
Authority base：`e37d955e5a69919c086fb6065135da7297002590`  
状态：`frozen_contract_only_download_not_authorized`

## 裁断

本合同只冻结一个可能在未来单独授权获取的对象：

| 项 | 冻结值 |
|---|---|
| Candidate | `lo2v2_microservice_observability_runs_2026` |
| Target ID | `lo2v2_index_json` |
| Zenodo record / revision | `18937117` / `4` |
| DOI | `10.5281/zenodo.18937117` |
| Artifact key | `LO2v2_index.json` |
| Official URL | `https://zenodo.org/api/records/18937117/files/LO2v2_index.json/content` |
| Exact bytes | `31,028,530` |
| MD5 | `2efcff67820ba1df40fae362919271eb` |
| Maximum artifact count | `1` |
| Download authorized now | **否** |

合同输入为已提交的逐族 metadata review：

- commit：`e37d955e5a69919c086fb6065135da7297002590`
- JSON SHA-256：`a09d27ceb0ed6733e6526c06281907f801265bc8ce0aea6e5cc3a1cbb3b628e7`
- verdict：`approve_as_metadata_candidate_not_source_role`

## 单对象边界

仅 `LO2v2_index.json` 属于冻结目标。以下对象全部排除，且不得自动回退：

- `LO2v2.zip`
- `LO2v2-metrics.zip`
- `light-oauth2-logs.zip`
- `light-oauth2.zip`
- `light-oauth2-metrics.zip`
- 其他 revision、concept-record 对象、mirror、cache、byte range、重命名副本或本地切片

本轮不创建 launcher，不发起 file HTTP request，不下载、不续传，也不打开或解析任何 JSON。

## 为什么只选择 index

`LO2v2_index.json` 是 record 中唯一的非 archive 对象，也是逐族评审指定的最窄 manifest 候选面。它可能用于未来核验：

- 是否存在 115 个唯一完整 runs；
- 是否每个 run 恰有 54 tests；
- 是否有 partial、aborted、retry 或 duplicate run；
- run identifier 是否能形成稳定 pointer candidate；
- LO2v1 与 LO2v2 是否存在 exact/near overlap。

它不是 Candidate Claim IR evidence，不能代替 runtime logs、metrics 或 traces。指向 index 的 pointer 也不能绑定从未打开和验证的 runtime archive content。

## 未来获取硬约束

未来若单独授权，授权必须点名 `lo2v2_index_json`，并遵循：

1. 只允许一个 initial attempt；失败后不得自动 retry。
2. 未另行授权不得 resume。
3. 响应体只能写入冻结的单一目标位置，写入上限严格为 `31,028,530` bytes。
4. 只允许从冻结的官方 URL 发起；不得换 source、revision、mirror、cache、range 或 slice。
5. 先核验 exact size；只有 size 完全相等才计算 MD5。
6. 只有 MD5 与 `2efcff67820ba1df40fae362919271eb` 字节级一致才可记为 `verified`。
7. size 或 MD5 失败后硬停；不得重启、打开 JSON、改 role 或改 credit。

## size + MD5 后仍须硬停

即使未来 identity 验证通过，也不得自动打开、stream、parse、validate、pretty-print、transform、count、sample 或 grep JSON。

下一阶段必须先另行冻结：

- JSON reader 名称、版本、executable/package identity 与 SHA-256；
- invocation、parser、redaction 与 fail-closed 规则；
- input bytes、object count、nesting depth、string length 与 timeout caps；
- bounded notice、schema、manifest、lineage、label-isolation、v1/v2 overlap 与 pointer probe；
- 禁止持久化 raw run IDs、test/task names、paths、timestamps、service identifiers 或 ordinary values。

reader 合同冻结后，audit execution 仍须再次单独授权。

## 科学和监督边界

以下不得由 successful acquisition 或 checksum 推导：

- 115 个 runs 已经是 115 个独立 lineages；
- 6,210 个 test executions 是独立 samples；
- 每个 run 均完整且没有 duplicate/retry；
- repeated system、seed、cache、image、host 与 temporal nuisance 已受控；
- correct/error、specific error task 与 initialization leakage 已隔离；
- LO2v1 与 LO2v2 已完全不重叠；
- index 可以充当 runtime evidence；
- index pointer 可以绑定 unopened logs、metrics 或 traces。

test/task names、correct/error labels、expected outcomes、error targets、label-bearing paths、analysis outputs、initialization leakage proxies，以及未经清除的 log/trace/metric counts 或 sizes 均不得进入 model view。

## 权限结论

| 权限或 credit | 结果 |
|---|---|
| HTTP file request / download / resume | 未授权 |
| JSON open / read / parse | 未授权 |
| notice/schema/manifest/lineage/label/overlap/pointer audit | 未授权 |
| runtime archive acquisition | 未授权 |
| effective catalog / source role / train admission | 未授权 |
| family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| baseline / fine-tuning / training samples | 未授权 |
| L2 Gate | 未通过 |
| commit / push of this contract | 未授权 |

下一动作：硬停。只有新的显式授权点名 `lo2v2_index_json` 后，才可执行一次冻结对象获取；即使 exact size 与 MD5 均通过，也必须在任何 JSON reader 或数据审计之前再次停止。

