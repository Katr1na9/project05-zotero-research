# Project05 Qwen2.5 QLoRA 容量度量与配置修订 v0.29

日期：2026-07-19

状态：`draft_for_user_review_no_execution_authority`

适用范围：Paper B / LLM evidence compiler 本地 QLoRA 容量 Gate。本文不授权新的压力预检、正式训练、checkpoint selection、generation、C07–C12 或 M3 接线。

## 1. 执行摘要

本修订的推荐裁决是：

1. **不追高 `peak reserved` 阈值**。不得把 10.5 GiB 直接抬到 v0.27 观察到的 12.84 GiB，也不得把 v0.27 事后改判为通过；
2. **修正硬 Gate 的测量构念**。保留 10.5 GiB 这个预注册数值，但将它用于 PyTorch `peak allocated`，同时加入同步采样的 CUDA `minimum free memory >= 512 MiB` 与“无 CUDA OOM”硬条件；
3. **`peak reserved` 保留为诊断指标，不再作为物理显存硬上限**。原因是本机记录的 `peak reserved` 已超过显卡报告的物理总显存，不能在当前 Windows/WDDM + PyTorch 2.3.1 栈中被解释为逐字节的物理驻留量；
4. **暂不修改科学配置**。Qwen revision、NF4、LoRA r16/alpha32/七类 target、1024 tokens、数据、seed、microbatch 1、accumulation 16、PagedAdamW8bit、scheduler 与三 epoch 目标均保持不变；
5. 若新的双重容量 Gate 仍失败，才进入独立的配置修订。第一候选是 attention-only LoRA r16，而不是缩短序列或临时降低阈值。

因此，v0.29 是一项**前瞻性的度量修订**，不是对 v0.27 负结果的回写。

## 2. 已有证据

### 2.1 v0.25 正式训练硬停

唯一一次正式训练在 epoch 1 / optimizer step 3 后触发旧 `peak reserved <= 10.5 GiB` Gate：

- 已完成 48 / 3,600 microbatches；
- 已完成 3 / 225 optimizer steps；
- 完整 epoch、checkpoint 与 adapter 均为 0；
- step 1 记录 `11,240,734,720` bytes reserved；
- step 2 记录 `11,249,123,328` bytes reserved；
- step 3 的实际越界值未被记录，禁止补造；
- 该次执行仍是合法的容量失败，不能因本修订而改判。

### 2.2 v0.27 最长序列压力预检

v0.27 对冻结 train 中最长 16 条执行完整累积与一个 optimizer step：

| 指标 | 结果 |
|---|---:|
| token 范围 | 982–1,021 |
| token 总量 | 15,999 |
| microbatches | 16 / 16 |
| optimizer steps | 1 / 1 |
| loss / gradient norm | 全部有限 |
| CUDA OOM | 否 |
| peak allocated | 10,428,610,048 bytes（9.712 GiB） |
| peak reserved | 13,788,774,400 bytes（12.842 GiB） |
| 旧上限 | 11,274,289,152 bytes（10.5 GiB） |
| 清理后 reserved | 50,331,648 bytes |
| checkpoint / adapter / generation | 0 / 0 / 0 |

本机 NVIDIA 驱动报告 11,264 MiB 名义总显存；PyTorch `get_device_properties(0).total_memory` 报告 `11,810,832,384` bytes。v0.27 的 `peak reserved=13,788,774,400` bytes 高于这两个物理总量表达。

这不允许推断“显存足够完成 225 steps”，但足以推翻以下等价关系：

> `max_memory_reserved` = 本机逐字节物理显存驻留峰值。

v0.27 没有在 optimizer step 前后同步记录 `mem_get_info`，因此不能被事后套用新 Gate 改判；如要评估复合容量构念，必须另做一次前瞻性、单次授权的 M0。

### 2.3 指标语义

冻结 runtime 为 PyTorch `2.3.1+cu121`。其本地 API 文档定义：

- `max_memory_allocated`：由 tensor 占用、并由 PyTorch allocator 统计的峰值；
- `max_memory_reserved`：由 caching allocator 管理的峰值缓存/保留量；
- `mem_get_info`：CUDA driver 在同步采样点报告的 free / total memory。

三者测量的对象不同：

- allocated 更接近活跃 tensor 负载，但不覆盖所有非 PyTorch CUDA 分配；
- reserved 能诊断 allocator 缓存、碎片与段管理，但不是当前栈中的物理驻留量；
- free memory 能覆盖当前采样点的整体设备压力，但不是连续时间峰值。

所以合理的容量 Gate 必须组合使用，而不能把其中任一项单独冒充“真实显存”。

## 3. 路线裁决

