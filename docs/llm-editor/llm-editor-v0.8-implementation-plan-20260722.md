# Candidate-only Evidence-safe Semantic Editor v0.8：详细实施计划

**日期**：2026-07-22
**状态**：待审实施计划；仅授权文档与模型无关的 L1 准备，不授权长时间训练
**实施分支**：`feat/llm-editor-v0.8`
**权威规格**：v0.8；v0.7 仅作历史基线

## 1. 目标与非目标

目标数据流：

```text
raw source packet
  → LLM candidate proposal
  → Candidate Claim IR projection
  → candidate-only safety guard
  → schema / vocabulary / modality validation
  → pointer suggestion (unbound | ambiguous)
  → trusted external binder (本轨道不执行 admission)
  → Candidate Claim IR artifact for Kernel read-only dry run
```

LLM 输出恒定默认值：

```yaml
admission_status: candidate
certification_authority:
  allowed: false
  levels: []
promotion_status: none
binding_status: unbound  # 或 ambiguous
```

本轨道永不：写 `E_case`、执行 Promote/Revoke、修改 modality/Γ/action catalog/absence semantics、判断 SAT/UNSAT、宣布 CERTIFIED/STOP/UNRESOLVABLE、伪造 pointer/hash、依赖隐藏 ground truth 生成 action、合并冲突 claim。

## 2. 总体门禁

| Gate | 进入条件 | 失败处置 |
|---|---|---|
| G-L0 | 现状、数据、模型、失败模式与边界审计完成 | 停止编码 |
| G-L1A | Kernel schema 可定位，或 local projection 明确不声明兼容 | 只做 guard，不写兼容声明 |
| G-L1B | Authority Leakage=0、Modality Leakage=0、无 pointer 不得 bound、冲突不合并 | 不进入 L2 |
| G-L2 | 来源/许可/拆分/hash/hidden-GT exclusion/指标样本覆盖全通过 | 不冻结 test，不训练 |
| G-L3 | 同一评测 harness 完成未微调 baseline，逐样本错误可审计 | 不进入微调 |
| G-L4 | 技术栈、权重、数据、seed、超参和安全 Gate 单独冻结 | 不训练 |
| G-L5 | Candidate IR schema 通过；只读输出；未调用 Checker/E_case | 不交付 Kernel |

非安全指标的数值门槛在 L3 baseline 前冻结；不能看 test 后再改。硬安全门槛从现在起固定为零容忍。

## 3. L0 — 审计与冻结（本轮）

### Task L0.1：仓库、数据与模型审计

**产物**：

- `docs/llm-editor/llm-editor-v0.8-current-state-audit-20260722.md`

**验证**：

```powershell
git status --short --branch
git log -8 --oneline --decorate
python -m pytest 09-experiments/tests -k "llm or qwen or pointer_bound" -p no:cacheprovider -q
```

**退出条件**：记录 pre-existing failures；不改历史 authority/hash 使其通过。

### Task L0.2：接口问题登记

**产物**：`docs/spec-issues/SI-LLM-001` 至 `SI-LLM-005`。

**退出条件**：每个 issue 都写出当前字段、阻塞案例、建议变更、兼容性和认证安全影响；不直接修改共享 schema 或 Γ。

**Commit 边界**：`docs(llm): audit v0.8 editor contracts and blockers`

## 4. L1 — Contract Harness（优先实施）

### Task L1.1：建立 Candidate Claim IR 本地 projection

**先写失败测试**：

- `tests/compiler_contract/test_candidate_claim_ir_projection.py`

测试必须证明：

1. 合法 raw proposal 被转换为 candidate；
2. `admission_status` 只能是 `candidate`；
3. authority 恒为 `{allowed:false, levels:[]}`；
4. promotion 恒为 `none`；
5. pointer suggestion 不会产生 `bound`；
6. model 输出的 authority/promotion/lifecycle 字段被拒绝，不被静默覆盖；
7. 输入 `reported`/`hypothesized` 不会变成 `observed`。

