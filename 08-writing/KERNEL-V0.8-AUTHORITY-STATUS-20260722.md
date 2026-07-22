# Kernel v0.8 Authority Status

## Current A16 remediation authority snapshot

```text
Branch: feat/kernel-v0.8
Working state: uncommitted A16 remediation supplement
Regression: 131/131 PASS
A16 decision: NOT PASSED / NO-GO (unchanged)
Push / PR: NOT AUTHORIZED
Part B: CLOSED
CERTIFIED_STOP authority: NOT ESTABLISHED
```

Engineering remediation is complete for the second non-isomorphic Gamma,
model-relative formal ceiling, complete-world P6 recertification,
ceiling-bound P9 coverage, SI-003/006/007/008 dispositions, and the historical
15-commit/81-file review record. These facts prepare a new A16 re-review; they
do not change the existing human NO-GO ruling.

SI-010 is closed by the user's explicit exact-hash approval. The approved
artifact is `configs/admission-policy-kernel-v0.8.yaml` with canonical hash
`sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671`.
The APPROVED manifest hash is
`sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b`.
Gamma/fixture/ceiling references have been regenerated. This authority change
does not alter the existing A16 NO-GO, push/PR prohibition, Part B closure, or
the requirement for a separate level-complete certificate.

**状态日期：** 2026-07-22
**适用轨道：** Part A Counterexample Kernel only
**分支：** `feat/kernel-v0.8`
**本地 HEAD：** `c3173ae`
**实现状态：** `PART_A_IMPLEMENTED_A16_NOT_PASSED`
**A16 主门禁：** `NOT_PASSED` / `NO-GO`（2026-07-22 人工裁定）
**远端状态：** Push **不允许**；PR **不允许**；未 push；未创建 PR

## 1. 本文件的 authority 边界

本文件是 Kernel v0.8 轨道的当前状态入口。它记录用户已经逐项授予并完成的
P0–P11 实施权限，以及仍未授予的后续权限。它是描述性状态记录，不修改
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
- P11：P5 observation 到 Claim IR 的显式适配、P7 evaluate 与可选 P8 admit
  接入 E2E；不改变 modality，不取得 STOP 或 level-certificate 权限。

这些授权已经消耗完毕，不自动续展为重写 P0–P10 语义、增加算法或进入下一阶段
的权限。

用户随后于 2026-07-22 明确追加并消耗一个收口债务修复授权：FW-016 拆码、
Twin 从 case evidence/Γ 重算有限域约束，以及 catalog-bound predicate
projection 合同。该授权只覆盖上述三项，不续展为新的 Checker、Planner、M3*、
Part B、LLM 或训练权限。实现证据追加在 Part A 收口纪要第 6 节。

## 3. 当前允许与禁止

### 当前允许

- 对 P0–P11 做只读复核与自动回归；
- 记录 A16 裁定、限制与复审清单等非规范性状态文档；
- 在用户**另行授权某一补洞切片**后，才开始对应编码。

### 未授权

- 把 A16 解释为 Go，或宣布正式 `CERTIFIED_STOP` / level certification；
- Part B、随机 observation、机会约束或广域连接器；
- Planner/M3* 策略、训练、LLM 运行时或 `09-experiments` 改动；
- 未经授权启动 SI-010 / ceiling / 第二 Twin 等补洞实现；
- 修改 Γ/hash/action catalog/fixture expected 或 P0–P11 语义（除非补洞切片明确授权）；
- push、PR、merge 或 release。

## 4. A16 状态（人工裁定已落地）

用户于 2026-07-22 作出明确人工裁定：**先停着；A16 没过。**

```text
Decision: 先停着
Push: NO
PR: NO
A16: NOT PASSED / NO-GO
Part B: CLOSED
CERTIFIED_STOP authority: NOT ESTABLISHED
```

工程实现（P0–P11）与 `113/113` 自动回归仍然成立，但评审裁定认定：自动证据
不能证明真实形式 ceiling、外部有效性或正式 policy authority，也不能等同于
A16 条件全部满足。

