# Kernel v0.8 A16 人工评审包

## Re-review supplement status (2026-07-22, uncommitted)

This supplement addresses the NO-GO hard blocks but does not make the A16
decision. The current Git index contains exactly 70 Kernel/fixture/test/review
paths; forbidden LLM/training/Part B/`09-experiments` and local-junk scans
return zero staged matches. Current evidence:

| Required item | Current evidence | Re-review state |
|---|---|---|
| SI-010 policy authority | exact-hash APPROVED manifest, regenerated Γ/fixture/ceiling bindings, positive replay and negative tamper tests | **CLOSED; READY FOR RE-REVIEW** |
| single Twin / toy Gamma | structurally different three-world supply-chain Γ/fixture, A003/A004 admission, full Part A path | engineering evidence complete |
| formal ceiling | definition, schema, verifier, two frozen replay reports, outside-domain/resource/tamper fail-closed tests | engineering evidence complete |
| 81-file review | `kernel-v0.8-81-file-diff-audit-20260722.md`, including two findings and remediations | engineering record complete; human acceptance pending |
| SI-003/006/007/008 | authority/interface contracts plus explicit non-blocking scope exclusions | disposition recorded |
| full regression | `python -m unittest discover -s tests -p "test_*.py" -v` | `131/131 PASS` |

Material review findings were not waived: P6 previously treated two witnesses
as an exhaustive world table, and P9 trusted caller-declared coverage counts.
The current supplement fixes both and adds three-world and coverage-tamper
regressions. Frozen ceiling reports now replay exactly from Γ/compiler/catalog.

Current decision remains:

```text
A16: NOT PASSED / NO-GO
Push: NO
PR: NO
Part B: CLOSED
CERTIFIED_STOP authority: NOT ESTABLISHED
```

The user approved policy hash
`sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671`.
The APPROVED manifest hash is
`sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b`.
After final regression, the package is ready for a new human A16 ruling; no
status above changes until that separate ruling occurs.

**日期：** 2026-07-22
**分支：** `feat/kernel-v0.8`
**代码评审基线：** `d156b68`
**代码评审 tip：** `5e9c0ba`
**包状态：** `HUMAN_GATE_REVIEWED_NO_GO`（81 文件逐项 diff 审阅未完成）
**A16 decision：** `NOT PASSED`
**操作解释：** `NO-GO`
**Part B authority：** `CLOSED`
**Push / PR：** `NOT AUTHORIZED`

本文件最初只整理 A16 所需的 diff、测试证据和已知限制。用户于 2026-07-22
已完成人工裁定并维持 NO-GO；下文 §8 记录该裁定与复审前硬阻塞项。自动测试
通过不等于 A16 条件已全部满足。

## 1. 评审范围与复现入口

完整 Part A/P11 代码差异：

```text
git log --reverse --oneline d156b68..5e9c0ba
git diff --stat d156b68..5e9c0ba
git diff --name-status d156b68..5e9c0ba
```

当前统计为 15 个本地提交、81 个文件、12,069 行新增。所有 81 个文件相对于
基线均为新增路径；它们按审阅责任分组如下：

| 组 | 文件数 | 审阅重点 |
|---|---:|---|
| 状态/规范文档 | 3 | v0.8 规范、authority、Part A 收口是否互相一致 |
| `schemas/` | 5 | 有限域、Claim IR 字段分离、certificate/反例合同 |
| `configs/` | 2 | 冻结 Γ 与 action catalog；确定性 observation |
| `contracts/` | 2 | Γ hash canonicalization、predicate projection |
| `src/` | 23 | P1–P11 的 Checker、反例、动作、执行、Firewall、状态与 driver |
| `tests/` | 46 | Twin fixture、unit/integration 合同和负例 |
| **合计** | **81** | |

预裁定评审包及状态文档已在 `c3173ae` 收口；当前 working-tree 文档 delta
记录用户随后作出的人工 A16 决定。该文档 delta 不改变代码 tip；A16 decision
来自用户裁定，而不是来自测试、代码提交或文档提交本身。

## 2. 提交清单

| 切片 | 提交 | 内容 |
|---|---|---|
| P0 | `3b34f3e` | schemas、configs、Twin fixture、Candidate Claim IR 合同 |
| P0 rulings | `43ba22a` | Γ hash、promotion event、candidate/system 状态命名裁定 |
| P1 | `0e72757` | finite-domain Checker |
| P2 | `54174e3` | finite-witness MinDiff |
| P3 | `1ebbf91` | counterexample artifact assembler |
| P4 | `ede7b30` | distinguishing-action selection |
| P5 | `1bae135` | deterministic observation executor |
| P6 | `4da8d2a` | world elimination 与 recertification |
| P7 | `ee06f37` | epistemic Firewall admission |
| P8 | `5d678bf` | Promote/Revoke append-only audit lifecycle |
| P9 | `441c7c4` | system state 与 level-certificate gate |
| P10 | `93af889` | deterministic Kernel E2E driver |
| 状态收口 | `592f13f` | authority status 与 Part A closeout |
| 债务修复 | `d546b93` | FW 拆码、compiled Twin、predicate projection |
| P11 | `5e9c0ba` | observation→Claim IR、P7 evaluate、可选 P8 admit 接入 E2E |

