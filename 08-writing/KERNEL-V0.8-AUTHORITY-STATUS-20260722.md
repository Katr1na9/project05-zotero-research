# Kernel v0.8 Authority Status

## Current A16 authority snapshot

```text
Branch: feat/kernel-v0.8
Working state: A16 GO closeout (scoped Kernel Part A)
Regression: 155/155 PASS at the B1 contract review tip
(138 pre-B1 + 17 B1)
A16 Decision: PASSED / GO — Kernel v0.8 Part A only
Push: AUTHORIZED after final closeout commit and clean full replay
PR: AUTHORIZED for Kernel-only scope against main
Part B: B0 APPROVED; B1_FEDERATION_SCHEMAS AUTHORIZED on 2026-07-23;
B2_STOCHASTIC_OBSERVATION CONTRACT-ONLY AUTHORIZED on 2026-07-23;
B3_COST_INSTRUMENTATION AUTHORIZED FOR LOCAL TRACE AGGREGATION on 2026-07-23;
B4–B9 CLOSED
LLM integration: NOT AUTHORIZED by this ruling
Legacy M3*: OUT OF SCOPE / NOT VALIDATED
Broad-input evaluation: NOT AUTHORIZED
CERTIFIED_STOP authority:
ESTABLISHED ONLY FOR THE FROZEN FINITE-DOMAIN KERNEL Γ,
approved policy/catalog hashes, declared completeness assumptions,
and the recorded solver/proof policy.
```

## Part B B0 superseding scope update — 2026-07-23

The user explicitly authorized only `B0_PLANNING_AND_CONTRACTS`, without LLM.
This opens planning documents, boundary/contracts, JSON Schemas, non-executable
contract examples/manifests, spec issues and contract tests. It does not open
stochastic execution, broad connectors, full baselines, cost collection,
Planner/M3*, experiments, training or any B1–B9 slice.

The B0 manifest must state `execution_authority=false`,
`llm_integration=FORBIDDEN` and `stop_authority=NONE`. Part A
`CERTIFIED_STOP` authority remains limited to the already approved frozen
deterministic Kernel Gamma; B0 does not extend it.

## Part B normative slice map approval — 2026-07-23

PB-SI-002 is `CLOSED — APPROVED`. The following names now form the normative
v0.8 Part B map:

| Slice | Normative name | Authority state |
|---|---|---|
| B0 | `B0_PLANNING_AND_CONTRACTS` | COMPLETED / APPROVED |
| B1 | `B1_FEDERATION_SCHEMAS` | APPROVED / MERGED |
| B2 | `B2_STOCHASTIC_OBSERVATION` | APPROVED — CONTRACT ONLY / NO SAMPLING |
| B3 | `B3_COST_INSTRUMENTATION` | LOCAL REVIEW — TRACE AGGREGATION ONLY |
| B4 | `B4_BASELINE_PREREG` | CLOSED |
| B5 | `B5_PLANNER_INTERFACE` | CLOSED |
| B6 | `B6_CLOSED_LOOP_EVAL` | CLOSED |
| B7 | `B7_BROAD_CONNECTORS` | CLOSED |
| B8 | `B8_HOLDOUT_ANALYSIS` | CLOSED |
| B9 | `B9_FREEZE_AND_CLAIMS` | CLOSED |

This map ruling froze names and slice boundaries only. The later explicit B1
contract authorization is recorded below; it does not retroactively authorize
runtime work, B2–B9, LLM, push or PR. The v0.7 B1–B6 stages remain reference
lineage rather than direct number-equivalents; B7–B9 are v0.8 extensions.
Legacy `B0 no-acquisition` remains a different experiment arm and is not Part
B B0.

## Part B B1 federation-Schemas scope update — 2026-07-23

The user explicitly authorized `B1_FEDERATION_SCHEMAS` on the 13-file
allowlist. The completed local slice contains only semantic-family federation
Schemas, adapter-conformance contracts, non-executable abstract examples,
their manifest/spec issues, contract tests, the implementation plan and this
authority update.

```text
Execution authority: NO
Federation runtime: NOT AUTHORIZED
Real connectors / downloads / datasets: NOT AUTHORIZED
Stochastic execution / cost instrumentation: NOT AUTHORIZED
LLM / training / Planner / M3*: NOT AUTHORIZED
B2–B9: CLOSED
Push / PR: NOT AUTHORIZED
CERTIFIED_STOP: UNCHANGED
```

B1 requires source/record/content/range pointer identity, separates
`modality`, `truth_status`, `epistemic_role` and
`certification_authority`, treats open-world zero-hit as unknown, and requires
an explicit completeness declaration for closed-bounded absence semantics.
These are representation and conformance contracts only. They do not prove
that a real snapshot is complete, do not admit evidence, and do not issue a
certificate or `CERTIFIED_STOP`.

