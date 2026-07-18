# Project05 主线 LLM 证据编译层：WP4 CTI 来源 Gate 状态

日期：2026-07-17  
状态：`pending_user_source_review`  
结论：M3 系列方法与 LLM 编译层可以并行推进；WP4 元数据闸门、校验器和测试已完成，但尚未授权检索任何 CTI 正文。

## 1. 并行边界

LLM 路线只负责：

```text
日志 / CTI / provenance
→ 来源约束编译与语义对齐
→ controller_eligible=false 的 sidecar
→ 双方分别冻结后适配选定的 M3 controller
```

M3 继续负责调查粒度判断、取证动作规划与 STOP。LLM 不直接归因、不选动作、不控制停止。

本轮没有修改：

- `09-experiments/scripts/run_mvp.py`
- `09-experiments/scripts/run_m3star.py`
- `09-experiments/scripts/run_m3star_experiment.py`
- `09-experiments/results/m3star_*`
- C07–C12 real cases
- 既有 EvidenceClaim / alignment schemas

旧主线三个锁定文件的 SHA-256 均与 WP4 catalog 一致。LLM sidecar 在 compiler contract 与选定的 M3 controller interface 各自冻结前始终为 `controller_eligible=false`。

## 2. 已完成工件

- 权威来源目录：`09-experiments/llm_evidence_compiler_mainline/wp4/cti-text-source-catalog-v0.1.json`
- 来源 Gate 校验器：`09-experiments/scripts/validate_compiler_cti_source_gate.py`
- 负向测试：`09-experiments/tests/test_llm_evidence_compiler_wp4_source_gate.py`
- 实验 amendment：`08-writing/llm-evidence-compiler-cti-text-amendment-v0.1-20260717.md`
- 当前 readiness：`09-experiments/llm_evidence_compiler_mainline/wp4/cti-source-gate-readiness.json`

readiness 终态：

- `status=pending_user_source_review`
- eligible sources：3
- pending decisions：3
- activated sources：0
- bounded retrieval：false
- payload normalization：false
- component runtime：false
- model / embedding：false
- training / formal inference：false
- C07–C12 execution：false
- controller integration：false

## 3. 待逐项批准的三个来源

| 角色 | 候选 | 有条件用途 | 主要限制 |
|---|---|---|---|
| `unit` | CTID Blueprints 自有 Intrusion Analysis JSON 示例 | schema、pointer、reject/abstain 单元路径 | 只取固定 JSON；排除 PDF、模板及 actor/campaign/executive 示例 |
| `development` | MITRE ATT&CK malware/tool procedure descriptions | adapter/prompt 与合同调试 | 排除 intrusion-set、campaign、actor attribution、APT29、protected-family match；保留 MITRE attribution |
| `component_validation` | TRAM 所列 7 个 CISA 第一方通告候选 | held-out component interface pilot | 只授权有限检索；逐文档回到 `cisa.gov` 验证政府作者、来源和第三方嵌入物，任一不明即删除 |

建议裁决为三个候选均 `conditional_approve`，但批准只产生以下权限：固定 revision 的有限检索、逐文档许可/来源核验、protected-family exact + normalized 5-gram Jaccard 排除扫描。它不授权组件 runtime、模型、embedding、训练、正式推理、C07–C12 或 M3 集成。

继续保持拒绝：TRAM 全量 mjson、CISA CSAF 全库、CTID adversary emulation library。MISP Galaxy 仅作 inactive reserve。

## 4. 验证结果

- WP4 语法与 JSON：通过
- WP4 source-gate tests：7/7 通过
- 全部 compiler tests：54/54 通过
- 全实验测试：493 passed，6 skipped，346 subtests passed，0 failed

Gate 测试覆盖：未批准不得检索；三个 publisher family 不得跨角色；拒绝源不能激活；缺角色/家族时 fail closed；旧主线哈希变化时 fail closed；并行 M3 时 sidecar 不得被 controller 消费。

## 5. 下一步

1. 用户逐项批准或拒绝三个来源。
2. 若三个角色均获有条件批准，仅执行有限检索、逐文档许可/来源检查和 payload exclusion scan。
3. 扫描通过后另出 runtime Gate；不自动安装或运行 CTINexus、模型或 embedding。
4. M3 controller 冻结后再建立版本化 adapter；在此之前不修改 M3 运行接口。

当前阶段不需要双人语义审计。只有未来要声称“语义关系正确”“无支撑断言减少”或采用人工 unsupported 指标时，才另行设计最小人工审计。