**再实现**：

- `src/compiler/llm/__init__.py`
- `src/compiler/llm/candidate_ir.py`
- `src/compiler/llm/candidate_only_guard.py`
- `src/compiler/llm/exceptions.py`

在共享 schema 到位前，本地对象名称使用 `CandidateClaimIRProjection`，禁止命名为 Kernel canonical Claim IR；兼容状态必须是 `pending_kernel_schema`。

**Green 命令**：

```powershell
python -m pytest tests/compiler_contract/test_candidate_claim_ir_projection.py -q
```

### Task L1.2：Canonical schema validator 与 decoder-facing schema 分离

**先写失败测试**：

- `tests/compiler_contract/test_candidate_claim_ir_schema.py`
- `tests/llm_eval/test_constrained_schema_equivalence.py`

测试必须覆盖：

- unknown field fail-closed；
- authority leakage、modality change、假 pointer、错误类型全部失败；
- canonical schema 与 decoder-facing compatibility view 接受/拒绝同一组 fixtures；
- decoder view 不能放宽 canonical contract；
- validator 不依赖 torch、transformers、PEFT 或模型权重。

**再实现**：

- `src/compiler/constrained_decoder/__init__.py`
- `src/compiler/constrained_decoder/canonical_validator.py`
- `src/compiler/constrained_decoder/schema_projection.py`
- `tests/compiler_contract/fixtures/valid_candidate.json`
- `tests/compiler_contract/fixtures/authority_leak.json`
- `tests/compiler_contract/fixtures/modality_leak.json`
- `tests/compiler_contract/fixtures/unbound_pointer.json`

只有 Kernel schema 发布后才接入其 hash；此前测试使用本轨道 projection，不声明 shared compatibility。

### Task L1.3：Abstention 与 pointer suggestion

**先写失败测试**：

- `tests/compiler_contract/test_abstention_and_pointer_suggestion.py`

必须覆盖：

- 无 pointer → `binding_status=unbound`，不得产生 case evidence；
- 多个同等候选 pointer → `ambiguous`；
- source_id/record_id/content_hash 不完整 → abstain 或 unbound；
- 模型提供不存在的 record_id/content_hash → reject，不修补；
- binder 是独立依赖，本轨道输出只含 suggestion；
- abstain 不填“最可能实体”。

**再实现**：

- `src/compiler/llm/abstention.py`
- `src/compiler/llm/pointer_suggestion.py`

### Task L1.4：Modality、epistemic role 与 truth status 保持

**先写失败测试**：

- `tests/compiler_contract/test_modality_authority_preservation.py`

矩阵至少覆盖：

- observed endpoint log；
- reported CTI；
- derived rule output；
- hypothesized model proposal；
- unknown source；
- attempted reported→observed；
- attempted hypothesized→case_evidence；
- attempted authority level injection。

**再实现**：

- `src/compiler/llm/source_semantics.py`
- `src/compiler/llm/safety_metrics.py`

`modality` 必须来自受信输入合同或程序映射，不能由模型自由改写。

### Task L1.5：冲突保留

**先写失败测试**：

- `tests/compiler_contract/test_contradiction_preservation.py`

同 subject/predicate、相反 object/polarity、不同 pointer 的 claim 必须保留为两条独立 candidate；禁止 legacy dedup；`truth_status=conflicted` 只能由规则化冲突标记器标注，不能合成“综合事实”。

**再实现**：

- `src/compiler/llm/conflict_preservation.py`

### Task L1.6：Candidate-q proposer contract shell

此任务受 `SI-LLM-002` 阻塞。Kernel 给出 q schema 前，只能创建测试占位和明确的 `NotImplementedError`，不能私自定义可认证 q。

预计文件：

- `src/compiler/llm/candidate_q.py`
- `tests/compiler_contract/test_candidate_q_authority_boundary.py`