| 路线 | 是否改变科学配置 | 预期作用 | 裁决 |
|---|---|---|---|
| 把 reserved 上限抬到 12.84 GiB 或更高 | 否 | 让已见结果通过 | **拒绝**：超过物理总量且构成结果后追阈值 |
| 保留 10.5 GiB，但改用于 peak allocated；增加 512 MiB min-free 与 OOM Gate | 否 | 修复测量构念，同时保留原上限隐含的约 512 MiB 安全裕量 | **推荐作为 v0.29 唯一路线** |
| 只用“没有 OOM”判通过 | 否 | 最大化可运行性 | **拒绝**：没有显式安全裕量 |
| 再轮换 allocator，直到某个通过 | 否 | 可能降低碎片 | **拒绝作为 v0.29**：多次试错会产生选择偏倚 |
| non-reentrant gradient checkpointing | 不改模型目标，但改变 autograd 实现 | 可能降低重计算/显存开销 | 保留为后续独立实现修订，不与度量修订混跑 |
| attention-only LoRA r16 | **是**：改变 target modules | trainable 参数约减少 75% | 配置失败后的第一候选 |
| 七类 target、LoRA r8 | **是**：降低 adapter rank | trainable 参数约减少 50% | 第二候选，不与 attention-only 同时试 |
| attention-only LoRA r8 | **是**：同时改结构与 rank | trainable 参数约减少 87.5% | 末级候选，需重新论证容量与表达力 |
| sequence length 1024 → 768/512 | **是**：改变可见上下文或样本组成 | 显著降低 activation | **当前拒绝**：直接伤害长日志语义编译目标 |
| accumulation 16 → 8 | **是**：改变 effective batch | 对 optimizer-state 峰值帮助有限 | **当前拒绝** |
| epochs 3 → 1 | **是** | 缩短时间，不降低单步峰值 | **拒绝作为容量措施** |
| CPU/model-layer offload | 执行路径改变，数值与性能风险待验证 | 可降低 GPU 驻留 | 仅在本地纯 GPU 路线失败后另立修订 |

## 4. v0.29 唯一建议预检：M0 度量复核

### 4.1 保持不变

M0 必须逐字段继承 v0.27：

- `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`；
- 4-bit NF4、double quant、FP16 compute；
- LoRA `r=16 / alpha=32 / dropout=0.05`；
- `q_proj/k_proj/v_proj/o_proj/gate_proj/up_proj/down_proj`；
- sequence length `1024`，禁止截断；
- microbatch `1`、accumulation `16`；
- 相同 1,200 train、tokenizer、serialization、seed、optimizer 与 scheduler；
- 相同最长 16 条及 selection digest `BCF7D96DBD6AFCBFD127137397B638F1662A30D53D5E1F9A853B2D65CAE5BB7D`；
- 相同 `PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128,garbage_collection_threshold:0.8` 与逐 microbatch 清理动作；
- 相同 RTX 2080 Ti、本地 runtime 与模型快照；
- 一个完整 accumulation group、恰好一个 optimizer step；
- 不保存 adapter/checkpoint，不 generation，不访问 development/test。

不得在 M0 中同时引入新 allocator、non-reentrant checkpointing、LoRA target/rank、序列、数据或阈值修改。

### 4.2 新增测量

在模型加载前重置一次全局 peak；之后禁止重置。每个正式采样点必须先执行 `torch.cuda.synchronize(0)`，再记录：

- `memory_allocated`；
- `max_memory_allocated`；
- `memory_reserved`；
- `max_memory_reserved`；
- `mem_get_info` 的 free / total；
- 是否发生 CUDA OOM；
- 墙钟时间。

采样点固定为：

1. 模型、LoRA 与 optimizer 对象创建后；
2. 每个 microbatch backward 与冻结清理动作完成后；
3. gradient clipping 后、optimizer step 前；
4. optimizer step 后、scheduler/zero-grad 前；
5. zero-grad 与清理后；
6. 删除全部 GPU 对象并清理后。

外部 `nvidia-smi` 只能作操作日志，不进入主 Gate，避免低频外部采样漏掉瞬时峰值。

### 4.3 新硬 Gate

M0 只有同时满足以下条件才判 `passed_capacity_metric_preflight`：

1. 16 / 16 microbatches 和 1 / 1 optimizer step 完成；
2. loss 与 gradient norm 全部有限；
3. 七类 LoRA target 完整、trainable ratio `<1%`；
4. 无 CUDA OOM；
5. 全程 `max_memory_allocated <= 11,274,289,152` bytes（10.5 GiB）；
6. 所有同步采样点 `free memory >= 536,870,912` bytes（512 MiB）；
7. 设备总显存与冻结 RTX 2080 Ti 审计一致；
8. 终态 post-cleanup reserved `<=134,217,728` bytes（128 MiB）；
9. adapter/checkpoint/model/generation 输出为 0；
10. 无网络、无新下载、无新依赖、无 development/test、C07–C12 或 M3 访问。

`max_memory_reserved` 必须原样记录，但无通过阈值。不得删除、截断或用 current reserved 覆盖它。

### 4.4 为什么这不是放宽 Gate

