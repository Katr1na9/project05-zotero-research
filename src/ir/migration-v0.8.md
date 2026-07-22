# Kernel Claim IR v0.8 migration note

## Boundary

`claim-ir-kernel.schema.json` is a new Kernel contract. It does not replace the
legacy `evidence_claim.schema.json` or `acquisition_action.schema.json` in
place. Consumers must select a schema explicitly by version.

The LLM compiler may return only the Candidate Compiler response profile. The
trusted Kernel boundary owns `claim_id`, `pointer`, modality, truth status,
epistemic role, authority, admission, promotion, confidence, rule trace and
lifecycle state. The request may contain a Kernel-supplied pointer as source
context, but the compiler response may neither copy nor manufacture it.

## Required migration behavior

- 旧 Claim/Action 数据不得静默适配；必须由显式、可测试且带版本的 adapter 转换。
- Adapter must preserve the legacy source pointer or fail closed. It must not
  invent a pointer, convert `reported`/`derived` to `observed`, or grant
  certification authority.
- Legacy scalar action `cost` is not a Kernel action field. Feasibility and
  measured resources are migrated into separate records only when their
  provenance is available.
- Any compiler response containing Kernel-owned or hidden/oracle fields is
  rejected with the stable `CKI-*` interface errors.

No adapter implementation is part of P0; this note freezes the required
migration boundary for later authorized work.
