# SI-LLM-001：共享 Claim IR schema 工件缺失

**Owner**：Kernel/M3* 会话  
**LLM 轨道状态**：阻塞 shared compatibility 声明，不阻塞本地 safety guard

## 当前字段

v0.8 规格定义了 Claim IR 最小字段和不变量，并指定共享文件 `schemas/claim-ir-kernel.schema.json`，但当前分支没有 `schemas/` 目录、JSON Schema、schema id/version/hash 或可导入公共类型。

## 阻塞案例

LLM 可构造包含 `modality`、`truth_status`、`certification_authority`、`binding_status`、`admission_status` 与 `promotion_status` 的候选 dict，但无法证明它通过 Kernel 实际消费的 schema。旧 `candidate_claim_envelope.schema.json` 缺少上述字段，不能替代。

## 建议变更

由 Kernel 会话发布：

1. `schemas/claim-ir-kernel.schema.json`；
2. 稳定 `$id`、schema version 与 hash；
3. canonical predicate/entity type 的引用方式；
4. candidate-only 输出必填/只读/禁止字段；
5. 一个最小 valid candidate fixture 与 authority-leak invalid fixture。

## 兼容性影响

旧 CandidateClaimEnvelope 只能作为 legacy 输入，必须通过显式 converter；不能做字段别名或原地升级。共享 schema 发布前，本轨道输出标记 `pending_kernel_schema`。

## 对认证安全的影响

高。没有共享 schema 时，authority、modality 或 lifecycle 字段可能被不同实现解释为可认证状态，形成 silent promotion。不得在该 issue 关闭前把 LLM 输出写入 Kernel 或 E_case。
