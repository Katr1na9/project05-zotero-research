# LLM evidence compiler：Qwen2.5 4090 optimizer 稳定性诊断通过

日期：2026-07-19

## 结论

v0.33 单次 optimizer stability diagnostic 已通过。LoRA 可训练参数的更新器由 bitsandbytes `PagedAdamW8bit` 替换为 PyTorch `AdamW` 后，在相同正式 train split、epoch ordering、seed、1024-token 上限、LoRA 配置、gradient accumulation 和 scheduler 下完成 180/180 optimizer steps 与 2,880/2,880 microbatches。

本次诊断超过 v0.32 primary v0.2 的第 173 步故障点，未复现 `CUDA error: an illegal memory access was encountered`。该结果支持把 `torch.optim.AdamW` 作为下一次 fresh primary 的稳定 optimizer 候选；它不是正式训练结果，不授权 checkpoint 选择、推理、评价或 M3 接入。

## 执行记录

- GPU：NVIDIA GeForce RTX 4090，固定 physical index 2 与原 smoke UUID；
- optimizer：`adamw_torch`，`betas=(0.9,0.999)`、`eps=1e-8`、`foreach=False`、`fused=False`、`capturable=False`；
- bitsandbytes：仍用于 4-bit NF4 + double quantization 底座，不再用于 optimizer；
- `CUDA_LAUNCH_BLOCKING=1`；
- wall time：3,799.224 seconds；
- trainable parameters：40,370,176 / 4,393,342,464，ratio 0.00918894；
- loss：2,880/2,880 有限；gradient norm：180/180 有限；
- adapter/checkpoint/optimizer state/generation：0 / 0 / 0 / 0。

## 显存 Gate

- peak allocated：8,301,579,264 bytes，低于 23,622,320,128 bytes 上限；
- peak reserved：23,695,720,448 bytes，仅作诊断，不作 blocking；
- minimum synchronized free：1,075,970,048 bytes，高于 1,073,741,824 bytes 下限；
- cache normalization：180 steps 中 105 次触发；
- post-cleanup reserved：69,206,016 bytes，低于 268,435,456 bytes 上限；
- 进程退出后 GPU：24,094 MiB free / 18 MiB used。

显存余量仍接近 1 GiB blocking 下限，因此下一次正式训练必须继续使用 v0.32 cache-normalized memory protocol，不得取消 cache release 或降低阈值。

## 审计工件

- `qwen25-4090-optimizer-stability-diagnostic-v0.1.json`：SHA-256 `DCDF92669636D589831BD0D44363EF684F4BCB481146BE0B75D0F8691A978158`；
- `qwen25-4090-optimizer-stability-progress-v0.1.jsonl`：SHA-256 `851681BFC6B8ED5E12842E8248E3DA2610E1F77297B72C18105A771E01E05E86`；
- raw pair payload、raw generation、模型权重、adapter、checkpoint 与 optimizer state 均未下载或提交。

## 启动前修正

第一次 launcher 尝试在模型加载前因 v0.3 三层合同只解析一层而 fail-closed，forward/backward/optimizer step 和模型工件写入均为 0。修正为逐级 SHA 验证的递归合同合并后，19 项本地 4090/optimizer 测试通过，再执行唯一一次 180-step 诊断。该 preflight 失败不计为 optimizer-bearing diagnostic execution。

## 下一 Gate

当前硬停在 fresh formal primary authorization：

- 不使用或评价 v0.2 epoch 1/2 checkpoint；
- 不自动 resume 或重跑；
- 不执行 training-validation generation、General/Adapted 对照、C07-C12、M3 接入；
- 下一步若获用户批准，须以标准 AdamW 从固定底座 fresh 初始化，完成 225-step / 3-epoch 正式训练，并保持其余科学配置及显存 Gate 不变。