测试先固定：candidate q 无 authority、无 certified level、无 action execution、无 SAT/UNSAT 字段。

### Task L1.7：L1 综合安全 Gate

**命令**：

```powershell
python -m pytest tests/compiler_contract -q
python -m pytest tests/llm_eval -q
python -m pytest 09-experiments/tests/test_qwen_pointer_bound_constrained_atomic.py -q
```

**硬断言**：

- Authority Leakage Rate = 0；
- Modality Leakage Rate = 0；
- invalid pointer 被标为 bound 的数量 = 0；
- conflict merge 数量 = 0；
- 所有 abstention 都不进入 case evidence；
- 没有代码调用 legacy `admit_candidates()`、Checker、Promote 或 E_case writer。

**Commit 边界**：

1. `test(llm): freeze candidate-only safety contract`
2. `feat(llm): add candidate IR projection and guard`
3. `feat(llm): add abstention pointer and conflict preservation`

## 5. L2 — Dataset Preparation（L1 Gate 后）

### Task L2.1：数据合同与转换器

**预计文件**：

- `datasets/llm/README.md`
- `datasets/llm/contracts/candidate-editor-example.schema.json`
- `datasets/llm/contracts/split-manifest.schema.json`
- `training/prepare_candidate_editor_dataset.py`
- `training/audit_candidate_editor_dataset.py`
- `tests/llm_eval/test_candidate_editor_dataset.py`

旧 1,500 pairs 只可作为经审计的迁移来源，不直接改名。转换后每条数据必须显式覆盖或声明不适用：modality、truth_status、epistemic_role、pointer suggestion、abstention、conflict group、time normalization、candidate-q。

### Task L2.2：样本族

至少包含：

1. 正例 candidate extraction；
2. 无支持记录的负例；
3. 无 pointer / pointer ambiguity；
4. reported CTI modality 保持；
5. hypothesized proposal 不提升；
6. 冲突 claim 并存；
7. unsupported entity hallucination；
8. exact/bounded/approximate/unknown temporal normalization；
9. candidate-q supported / unsupported（待 q schema）；
10. authority/promotion prompt-injection 负例。

### Task L2.3：拆分与冻结

- 先按 source family 分割，再按样本族检查覆盖；
- train/dev/test 来源族不重叠；
- test 在任何 prompt/adapter 调参前冻结；
- Kernel fixture hidden answer 不进入 prompt、训练或候选生成；
- 记录 license、source revision、hash、normalizer version、seed；
- payload 仍保持受控，不因 clean checkout 缺失而复制私有数据。

**L2 Gate**：schema 100% valid；无 split leakage；hard safety fixture 覆盖完整；license 与数据重建合同明确；test hash 冻结。

**Commit 边界**：`data(llm): freeze candidate editor dataset contracts and split audit`

## 6. L3 — 未微调 Baseline

### Task L3.1：统一评测 harness

**预计文件**：

- `src/compiler/llm/evaluator.py`
- `tests/llm_eval/test_metric_definitions.py`
- `training/run_candidate_editor_baseline.py`
- `prompts/candidate-editor-v0.8.txt`

统一 harness 同时评估 General 和后续 Adapted，不允许条件间改变输入、prompt、decoder、token limit、binder 或 scorer。模型输出与 program-bound 字段分开计分。

### Task L3.2：冻结 13 项指标定义

必须输出总体、source-family macro、modality slice 与失败原因分布：

1. Schema Validity；
2. Canonical Predicate Validity；
3. Entity Type Validity；
4. Modality Preservation；
5. Authority Leakage Rate；
6. Modality Leakage Rate；
7. Pointer Suggestion Precision；
8. Abstention Precision / Recall；
9. Contradiction Preservation；
10. Unsupported Entity Hallucination Rate；
11. Temporal Normalization Accuracy；
12. Candidate-q Recall；
13. Candidate-q Unsupported Rate。

总体 F1 不得掩盖 Authority/Modality leakage，也不得掩盖 supported path collapse。

