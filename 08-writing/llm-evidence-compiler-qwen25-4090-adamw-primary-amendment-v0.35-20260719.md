# Project05 Qwen2.5 4090 AdamW 正式训练修订 v0.35

日期：2026-07-19

用户在 v0.34 optimizer stability Gate 通过后要求“继续推进”。本修订授权一次 fresh 225-step / 3-epoch formal primary；不授权复用 v0.2 checkpoint、自动重跑、checkpoint 选择、推理、评价或 M3 接入。

## 冻结配置

固定 Qwen2.5-7B-Instruct revision、1,200/300 数据、1024 tokens 禁止截断、LoRA r16/alpha32/dropout0.05、七类 target modules、microbatch 1、accumulation 16、learning rate 2e-4、cosine/warmup7、gradient clipping 1.0、seed `2026071601` 与单卡 4090 均不变。

唯一训练实现变化延续 v0.33：LoRA 参数使用单张量 `torch.optim.AdamW`，`betas=(0.9,0.999)`、`eps=1e-8`、`foreach=False`、`fused=False`、`capturable=False`。bitsandbytes 继续只承担 NF4 double-quantized base loading。

## 执行与 Gate

- 从固定底座 fresh 初始化 adapter、optimizer、scheduler；
- 3 epochs、225 optimizer steps、3,600 microbatches；
- 每 epoch 保存 adapter-only、optimizer、scheduler、RNG 与 trainer-state；
- 每步执行有限值、allocated/free memory 与 24-hour wall Gate；
- 继续使用 cache-normalized free-memory protocol，阈值不降低；
- 输出到全新 `server-output/primary-adamw-v0.35`，拒绝覆盖或 resume；
- 完成后只证明训练运行完成，不证明 adapter 优于 General。

任何 CUDA、OOM、数值、资源或显存 Gate 失败均立即停止，不自动重跑、resume、换卡或改参。通过后硬停在 checkpoint selection / training-validation evaluation 的单独授权点。

