# Project05 Qwen2.5 4090 optimizer 稳定性修订 v0.33

日期：2026-07-19

适用范围：Project05 主线前端 LLM evidence compiler 的单卡 Qwen2.5-7B-Instruct QLoRA。本文只授权优化器故障诊断、实现替换和一次有界稳定性压力诊断；不授权正式重训、checkpoint 选择、推理、评价或 M3 接入。

## 1. 已观察故障

v0.32 primary v0.2 在第 173/225 个 optimizer step 结束附近失败，完成 2/3 epochs 和 2,784 microbatches。异常为 `CUDA error: an illegal memory access was encountered`，调用栈位于 bitsandbytes `PagedAdamW8bit` 的 `optimizer.step()` / CUDA 同步路径。

故障发生时：

- loss 与 gradient norm 均为有限值；
- memory Gate 通过，peak allocated 为 8,003,503,616 bytes；
- minimum synchronized free 为 1,073,872,896 bytes，高于 1 GiB 下限；
- 触发点 free 为 3,338,797,056 bytes；
- GPU 进程退出后显存恢复到 18 MiB used。

据此，当前证据支持“bitsandbytes paged optimizer 运行时稳定性故障”，不支持把它归因为 OOM、数据截断、梯度发散或科学配置失败。由于 CUDA 错误可能异步报告，不能声称已经定位到某一条具体内核指令；本修订只把故障域限定在 optimizer 更新链路。

## 2. 替换范围

保留以下科学配置不变：

- `Qwen/Qwen2.5-7B-Instruct` 与固定 revision；
- 4-bit NF4、double quantization、FP16 compute；
- LoRA r16 / alpha32 / dropout 0.05 与七类 target modules；
- 1,200 train / 300 training-validation、1024 tokens、禁止截断；
- microbatch 1、gradient accumulation 16、effective batch 16；
- learning rate 2e-4、weight decay 0、cosine scheduler、warmup 7；
- gradient clipping 1.0、seed `2026071601`。

仅将 LoRA 可训练参数的 optimizer 从 bitsandbytes `PagedAdamW8bit` 替换为 PyTorch `torch.optim.AdamW`。底座的 NF4 量化仍由 bitsandbytes 提供，因此本修订不是取消 QLoRA。

AdamW 实现写死为：`betas=(0.9, 0.999)`、`eps=1e-8`、`foreach=False`、`fused=False`、`capturable=False`。禁用 fused/foreach 是为了使诊断走最保守的单张量 PyTorch 更新路径。优化器只接收 `requires_grad=True` 的 LoRA 参数，预计增加的状态显存远低于 4090 的既有余量，但仍必须服从原 22 GiB allocated 上限和 1 GiB synchronized free 下限。

## 3. 一次性稳定性诊断

授权一次 fresh diagnostic：

- 从固定底座重新初始化 adapter、optimizer 和 scheduler；
- 使用正式 train split、正式 epoch ordering 和相同 seed；
- 执行 180 optimizer steps，即 2,880 microbatches；
- 180 steps 覆盖并超过旧故障点 173；
- scheduler 总步数仍为正式计划的 225；
- 设置 `CUDA_LAUNCH_BLOCKING=1`，使新 CUDA 故障尽量在实际调用点同步报告；
- 每个 optimizer step 后做同步显存采样和原 memory Gate；
- 不保存 adapter、optimizer、scheduler、RNG 或 checkpoint；
- 不访问 training-validation、development、C07-C12 或 M3；
- 不执行 generation。

该诊断会更新并最终丢弃临时 LoRA 参数，因此不能作为正式训练结果、不能参与 checkpoint 选择，也不能用其 loss 写论文结论。

## 4. 判定 Gate

只有同时满足以下条件才记为 optimizer stability passed：

1. 完成 180/180 optimizer steps 和 2,880 microbatches；
2. 所有 loss、gradient norm 均为有限值；
3. 无 CUDA illegal access、OOM 或其他 runtime error；
4. allocated/free memory Gate 全程通过；
5. 清理后 reserved memory 不超过 256 MiB；
6. adapter/checkpoint/generation 数均为 0；
7. 仅产生脱敏 progress、pass/failure audit。

若失败，立即停止，不自动切 optimizer、不降低序列长度/rank/batch、不 resume。若通过，只能得出“标准 AdamW 在一次覆盖旧失败点的诊断中稳定”，下一步仍需用户单独批准 fresh 225-step 正式训练。

## 5. 仍关闭的范围

- v0.2 epoch 1/2 checkpoint 的选择、恢复或评价；
- 新正式 primary、自动 retry/resume；
- training-validation generation、General/Adapted 公平对照；
- development/test/C07-C12 推理；
- M3 runtime 接入；
- merged model、Hub upload；
- Paper A 结果修改或正向 LLM 论文主张。
