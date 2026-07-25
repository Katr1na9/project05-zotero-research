# LLM Evidence-safe Semantic Editor v0.8：L0 现状审计

**日期**：2026-07-22
**分支**：`feat/llm-editor-v0.8`
**worktree**：`.worktrees/llm-editor-v0.8`
**基线提交**：`d156b68`
**状态**：L0 完成；L1 尚未编码；未开始数据重建、模型加载、推理或训练

## 1. 权威规格与版本关系

| 材料 | 角色 | SHA-256 |
|---|---|---|
| `active-attribution-experiment-revision-plan-v0.8-20260721.md` | 当前 Kernel 实施规格 | `99FA98B9489CFE49D4DA6FE02E06B457201A59D9024CA62233C5DD82F7B7BAA9` |
| `active_attribution_experiment_revision_plan_v0.7_implementation_ready.md` | 历史基线、演进对照 | `B1FF751758377AFA2E3287CE68A2E579AC0A4BCB8C687BF4731E1927290DE0DA` |
| 用户给出的 LLM 轨道职责与目录边界 | 本轨道直接实施约束 | 本任务消息 |

v0.7 不是当前实施权威。v0.8 继承其 `modality`、`truth_status`、`certification_authority` 分离思想，并进一步收紧有限域、P0 门禁、确定性 Kernel、Promote pointer 不变量和状态判定顺序。本轨道另受更严格的 Candidate-only 约束：LLM 只能产生候选 Claim IR、pointer suggestion 和候选 q，不能取得 admission、certification、Promote、Checker 或 STOP 权。

## 2. 仓库与目录现状

规格指定的下列目录在基线提交中均不存在：

- `src/compiler/llm/`
- `src/compiler/constrained_decoder/`
- `training/`
- `datasets/llm/`
- `prompts/`
- `tests/compiler_contract/`
- `tests/llm_eval/`
- `docs/llm-editor/`
- `schemas/`
- `configs/`

已有 LLM 实验集中在：

- `09-experiments/scripts/`
- `09-experiments/tests/`
- `09-experiments/llm_evidence_compiler_mainline/`
- `09-experiments/llm_compiler/`

因此 v0.8 不是对现有包做一次改名，而是需要在新目录建立清晰的 Candidate-only 边界，并把可复用的机械校验从旧的 admission 路径中隔离出来。

## 3. 当前模型与训练技术栈

| 项 | 当前冻结事实 |
|---|---|
| 基座模型 | `Qwen/Qwen2.5-7B-Instruct` |
| revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Python | 3.11.9 |
| PyTorch | 2.3.1+cu121 |
| Transformers | 4.45.2 |
| PEFT | 0.13.2 |
| bitsandbytes | 0.43.1 |
| 训练方式 | RTX 4090、NF4 4-bit QLoRA、causal SFT、assistant-only loss |
| Adapter | `project05_obs_compiler` |
| LoRA | rank 16，alpha 32，dropout 0.05；q/k/v/o/gate/up/down projections |
| 可训练参数 | 40,370,176 / 4,393,342,464，约 0.9189% |
| 训练调度 | 1,200 train，3 epochs，225 optimizer steps，epoch 1/2/3 各存 checkpoint |
| 历史选择 | epoch 2，但选择规则后来被证实可被负类高分劫持 |

该技术栈是“已存在且曾运行”的事实，不等于 v0.8 已批准继续训练。L4 之前不得更换模型或训练框架，也不得把旧 adapter 视为 v0.8 可用模型。

## 4. 当前数据状态

冻结审计记录了 1,500 个 label-blind candidate pairs：

| Split | Family | 数量 | supported / unsupported |
|---|---|---:|---:|
| train | CAM-LDS filtered | 300 | 150 / 150 |
| train | BETH process events | 300 | 150 / 150 |
| train | SOCBED winlogbeat | 300 | 150 / 150 |
| train | Atomic Red Team | 300 | 150 / 150 |
| training-validation | Loghub Linux | 150 | 75 / 75 |
| training-validation | Zeek non-PCAP | 150 | 75 / 75 |

审计事实：

- train 与 training-validation 来源族不重叠；
- exact/near protected payload match 均为 0；
- BETH 标签字段未读、未用；
- 正负样本各 750；
- 最长序列 1,021 tokens，p95 为 881，全部不截断地低于 1,024；
- pair payload 与规范化语料被 Git 忽略，在干净 worktree 中不存在；
- 仓库只保留计数、hash、合同和脱敏审计。

结论：现有数据可作为历史证据和可能的迁移输入，但不能从干净 checkout 直接执行 L2/L3。必须先有单独的数据重建或受控 staging 合同。更重要的是，旧数据只监督 `supported` 与 `unsupported_by_bound_pointer`，不覆盖 v0.8 的 modality、authority、conflict、abstention、temporal normalization 与 candidate-q 全合同。

## 5. 当前输出合同与 v0.8 不兼容处

### 5.1 旧 CandidateClaimEnvelope

旧 schema 包含 `source_pointer`、`entity_scope`、`proposed_claim` 和 `proposed_target_node_ids`，但缺少：

- `modality`
- `truth_status`
- `epistemic_role`
- `certification_authority`
- `binding_status`
- `admission_status`
- `promotion_status`
- `admissible_levels`
- `support_claim_ids` / `contradict_claim_ids`

它不能被重命名为 v0.8 Claim IR。

### 5.2 旧 admission 是明确越权路径

`09-experiments/scripts/validate_compiler_admission.py` 会：

1. 把 candidate 转为 `ADM-*` claim；
2. 创建 `controller_eligible: true` 的 claim-node link；
3. 合并重复 claim；
4. 返回 admitted claims 和 entity bindings。

