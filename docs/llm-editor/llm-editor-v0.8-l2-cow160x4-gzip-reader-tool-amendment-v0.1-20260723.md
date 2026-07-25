# COW160x4 gzip reader/tool amendment v0.1

日期：2026-07-23
Authority base：`afc50ae17be632b78146df3ab2f08b95fe6bc690`
状态：`reader_and_parser_identity_frozen_audit_not_authorized`

## Reader identity

现有本地 reader 固定为 CPython `3.11.15` 标准库
`gzip/json/hashlib`，zlib compile/runtime 版本均为 `1.3.2`。本阶段没有安装
或下载任何 reader。

| Component | Bytes | SHA-256 |
|---|---:|---|
| venv Python executable | `45,568` | `0cf37e7be6ee71edef78e6c81f7dcef58237b204af36d6e83393c96538a52372` |
| base Python executable | `91,648` | `ae7e969410d751d010c2ca03394fe5c53230fbf48ca7d368b897e455eca14fba` |
| `python311.dll` | `5,842,944` | `e1b53c741751563eca9eac70378de5be36994adac8c27e8ec375971579e23b50` |
| stdlib `gzip.py` | `24,074` | `8e0a7f850ef481fea41e0de9b52b4a014573b58e500ae83b92e5888d7a061008` |
| stdlib `json/__init__.py` | `14,020` | `d5d41e2c29049515d295d81a6d40b4890fbec8d8482cfb401630f8ef2f77e4d5` |
| stdlib `hashlib.py` | `11,765` | `e2bffb462e4d43e6637b9450e259e8ba2a56626ba3037d68aa1cee68b3f61d4a` |

路径在机器合同中使用 `%LOCALAPPDATA%` 与 `%APPDATA%` 模板，不提交用户名。
任一版本、路径、bytes 或 hash 漂移都必须在接触 source 前 fail closed。

## Parser identity

- Script：`datasets/llm/audit_cow160x4_session_aggregation_v0_1.py`
- Bytes：`25,953`
- SHA-256：`a2157bdce0fb939aee2898ef0c4f14e33b8df98fd115cfabdb6831e37836bcb6`
- Syntax：通过
- Target stat/open/decompress：未发生

`plan` 模式只核验 reader identity，不 stat 或打开 gzip；本阶段未执行该模式。
`execute` 必须同时给出单独的 authority JSON，并由 authority 钉死运行时 script
和 audit-contract SHA-256、target ID 与全部 caps。若结果文件已存在，
`execute` 必须在 source open 前拒绝。

## I/O boundary

执行器仅允许未来在独立授权下进行 bounded streaming。它不得 extract，不得
持久化 decompressed content、raw line/key/value、session identifier 或本地
payload 路径。成功和失败结果都只能包含 aggregate counts、hashes、reason
codes 与 boolean Gate。

本阶段没有打开 gzip、读取 header/trailer、解压、读取 JSONL，也没有运行
privacy、notice、schema、manifest、lineage 或 pointer probe。

## 权限结论

- Reader/parser identity：已冻结
- Audit execution：未授权
- gzip open/decompress：未授权
- source role / catalog / credit：未改变，credit 全部为 0
- baseline / fine-tuning / L2：未启动、未通过
- commit / push：未授权

下一步仅为依据该 reader/parser identity 冻结审计合同；合同冻结后仍需新的
独立执行授权。
