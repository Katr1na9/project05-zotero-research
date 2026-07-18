# Project05 主线 LLM 证据编译层：Qwen2.5 路线恢复记录

日期：2026-07-18  
状态：`qwen25_paired_route_locked_design_only`

## 本轮裁决

用户已批准恢复 Qwen，并采用同一固定底座的配对比较：

- `QWEN-GENERAL`：原版 `Qwen/Qwen2.5-7B-Instruct`，adapter 关闭；
- `QWEN-ADAPTED`：同一 checkpoint，启用 `project05_obs_compiler` QLoRA adapter。

这不是全参数微调。底座保持冻结，可训练参数必须 `<1%`，只保存 adapter。LLM 仍是 Project05 主线前端的证据语义编译层；M3 继续负责可支持溯源粒度、最低成本取证动作和 STOP。

## 新增权威工件

- `08-writing/llm-evidence-compiler-qwen25-paired-route-amendment-v0.1-20260718.md`
- `09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.2.json`

OLMo 修订案与此前 Qwen 撤销记录作为历史保留，但不再具有当前模型选择权威。主线融合设计、public/private 隔离、机械准入、测试族隔离及 `controller_eligible=false` 约束保持不变。

## 当前硬停

本轮未安装或变更模型环境，未下载 tokenizer/权重，未训练，未运行正式推理，未执行 C07–C12 模型调用，未接线 M3，也未修改 `run_mvp.py`、冻结案例和旧结果。

下一步是无模型依赖的公平性合同和训练数据复验；通过后才能单独申请 tokenizer/runtime/权重授权。

## 验证

- Qwen authority / fairness / data fail-closed 定向测试：11/11 通过；
- 全部主线 compiler 回归：91/91 通过；
- 全实验测试：546 passed，6 skipped；
- 未产生模型、tokenizer、adapter、训练 checkpoint 或正式推理输出。