The local B1 review tip passed `17/17` B1 tests and `155/155` full repository
tests. `compileall`, `git diff --check` and the exact 13-file allowlist audit
also passed. These results do not authorize commit, push, PR or B2–B9.

## Part B B1 range-semantics ownership decision — 2026-07-23

The user separately authorized
`B1_SI002_RANGE_SEMANTICS_DECISION_ONLY`. PB-B1-SI-002 is
`CLOSED — APPROVED` with the following narrow ruling:

```text
range_semantics: CONFORMANCE_ENVELOPE_ONLY
Kernel Claim IR: UNCHANGED
byte_or_row_range inference: FORBIDDEN
missing/mismatched conformance contract: FAIL_CLOSED
Candidate Compiler pointer/range ownership: NONE
```

The normative contract is
`contracts/part-b-b1-range-semantics-v0.8.md`. The ruling leaves the approved
B1 federation, adapter-conformance and manifest hashes unchanged.

Issue closure is not production adapter authority. It creates no connector,
resolver, federation runtime, admission/certification result or
`CERTIFIED_STOP` authority. B2–B9, LLM and Part A behavioral changes remain
unauthorized. This local decision slice is not authorized for push or PR
without a later explicit instruction.

Local verification for the final seven-file decision slice passed `18/18`
targeted B1 tests and `156/156` full repository tests. `compileall`,
`git diff --check`, the exact allowlist audit and replay of the three frozen B1
hashes also passed. These results do not expand the authority stated above.

## Part B B2 stochastic-observation contract scope — 2026-07-23

The user separately authorized `B2_STOCHASTIC_OBSERVATION` on an exact
13-file contract-only allowlist based on `origin/main@0a6c841`.

```text
execution_authority=false
sampling_authority=false
PB-SI-003: OPEN — BLOCKS STOCHASTIC EXECUTION
Stochastic runtime / sampler / empirical estimation: NOT AUTHORIZED
Real connectors / downloads / datasets: NOT AUTHORIZED
Cost instrumentation / Planner / M3*: NOT AUTHORIZED
LLM / training: NOT AUTHORIZED
B3–B9: CLOSED
CERTIFIED_STOP: UNCHANGED / NO B2 AUTHORITY
Commit / push / PR: NOT AUTHORIZED
```

B2 may freeze finite exact probability, catalog, TV-replay and future
simulation-envelope contracts. Algebraic replay of frozen design tables in a
contract test is not sampling or simulation. Production world-pair selection,
threshold scope, multi-pair aggregation and estimated-model acceptance remain
`UNRESOLVED_PB_SI_003` and fail closed.

The B2 examples cannot execute, enter the Part A formal ceiling, produce case
evidence, eliminate worlds, issue a certificate or emit `CERTIFIED_STOP`.
Passing contract tests or approving hashes later would establish identity and
internal consistency only, not empirical validity or execution authority.

The approved local review state passed `15/15` B2 tests and `171/171` full repository
tests. `compileall`, `git diff --check`, placeholder-hash scanning, canonical
hash replay and the exact 13-file allowlist audit also passed. The approved
contract artifact identities are:

```text
Catalog: sha256:200f0ccd89525bcbda89ea77101cdcab7fda675888938ee106e389a1a8beeab5
TV policy: sha256:b25ed05fdbd9780c1d0de1889e7651220e8a2fc9ce6a86fcdf4720926a31d3e8
B2 manifest: sha256:6d6f67d9722eff1b2e1aa75277b0c390dc485751067728a347ae89c77f83faed
```

Their approval does not close `PB-SI-003` or authorize push, PR, execution,
sampling, B3–B9, LLM or any extension of `CERTIFIED_STOP`. The user authorized
only a local commit of the exact 13 B2 files.

The user subsequently ratified a naming-only correction to the B2 13-file
allowlist:

```text
part-b-tv-acceptance-policy.schema.json
  -> part-b-stochastic-tv-policy.schema.json
part-b-tv-acceptance-policy-v0.8.yaml
  -> part-b-stochastic-tv-policy-v0.8.yaml
test_part_b_b2_tv_policy.py
  -> test_part_b_b2_stochastic_observation.py
```

The right-hand paths are normative. This ratification changes no B2 semantics,
authority boundary or artifact hash and is included in the approved B2
contract slice.

## Part B PB-SI-003 world-pair / delta decision — 2026-07-23

The user separately authorized closure of PB-SI-003 for exact finite
world-pair and threshold semantics:

