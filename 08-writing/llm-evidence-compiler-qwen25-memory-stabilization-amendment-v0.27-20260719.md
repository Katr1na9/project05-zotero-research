# Project05 Qwen2.5 QLoRA 显存稳定化修订 v0.27

日期：2026-07-19

状态：`approved_for_implementation_and_one_stress_preflight_only`

## 1. 修订原因

Task 4 的唯一正式训练在 epoch 1 / optimizer step 3 后触发预注册的 `10.5 GiB` peak reserved VRAM 硬闸门。该次运行完成 48 microbatches、3 optimizer steps，但没有形成完整 epoch、checkpoint 或 adapter；v0.25 已消费并由 v0.26 关闭。

失败不是 OOM，也不是模型质量结果。直接原因是正式训练序列长度包络没有被原单步 smoke 覆盖：

| 累积组 | 16 条总 tokens | 平均 | 最大 |
|---|---:|---:|---:|
| epoch 1 / step 1 | 9,745 | 609.06 | 892 |
| epoch 1 / step 2 | 9,448 | 590.50 | 870 |
| epoch 1 / step 3（失败） | 11,186 | 699.13 | 988 |
| 全局最长 16 条 | 15,999 | 999.94 | 1,021 |

原 smoke 证明一个普通 16-microbatch 累积组可运行，却没有证明最长序列累积组的显存上界。v0.27 修订因此只解决两个问题：减少变长序列之间的 allocator 缓存/碎片积累，以及用冻结训练集的最长 16 条建立保守压力预检。

## 2. 不允许改变的科学配置

以下字段逐字继承 primary config v0.1，不得在本修订中修改：

- Qwen2.5-7B-Instruct 固定 revision；
- 4-bit NF4、double quantization、FP16 compute；
- LoRA `r=16 / alpha=32 / dropout=0.05` 与七类 target modules；
- sequence length `1024`、禁止截断；
- microbatch `1`、gradient accumulation `16`、effective batch `16`；
- train 1,200、training-validation 300、4+2 来源族；
- learning rate、optimizer、scheduler、warmup、gradient norm、seed 与 epoch 顺序；
- RTX 2080 Ti、本地固定 runtime/model snapshot；
- peak reserved VRAM 上限仍为 `11,274,289,152` bytes（10.5 GiB）；
- 24 小时与 30 GB 资源上限；
- adapter-only，禁止 merged model、Hub、服务器和新下载。

不得用降 seq、降 rank、减少 target modules、改 batch、过滤长样本、重排正式训练顺序、换 GPU 或提高显存阈值救场。

## 3. 唯一允许的实现级稳定化

压力预检与未来可能的 primary retry 必须共同使用：

1. 启动前固定 `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128,garbage_collection_threshold:0.8`；
2. 每个 microbatch 完成 backward 后删除 batch/loss 强引用，执行 Python GC 与 `torch.cuda.empty_cache()`，但不重置 peak memory 统计；
3. 保留 gradient checkpointing、4-bit QLoRA 和相同 optimizer；
4. 从模型加载前开始记录全局 `max_memory_allocated` 与 `max_memory_reserved`；
5. 禁止把 `empty_cache()` 后的瞬时值冒充峰值，Gate 仍使用不重置的全局 peak reserved；
6. 所有稳定化动作只改变内存块生命周期，不改变输入、目标、梯度累积边界、optimizer 数学更新或正式训练顺序。

## 4. 最长序列压力集

压力集只从冻结 train 1,200 条中选择，选择器不得读取 `support_decision`、来源族、candidate 内容或攻击标签：

1. 按冻结 tokenizer 与 serialization 计算完整 prompt+target tokens；
2. 按 token length 降序；
3. 同长度按 `SHA-256(example_id)` 升序；
4. 取前 16 条，预期长度为 `982–1021`，总计 `15,999`；
5. 输出只记录长度、计数和 selection digest，不记录原始 ID、prompt、target 或 payload。

该组比失败 step 3 更重，因此适合作为容量包络，而不是训练效果样本。

## 5. 唯一授权的压力执行

用户已授权一次 v0.27 压力预检。它可以：

- 重验全部固定输入、runtime 与 15.24 GB 模型快照；
- 加载 4-bit 底座并附加内存中的 LoRA；
- 对最长 16 条执行一次 assistant-only forward/backward 累积；
- 创建相同 PagedAdamW8bit 与 cosine scheduler，并执行恰好 1 个 optimizer step；
- 记录 loss、gradient norm、allocated/reserved peak、墙钟和清理后显存；
- 立即丢弃内存中 adapter/optimizer，不保存 adapter 或 checkpoint。

它不授权第二次正式训练、checkpoint selection、generation、development/test、C07–C12 或 M3。

## 6. 压力 Gate

只有同时满足以下条件才判 `passed_memory_stress_preflight`：

- 16/16 最长样本无截断完成；
- loss 与 gradient norm 有限；
- optimizer steps 恰好为 1；
- 七类 LoRA target 完整、trainable ratio `<1%`；
- global peak reserved `<=11,274,289,152` bytes；
- 无 CUDA OOM；
- adapter/checkpoint/model files written = 0；
- post-cleanup reserved 回落并记录；
- 无网络、无新依赖、无受保护 split 或下游访问。

失败时写脱敏失败审计并停止，不得尝试第二种 allocator、另一批样本或第二次执行。

## 7. 结果后的权限

- 压力预检失败：保持 v0.26 终态，必须重新裁决硬件/阈值/科学配置；
- 压力预检通过：只证明该稳定化实现覆盖冻结训练集的最长 16 条单步包络，不证明 225-step 稳定完成或 adapter 有效；
- 即使通过，primary retry 仍需新的执行器哈希、失败后从头重训的科学解释，以及用户单独显式授权；
- 禁止跳过 retry 授权直接进入 Task 5。
