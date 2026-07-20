# Project05 Qwen2.5 4090 v0.35 中断记录与恢复闸门 v0.36

日期：2026-07-20

## 1. 结论

v0.35 AdamW 正式训练在 `194/225` optimizer steps、第三个 epoch 内被外部会话中断，不能登记为正式训练完成。现有证据没有出现 CUDA、OOM、数值、显存 Gate 或 optimizer 失败；训练已经稳定越过旧 v0.2 在第 173 步出现的 illegal-memory-access 故障点。

服务器审计显示训练进程已经退出，绑定 GPU 已释放；输出目录仅存在 epoch 1 和 epoch 2 的完整 checkpoint，未生成成功审计，也未生成 Python failure audit。该组合与前台 SSH 会话消失导致的 terminal hangup 相符，但没有直接证据可以把具体信号写成确定原因。

## 2. 冻结事实

| 项目 | 冻结值 |
|---|---:|
| 输出目录 | `/home/myy/project05-qwen25-4090-v0.1/server-output/primary-adamw-v0.35` |
| 已完成 optimizer steps | 194 / 225 |
| 已完成 microbatches | 3,104 / 3,600 |
| 完整 epoch | 2 / 3 |
| progress events | 197 |
| progress SHA-256 | `50E1462B2E2C30C11E352DE1110BFA7F34562698FBA343E84E57F18596951E288` |
| 最后 loss mean | `6.256204648025232e-05` |
| 最后 gradient norm | `0.004699285142123699` |
| 最后 free memory | `1,180,827,648` bytes |
| 事后 GPU | 24,094 MiB free / 18 MiB used |

完整训练权重、adapter、optimizer/scheduler/RNG 状态、原始训练文本和完整进度日志继续留在服务器；Git 只保存脱敏的统计摘要。

## 3. 科学解释边界

本次运行可以增加一条有限证据：标准单张量 `torch.optim.AdamW` 在相同 QLoRA 配置下越过了原故障点，并连续运行至第 194 步。它不能证明三轮训练已完成，也不能用于选择 epoch 1/2 checkpoint、比较 General 与 Adapted、生成 validation 结果或接入 M3。

不得把“与 SSH hangup 相符”改写为“已证明由 SIGHUP 导致”，也不得把不完整 checkpoint 当作正式 adapter 结果。

## 4. 恢复选择

### 方案 A：fresh detached rerun（推荐）

从固定 Qwen base 重新初始化 adapter、optimizer 和 scheduler，保持 v0.35 的数据、seed、LoRA、训练步数和显存 Gate 全部不变，仅把启动方式改为脱离 SSH 生命周期的持久后台进程，并使用全新输出目录。该方案重复约一小时计算，但不引入 checkpoint-resume 实现和恢复等价性的新变量。

### 方案 B：从 epoch 2 checkpoint resume

从第 150 步保存的 adapter、optimizer、scheduler 和 RNG 状态恢复，补跑剩余 75 步。该方案更快，但需要新增恢复实现、状态完整性检查、数据迭代位置与 scheduler 等价性测试，并形成单独的方法修订；否则不能把结果与 fresh 225-step protocol 等同。

## 5. 当前硬停

在用户知情选择恢复方案前：

- 不重启、不 resume、不覆盖 v0.35 输出；
- 不选择或评估 epoch 1/2 checkpoint；
- 不下载 checkpoint；
- 不开展 training-validation、C07–C12 正式推理或 M3 集成；
- 不写训练完成或 adapter 正向效果声明。

恢复授权应写入新的 authority lock；v0.35 的一次执行额度已消耗并关闭。
