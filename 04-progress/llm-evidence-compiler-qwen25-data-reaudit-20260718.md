# Project05 主线 Qwen2.5 数据复验与公平性合同

日期：2026-07-18  
状态：`superseded_by_v0_2_kev_formal_null_rejected`

## 结论

原版 Qwen 与 QLoRA Qwen 的同底座公平性合同已经冻结；现有历史语料只做只读复验，没有复制进主线。后续 CISA KEV 文献审查已经否决其正式 train-null 资格，并取消 50 条单人审核依赖。权威终态转至 `qwen-data-reuse-readiness-v0.2.json`；仍不能进入 tokenizer、环境或训练阶段。

## 公平性合同

`09-experiments/llm_evidence_compiler_mainline/contracts/qwen-paired-fairness-contract-v0.1.json` 固定：

- General 与 Adapted 共用 `Qwen/Qwen2.5-7B-Instruct@a09a354...e8bc28`；
- base、tokenizer、quantization、prompt、schema、public input、decode、hardware、admission 和 scorer 必须逐项 hash 相同；
- 唯一允许差异是 `adapter_state`；
- 同一加载底座内记录 adapter off/on；
- 独立统计单位是 6 个 case/attack chain，重复生成不是独立样本；
- 测试输出不能用于改 prompt、训练数据、超参数、checkpoint 或 Gate。

## 历史候选复验

| Split | Observation | Null | Total | 来源族 | 比例判定 |
|---|---:|---:|---:|---:|---|
| train | 2394 | 2 | 2396 | 4 | **失败** |
| training-validation | 483 | 517 | 1000 | 2 | 候选通过 |

历史 exclusion audit 为 exact=0、near=0、blocked-family=0，最大 Jaccard 0.4857，小于冻结阈值 0.85；但迁入主线前仍须按当前路径和 hash 重跑。3396 条作者队列的 decision 全空，因此这些只是提案记录，不是已冻结训练样本。

## Train-null 缺口

正式 1200-packet 训练集在 40%–60% 角色约束下至少需要 480 条 null。当前只有 2 条，最低缺口 478。

V3-BN-01 的固定 CISA KEV 工件在 CC0 许可下可以处理，但快速证据审查未找到同任务直接先例，并确认 KEV 的 CVE 级利用状态不能提供案件级事件未发生的真值。其正式 train-null 贡献固定为 0；50 条空白队列只保留为历史工件，不再要求用户审核。当前最低缺口仍为 478。

## 当前硬停

- 不构建正式训练 packets；
- 不用 validation null 填 train；
- 不把缺攻击行、路径名或 extractor failure 当 null；
- 不放宽 CAM-LDS 禁令；
- 不下载 tokenizer/权重，不安装环境，不训练。

机器可读终态位于 `09-experiments/llm_evidence_compiler_mainline/qwen-data-reuse-readiness-v0.2.json`。

## 下一步

下一步不再做 KEV 单人审核，而是调研具有显式非蕴含、传感器覆盖保证或受控反事实真值的独立 train-null 来源。候选必须先过许可与外部证据 Gate，再进入行级质量抽检。未解决 478 条缺口前，继续下载 Qwen 或安装训练环境没有科学意义。

## 验证

- 公平性/数据复验定向测试包含在 Qwen authority suite 中：11/11 通过；
- 全部主线 compiler 回归：91/91 通过；
- 全实验回归：546 passed，6 skipped。
