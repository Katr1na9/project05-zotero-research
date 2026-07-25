# `source_field` → `allowlisted_source_slot` mapping（draft）

状态：`design_only_mapping_not_implemented`。唯一 surface 是
`project05_depth2_public`。本设计不实现或执行 minting，不创建
HMAC key，不创建 fixture。

## 固定映射

已按 pinned schema 的 `source_field` enum 顺序建立 38→38 的 total
bijection。每个字段恰有一个 slot，每个 slot 恰对应一个字段：

`config.case_id → afs_0001`  
`config.budget_total → afs_0002`  
…  
`action.natural_language_request → afs_0038`

完整 38 项映射在同名 JSON 中；槽位 token 统一为：

`^afs_[0-9]{4}$`

长度固定 8，只有 lowercase ASCII、数字和下划线；不含点、斜杠、反斜杠、
filesystem/member/raw path 或语义字段名。

HMAC canonical tuple 使用 slot token，不使用 source-field 文本、文件路径、
archive member path 或 payload bytes。

## Fail-closed

unknown source field、无映射字段、重复 source field、重复 slot、ordinal gap
或 token 格式不符时一律 reject；不得回退到原始字段名、ordinal 或临时生成 token。

本映射不授权 Claim-ID mint、admission、Kernel ingestion、certificate、
catalog、source role、lineage/quota/credit、L2、M1/M2。未创建代码、fixture、
secret，未 commit/push。
