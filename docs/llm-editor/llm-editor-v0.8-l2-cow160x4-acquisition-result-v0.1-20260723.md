# COW160x4 acquisition result v0.1

日期：2026-07-23  
Authority base：`5d2a26e3f21384a44ddb43d1ea70d67e0e06303b`  
状态：`verified_identity_only_hard_stop`

## 结果

点名对象 `cow160x4_session_aggregation_jsonl_gz` 的唯一一次 initial
attempt 已完成。未发生 retry、resume 或换源。

| 核验项 | 冻结值 | 实际值 | 结果 |
|---|---:|---:|---|
| Bytes | `1,328,104,319` | `1,328,104,319` | PASS |
| MD5 | `1f3897650fb420c97c14ff452398c3f8` | `1f3897650fb420c97c14ff452398c3f8` | PASS |
| stderr bytes | `0` | `0` | PASS |

核验顺序严格为 exact size 后 MD5。只有两者都精确匹配后才记录
`identity_verified=true`。

## Attempt 审计

- Target：`cow160x4_session_aggregation_jsonl_gz`
- Zenodo record/revision：`21260400 / 6`
- Artifact key：`session_aggregation.jsonl.gz`
- Initial attempt：`1`
- Additional attempt：`0`
- Transport：`curl 8.21.0`
- `--max-filesize`：`1,328,104,319`
- 自动 retry：未使用
- resume：未使用
- source substitution：未使用
- 开始时间：`2026-07-23T12:13:52.7336403Z`
- artifact 最后写入时间：`2026-07-23T12:34:16.5987715Z`
- 进程终态：已观察
- stderr：空

启动端未持久化 curl exit code，因此本报告不猜测该值。成功裁断完全依据合同
要求的 terminal process、exact size、MD5 与空 stderr；其中 size 与 MD5 均已
独立核验。

## 内容访问边界

本次没有：

- 打开或读取 gzip header/trailer；
- 解压、stream、计行或读取 JSONL；
- 读取 schema、字段或 session identifier；
- 执行 notice、manifest、lineage、privacy、protected-overlap 或 pointer probe；
- 安装或执行 gzip reader；
- 生成训练样本、运行 baseline 或微调。

结果工件不含本地 raw 路径、payload bytes、member/line path、session 标识或
任何 IP、timestamp、command、credential、URL、filename、fingerprint、
geolocation、event value。

## 科学与角色边界

此次结果只证明本地压缩对象与冻结的 Zenodo artifact identity 一致，不证明：

- session 唯一性或独立性；
- one-session-to-one-record；
- duplicate/reconnect/retry/campaign grouping；
- 隐私字段隔离、nested rights 或恶意内容安全；
- deterministic pointer round trip；
- source-role 或训练适用性。

family、lineage、sample、quota credit 仍为 `0 / 0 / 0 / 0`。未写 effective
catalog，未批准 source role，L2 Gate 未通过。

## 硬停

已停在 reader 合同之前。不得自动打开 gzip、解压或进入任何数据审计。下一步
必须另行冻结 gzip reader、privacy/notice/schema/manifest/lineage/pointer
合同，并取得独立执行授权。