## 3. P11 精确 diff 清单

P11 单提交为 9 个文件，1,033 行新增、80 行删除：

| 状态 | 路径 | 作用 |
|---|---|---|
| M | `src/cli/__init__.py` | 公开 P11 配置/审计元数据 API |
| M | `src/cli/kernel_e2e.py` | P5 后可选执行 adapter→P7→P8，不影响默认 P10 |
| A | `src/ir/observation_claim.py` | 显式、确定性 observation→Claim IR 适配器 |
| M | `tests/integration/test_twin_epistemic_firewall_admission_p7.py` | 移除测试侧 action-ID 猜测 helper |
| A | `tests/integration/test_twin_firewall_admit_driver_p11.py` | Twin P11 主合同与 fail-closed 测试 |
| M | `tests/integration/test_twin_kernel_e2e_p10.py` | 可选注入 P11 config，默认路径不变 |
| M | `tests/integration/test_twin_promote_revoke_audit_p8.py` | P8 改用生产适配器 |
| M | `tests/integration/twin_kernel_inputs.py` | 显式 Twin adapter/admission 测试上下文 |
| A | `tests/unit/test_observation_claim_adapter.py` | 适配、确定性、oracle/hidden 与 pointer 负例 |

P11 不修改 Γ、Γ hash、action catalog、fixture expected、Checker/MinDiff 语义、
Planner/M3*、Part B、LLM、训练或 `09-experiments`。

## 4. 测试矩阵

以下结果于 2026-07-22 在 `feat/kernel-v0.8 @ 5e9c0ba` 复跑：

| 层级 | 命令 | 结果 | 覆盖意义 |
|---|---|---:|---|
| P11 定向 | `python -m unittest tests.unit.test_observation_claim_adapter tests.integration.test_twin_firewall_admit_driver_p11 -v` | 8/8 | adapter、四条 Twin 决策、可选 admit、未执行 ID fail closed |
| P7/P8/P10 邻接 | `python -m unittest tests.integration.test_twin_epistemic_firewall_admission_p7 tests.integration.test_twin_promote_revoke_audit_p8 tests.integration.test_twin_kernel_e2e_p10 -v` | 8/8 | Firewall、审计生命周期与默认 P10 不回归 |
| Schema + fixture | `python -m unittest tests.unit.test_kernel_schemas tests.integration.test_twin_counterexample_fixture -v` | 13/13 | 五个 schema、Γ/catalog hash、fixture 与 authority 边界 |
| 全量 | `python -m unittest discover -s tests -p "test_*.py" -v` | 113/113 | P0–P11 全部 unit/integration |
| Python 编译 | `python -m compileall -q src tests` | passed | 语法/import 可编译 |
| 补丁格式 | `git diff --check`、`git diff --cached --check` | passed | 空白与补丁格式 |

该表是历史 P0–P11 快照。当前 supplement 已增加第二 Γ、形式 ceiling 与正式
policy authority；测试仍不证明外部有效性、持久化审计或 Part B 性能。

## 5. A16 条件证据映射

下表是证据索引，不是 Go 判定：

| A16 条件 | 当前自动证据 | 评审状态 |
|---|---|---|
| Schema 校验 | `test_kernel_schemas.py`、Twin fixture validation | 有自动证据 |
| Promote 不改变 modality | P8 unit/integration tests | 有自动证据 |
| Checker 真值表 | truth-table contract + finite-domain tests | 有自动证据 |
| candidate ≠ level | Checker、certificate issuer、system state tests | 有自动证据 |
| heuristic 不抬 `ℓ_cert` | schema、P4/P6/P7/P9 tests | 有自动证据 |
| timeout/resource exhaustion 不当 UNSAT | Checker/MinDiff tests | 有自动证据 |
| deterministic observation 可复现 | P5 executor + Twin tests | 有自动证据 |
| zero-hit 合法性 | P6 与 fixture tests | 有自动证据 |
| No Evidence Laundering | P7/P8/P11 tests | 有自动证据 |
| Checker 与 LLM 权限分离 | candidate-only schema/interface tests | Kernel 侧有证据；跨轨规范性仍见 SI-006 |
| Γ/catalog/policy hash | canonical hash contracts + fixture replay | policy/manifest 已 exact-hash APPROVED；仍不等于 level certificate |
| 一屏反例与 MinDiff | P2/P3 两套异构 fixture tests | 两套冻结有限域有证据 |
| 形式 ceiling | model-relative 定义、验证器、两套可重放报告与域外 fail-closed 测试 | **冻结模型内证据完成；不外推为真实世界穷尽性** |
| 所有 Go 条件均自动测试 | 历史 113 项；current supplement 131 项 | **工程补洞已完成；仍需人工 A16 新裁定** |

因此当前只能说“工程评审材料已齐”，不能说“A16 Go 条件全过”。

## 6. 已知限制与未关闭事项

