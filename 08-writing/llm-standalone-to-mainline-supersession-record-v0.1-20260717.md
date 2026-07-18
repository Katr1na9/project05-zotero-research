# Project05 LLM 独立支线转主线前端路线替代记录 v0.1

日期：2026-07-17  
状态：`effective_for_wp0_wp1`  
用户裁决：已批准 `llm-evidence-compiler-mainline-integration-design-v0.1-20260717.md`，继续下一步

## 1. 权威路线

当前权威目标是：把 LLM 作为 Project05 主线的证据语义编译层，将日志、CTI 文本和 provenance 事件转换为可回指的案件证据图，再由既有控制器判断可支持溯源粒度并在成本约束下选择取证动作或 STOP。

`llm-apt-provenance-research-design-v0.1/v0.2`、Qwen2.5 QLoRA amendment、Phase 1 implementation plan、训练来源 Gate 和 train-null amendment 保留为历史探索材料，不再授权独立 Paper B、训练或正式推理。

## 2. 可复用与不可继承

允许复用：

- public/private 物理分包；
- request/candidate/canonical ID 隔离；
- 机械 pointer/schema admission；
- dependency-free stub；
- prompt/config/run hash chain；
- 许可、来源和 payload exclusion 的 fail-closed 思想。

不得自动继承：

- 任何模型权重下载授权；
- torch/transformers/bitsandbytes 环境安装授权；
- QLoRA 训练或训练语料使用授权；
- 旧 Paper B 标题、RQ、正向结果或 G2 人工声明；
- Phase 2/3、LLM selector 或 LLM 直接动作控制。

## 3. WP0–WP1 授权

本次只授权：

1. 冻结路线、设计和 prior-art review 哈希；
2. 新建 candidate/entity/link/decision/run manifest 合同；
3. 实现 public request builder、机械准入器和 stub；
4. 运行信息边界、负向路径及 legacy 不变测试；
5. 形成 M1 接口审阅包。

完成后在 M1 硬停。不得安装模型环境、下载权重、训练、正式推理、覆盖 C07–C12 或修改 `run_mvp.py`。

## 4. 权威哈希

| 工件 | SHA-256 |
|---|---|
| 主线融合设计 v0.1 | `A99D4895BF0BD95DF40B2E2A342ADCF07A5BBD10369FCD84935AE0C58D00B002` |
| prior-art review v0.1 | `C79272788C67D4F4FE2ACEDC1552D6A191BC772DDEAE20A3E95E7C0756C3658F` |
| `run_mvp.py` WP1 前基线 | `A7EBCF2739B7CD708011DB378D0F18AF3EB970C6236813BE7F8258D5394A952E` |
| `evidence_claim.schema.json` WP1 前基线 | `5FCA1B77512C5C966860781214DCB83BEE76CFECA56B9E4AE3B91657D73CA63A` |
| `alignment_state.schema.json` WP1 前基线 | `462C8E5F657A4467FC4B945FBAB60A2FF86D1D1470DBA8D5C3937F46E14EA61E` |

机器可读副本位于 `09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.1.json`。