这些行为违反 Candidate-only、无 silent promotion 和冲突保留约束。新 LLM 路径不得调用 `admit_candidates()`，也不得把其输出当作 v0.8 dry-run 结果。

可复用的只有无私有 gold 的机械检查思想：pointer 是否存在、surface 是否可回指、predicate allowlist、scope 冲突与时间窗冲突。

### 5.3 Pointer-bound redesign

v0.44 已正确把 pointer 从模型生成目标中移除：

```text
LLM → support_decision + pointer-free edge_fields
trusted binder → deep-copy bound pointer
```

这一模式可继承为 v0.8 的 pointer suggestion / binder 分权基础，但旧 binder 输出仍是 legacy strict compiler shape，而不是 Candidate Claim IR。

## 6. 已冻结负结果

v0.43 General/Adapted 原子配对评测是不可改写的 training-validation 负结果：

- General：16/16 `invalid_top_level_schema`；
- Adapted：8/8 unsupported 正确；
- Adapted：8/8 supported 均为 `invalid_edge_source_pointer`；
- 两个 held-out family 的 supported-class F1 都是 0；
- adapter 已被标记为 `not_mainline_eligible`。

科学解释只能是：旧 SFT 学会了短的拒答路径，没有学会正例结构化生成。不得换 checkpoint、放宽 parser、修改指标或把 macro-F1 `+0.50` 改写成正向结果。

## 7. Constrained decoding 现状

v0.45 在零模型调用的兼容性预检中失败：

```text
AttributeError: 'bool' object has no attribute 'get'
model_loaded = false
model_calls = 0
```

根因位于 `lm-format-enforcer==0.10.6` 与当前 schema/dependency 组合对 boolean subschema（例如 `additionalProperties: false`）的处理；顶层 `oneOf` 也需要 decoder-facing compatibility view。

旧 worktree 中存在未提交的 v0.46 兼容实验、schema view 和依赖 patch。它们没有进入本分支，不能作为已批准实现或已验证修复。L1 先实现独立于 decoder library 的 canonical validator；任何 decoder compatibility layer 必须证明与 canonical schema 等价，且不能成为放宽 schema 的旁路。

## 8. 指标覆盖差距

| v0.8 必测指标 | 旧管道状态 | L1/L2 需求 |
|---|---|---|
| Schema Validity | 有 legacy schema/strict parser | 改为 Candidate Claim IR canonical schema |
| Canonical Predicate Validity | 部分有 allowlist | 对接 Kernel canonical predicate vocabulary |
| Entity Type Validity | 仅非空字符串 | 对接 Kernel entity type vocabulary |
| Modality Preservation | 无 | 输入继承 + guard 不变量 |
| Authority Leakage Rate | 无 | 强制 false/empty，任何泄漏硬失败 |
| Modality Leakage Rate | 无 | reported/hypothesized 不得提升 observed |
| Pointer Suggestion Precision | 无独立 suggestion 指标 | suggestion 与 binder 结果分开评分 |
| Abstention Precision / Recall | 训练数据近乎无 abstain | 新建 ambiguous/no-pointer 样本 |
| Contradiction Preservation | 旧 admission 会 dedup | 禁合并，冲突配对测试 |
| Unsupported Entity Hallucination Rate | 有 surface 检查思想 | 候选实体逐项可回指评分 |
| Temporal Normalization Accuracy | 仅有 time conflict check | 新建 exact/bounded/approximate/unknown gold |
| Candidate-q Recall | 无 | 等 Kernel 发布 q schema 后实现 |
| Candidate-q Unsupported Rate | 无 | 等 Kernel 发布 q schema后实现 |

硬安全指标当前不能声明达标，因为新合同尚未实现。历史 `controller_eligible=false` 实验审计不等于 v0.8 Authority Leakage Rate 已测为 0。

## 9. 基线测试证据

历史 LLM 相关 pytest 基线：

```text
328 passed
13 failed
1 skipped
518 deselected
265 subtests passed
```

命令：

```powershell
python -m pytest 09-experiments/tests -k "llm or qwen or pointer_bound" -p no:cacheprovider -q
```

另有：

- legacy compiler unittest：152 tests，2 failures，1 error，1 skipped；
- Qwen unittest：84 tests，4 failures，5 errors。

失败主要来自 Git-ignored payload/runtime audit 不在 clean worktree、历史 source-root 缺失和过时 hash/sidecar 锁。不得通过复制私有/服务器 payload、改冻结结果或重写历史 authority 来刷绿。

## 10. 当前阻塞项

1. Kernel-owned `schemas/claim-ir-kernel.schema.json` 尚不存在；
2. candidate-q 的机器可校验输出合同未定义；
3. legacy pointer 使用 `artifact_id/record_sha256`，Kernel 使用 `source_id/content_hash`，映射未定；
4. `lifecycle_state` 是只读派生字段，但 candidate-only 输出是否应省略尚需确认；
5. legacy `source_modality` 与 Kernel `modality`/`source_family` 是不同语义轴，不能直接映射；
6. clean checkout 缺少受控的 1,500 pair payload；
7. constrained decoder 兼容性尚未通过；
8. 旧 adapter 已失去主线资格，不能作为 v0.8 baseline 之外的默认组件。

这些问题已分别登记在 `docs/spec-issues/`。其中 1–5 由 Kernel 会话拥有最终解释权。

## 11. L0 裁断

- 可以进入模型无关的 L1：Candidate Claim IR 转换层、candidate-only guard、canonical validation、abstention、pointer suggestion、modality/authority/conflict tests。
- 不能进入 L2 数据冻结、L3 模型 baseline、L4 微调或 L5 Kernel integration。
- 不修改共享 Schema、Γ、action catalog 或公共 Claim IR 类型。
- 不把旧 admission、旧 adapter 或 v0.43 macro-F1 带入新主线。
