# Kernel v0.8 Authority Status

**状态日期：** 2026-07-22
**适用轨道：** Part A Counterexample Kernel only
**分支：** `feat/kernel-v0.8`
**本地 HEAD：** `93af889`
**实现状态：** `PART_A_IMPLEMENTED_PENDING_A16_REVIEW`
**A16 主门禁：** `PENDING_HUMAN_REVIEW`（按 `NO-GO` 执行）
**远端状态：** 未 push；未创建 PR；当前没有远端分支包含 `93af889`

## 1. 本文件的 authority 边界

本文件是 Kernel v0.8 轨道的当前状态入口。它记录用户已经逐项授予并完成的
P0–P10 实施权限，以及仍未授予的后续权限。它是描述性状态记录，不修改
`active-attribution-experiment-revision-plan-v0.8-20260721.md` 的规范语义，
也不替代新的用户授权。

冲突时按以下优先级处理：

1. 用户对具体切片的最新明确裁定；
2. v0.8 Kernel Implementation Specification；
3. 已批准的 `contracts/gamma-hash-v0.8.md`；
4. 冻结 Schema、Γ、action catalog 与 Twin fixture；
5. 本状态记录与收口纪要。

7 月 15 日的 `AUTHORITATIVE-DOCUMENTS-20260715.md` 继续作为当日全项目写作与
实验快照保留；本文件只新增 Kernel v0.8 轨道状态，不追溯改写该历史快照。

## 2. 已消耗并完成的授权

用户已按人工门禁逐次授权并完成：

- P0：schemas、configs、Twin fixture、Candidate Claim IR 合同；
- P1–P3：有限域 Checker、MinDiff、counterexample artifact；
- P4–P6：可区分动作选型、确定性执行、世界消元与再认证；
- P7–P8：Epistemic Firewall admission、Promote/Revoke 审计生命周期；
- P9：唯一系统状态推导与 level-complete certificate gate；
- P10：不增加新算法的确定性 Twin E2E driver。

这些授权已经消耗完毕，不自动续展为重写 P0–P9 语义、增加算法或进入下一阶段
的权限。

## 3. 当前允许与禁止

### 当前允许

- 对 P0–P10 做只读复核与自动回归；
- 修正文档中的状态、链接和非规范性实施记录；
- 准备供人工审阅的 diff、测试清单和 PR 文案草案。

### 未授权

- 宣布 A16 Go；
- Part B、随机 observation、机会约束或广域连接器；
- Planner/M3* 策略、训练、LLM 运行时或 `09-experiments` 改动；
- 修改 Γ/hash/action catalog/fixture expected 或 P0–P9 语义；
- 由 driver、LLM、M3*、概率阈值或人工判断直接发
  `CERTIFIED_STOP`；
- push、PR、merge 或 release，除非用户明确选择该外部动作。

## 4. A16 状态

P0–P10 的实现和自动测试为 A16 评审提供了工程证据，但没有替代 A16 裁定。
当前权威状态是：

```text
Part A implementation: COMPLETE
A16 review package: READY FOR HUMAN REVIEW
A16 decision: PENDING
Operational interpretation: NO-GO
Part B authority: CLOSED
```

特别是 SI-010 仍明确禁止使用 fixture 的 policy-hash 占位进行正式认证。
在实际 policy artifact、真实 hash 与所有绑定引用冻结前，不得把 Twin schema
通过写成正式 level certification。

其他仍保留的 spec issues 见 `src/scope/kernel-v0.8-spec-issues.md`。这些 issue
不得通过本状态文件静默关闭。

## 5. 可审计入口

| 用途 | 当前入口 |
|---|---|
| 规范 | `08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md` |
| 实施收口 | `04-progress/kernel-v0.8-part-a-closeout-20260722.md` |
| Spec issues | `src/scope/kernel-v0.8-spec-issues.md` |
| Γ hash 合同 | `contracts/gamma-hash-v0.8.md` |
| Twin fixture | `tests/fixtures/TWIN-COUNTEREXAMPLE-001/` |
| P10 driver | `src/cli/kernel_e2e.py` |
| P10 integration test | `tests/integration/test_twin_kernel_e2e_p10.py` |

本状态记录完成后应停在人工评审门禁。push、PR 与 A16 Go 分别是独立决定；其中
任何一个都不能由另一个默示产生。