| 项 | 当前事实 | 对 A16 的影响 |
|---|---|---|
| SI-003 | 已由 `gamma-schema-authority-v0.8.md` 冻结完整 schema 对 Appendix skeleton 的权威关系 | 工程修复完成；不静默改写规范正文 |
| SI-006 | 已由 `compiler-kernel-boundary-v0.8.md` 冻结 Compiler/Kernel ownership 共享接口 | Kernel 侧合同完成；LLM 轨接入仍须独立授权 |
| SI-007 | legacy M3* runtime 与确定性 Kernel 明确作范围隔离 | 延期且不阻塞 Part A；不得声称 M3* 已接入或验证 |
| SI-008 | 旧 M3* CSV 对 CRLF/LF 敏感且排除在本次可复现范围外 | 延期且不阻塞 Part A；历史 artifact debt 保留 |
| **SI-010** | exact-hash policy/manifest 已批准并重绑定 | **已关闭；但单独不足以发 level certificate/`CERTIFIED_STOP`** |
| fixture 外推边界 | 已有 endpoint 与三世界 supply-chain 两套非同构完整链 | 关闭单一 Twin 工程缺口；仍不声称广域或真实世界穷尽性 |
| Narrow compiler | `EvidenceGammaFiniteProblemCompiler` 针对冻结 Twin 机制规则 | 不是通用规则引擎或真实广域 ceiling 证明 |
| P11 执行覆盖 | 默认 P4/P5 实际产生 OBS-001/002；OBS-003/004 的 deny 由同一生产 adapter 在冻结 evaluator rows 上合同测试 | 不能声称默认 E2E 实际执行了 control/heuristic 动作 |
| Runtime schema | adapter 输出经测试验证 schema-valid，但生产 adapter 内部不调用通用 JSON Schema validator | 部署边界若要求运行时验证，需新授权设计 |
| Audit persistence | P8/P11 ledger 在当前 driver run 内 append-only、可验 hash chain | 尚无持久化存储、跨进程恢复或并发语义 |
| 外部评估 | 未实施 Part B、广域连接器、随机 observation、机会约束 | 不存在外部有效性或性能 Go 证据 |

P11 的 P7 allow 或 P8 admit 只表示候选 case evidence 通过当前准入/生命周期合同；
它们不等于 level-complete certification。测试中任何 SHA-256-shaped policy value
在没有获批 artifact 绑定前都不得被解释为正式 authority。

## 7. 人工评审检查表

- [x] 工程审阅记录核对 15 个提交均在逐切片授权范围内（待 A16 人工接受）；
- [x] 工程审阅记录覆盖 81 文件总 diff，未发现 LLM、训练、Part B 或 `09-experiments` 混入（待 A16 人工接受）；
- [x] 工程审阅记录核对 P11 diff，默认 P10 行为与 STOP gate 未改变（待 A16 人工接受）；
- [x] 工程审阅记录核对 OBS-001/002 allow/admit 与 OBS-003/004 deny 的证据边界（待 A16 人工接受）；
- [x] 工程审阅记录核对 P11 adapter 的 pointer、modality、oracle/hidden fail-closed 不变量（待 A16 人工接受）；
- [x] SI-010 已由用户 exact-hash 批准关闭，绑定与负例均已复验；
- [x] 对 SI-003、SI-006、SI-007、SI-008 分别作正式 disposition
      （本轮修复 / 明确延期且不影响 A16 / 构成阻塞）；
- [x] 增加第二套非同构 Γ/fixture，并把 ceiling 声明限定为冻结模型内；
- [x] 已冻结真实 admission-policy artifact/hash 并重算全部绑定引用；
- [x] 单独决定是否允许 push：**不允许**；
- [x] 单独决定是否创建 PR：**不允许**；
- [x] Part B authority：**继续 CLOSED**（仅在未来明确 A16 Go 后另议）。

> 注：检查表中未勾选项表示复审前仍须留下逐项书面结论；已勾选项记录本次
> 2026-07-22 裁定结果，不表示对应工程工作已完成。

## 8. 人工裁定结论（2026-07-22）

```text
Decision: 先停着

Push: NO
PR: NO

A16: NOT PASSED / NO-GO

Original requirements before re-review (historical ruling; engineering response is indexed above):
1. 冻结并批准 admission-policy artifact 与真实绑定 hash，关闭 SI-010；
2. 补足真实形式 ceiling 证据；
3. 关闭单一 Twin / narrow compiler 的“玩具 Γ”外推问题；
4. 完成 15 提交、81 文件的人工 diff 审阅；
5. 对 SI-003、SI-006、SI-007、SI-008 分别作正式裁定；
6. 重新生成评审包并复跑完整测试矩阵。

Part B: CLOSED
CERTIFIED_STOP authority: NOT ESTABLISHED

Engineering implementation: P0–P11 PRESENT
Automated regression at ruling time: 113/113 PASS
```

当前不应 push，也不应开 PR。上述工程补洞不自行推翻历史裁定；完整矩阵复跑后
仍须一次新的 A16 人工复审。本裁定不授权 Part B 或任何未明确授权的后续切片。