**原 A16 裁定要求的复审材料（保留作审计历史）：**

1. 冻结并批准 admission-policy artifact 与真实绑定 hash，关闭 SI-010；
2. 补足真实形式 ceiling 的可审证据（定义、域、证明/测试边界、域外 fail-closed）；
3. 关闭单一 Twin / narrow compiler 的“玩具 Γ”外推问题（第二非平凡 Γ/fixture
   **或** 明确收窄声明范围并删除过度通用表述）；
4. 完成 15 提交、81 文件的人工 diff 审阅并留下逐项结论；
5. 对 SI-003、SI-006、SI-007、SI-008 分别作正式裁定
   （本轮修复 / 明确延期且不影响 A16 / 构成阻塞）；
6. 重新生成评审包并复跑完整测试矩阵。

截至当前 supplement，上述 1–5 项已有工程证据，最终完整矩阵与评审包在批准
policy 绑定后重放；这些材料仍须新的人工 A16 复审接受。在新的明确 Go 裁定前：
**禁止推进 Part B，禁止 push/PR，禁止把工程完成解释为 A16 Go。**

其他仍保留的 spec issues 见 `src/scope/kernel-v0.8-spec-issues.md`。这些 issue
不得通过本状态文件静默关闭。

## 5. 可审计入口

| 用途 | 当前入口 |
|---|---|
| 规范 | `08-writing/active-attribution-experiment-revision-plan-v0.8-20260721.md` |
| 实施收口 | `04-progress/kernel-v0.8-part-a-closeout-20260722.md` |
| A16 评审包 | `08-writing/kernel-v0.8-a16-review-package-20260722.md` |
| Spec issues | `src/scope/kernel-v0.8-spec-issues.md` |
| Γ hash 合同 | `contracts/gamma-hash-v0.8.md` |
| Twin fixture | `tests/fixtures/TWIN-COUNTEREXAMPLE-001/` |
| P10 driver | `src/cli/kernel_e2e.py` |
| P10 integration test | `tests/integration/test_twin_kernel_e2e_p10.py` |
| P11 adapter | `src/ir/observation_claim.py` |
| P11 integration test | `tests/integration/test_twin_firewall_admit_driver_p11.py` |

本状态记录以本节人工裁定为准。push、PR 与 A16 Go 分别是独立决定；其中
任何一个都不能由另一个默示产生。当前三者均为 **不允许 / 没过**。

## 6. 收口债务修复状态

```text
FW reason-code collision: SPLIT (FW-016 context / FW-017 kind)
Twin finite constraints: COMPILED FROM GAMMA + ADMITTED CASE EVIDENCE
Predicate projection: CALLER-SUPPLIED ACTION BINDING, CATALOG-RESOLVED
Regression after P11: 113/113 PASS
Human A16 ruling: NOT PASSED / NO-GO (2026-07-22)
```

该债务修复状态不修改冻结 v0.8 规范字节，也不签发 level certificate。SI-010
随后已由用户对精确 policy hash 的独立批准关闭；该关闭不追溯地产生 STOP 权威。

## 7. P11 Firewall/admit 接线状态

P11 已在本地提交 `5e9c0ba` 完成。生产适配器只从本次 P5 实际输出、冻结
action catalog 和显式调用方上下文构造 Claim IR；`pointer.record_id` 绑定
`observation_id`，`modality` 固定保持 `observed`，oracle/hidden、未知 action、
缺失 pointer 行和未实际执行的 observation ID 均 fail closed。

Twin 默认可执行路径中的 OBS-001/002 经 Firewall 为 allow，启用 P8 时可 admit；
OBS-003/004 在同一生产适配器的冻结行合同测试中分别因 control/heuristic 被
deny。P11 仍沿既有 feedback/Recert/SystemState 路径，单 hit 结果为
`CANDIDATE_CERTIFIED + CONTINUE`，不签发 level certificate，也不产生
`CERTIFIED_STOP`。

P11 工程接线不改变 2026-07-22 的 A16 **NOT PASSED / NO-GO** 裁定。