### Task L3.3：baseline 执行门禁

只有以下事实明确才可执行：模型/revision、本地权重来源、runtime、decoder compatibility、数据 hash、许可、seed、输出隐私策略、GPU 边界。先在 dev/training-validation 小面板执行；不触碰正式 test。

**Commit 边界**：`eval(llm): record immutable candidate editor baseline`

## 7. L4 — Fine-tuning（单独授权）

旧 `project05_obs_compiler` 只作为冻结负结果，不续训、不改名复用。若 L3 表明微调仍有必要，则建立新 adapter id 和新合同。

### Task L4.1：训练前冻结

- Qwen revision 或现有明确技术栈；不得自行换模型；
- train/dev hash；
- assistant-only loss；
- seed、LoRA、optimizer、scheduler、sequence length；
- positive-path、abstention、authority/modality safety 权重策略；
- checkpoint eligibility 先于 ranking。

### Task L4.2：checkpoint 硬门槛

任何 checkpoint 若出现以下任一情况即不合格：

- Authority Leakage > 0；
- Modality Leakage > 0；
- supported schema-valid rate = 0；
- supported-class F1 = 0；
- 无 pointer 被标为 bound；
- conflict 被合并；
- macro-F1 仅由 abstain/unsupported 路径抬高。

没有 checkpoint 合格时报告负结果，不换指标、不放宽 parser、不访问 test 救场。

### Task L4.3：General vs Adapted

同一进程、同一 base、同一输入、同一 prompt、同一 constrained decoder、同一 binder/scorer，只切换 adapter on/off。结果先停在 dev/training-validation Gate；正式 test 需另行授权。

**Commit 边界**：

1. `train(llm): freeze candidate editor fine-tuning authority`
2. `train(llm): record immutable adapter result`

## 8. L5 — Integration Dry Run

**预计文件**：

- `src/compiler/llm/export_candidate_ir.py`
- `tests/llm_eval/test_kernel_read_only_handoff.py`
- `docs/llm-editor/kernel-handoff-manifest.md`

只输出 Candidate Claim IR 文件及 manifest/hash，交给 Kernel 会话只读消费。不得调用真实 Checker，不写 E_case，不生成 certificate，不执行 Promote，不宣布 STOP。

兼容报告必须逐项说明：

- shared schema id/version/hash；
- 通过/失败数量；
- pointer binding 状态；
- modality/authority leakage 是否为 0；
- 未实现或被 abstain 的字段；
- spec issues 处置状态。

**Commit 边界**：`feat(llm): export read-only candidate IR handoff`

## 9. 拟修改文件总表

| 目录 | 用途 | 当前是否可动 |
|---|---|---|
| `src/compiler/llm/` | projection、guard、abstention、pointer、conflict、metrics | L1 可动 |
| `src/compiler/constrained_decoder/` | canonical validator 与 schema projection | L1 可动 |
| `tests/compiler_contract/` | 权限、模态、pointer、冲突硬测试 | L1 可动 |
| `tests/llm_eval/` | decoder、数据和评测测试 | L1 可动 |
| `docs/llm-editor/` | 审计、计划、结果、handoff | 可动 |
| `docs/spec-issues/` | 向 Kernel 提接口问题 | 可动 |
| `datasets/llm/` | L2 合同与受控 manifest | L2 Gate 后 |
| `training/` | 数据构建、baseline、微调入口 | L2/L3 Gate 后 |
| `prompts/` | 冻结 prompt | L3 Gate 后 |
| `schemas/`、`configs/` | Kernel-owned | 不直接修改 |

## 10. 首次实施停点

计划通过后，第一批只执行 L1.1–L1.5 的模型无关 TDD。若 shared schema 仍缺失，输出保持 `pending_kernel_schema`，不能声称与 Kernel Claim IR 兼容。完成 L1 安全 Gate 后汇报，不自动开始数据重建、下载、模型 baseline 或微调。
