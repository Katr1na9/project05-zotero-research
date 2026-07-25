# COW160x4 bounded gzip audit contract v0.1

日期：2026-07-23
Authority base：`afc50ae17be632b78146df3ab2f08b95fe6bc690`
状态：`frozen_contract_only_audit_execution_not_authorized`

## 裁断

已冻结 `cow160x4_session_aggregation_jsonl_gz` 的 reader、privacy、notice、
schema、manifest、lineage 与 pointer 审计合同，但没有授权执行。

本阶段没有 stat/open gzip、读取 header/trailer、解压或读取 JSONL。只完成了
reader metadata pin、parser syntax validation 和合同编写。

## Reader 与 parser

Reader 固定为 CPython `3.11.15` 标准库 `gzip/json/hashlib`，zlib
compile/runtime 均为 `1.3.2`。解释器、DLL 和模块的路径模板、bytes 与
SHA-256 已在 reader amendment 中逐项冻结。

| 工件 | SHA-256 |
|---|---|
| Reader amendment JSON | `cc3020aedb2528fe81cbee0f8036c2b2cf225d90973ac92de49755d17c7198cd` |
| Audit script | `a2157bdce0fb939aee2898ef0c4f14e33b8df98fd115cfabdb6831e37836bcb6` |
| Acquisition contract | `bd9cd8c9d4275efe120078b912e034551d86f8934ad3127f1ea6654524f7f97d` |
| Acquisition result | `a2f0e5f530c386e40960b84f5e07000fdfbcc2a8a4e229e85bc524cb36b86f78` |

执行脚本：
`datasets/llm/audit_cow160x4_session_aggregation_v0_1.py`

`execute` 必须提供独立 authority JSON。authority 必须点名 target，批准一次
gzip open/decompression，钉死运行时 script/contract hash，并逐项匹配全部
caps。结果文件一旦存在，后续 execute 必须在 source open 前拒绝。

## 冻结 caps

| Cap | 值 |
|---|---:|
| Wall time | `300 s` |
| Compressed source | `1,328,104,319 bytes` |
| Decompressed bytes returned | `33,554,432` |
| JSONL lines | `4,096` |
| Per-line bytes | `262,144` |
| Object keys | `256` |
| JSON depth | `4` |
| Session UTF-8 bytes | `256` |
| Scalar string UTF-8 bytes | `16,384` |
| Notice-envelope records | `16` |
| JSON/Markdown result | each `262,144 bytes` |

不允许 extract、持久化 decompressed content、自动 retry 或 resume。

## Privacy / notice / schema

- `session` 只可在内存中用于 opaque uniqueness 与 digest，不得持久化或进入
  模型。
- `src_ip`、`honeypot_ip`、timestamps、event counts 均不得持久化、进入模型
  或定义 lineage/split。
- credential、command、URL、filename、fingerprint、geolocation、payload、
  raw message、label 与 ground truth 均为禁止输出。
- 结果只能记录 sensitive-key aggregate count；不得记录 raw key/value。
- gzip 没有 ZIP central directory，也不假定存在独立 notice member。
- record-scope CC-BY-4.0 不自动关闭 nested/third-party rights。
- bounded probe 无法关闭 nested-notice 或完整 privacy Gate。
- schema 只检查 bounded prefix 的 UTF-8、JSON object、required field、深度与
  尺寸；不是全数据集验证。

## Manifest / lineage

候选 group key 是 curator 声明的 `session`。脚本只在内存中计算其 exact
UTF-8 SHA-256，并只输出 unique/duplicate aggregate counts。

看到至少 4 个非空 session 只能证明 bounded prefix 中存在候选组，不能证明：

- 全局 unique session 数；
- one-session-to-one-record；
- duplicate/reconnect/retry/campaign policy；
- statistical independence；
- source role 或 lineage credit。

host、configuration、country、day、file、event type、attack class 与 verdict
均不得替代 run/session lineage。Cowrie emulated response 不得表述为真实 OS
execution 或 host state。

## Pointer

候选 shape 固定为：

```text
artifact_md5
+ one-based decompressed record ordinal
+ SHA-256(exact UTF-8 session bytes)
```

只允许输出 aggregate pointer digest。不得输出 raw session、local path 或
per-record pointer。gzip 没有随机访问能力，bounded in-memory canonical
round trip 不等于 source round trip；所有候选必须保持 `binding_status=unbound`。

## 结果解释

即使 bounded probe 没有 schema/privacy 失败，最高状态仍是
`bounded_probe_hold_nested_notice_and_full_lineage_unclosed`。它不授予：

- effective catalog 或 source role；
- family/lineage/sample/quota credit；
- pointer binding；
- train admission；
- L2 Gate。

family、lineage、sample、quota credit 固定为 `0 / 0 / 0 / 0`。

## 硬停

当前没有 execution-authority JSON，也没有运行 `plan` 或 `execute`。下一步必须
由新的显式授权点名 `cow160x4_session_aggregation_jsonl_gz`；不得自动解压或
进入 source-role review。