```text
PB-SI-003: CLOSED — APPROVED FOR EXACT FINITE TABLES ONLY
required pairs: all legal worlds partitioned by q; complete support × alternative
single Checker witness pair: insufficient
pair encoding: unordered / canonical lexicographic / frozen pre-outcome
delta_a: exact rational / per action / inclusive >= / future catalog hash
aggregation: MINIMUM_TV_WORST_CASE
decision_rule_authority=true
execution_authority=false
sampling_authority=false
estimated-model acceptance: UNRESOLVED_PB_B2_SI_003
simulation reproducibility: UNRESOLVED_PB_B2_SI_002
CERTIFIED_STOP: UNCHANGED / NO PART B AUTHORITY
```

The normative artifact is
`configs/part-b-b2-world-pair-delta-decision-v0.8.yaml` and its human-readable
contract. The three previously approved B2 hashes remain unchanged and remain
the historical snapshot created while PB-SI-003 was OPEN. No executable
stochastic catalog currently binds a production `delta_a`; therefore issue
closure does not authorize a sampler, stochastic executor, observation,
evidence admission, Planner/M3*, performance claim or `CERTIFIED_STOP`.

## Part B B3 cost-instrumentation scope — 2026-07-23

The user separately opened `B3_COST_INSTRUMENTATION` for the auditable
eight-dimensional cost contract and instrumentation:

```text
instrumentation_authority=true
input: evaluator-supplied integer trace events
UNKNOWN_NOT_ZERO
SEPARATE_NOT_HIGH_COST
action_execution_authority=false
sampling_authority=false
scalarization_authority=false
performance_claim_authority=false
B4–B9: CLOSED
CERTIFIED_STOP: UNCHANGED / NO B3 AUTHORITY
Commit / push / PR: NOT AUTHORIZED
```

B3 deterministically aggregates the ordered vector
`[T_human, T_wall, T_CPU, M_byte_sec, D_scan, N_record, C_money, T_auth]`
using exact-rational output and event-level provenance. It does not call a
clock, hook the existing Executor, run an action, sample B2, access a
connector or enter Planner/M3*.

PB-SI-004 is closed only for trace-instrumentation governance. Production
capture adapters, memory cadence, cross-currency FX normalization,
scalarization, sensitivity analysis and any cost/performance superiority
claim remain open in `src/scope/part-b-b3-spec-issues.md`. B3 cannot issue a
certificate, system state or `CERTIFIED_STOP`.

The earlier same-day `NOT PASSED / NO-GO` ruling is retained below as audit
history and is **superseded** by the scoped GO ruling recorded in §4.1.

SI-010 remains closed by the user's exact-hash approval. The approved policy
artifact is `configs/admission-policy-kernel-v0.8.yaml` with canonical hash
`sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671`.
The APPROVED manifest hash is
`sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b`.

**状态日期：** 2026-07-22
**适用轨道：** Part A Counterexample Kernel only
**分支：** `feat/kernel-v0.8`（Kernel-only PR 分支从 `main` 仅 cherry-pick Kernel 提交）
**本地开发 tip（裁定前）：** `a85b99a`
**实现状态：** `PART_A_IMPLEMENTED_A16_PASSED_SCOPED`
**A16 主门禁：** `PASSED` / `GO`（2026-07-22 复审裁定；范围受限）
**远端状态：** Push **已授权**（须最终 closeout + 干净复验）；PR **已授权**（仅 Kernel-only）

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

用户于 2026-07-22 批准 admission-policy exact hash（关闭 SI-010），并在同日
复审中作出范围受限的 A16 GO（见 §4.1）。该 GO 不授权 Part B、LLM、legacy
M3* 接线或广域评估。

## 3. 当前允许与禁止

### 当前允许

- 对 P0–P11 做只读复核与自动回归；
- 在最终 closeout commit 上执行完整复验；
- push Kernel-only 分支，并创建 **仅含** P0–P11 / schemas / configs /
  contracts / Part A tests-fixtures / authority-review-closeout 文档的 PR；
- 在冻结有限域 Γ、批准的 policy/catalog hashes、声明的 completeness
  assumptions 与 recorded solver/proof policy 下，承认 level-complete
  `CERTIFIED_STOP` 权限（模型相对，非现实世界绝对认证）。

### 未授权

- Part B、随机 observation、机会约束或广域连接器；
- Planner/M3* 策略、训练、LLM 运行时或 `09-experiments` 改动；
- 声称 M3* 已被 Kernel 验证、formal ceiling 为现实世界绝对下界、audit 已
  支持持久化/并发、或完整端到端系统已完成；
