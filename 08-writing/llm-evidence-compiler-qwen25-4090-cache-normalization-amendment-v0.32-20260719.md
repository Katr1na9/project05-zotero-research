# Project05 Qwen2.5 QLoRA：RTX 4090 allocator cache 规范化修订 v0.32

日期：2026-07-19

状态：`implementation_ready_pending_explicit_retry_authorization`

适用范围：Project05 主线前端 LLM evidence compiler 的单卡 Qwen2.5-7B-Instruct QLoRA。本文只处理第一次 4090 primary 在显存安全 Gate 上的停止，不授权自动重跑、resume、checkpoint 选择、正式推理或 M3 接入。

## 1. 已冻结事实

1. 4090 准备 Gate 已通过：固定 revision 的 14 个模型文件、运行时、NF4 CUDA 探针和资源上限均合格。
2. 纠正后的最长 16 序列 smoke 已通过：16 microbatches、1 optimizer step、loss/gradient 有限，峰值 allocated 8,143,077,376 bytes，最低同步 free 8,942,387,200 bytes，清理后 reserved 50,331,648 bytes，无 adapter/checkpoint 写入。
3. 第一次 primary 从头启动并完成 32 microbatches、2 optimizer steps；在第 2 步 optimizer 更新和梯度清零后，被 `free >= 1 GiB` Gate 停止。完成 epoch 为 0，checkpoint 为 0，不存在可恢复状态。
4. 第 1 步已落盘样本为：allocated 8,003,503,616 bytes、reserved 22,351,446,016 bytes、driver free 2,344,747,008 bytes。allocated 仅约 7.45 GiB，而 allocator 保留了大量当时未被活跃张量占用的缓存块。
5. 失败不是 CUDA OOM；进程退出后同一 GPU 恢复至约 24,078 MiB free / 34 MiB used。

权威脱敏证据：

- `qwen25-4090-longest-sequence-smoke-result-v0.1.json`，SHA-256 `8E1D7346D464F99F45D036AF8E92AF58A238F240718A6D88AA264684DD721511`；
- `qwen25-4090-primary-training-failure-result-v0.1.json`，SHA-256 `E709BEBF402AE886766226B7364CB8CB192D34A8F1D2777FD8A3A5325F29E701`；
- `qwen25-4090-primary-training-progress-v0.1.jsonl`，SHA-256 `C7DAB1E4E2D0C6561FB7B4849FDE894AD9685A3AF8EA4C38902A4567B97D93CE`。

## 2. 诊断

原 v0.30 同时规定：

- `peak allocated <= 22 GiB`；
- 每个同步点 `driver free >= 1 GiB`；
- `peak reserved` 只作诊断。

但 PyTorch 的未使用 allocator cache 同时计入 reserved 并从 driver free 中扣除。因此，虽然合同声明 reserved 非阻塞，当前实现仍通过 driver free 间接把未使用 cache 变成阻塞量。第一次 primary 正是该口径冲突，而不是实际活跃张量逼近 22 GiB。

## 3. 修订裁决

不调整下列值：

- `maximum_peak_allocated_bytes = 23,622,320,128`（22 GiB）；
- `minimum_synchronized_free_bytes = 1,073,741,824`（1 GiB）；
- 模型、revision、数据 1,200/300、1024 tokens、NF4、LoRA r16/alpha32、microbatch 1、accumulation 16、学习率、optimizer、scheduler、3 epochs、225 steps 和 seed。

只修订内存卫生与度量顺序：

1. 每个 optimizer step 完成且 `optimizer.zero_grad(set_to_none=True)` 后同步采样一次；
2. 若该时刻 driver free 已不低于 1 GiB，直接作为阻塞样本，不调用 cache release；
3. 若低于 1 GiB，调用 `torch.cuda.empty_cache()`，它只释放未被活跃张量占用的 allocator cache；随后再次同步采样；
4. `allocated <=22 GiB` 与 `free >=1 GiB` 均在 cache 规范化后的阻塞样本上判定；释放前 allocated/reserved/free 保留为诊断字段；
5. 规范化后仍不满足任一阈值时立即失败，不再重试或改配置。

该修订不删除 1 GiB 物理余量，不把真实活跃张量误称为 cache，也不改变 forward、backward、optimizer 更新、样本顺序或随机种子。代价仅可能是 cache 重新分配带来的运行时间增加。

## 4. smoke 复用边界

不再执行第二次有 optimizer 的 smoke。允许新合同仅在同时满足以下精确条件时复用已通过的 v0.31 smoke：

- smoke 状态为 `passed_4090_longest_sequence_smoke`；
- smoke artifact SHA-256 精确为 `8E1D7346D464F99F45D036AF8E92AF58A238F240718A6D88AA264684DD721511`；
- 原 contract、training config、authority SHA-256 与新合同 allowlist 完全一致；
- primary 仍绑定 smoke 中相同 GPU UUID。

理由：旧 smoke 在不释放 cache 的更严格路径下已经通过；新修订不会改变 smoke 的模型计算。第一次 primary 暴露的是跨 optimizer step 的 allocator cache 累积，重复单步 smoke 不能增加判别力。

## 5. 重新执行边界

若用户另行显式批准，只允许一次全新 primary v0.2：

- 输出到全新 `server-output/primary-v0.2`，不得覆盖或 resume `primary-v0.1`；
- 从同一固定底座重新初始化 adapter、optimizer 和 scheduler；
- 3 epochs / 225 steps；每 epoch adapter-only checkpoint；
- 失败 manifest 必须额外保存触发时 cache 释放前诊断样本、规范化后阻塞样本和最终 Gate 汇总；
- 第二次失败后不自动重跑、不再临时改阈值。

当前文件本身不是执行授权。执行前必须有新的 authority lock 明确允许一次 v0.2 primary。

## 6. 结论边界

即使 v0.2 训练通过，也只说明固定 task/schema-adapted adapter 完成训练；它不证明优于原版 Qwen，不授权 C07–C12、formal inference、M3 接线或论文正向结论。
