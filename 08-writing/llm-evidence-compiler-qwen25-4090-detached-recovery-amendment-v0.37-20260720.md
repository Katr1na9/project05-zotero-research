# Project05 Qwen2.5 4090 后台恢复重训修订 v0.37

日期：2026-07-20

用户在知悉 v0.35 于第 194/225 步被外部会话中断后，明确批准恢复重新训练。本修订把该决定解释为推荐的 **fresh detached rerun**：从固定底座重新初始化一次正式训练，不复用、不选择、不评估 v0.35 的任何 checkpoint。

## 冻结不变项

Qwen2.5-7B-Instruct revision、1,200/300 数据、1024 tokens 禁止截断、LoRA r16/alpha32/dropout0.05、七类 target modules、microbatch 1、accumulation 16、3 epochs、225 optimizer steps、learning rate `2e-4`、cosine/warmup7、gradient clipping 1.0、seed `2026071601`、单张量 `torch.optim.AdamW`、NF4 4-bit base 与 cache-normalized memory Gate 全部保持 v0.35 不变。

唯一执行性变化是启动生命周期：

- 使用 `nohup + setsid` 启动独立 worker，使训练不依赖 SSH 前台会话；
- stdout/stderr 写入 `/home/myy/project05-qwen25-4090-v0.1/server-output/primary-adamw-detached-v0.37-launch/worker.log`；
- PID 写入同目录 `worker.pid`；
- 正式结果写入全新的 `server-output/primary-adamw-detached-v0.37`；
- worker 启动前继续验证用户、路径边界、固定 smoke GPU、空闲显存、合同哈希和输出目录不存在。

后台化只修复进程生命周期，不改变训练方法、超参数或科学比较。若 worker 出现 CUDA、OOM、数值、资源或显存 Gate 失败，立即停止，不自动 retry、resume、换卡或改参。

## 授权范围

仅授权一次全新 225-step / 3-epoch detached AdamW primary。v0.35 输出保持只读，epoch 1/2 checkpoint 不进入新运行。

本授权仍不包括 checkpoint 选择、training-validation generation、General vs Adapted 评价、C07–C12 正式推理、M3 接入、model merge、Hub upload、Paper A 结果修改或 DOCX/PPT/PDF 生成。训练完成后硬停在独立评价授权点。
