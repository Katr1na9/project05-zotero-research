# LO2v2 index JSON reader + bounded audit contract v0.1

日期：2026-07-23  
Authority base：`602be47262c387aa0f6c0f2459e9e7e5af2d6492`  
状态：`frozen_contract_only_audit_execution_not_authorized`

## 冻结范围

本合同只针对已通过 exact size + MD5 的 `lo2v2_index_json`，冻结：

- JSON reader identity；
- privacy / identifier probe；
- nested notice probe；
- syntax / structural schema probe；
- 115-run manifest candidate probe；
- lineage 与 repeated-system nuisance 边界；
- protected label 与 LO2v1 initialization-leak probe；
- v1/v2 overlap 准备；
- hashed pointer-candidate probe。

本轮没有 stat/open/read/parse target，也没有运行 plan 或 execute。

## Reader 与 parser

| 项 | 冻结值 |
|---|---|
| Reader | CPython stdlib `json/hashlib/re` |
| Python | `3.11.15` |
| Reader amendment SHA-256 | `725baaf4580fb11496d73a4b9b4ce6b35d414928a85dfb8f87841a5249ea76f8` |
| Audit script | `datasets/llm/audit_lo2v2_index_v0_1.py` |
| Script bytes | `30,574` |
| Script SHA-256 | `170a2d115e35c080ca3c64d4d01356a0046db5603d86f42d3b04335b288a8c85` |
| Syntax AST parse | 通过 |
| Script executed | 否 |

## Execution Gate

future execute 必须有新的 authority JSON：

- `status=authorized_once`；
- 精确点名 `lo2v2_index_json`；
- 明确授权 JSON open/read/parse 以及 label、v1/v2 digest preparation、pointer probe；
- 绑定 runtime script 与 contract SHA-256；
- 全部 caps 字节级匹配；
- `automatic_retry=false`、`resume=false`；
- result JSON/Markdown 尚不存在。

任何缺失或 hash/cap 不匹配必须在 source stat/open 前 fail closed。

## Caps

| Cap | 值 |
|---|---:|
| Wall time | 300 seconds |
| Exact input bytes | 31,028,530 |
| JSON depth | 32 |
| Total nodes | 2,000,000 |
| Keys per object | 4,096 |
| Items per array | 200,000 |
| UTF-8 bytes per scalar string | 262,144 |
| Run candidates | 4,096 |
| Result bytes per file | 262,144 |
| Execute count | 1 |

目标只在内存中解析；禁止 extract、transform、raw JSON persistence，以及 raw key/value/run/test/path/pointer persistence。

## Label 与 privacy

label scan 预注册 `correct/error/failure/anomaly/expected/response/outcome/status/label/ground_truth/task/test` 等 token。

privacy/identifier scan 预注册 credential、authorization、secret、token、username、header、URL、IP、host、container、service、path、file、trace 等 token。

扫描只允许输出 aggregate counts。任何匹配都 fail closed；零匹配也不能单独证明不存在语义标签或敏感信息。

LO2v1 官方说明中的 initialization-row correctness leak 默认仍未修复。bounded token scan 不能自动关闭该 Gate。

## Manifest 与 lineage

source-native run candidate 只接受：

`^LO2_run_[0-9]{9,}$`

raw run ID 只在内存中转换为 SHA-256；输出只允许 unique count 与一个 aggregate digest。

未来 probe 可核：

- unique candidate 是否为 115；
- occurrence/location 是否重复；
- 是否检测到与每个 run 相关的 54-item test container。

但这些结果不证明 completed execution、duplicate/retry、system reset、seed、cache、image、host、temporal nuisance 或统计独立性。Family/lineage/sample/quota credit 始终为 `0`。

## v1/v2 overlap

本合同没有 v1 payload、index 或 run-digest set，也不授权下载或打开 v1。

future audit 最多输出一个 v2 run-digest-set aggregate SHA-256，供未来另行授权的比较使用。没有 v1 comparison 时，`v1_v2_overlap_gate=false`，不得把“未比较”写成“不重叠”。

## Pointer

candidate shape：

```text
artifact_md5
+ run_id_sha256
+ json_pointer_sha256
```

raw JSON pointer、run ID、local path 和 per-run candidate 均不得持久化。内存 canonical round trip 即使通过，也不等于 runtime log/metric/trace binding；`binding_status` 始终保持 `unbound`。

## Notice 与 schema

record-scope `CC-BY-4.0` 不自动关闭 embedded/nested rights；code 的 `Apache-2.0` 也不能替代 dataset 或第三方内容权利。

JSON syntax parse 可检查 root type、aggregate node/collection counts、hashed schema signatures 与 list-length cardinalities，但不能自动关闭 semantic schema、source role 或 training Gate。

## 结果解释

允许的 terminal status 包括：

- `fail_closed_protected_label_surface_detected`
- `fail_closed_privacy_or_identifier_surface_detected`
- `hold_manifest_run_count_unclosed`
- `bounded_probe_hold_notice_lineage_v1_v2_and_pointer_unclosed`
- `failed_closed_terminal_no_automatic_retry`

任何 bounded pass 都不等于：

- source role；
- lineage independence；
- label isolation；
- v1/v2 disjointness；
- pointer binding；
- train data；
- L2 Gate。

## 当前权限

- target stat/open/read/parse：未授权；
- plan/execute：未运行；
- audit execution authority：未创建；
- catalog/source role/train admission：未授权；
- family/lineage/sample/quota credit：`0 / 0 / 0 / 0`；
- baseline/fine-tuning：未授权；
- commit/push：未授权。

下一步：硬停。只有新的显式授权和独立 execution-authority JSON 才可执行一次 bounded audit。
