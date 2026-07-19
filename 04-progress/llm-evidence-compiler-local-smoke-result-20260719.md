# LLM evidence compiler：本地 QLoRA smoke 结果

日期：2026-07-19
状态：`passed_one_step_adapter_only_smoke`
执行位置：本地 NVIDIA GeForce RTX 2080 Ti

## 结论

固定 revision 的 `Qwen/Qwen2.5-7B-Instruct` 已在本地完成一次受限、adapter-only 的 QLoRA optimizer step，并通过预注册的运行时、模型哈希、可训练参数比例、显存、资源和信息边界 Gate。

这个结果只证明当前运行栈能够执行受限 smoke；它不证明 adapter 带来质量增益，也不授权正式训练、正式推理、C07–C12 执行、M3 接入或论文正向结论。

## 准备 Gate

- 固定 revision：`a09a35458c702b33eeacc393d103063234e8bc28`
- 白名单文件：14/14
- 仓库字节数：15,242,807,270
- 权重字节数：15,231,271,888
- 四个权重分片的字节数与 SHA-256：全部匹配合同
- GPU：NVIDIA GeForce RTX 2080 Ti，compute capability 7.5
- NF4 CUDA 探针：通过
- 环境、缓存和输出：24,023,078,772 / 30,000,000,000 字节

本地 preparation audit 位于 Git-ignored 运行目录，其 SHA-256 为：

`315837270E84C020D097B471D44A63E1C933B7534E52831882F575D3401F206A`

## 单步 smoke

| 指标 | 结果 | Gate |
|---|---:|---:|
| 选中样本 | 20（10 supported + 10 unsupported） | 固定为 20 且平衡 |
| 训练 microbatch | 16（8 + 8） | 固定为 16 且平衡 |
| optimizer step | 1 | 必须恰好为 1 |
| loss first / last / mean | 0.9473 / 0.8813 / 0.6207 | 全部有限 |
| gradient norm | 1.8352 | 记录项 |
| 可训练参数 | 40,370,176 / 4,393,342,464 | 低于 1% |
| 可训练比例 | 0.918894% | 低于 1% |
| 峰值 reserved VRAM | 10.417969 GiB | 不超过 10.5 GiB |
| 显存余量 | 84 MiB | 正值，但很窄 |
| smoke wall time | 82.781 秒 | 不超过 180 分钟 |

adapter 已以三个文件保存并成功重载；未保存 merged model。一次 training-validation 生成产生 6 个 token，只在审计中记录生成文本 SHA-256，没有记录原文。

本地 smoke audit 位于 Git-ignored 运行目录，其 SHA-256 为：

`00A952B64A467FBF638DE84FBA06C1A5EEE44447DF3D448D1F23A0EF64435C73`

## 信息与授权边界

- 未把原始训练对或生成文本写入版本化审计。
- 未访问 development/test 或 C07–C12。
- 未运行正式推理。
- 未接入或停止 M3。
- 未修改 Paper A。
- 未连接服务器；服务器路线继续保持废止。

## 验证

专项测试：

`python -m unittest 09-experiments/tests/test_qwen_qlora_smoke.py -v`

结果为 17/17 通过。测试覆盖合同、路径边界、固定 revision、运行时 pin、均衡选择、assistant-only loss mask、adapter-only 输出、v0.21 哈希链和正式训练 Gate 关闭。

全部 `test_llm_evidence_compiler*.py` 回归共运行 149 项：145 通过、1 跳过、2 失败、1 错误。三项未通过分别是既有 citation report 冻结 SHA 不一致、positive-remap 历史 records 根目录缺失、WP2 rule snapshot sidecar SHA 不一致。相关测试、脚本和证据文件均未被本任务修改，因此没有改写冻结材料来消除这些既有状态。

本地 preparation/smoke audit 与版本化结果锁已按 audit SHA、revision、字节数、optimizer step、microbatch、loss、trainable ratio、peak VRAM 和 adapter 文件逐字段交叉核对，结果通过。

## 风险与下一 Gate

峰值显存虽然通过，但距离上限只有 88,080,384 字节（84 MiB）。因此本次结果不能外推为多步正式训练稳定性证明。正式训练必须另立合同和显存策略，并经用户单独授权；当前仍硬停在结果复核。

机器可读的脱敏结果锁：

`09-experiments/llm_evidence_compiler_mainline/results/qwen25-qlora-local-smoke-result-v0.2.json`
