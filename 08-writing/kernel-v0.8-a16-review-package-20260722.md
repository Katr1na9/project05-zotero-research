# Kernel v0.8 A16 人工评审包

**日期：** 2026-07-22
**分支：** `feat/kernel-v0.8`
**代码评审基线：** `d156b68`
**代码评审 tip：** `5e9c0ba`
**包状态：** `READY_FOR_HUMAN_REVIEW`
**A16 decision：** `PENDING`
**操作解释：** `NO-GO`
**Part B authority：** `CLOSED`

本文件只整理 A16 所需的 diff、测试证据和已知限制，不裁定 Go，不授予 Part B、
Planner/M3*、LLM、训练、push、PR、merge 或 release 权限。自动测试通过不等于
A16 条件已全部满足。

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

本评审包及同步修改的状态文档属于 `5e9c0ba` 之后的文档 delta，应作为独立
working-tree diff 审阅；它们不改变代码 tip，也不构成 A16 decision。

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

测试证明冻结合同与当前 Twin 代码一致；它不证明外部有效性、真实环境 ceiling、
持久化审计、正式 policy authority 或 Part B 性能。

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
| Γ/catalog 预冻 hash | canonical hash contract + fixture replay | Γ/catalog 有证据；policy artifact 仍见 SI-010 |
| 一屏反例与 MinDiff | P2/P3 Twin tests | 单一 Twin 有证据 |
| 真实形式 ceiling | 仅冻结有限 Twin 与 formal catalog eligibility | **尚不能据此认定真实 ceiling** |
| 所有 Go 条件均自动测试 | 现有 113 项覆盖 Kernel 合同 | **SI-010、真实 ceiling、单 Twin 外推仍未闭合** |

因此当前只能说“工程评审材料已齐”，不能说“A16 Go 条件全过”。

## 6. 已知限制与未关闭事项

| 项 | 当前事实 | 对 A16 的影响 |
|---|---|---|
| SI-003 | Appendix Γ skeleton 不具完整 schema 字段 | 规范文本仍存在层级差异，需人工确认权威解释 |
| SI-006 | Compiler/Kernel ownership 的共享 profile 尚非规范裁定 | LLM 轨接入前仍需共享接口裁定 |
| SI-007 | legacy M3* runtime 与确定性 Kernel 边界冲突 | 不能把当前 Kernel 结果外推为 M3* 已接入或已验证 |
| SI-008 | 旧 M3* CSV 对 CRLF/LF 敏感 | 历史 artifact reproducibility debt 未解决 |
| **SI-010** | 无获批 admission-policy artifact 及真实绑定 hash | **禁止正式 certification；禁止由此发 `CERTIFIED_STOP`** |
| 单一 Twin | 当前只有一个完整 Twin 反例链 | 不足以自动消除 A16 的“玩具 Γ/外推性”担忧 |
| Narrow compiler | `EvidenceGammaFiniteProblemCompiler` 针对冻结 Twin 机制规则 | 不是通用规则引擎或真实广域 ceiling 证明 |
| P11 执行覆盖 | 默认 P4/P5 实际产生 OBS-001/002；OBS-003/004 的 deny 由同一生产 adapter 在冻结 evaluator rows 上合同测试 | 不能声称默认 E2E 实际执行了 control/heuristic 动作 |
| Runtime schema | adapter 输出经测试验证 schema-valid，但生产 adapter 内部不调用通用 JSON Schema validator | 部署边界若要求运行时验证，需新授权设计 |
| Audit persistence | P8/P11 ledger 在当前 driver run 内 append-only、可验 hash chain | 尚无持久化存储、跨进程恢复或并发语义 |
| 外部评估 | 未实施 Part B、广域连接器、随机 observation、机会约束 | 不存在外部有效性或性能 Go 证据 |

P11 的 P7 allow 或 P8 admit 只表示候选 case evidence 通过当前准入/生命周期合同；
它们不等于 level-complete certification。测试中任何 SHA-256-shaped policy value
在没有获批 artifact 绑定前都不得被解释为正式 authority。

## 7. 人工评审检查表

- [ ] 核对 15 个提交均在逐切片授权范围内；
- [ ] 核对 81 文件总 diff，确认无 LLM、训练、Part B 或 `09-experiments` 混入；
- [ ] 核对 P11 的 9 文件 diff，确认默认 P10 行为与 STOP gate 未改变；
- [ ] 核对 OBS-001/002 allow/admit 与 OBS-003/004 deny 的证据边界；
- [ ] 核对 P11 adapter 的 pointer、modality、oracle/hidden fail-closed 不变量；
- [ ] 对 SI-003、SI-006、SI-007、SI-008、SI-010 分别作保留/修复裁定；
- [ ] 明确判断单一 Twin 与 narrow compiler 是否触发 A16“玩具 Γ”No-Go 条款；
- [ ] 在任何 Go 前冻结真实 admission-policy artifact/hash 及全部绑定引用；
- [ ] 单独决定是否允许 push；
- [ ] 单独决定是否创建 PR；
- [ ] 若且仅若人工明确裁定 A16 Go，再另行讨论 Part B authority。

## 8. 当前结论

```text
Engineering implementation: P0–P11 PRESENT
Automated regression: 113/113 PASS
A16 review package: READY FOR HUMAN REVIEW
A16 decision: PENDING
Operational interpretation: NO-GO
Formal level certificate authority: NOT ESTABLISHED
Part B authority: CLOSED
Push / PR: NOT AUTHORIZED
```

本文件到此停止，不作 Go/No-Go 最终裁定。