- 把本 GO 解释为广域真实环境攻击归因认证；
- 将含 LLM/training/Part B/`09-experiments` 谱系的整支开发分支直接对
  `main` 开 PR（必须 Kernel-only 重放分支）。

## 4. A16 状态

### 4.0 历史裁定（已被取代；保留审计）

用户于 2026-07-22 曾作出明确人工裁定：**先停着；A16 没过。**

```text
Decision: 先停着
Push: NO
PR: NO
A16: NOT PASSED / NO-GO
Part B: CLOSED
CERTIFIED_STOP authority: NOT ESTABLISHED
```

该裁定要求的复审材料（SI-010、formal ceiling、第二 Γ/fixture、81 文件审阅、
SI-003/006/007/008 disposition、完整矩阵）随后以工程证据补齐，见
`08-writing/kernel-v0.8-a16-review-package-20260722.md`。

### 4.1 现行复审裁定（2026-07-22）— 取代 §4.0

```text
Decision: GO — Kernel v0.8 Part A only

A16: PASSED
Push: AUTHORIZED after final closeout commit and clean full replay
PR: AUTHORIZED for Kernel-only scope

Part B: CLOSED
LLM integration: NOT AUTHORIZED by this ruling
Legacy M3*: OUT OF SCOPE / NOT VALIDATED

CERTIFIED_STOP authority:
ESTABLISHED ONLY FOR THE FROZEN FINITE-DOMAIN KERNEL Γ,
approved policy/catalog hashes, declared completeness assumptions,
and the recorded solver/proof policy.
```

**裁定依据（材料审查）：** SI-010 exact-hash 批准与负例；第二套非同构三世界
Γ/fixture；model-relative formal ceiling；81 文件审阅记录；SI-003/006/007/008
disposition；131/131 回归；forbidden-scope 扫描无越界混入。

**GO 生效条件：** (1) 提交本复审裁定及 supplement；(2) 在最终 commit 上重跑
完整测试、`compileall`、`git diff --check`；(3) working tree clean；(4) PR
diff 仅含 Kernel 授权路径。任一失败则 GO 自动暂停为 HOLD。

本裁定仅证明 Kernel v0.8 在冻结有限域 Γ 下满足 A16。它不证明真实世界穷尽性、
广域输入外部有效性、随机 observation、持久化审计、完整 M3* 或 Part B 性能。

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
| Admission policy | `configs/admission-policy-kernel-v0.8.yaml` |
| Approval manifest | `configs/admission-policy-approval-kernel-v0.8.yaml` |
| Twin fixture | `tests/fixtures/TWIN-COUNTEREXAMPLE-001/` |
| Supply-chain fixture | `tests/fixtures/TWIN-SUPPLY-CHAIN-002/` |
| P10 driver | `src/cli/kernel_e2e.py` |
| P11 adapter | `src/ir/observation_claim.py` |

本状态记录以 §4.1 现行复审裁定为准。Push 与 PR 已在该裁定的生效条件下授权；
Part B / LLM / legacy M3* / 广域评估仍分别需要新的明确授权。

## 6. 收口债务修复状态

```text
FW reason-code collision: SPLIT (FW-016 context / FW-017 kind)
Twin finite constraints: COMPILED FROM GAMMA + ADMITTED CASE EVIDENCE
Predicate projection: CALLER-SUPPLIED ACTION BINDING, CATALOG-RESOLVED
Regression after A16 remediation: 131/131 PASS
Human A16 ruling: PASSED / GO — Kernel Part A only (2026-07-22)
```

该债务修复状态不修改冻结 v0.8 规范字节。SI-010 已由精确 policy hash 批准关闭。

## 7. P11 Firewall/admit 接线状态

P11 已在本地提交 `5e9c0ba` 完成。生产适配器只从本次 P5 实际输出、冻结
action catalog 和显式调用方上下文构造 Claim IR；`pointer.record_id` 绑定
`observation_id`，`modality` 固定保持 `observed`，oracle/hidden、未知 action、
缺失 pointer 行和未实际执行的 observation ID 均 fail closed。

Twin 默认可执行路径中的 OBS-001/002 经 Firewall 为 allow，启用 P8 时可 admit；
OBS-003/004 在同一生产适配器的冻结行合同测试中分别因 control/heuristic 被
deny。P11 仍沿既有 feedback/Recert/SystemState 路径；candidate-level 结果不得
被洗成未满足冻结 Γ completeness 假设的 level certificate。

在 §4.1 裁定下，level-complete `CERTIFIED_STOP` 仅在冻结有限域 Kernel Γ、批准
policy/catalog、声明 completeness 与 recorded solver/proof policy 同时满足时
成立；P11 allow/admit 本身仍不是该证书。
