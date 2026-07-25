# Opaque Claim-ID minting design（draft）

状态：`design_only_minting_not_authorized`。唯一 surface 是
`project05_depth2_public`；本文件不实现、不执行 minting，也不创建
HMAC key。

## Pins

- Projection SHA：`4784ff3a29f2c3cb8d04bc187b1f2cd1d95b9ead51c3ad0d7c4da30f4cd557e8`
- Schema SHA：`5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e`
- Compiler SHA：`a132dd140ab13e3fe762f169b8799b4e35886ecf8ea07271e8482a1046c14de1`
- M0 disposition SHA：`03a6014177960b51e25e1c18acaef334bfd48f0015995b5637006666e6d4c60f`
- Base commit：`c0dc780f12af9a1c0e019cf0d9bf032983ce8ab0`

## Algorithm

未来若另有 execute authority，使用 authority-bound HMAC-SHA-256：

`clm_` + 无 padding 的 base64url(full 256-bit digest)

规范化消息只包含：

`claim-id-mint-v0.1 | surface_id | allowlisted_source_slot | opaque_case_reference | within_package_ordinal`

`allowlisted_source_slot` 是 schema 控制的不透明槽位，不是文件系统路径或 archive member path。算法永远不读取或派生自 labels、outcomes、raw paths、payload bytes、oracle、mask membership、hidden/recoverable IDs、credentials 或 secrets。key 只由未来 authority 在外部提供，仓库和日志均不保存 key material。

## 状态迁移

当前 package/per-claim 均为：

`not_minted / not_admitted / pending_kernel_schema`

未来一次性 authority 成功执行后，仅允许：

`not_minted → minted_opaque`

`admission_state` 仍为 `not_admitted`，`kernel_state` 仍为
`pending_kernel_schema`。opaque ID 不授 source role、lineage、quota、credit、
certificate 或 L2。

## Fixture specs

仅规格，不创建、不实现、不运行：

- `mint_valid_public_projection`
- `mint_antileak_labels_outcomes`
- `mint_antileak_paths_payloads`
- `mint_antileak_oracle_hidden_mask`

所有 anti-leak 规格预期 fail-closed、零 ID、无 package 输出。

裁断上限：
`approve_for_separate_metadata_candidate_review_not_source_role`。
