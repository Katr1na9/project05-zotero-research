# M0 structural completion disposition（draft）

状态：`draft_disposition_not_effective`。本文件只记录
`project05_depth2_public` 的结构性编译完成度，不改变任何 Gate。

## 已完成

- schema：`schemas/claim-ir-kernel.schema.json`
  - SHA-256：`5bffd7e2cf0da224422ea0d8679c18ffeed4bbc0546bbfcd92c3137fce73419e`
- compiler：`src/compiler/llm/m0_rule_compiler.py`
  - SHA-256：`a132dd140ab13e3fe762f169b8799b4e35886ecf8ea07271e8482a1046c14de1`
- 绑定 commit：`7d67898472bb616b29a1954f1ccb8e84548c9157`
- 1 个 valid fixture 通过，4 个 authority-leak fixture 全部
  `forbidden_field` 拒绝。
- valid package：41 claims，`claim_id=null`，状态为
  `not_minted / not_admitted / pending_kernel_schema`。
- Draft 2020-12 校验：0 errors；M0 compiler tests 4/4；
  schema validation test 1/1。

## 仍阻塞

- Claim-ID minting：未授权。
- Kernel / E_case / certificate：未授权；certificate surface 仍为 vacant。
- admission、source role、catalog、lineage/quota/credit、L2：未授权。
- M1/M2 实现：未授权。

`pending_kernel_schema` 只是阻塞状态值，不是 Kernel ingestion 或科学有效性批准。

裁断上限：
`approve_for_separate_metadata_candidate_review_not_source_role`。

本轮未改代码、schema 或 fixtures，未 commit、未 push。
