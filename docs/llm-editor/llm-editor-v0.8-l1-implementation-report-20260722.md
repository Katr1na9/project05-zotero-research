# LLM Evidence-safe Semantic Editor v0.8：L1 实施报告

**日期**：2026-07-22
**分支**：`feat/llm-editor-v0.8`
**基线**：`d156b68`
**范围**：仅模型无关 L1；未启动数据重建、模型 baseline、正式推理或微调

## 1. 结果裁断

L1.1–L1.5 已实现并通过本地合同测试。当前产物是 `pending_kernel_schema` 的 Candidate Claim IR 本地 projection 与安全护栏，不是 Kernel canonical Claim IR，也不是模型效果结果。

已实现：

- Candidate-only projection 与递归控制面 guard；
- fail-closed canonical validator 与等价 decoder-facing schema view；
- 显式 abstention 和可见目录约束的 pointer suggestion；
- trusted modality / epistemic role / truth status 保持；
- Authority Leakage Rate 与 Modality Leakage Rate；
- 不去重、不综合的冲突保留与对称 contradiction links。

未实现或未启动：

- L2 数据重建与 train/dev/test 冻结；
- L3 未微调模型 baseline；
- L4 QLoRA 或其他微调；
- Candidate-q proposer；
- Kernel Checker、Promote、E_case 或 STOP 集成。

## 2. 创建或修改的文件

核心实现：

- `src/compiler/llm/__init__.py`
- `src/compiler/llm/candidate_ir.py`
- `src/compiler/llm/candidate_only_guard.py`
- `src/compiler/llm/exceptions.py`
- `src/compiler/llm/abstention.py`
- `src/compiler/llm/pointer_suggestion.py`
- `src/compiler/llm/source_semantics.py`
- `src/compiler/llm/safety_metrics.py`
- `src/compiler/llm/conflict_preservation.py`
- `src/compiler/constrained_decoder/__init__.py`
- `src/compiler/constrained_decoder/canonical_validator.py`
- `src/compiler/constrained_decoder/schema_projection.py`

测试与 fixture：

- `tests/compiler_contract/test_candidate_claim_ir_projection.py`
- `tests/compiler_contract/test_candidate_claim_ir_schema.py`
- `tests/compiler_contract/test_abstention_and_pointer_suggestion.py`
- `tests/compiler_contract/test_modality_authority_preservation.py`
- `tests/compiler_contract/test_contradiction_preservation.py`
- `tests/compiler_contract/fixtures/*.json`
- `tests/llm_eval/test_constrained_schema_equivalence.py`

文档：

- `docs/llm-editor/llm-editor-v0.8-current-state-audit-20260722.md`
- `docs/llm-editor/llm-editor-v0.8-implementation-plan-20260722.md`
- 本报告
- `docs/spec-issues/SI-LLM-001` 至 `SI-LLM-006`

## 3. 当前模型与训练栈

仓库历史冻结栈仍为 Qwen2.5-7B-Instruct（revision `a09a35458c702b33eeacc393d103063234e8bc28`）+ Transformers 4.45.2 + PEFT 0.13.2 + bitsandbytes 0.43.1 的 NF4 QLoRA。旧 adapter `project05_obs_compiler` 的 v0.43 正例 supported F1 为 0，已失去主线资格。

本次 L1 没有导入 torch、transformers 或 PEFT，没有加载权重、adapter，没有执行模型调用，也没有更换训练框架。

## 4. 数据来源、版本与拆分

L1 不读取样本 payload。L0 仅登记历史冻结的 1,500 个 label-blind candidate pairs：

| Split | 来源族 | 数量 |
|---|---|---:|
| train | CAM-LDS filtered | 300 |
| train | BETH process events | 300 |
| train | SOCBED winlogbeat | 300 |
| train | Atomic Red Team | 300 |
| training-validation | Loghub Linux | 150 |
| training-validation | Zeek non-PCAP | 150 |

