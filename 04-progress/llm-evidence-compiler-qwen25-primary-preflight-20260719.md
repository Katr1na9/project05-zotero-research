# Project05 主线 Qwen2.5 QLoRA：Task 3 零步预检记录

日期：2026-07-19
状态：`passed_zero_step_primary_preflight_primary_training_closed`

## 结论

Task 3 的正式零步预检已经通过。本次只验证固定数据、固定 revision 权重、本地运行时、4-bit 模型装载、LoRA 模块覆盖、参数比例、显存、磁盘与时长容量；没有执行模型 forward、generation、loss、backward 或 optimizer step，也没有保存 adapter/checkpoint。

因此，本结果只证明当前本地 RTX 2080 Ti 路线具备进入正式训练闸门的工程容量，不证明微调有效，不构成论文正向结果。Task 4 正式训练仍然关闭，必须取得新的明确授权。

## 已通过的闸门

| 闸门 | 预检结果 |
|---|---:|
| 训练 / training-validation 数据 | 1200 / 300 |
| 来源族 | 4 train + 2 validation，零重叠 |
| supported / unsupported | 两个 split 均为 50% / 50% |
| 固定模型 | `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28` |
| 快照复核 | 14 文件，15,242,807,270 bytes，全部重新计算 hash |
| LoRA 模块 | 7 类目标模块全部存在，各 28 个，共 196 个 |
| 可训练参数 | 40,370,176 / 4,393,342,464 = 0.918894%，低于 1% |
| 峰值预留显存 | 10,064,232,448 / 11,274,289,152 bytes，通过 |
| 清理后预留显存 | 2,097,152 bytes |
| 线性训练预测 | 5.174 小时 |
| 保守总时长预测 | 16.348 小时，低于 24 小时 |
| 含 2 GB 预留的资源预测 | 26,186,006,603 bytes，低于 30 GB |

## 零步边界

- forward / generation / loss / backward：全部 0；
- optimizer / scheduler 对象与 optimizer step：全部 0；
- adapter / checkpoint 写出：0；
- 网络或新增下载：无；
- C07–C12、development/test、M3、服务器和 Paper A：均未访问或修改；
- 本次 PowerShell 仅使用进程级 `-ExecutionPolicy Bypass` 启动受控脚本，没有更改系统执行策略。

## 可复核工件

- 本地 Git-ignored 原始审计：`.local-qwen25-smoke/local-output/primary-preflight-v0.1.json`，4442 bytes，SHA-256 `56BA67995A5CA5A0FEEAE3CAAF780F0A65A678B54579C213F5BA1CB5F1C7DF73`；
- 仓库内脱敏结果：`09-experiments/llm_evidence_compiler_mainline/results/qwen25-primary-preflight-result-v0.1.json`；
- 零步预检合同：`09-experiments/llm_evidence_compiler_mainline/contracts/qwen25-primary-preflight-contract-v0.1.json`；
- Task 3 执行授权：`09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.23.json`；
- Task 3 结果终态：`09-experiments/llm_evidence_compiler_mainline/contracts/authority-lock-v0.24.json`。

## 当前硬停

Task 4 正式 QLoRA 训练、checkpoint 选择、paired runner、正式推理、C07–C12 运行和 M3 接线均未获授权。下一项如获明确批准，才可按冻结配置执行 3 epochs / 225 optimizer steps 的 adapter-only 主训练。

## 验证

- primary + smoke + preflight + result 定向测试：51/51 通过；
- 相邻 LLM compiler 回归：149 项中 145 passed、1 skipped、2 failures、1 error；
- 相邻回归的非绿项与 Task 1–2 基线完全一致：citation report 冻结 SHA 不匹配、positive-remap 历史 records root 缺失、WP2 rule snapshot sidecar SHA 不匹配；
- Task 3 未修改上述异常涉及的路径，也没有通过改动冻结工件来消除它们。