- 数值上限 10.5 GiB 没有提高；
- 新增了 512 MiB driver-free 安全裕量，与原 11 GiB 物理总量和 10.5 GiB 上限之间的名义差额一致；
- 仍要求无 OOM、完整最长序列、完整 optimizer step 与终态释放；
- v0.25/v0.27 仍按当时合同记为失败；
- M0 若失败，禁止再换一个度量或阈值救场。

变化仅在于：把 10.5 GiB 绑定到它真正能解释的 live-tensor peak，同时用 driver-free Gate 补足非 PyTorch 分配风险。

## 5. M0 之后的权限

### 5.1 M0 失败

以下任一情况均保持正式训练关闭：

- CUDA OOM；
- `peak allocated >10.5 GiB`；
- 任一同步点 free memory `<512 MiB`；
- 样本、数值、target module、输出或范围 Gate 失败。

失败后不得尝试第二度量、第二阈值或第二次 M0。下一步只能提交新的配置/实现修订供审阅。

### 5.2 M0 通过

通过只证明：冻结最长序列单步包络在新的复合容量构念下可运行。它不证明 225-step 训练一定完成，也不证明 adapter 有效。

M0 通过后仍须：

1. 固化脱敏结果与新的关闭 authority；
2. 单独提交正式 retry authority；
3. 正式 retry 必须从头开始，禁止续接 v0.25；
4. 每个 optimizer step 使用相同 allocated / min-free / OOM Gate；
5. 任一 Gate 失败立即停止，不自动重跑；
6. checkpoint selection 与正式推理仍需训练完成后的独立授权。

## 6. 若必须改变科学配置

只有 M0 失败才进入本节。不得同时试多个配置并挑最好看的结果。

### C1：attention-only LoRA r16（第一候选）

冻结 target 为 `q_proj/k_proj/v_proj/o_proj`，其余配置不变。根据 Qwen2.5-7B 冻结结构：

- 预计 trainable 参数：`10,092,544`；
- 预计 trainable ratio：约 `0.2313%`；
- 相对现行 `40,370,176` trainable 参数减少 75%；
- 必须通过零步参数清单与最长序列容量预检；
- Paper B 必须明确称为 attention-projection LoRA，不能与七类 target 结果混写。

C1 的优势是保留 r16、完整 1024 tokens 与全部训练样本，同时采用文献中常见的 attention projection LoRA。代价是 adapter 不再直接更新 MLP projections，任务表达力可能下降，必须通过 General vs Adapted 配对评估决定是否保留。

### C2：七类 target、LoRA r8（第二候选）

- 预计 trainable 参数：`20,185,088`；
- 预计 trainable ratio：约 `0.4616%`；
- 相对现行参数减少 50%；
- 保留七类 target，但降低每个 target 的低秩容量。

不得在看过 C1 任务效果后无预注册地切换到 C2。若要比较 C1/C2，必须把它改成明确的 adapter-capacity 消融，而不是容量救火。

### C3：attention-only LoRA r8（末级候选）

- 预计 trainable 参数：`5,046,272`；
- 预计 trainable ratio：约 `0.1158%`；
- 同时改变 target 与 rank，解释成本最高；
- 仅在 C1 仍无法满足物理容量且项目仍决定坚持本地 2080 Ti 时讨论。

## 7. 实施任务（审阅通过后才授权）

| Task | 内容 | 是否含模型执行 |
|---|---|---|
| M0-1 | 新建 capacity-metric contract、authority 草案与 model-free tests | 否 |
| M0-2 | 实现同步采样器与脱敏审计；旧训练器字节不变 | 否 |
| M0-3 | 运行静态测试、哈希链和 98 项相邻 QLoRA 回归 | 否 |
| M0-4 | 用户显式授权后执行唯一一次 M0 | 是：16 microbatches + 1 step |
| M0-5 | 固化 pass/fail，关闭全部下游 Gate | 否 |
| M0-6 | 若通过，另行审阅正式 retry authority | 尚未授权 |

M0-1 至 M0-3 的实现授权与 M0-4 的 GPU 执行授权必须分离。本文被批准也不自动授权 M0-4。

## 8. 声明边界

允许的结论：

> v0.27 暴露了 reserved-memory 指标在当前本机软件栈中的构念失配；v0.29 前瞻性地用 live-tensor peak、driver free memory 与 OOM 组成复合容量 Gate。

禁止的结论：

- v0.27 实际通过；
- RTX 2080 Ti 已证明可完成三 epoch；
- 提高显存阈值不会影响治理可信度；
- adapter 已训练或有效；
- M0 通过即可进入 checkpoint selection、正式推理、C07–C12 或 M3。

## 9. 审阅裁决项

审阅者只需裁决以下三点：

1. 是否接受“10.5 GiB 绑定 peak allocated + minimum free 512 MiB + no OOM”的复合容量 Gate；
2. 是否接受 `peak reserved` 降为完整记录的诊断项，而非物理显存硬 Gate；
3. 是否仅授权 M0-1 至 M0-3 的实现与测试，待其通过后再单独授权一次 M0 GPU 预检。

在这三项明确批准前，v0.28 的全关闭状态保持不变。
