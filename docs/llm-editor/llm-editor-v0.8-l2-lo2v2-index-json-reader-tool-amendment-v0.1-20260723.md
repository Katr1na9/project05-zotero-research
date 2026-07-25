# LO2v2 index JSON reader/tool amendment v0.1

日期：2026-07-23  
Authority base：`602be47262c387aa0f6c0f2459e9e7e5af2d6492`  
状态：`reader_and_parser_identity_frozen_audit_not_authorized`

## 冻结 reader

| 项 | 值 |
|---|---|
| Reader | CPython standard-library `json/hashlib/re` |
| Python | `3.11.15`，64-bit Windows |
| Parser | `datasets/llm/audit_lo2v2_index_v0_1.py` |
| Parser bytes | `30,574` |
| Parser SHA-256 | `170a2d115e35c080ca3c64d4d01356a0046db5603d86f42d3b04335b288a8c85` |
| Syntax AST parse | 通过 |
| Plan / execute run | 均未运行 |
| Target stat/open/read | 均为否 |

reader 的 venv executable、base executable、`python311.dll`、stdlib
`json`、`hashlib` 与 `re` 模块均已冻结 exact path template、bytes 与
SHA-256。任一身份不匹配，future execution 必须在 source stat/open 前
fail closed。

## 两种 invocation

Plan：

```text
python datasets/llm/audit_lo2v2_index_v0_1.py --mode plan
```

Plan 只允许验证 reader identity，不得 stat/open target。本轮没有执行 plan。

Execute：

```text
python datasets/llm/audit_lo2v2_index_v0_1.py --mode execute --authority-json <separately-authorized-json>
```

Execute 必须有新的 authority JSON，精确点名 `lo2v2_index_json`，绑定
script/contract SHA-256，并逐项匹配全部 caps。result 已存在时禁止第二次执行。

## Reader 行为

- 先重验 target exact size 与 MD5，再允许 decode/parse；
- JSON 只允许在内存中读取；
- 不 extract、不转换或持久化 raw JSON；
- 不持久化 raw key/value、run/test identity、path、timestamp 或 pointer；
- 只允许 aggregate counts、digests、boolean Gates 与非敏感 failure code；
- terminal failure 不得自动 retry。

## 当前权限

- JSON open/read/parse：未授权；
- audit execution：未授权；
- catalog、source role、train admission：未授权；
- family/lineage/sample/quota credit：`0 / 0 / 0 / 0`；
- L2 Gate：`false`；
- commit/push：未授权。