这些 payload 不在干净 checkout 中，且旧标签不覆盖 v0.8 的完整安全合同，因此不能视为 L2 已完成。test split 尚未在本轨道重建或触碰。

## 5. 合同测试与指标

最终命令：

```powershell
python -m pytest tests/compiler_contract tests/llm_eval -q
```

结果：`47 passed, 73 subtests passed`。

| 指标/合同 | L1 状态 |
|---|---|
| Schema Validity | canonical 与 decoder-facing fixture/boundary tests 通过 |
| Modality Preservation | observed/derived/reported/hypothesized/unknown 全覆盖 |
| Authority Leakage Rate | 非空安全 fixture panel 为 0；泄漏 fixture 可被检出 |
| Modality Leakage Rate | 非空安全 fixture panel 为 0；reported/hypothesized→observed 被拒绝 |
| Pointer Suggestion | 仅可见 catalog 三元组；无绑定 transition |
| Abstention | stable reason code；不填 most-likely entity |
| Contradiction Preservation | 冲突候选分离、对称引用、重复候选保留 |

零分母定义：两项 leakage rate 返回 0.0，但 `hard_safety_pass=false`，禁止空面板真空过 Gate。

上述是合同 harness 的机械结果，不是 General/Adapted 模型实证；Schema Validity、Pointer Precision、Abstention P/R 等模型指标仍待 L2/L3。

## 6. 典型失败案例

- 模型输出 `admission_status`、authority、binding、lifecycle、Promote/Revoke、Checker、SAT/UNSAT、STOP 或 Γ/catalog mutation：递归拒绝；
- reported/hypothesized 来源自行声明 observed：拒绝；
- pointer 三元组不完整或不在可见 catalog：拒绝或显式 abstain；
- 单个核验 pointer：仍是 `unbound`，不暴露 binding transition；
- 多个等价候选 pointer：仅标 `ambiguous`；
- 不具备外部 predicate 互斥合同的 object 差异：保留候选但不擅自标冲突；
- 已带 authority leakage 的候选进入 conflict annotator：fail closed。

## 7. Authority / Modality leakage 裁断

L1 机械安全 fixture 上两项 leakage rate 均为 0，且泄漏注入测试能稳定失败。由于没有运行模型 baseline，不能声称某个 LLM 的经验 leakage 已为 0；该结论必须等 L3 的冻结评测面板。

## 8. 与共享 Claim IR 的兼容性

当前只保证本地 canonical schema 与 decoder-facing view 等价。共享 `schemas/claim-ir-kernel.schema.json` 在本分支仍不存在，因此所有输出固定：

```yaml
compatibility_status: pending_kernel_schema
admission_status: candidate
certification_authority: {allowed: false, levels: []}
promotion_status: none
binding_status: unbound|ambiguous
```

不能声称 Kernel schema 兼容，不能写入 E_case。pointer identity 仅使用本地可见 catalog 的 `record_id/source_id/content_hash`，不推断 legacy→Kernel 映射。

## 9. 向 Kernel 会话登记的 spec issues

1. SI-LLM-001：共享 Claim IR schema 工件缺失；
2. SI-LLM-002：Candidate-q 机器合同未定义；
3. SI-LLM-003：Legacy 与 Kernel pointer identity 不一致；
4. SI-LLM-004：lifecycle_state 派生边界；
5. SI-LLM-005：source_modality 与 epistemic modality/source_family 混淆；
6. SI-LLM-006：对象冲突依赖 canonical predicate 互斥语义。

## 10. 权限确认与下一 Gate

明确确认：LLM 没有取得认证、Promote/Revoke、Checker、SAT/UNSAT、E_case 写入或 STOP 权；冲突不会自动综合为事实，pointer suggestion 不等于 binding。

L1 完成后应停在独立授权点。下一阶段若获批准，应先解决 shared schema/source semantics 等阻塞并制定 L2 数据合同；不得从本报告自动推导出模型 baseline 或微调授权。
