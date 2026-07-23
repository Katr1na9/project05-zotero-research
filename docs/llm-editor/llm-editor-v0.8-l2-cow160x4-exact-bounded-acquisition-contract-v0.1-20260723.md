# COW160x4 `session_aggregation.jsonl.gz` exact bounded acquisition contract v0.1

日期：2026-07-23  
Authority base：`0856dde13e9c55ba608087da16d3976ead5341ef`  
状态：`frozen_contract_only_download_not_authorized`

## 裁断

本合同只冻结一个可能在未来单独授权获取的对象：

| 项 | 冻结值 |
|---|---|
| Candidate | `cow160x4_cowrie_ssh_session_provenance_2026` |
| Target ID | `cow160x4_session_aggregation_jsonl_gz` |
| Zenodo record / revision | `21260400` / `6` |
| DOI | `10.5281/zenodo.21260400` |
| Artifact key | `session_aggregation.jsonl.gz` |
| Official URL | `https://zenodo.org/api/records/21260400/files/session_aggregation.jsonl.gz/content` |
| Exact bytes | `1,328,104,319` |
| MD5 | `1f3897650fb420c97c14ff452398c3f8` |
| Maximum artifact count | `1` |
| Download authorized now | **否** |

合同输入是逐族 metadata review；其 SHA-256 固定为
`9e609602576e5648b493a95c9a18afc5c71eeb6e3799e055d7159f3e51870ff8`。
该 review 的裁断仅为
`approve_as_metadata_candidate_not_source_role`。

## 单对象边界

仅 `session_aggregation.jsonl.gz` 属于冻结目标。下列对象全部排除，且不得自动回退：

- `data_all.zip`
- `transferred_files.zip`
- `transferred_files_metadata.csv`
- `malformed.txt`
- 其他 revision、concept-record 对象、镜像、缓存、byte range、重命名副本或本地切片

本轮不创建 launcher，不发 HTTP 请求，不下载、不续传，也不读取或检查任何现存 payload。

## 未来获取硬约束

未来若单独授权，授权必须点名
`cow160x4_session_aggregation_jsonl_gz`，并遵循：

1. 只允许一个初始 attempt；失败后不得自动 retry。
2. 未另行授权不得 resume。
3. 响应体只能写入冻结的单一目标位置，写入上限严格为
   `1,328,104,319` bytes。
4. 先核验 exact size；只有 size 完全相等才计算 MD5。
5. 只有 MD5 与 `1f3897650fb420c97c14ff452398c3f8`
   字节级一致才可记为 `verified`。
6. size 或 MD5 失败后硬停；不得换源、打开 gzip、解压、解析、
   改 role 或改 credit。

## gzip 与后续审计边界

`.jsonl.gz` 是 gzip-compressed JSON Lines，不是带 central directory 的
ZIP。即使未来 size 和 MD5 均通过，也必须再次硬停。

任何下列动作都需要新的 reader 合同和独立执行授权：

- 读取 gzip header/trailer；
- 解压、stream、计行或解析 JSONL；
- notice/schema/manifest probe；
- session uniqueness、duplicate/reconnect/campaign grouping 与 lineage audit；
- privacy/field isolation、protected overlap 与 PANDAcap nuisance-independence；
- deterministic pointer round trip；
- source-role review。

后续 reader 合同必须预先固定 reader 名称、版本、可执行文件或包身份及
SHA-256、invocation、parser、redaction、timeout、compressed/decompressed
byte ceiling、line cap 和 fail-closed 行为。不得持久化解压内容或提交 raw
session、timestamp、IP 或字段值。

## 科学与安全硬停

获取并验明 artifact 身份不等于验证了 session 独立性。以下均保持未通过：

- 精确非空 unique-session 数；
- 一条 session 对应一条 aggregation record；
- duplicate、reconnect、retry 与 bot-campaign 相关性处置；
- derived aggregation 与 raw observed evidence 的语义边界；
- 隐私字段物理隔离、nested notice 与恶意内容安全；
- deterministic gzip record ordinal 与 pointer round trip；
- protected overlap；
- 与 PANDAcap SSH honeypot 模态的 nuisance independence。

`session` 当前只能作为 opaque grouping/pointer candidate。约 3,800 万
session 的 curator 声明、文件数、行数、160 个 honeypot、4 种配置、国家、
日期窗、event type、attack class 或 verdict 均不得转换为 lineage credit。
Cowrie emulated command/response 不得写成真实 OS execution 或 host state。

## 权限结论

| 权限或 credit | 结果 |
|---|---|
| HTTP / download / resume | 未授权 |
| gzip open / decompress / parse | 未授权 |
| notice/schema/manifest/lineage/pointer audit | 未授权 |
| effective catalog / source role / train admission | 未授权 |
| family / lineage / sample / quota credit | `0 / 0 / 0 / 0` |
| baseline / fine-tuning / training samples | 未授权 |
| L2 Gate | 未通过 |
| commit / push | 未授权 |

下一动作：硬停。只有新的显式授权点名
`cow160x4_session_aggregation_jsonl_gz` 后，才可执行一次冻结对象获取；即使
identity 验证通过，也不得自动进入 gzip reader 或任何数据审计。
