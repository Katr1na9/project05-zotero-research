# St.Gallen dual-surface reader/tool amendment v0.1

日期：2026-07-24

Authority base：`c9ddf09`

状态：`dual_reader_and_parser_identity_frozen_audit_not_authorized`

## 冻结结论

已冻结一个现有 CPython runtime 和两个严格隔离的 reader mode：

| Surface | Reader mode | 本轮执行 |
|---|---|---|
| Protected manifest | bounded full binary read → strict UTF-8 → in-memory JSON | 否 |
| Sensor telemetry | bounded binary `readline` → strict UTF-8 → per-line in-memory JSON | 否 |

Protected manifest 永不进入模型可见面。Sensor 也必须在后续 field isolation 和 source-role review 前保持不可见。

## Reader identity

| Component | Bytes | SHA-256 |
|---|---:|---|
| venv `python.exe` | 45,568 | `0cf37e7be6ee71edef78e6c81f7dcef58237b204af36d6e83393c96538a52372` |
| base `python.exe` | 91,648 | `ae7e969410d751d010c2ca03394fe5c53230fbf48ca7d368b897e455eca14fba` |
| `python311.dll` | 5,842,944 | `e1b53c741751563eca9eac70378de5be36994adac8c27e8ec375971579e23b50` |
| stdlib `json` | 14,020 | `d5d41e2c29049515d295d81a6d40b4890fbec8d8482cfb401630f8ef2f77e4d5` |
| stdlib `hashlib` | 11,765 | `e2bffb462e4d43e6637b9450e259e8ba2a56626ba3037d68aa1cee68b3f61d4a` |
| stdlib `re` | 15,889 | `029ead61f362489e9bb034f4c2503abee95462056541e9ad07715de3c353b0da` |

Python version：

`3.11.15 (main, Jun 23 2026, 15:20:37) [MSC v.1944 64 bit (AMD64)]`

任一 runtime path、size、SHA 或 version 不匹配，都必须在 stat/open 任一 surface 前 fail closed。

## Dormant parser

路径：

`datasets/llm/audit_stgallen_smart_factory_dual_surface_v0_1.py`

Identity：

- bytes：`56,500`
- SHA-256：`0291dc15193a5f6fe6d4d06b64d066bc6b98ac3bc2f4ad95227beefe6881e382`
- AST parse：通过
- plan mode：未执行
- execute mode：未执行
- 两份 surface：未由该 parser stat/open/read/parse

未来 execute 必须由独立 authority JSON 同时点名两个 target，并精确钉住 script、contract、reader 与全部 caps。结果文件若已存在，execute-once Gate 必须拒绝。

## 数据隔离

- Manifest 的 raw key/value、process-instance ID、时间戳和 JSON pointer 不落盘；
- manifest ID 只能在内存中变成 domain-separated SHA-256；
- sensor 按行流式读取，不把全文件加载到内存；
- sensor raw line/key/value/timestamp/byte offset/ordinal/pointer 不落盘；
- 只允许输出 aggregate counts、aggregate digests、boolean Gates 和脱敏 reason code；
- protected GT 不得进入 model input、prompt、target、candidate pointer suggestion 或监督。

## 当前权限

| 项 | 状态 |
|---|---|
| Reader/parser identity | 已冻结 |
| Reader/parser execution | 未授权 |
| Surface stat/open/read/parse | 未授权 |
| Audit authority JSON | 未创建 |
| Privacy/notice/schema/GT-exclusion/manifest/lineage/binding/pointer probe | 未执行 |
| Catalog / role / credit / L2 | 未改变，credit 全为 `0` |
| Commit / push 本轮工件 | 未执行 |
