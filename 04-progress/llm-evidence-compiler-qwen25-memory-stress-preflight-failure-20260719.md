# Project05 Qwen2.5 QLoRA：v0.27 最长序列显存压力预检结果

日期：2026-07-19

状态：`failed_memory_stress_preflight_peak_reserved_no_artifact`

## 裁决

v0.27 唯一获授权的最长序列压力预检完成了全部 `16/16` microbatches 和恰好 `1` 个 optimizer step，loss 与 gradient norm 均为有限值，但 PyTorch 全局 peak reserved VRAM 达到 `13,788,774,400` bytes，超过冻结的 `11,274,289,152` bytes（10.5 GiB）上限。因此压力 Gate 失败，v0.27 执行额度已消费，不得自动重跑或换用另一种 allocator。

本次失败不是 CUDA OOM，也不是模型质量结果。它证明当前 allocator 碎片治理与逐 microbatch 清理不足以在原 10.5 GiB reserved-memory 口径下覆盖最长序列累积组及 optimizer step。

## 冻结执行

| 项目 | 结果 |
|---|---:|
| 压力样本 | 16 条 |
| token 范围 | 982–1,021 |
| token 总量 | 15,999 |
| microbatches | 16 / 16 |
| optimizer steps | 1 / 1 |
| 墙钟 | 291.515 秒 |
| checkpoint | 0 |
| adapter | 未保存 |
| generation | 0 |

稳定化措施严格采用：

`PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128,garbage_collection_threshold:0.8`

每个 microbatch backward 后均删除 batch/loss 引用、执行 Python GC 和 `torch.cuda.empty_cache()`；未在循环内重置全局 peak 统计，也未改变 Qwen revision、NF4、LoRA、1024 tokens、batch/accumulation、数据、seed、optimizer、scheduler、GPU 或 Gate 上限。

## 数值与显存结果

| 指标 | 结果 |
|---|---:|
| loss first / last / mean | 0.314888 / 0.349060 / 0.369600 |
| gradient norm | 1.248153 |
| trainable ratio | 0.918894% |
| peak allocated | 10,428,610,048 bytes |
| peak reserved | 13,788,774,400 bytes |
| frozen reserved limit | 11,274,289,152 bytes |
| 超出量 | 2,514,485,248 bytes |
| 清理后 reserved | 50,331,648 bytes |
| CUDA OOM | 否 |

每个 microbatch 清理后的 current reserved 均为 `8,654,946,304` bytes；全局 peak reserved 在完整累积与 optimizer step 路径中升高。最终 Gate 仍以未重置的全局 peak reserved 裁决，不能用清理后瞬时值替代。

## 完整性与边界

- 本地脱敏结果：6,284 bytes，SHA-256 `AFF78D98210515E675729BE0A5A5D812EB145701AB6725E9DA45098E3388C272`；
- 压力 authority SHA-256：`8EFDD05F782A1C21C95F963CAF4F1F9BE27D0054C6459DEDAE75AB3B0CB8711F`；
- 压力 contract SHA-256：`87F810B8E4AB49756B2DE53B17AD327216B2E47CFFFC4ACBA5060A20F7EAE5F7`；
- 运行后 GPU 为 0 MiB、0% utilization；
- 未记录原始标识、prompt、target 或 payload；
- 未访问 development/test、C07–C12 或 M3；
- 未连接服务器、未下载、未安装依赖、未修改 Paper A；
- 未保存 adapter、checkpoint 或 merged model。

## 当前硬停

v0.27 只能支持“稳定化方案未通过原显存 Gate”的容量结论，不能支持任何 adapter 效果或正式训练结论。正式重训、checkpoint selection、generation、正式推理、C07–C12 与 M3 接线全部关闭。

如需继续，必须另行形成容量决策：要么修改资源度量/阈值并说明其科学含义，要么改变会影响训练配置的容量措施；任何路线均需要新修订和用户显式授权，不能在 v0.27 下尝试第二 allocator 或第二次压力运行。
