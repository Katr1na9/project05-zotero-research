# Project05 Qwen2.5 4090 正式训练结果与评价硬停 v0.38

日期：2026-07-20

## 1. 结论

Project05 evidence compiler 的一次 fresh detached Qwen2.5-7B-Instruct QLoRA 正式训练已按 v0.37 授权完整通过：3 epochs、225 optimizer steps、3,600 microbatches 全部完成，epoch 1/2/3 三个 adapter-only checkpoint 均已保存。正式状态为：

> `passed_single_4090_adamw_primary_adapter_training`

这只证明冻结训练协议已完整执行并产出三个候选 adapter checkpoint；尚不证明微调模型优于原版 Qwen，也不授权选 checkpoint、生成 training-validation 输出、运行 C07–C12 或接入 M3。

## 2. 权威证据

| 项目 | 结果 |
|---|---|
| 服务器输出 | `/home/myy/project05-qwen25-4090-v0.1/server-output/primary-adamw-detached-v0.37` |
| 成功 audit SHA-256 | `EF46A654F741DD521DA7922E01A559B7545EB501047C3594D2F808F006AE7AE5` |
| progress SHA-256 | `FA4BDFB4F055A2F386AB0A12062CB7B39025EBE36509BAE4E7F2C6A80FE72501` |
| 合同 SHA-256 | `B913202746F5729F535EFF3449461DF4F40432225B7A0F333A560501FF8EEACE` |
| 配置 SHA-256 | `FA821CC41AF16F2FE4D32A6A00041BAE13377046435A3A03A14FD4689C88E6BE` |
| authority SHA-256 | `8D140DF15BB175E033BB068A9DA603C28A2DA223FB1B913DD33B333D828F39CC` |
| worker 终态 | 正常退出；GPU 2 释放至 24,094 MiB free / 18 MiB used |
| failure audit | 不存在 |

Git 仅保存脱敏成功 audit。adapter、optimizer、scheduler、RNG、完整 progress 与训练数据继续留在服务器，不下载、不合并、不上传 Hub。

## 3. 冻结训练结果

| 维度 | 结果 |
|---|---:|
| epochs | 3 / 3 |
| optimizer steps | 225 / 225 |
| microbatches | 3,600 / 3,600 |
| wall time | 3,668.217 s（约 61.14 min） |
| trainable parameters | 40,370,176 / 4,393,342,464（0.9189%） |
| optimizer | 单张量 `torch.optim.AdamW`；未使用 bitsandbytes optimizer |
| overall training loss mean | 0.0138715 |
| epoch 1 loss mean | 0.0399338 |
| epoch 2 loss mean | 0.00147779 |
| epoch 3 loss mean | 0.000203031 |
| overall gradient norm mean / max | 0.0808474 / 1.88604 |

训练 loss 的下降不是泛化或任务增益证据。它只用于检查训练执行和数值稳定性；是否过拟合、哪个 epoch 更优，必须由预冻结的 training-validation-only checkpoint selection 决定。

## 4. Checkpoint 清单

| checkpoint | step | adapter SHA-256 | adapter bytes |
|---|---:|---|---:|
| epoch 1 | 75 | `9762070065DB311A04FD8AF362F882EE3AA5D3045E7E6E286A56D9011CBF5E1F` | 161,533,192 |
| epoch 2 | 150 | `D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11` | 161,533,192 |
| epoch 3 | 225 | `E0484CC1D95F38D30EFA8D81A9C6E2419875CF7E64F47AB3411C0F803EC53BED` | 161,533,192 |

三个 checkpoint 均包含 adapter、optimizer、scheduler、RNG 和 trainer-state；均未保存 merged model。当前不得凭训练 loss 直接选择 epoch 3。

## 5. 资源与安全 Gate

- 固定 GPU：RTX 4090 index 2，UUID `GPU-b0302acd-64e2-8218-7b5c-07a152007357`；
- peak allocated：8,301,579,264 bytes，低于 23,622,320,128 bytes 上限；
- minimum synchronized free：1,075,970,048 bytes，高于 1,073,741,824 bytes 下限，余量 2,228,224 bytes；
- runtime/cache/checkpoint/output：30,795,084,148 bytes，低于 34,000,000,000 bytes 上限，余量 3,204,915,852 bytes；
- 226 个显存样本全部通过；无 OOM、CUDA、数值或 wall-time failure；
- 未访问 development/test 或 C07–C12，未调用 generation，未接入 M3，未修改 Paper A，未生成 raw pair/output 审计，未上传 Hub。

显存 Gate 的最小余量较窄，应如实报告；但本次协议没有降低阈值，且所有阻断样本均实际通过。

## 6. 下一治理闸门

当前硬停在：

> `hard_stop_for_checkpoint_selection_and_evaluation_authorization`

下一步若另行授权，应严格复用 `qwen25-primary-training-contract-v0.1.json` 中已冻结的 checkpoint-selection snapshot：

1. 仅使用 300 条 training-validation（Loghub 150 + Zeek 150），不得访问 development/test 或 C07–C12；
2. 对 epoch 1/2/3 全量评估，`do_sample=false`、`maximum_new_tokens=256`、不修复 invalid output；
3. 主指标为 `family_macro_support_decision_f1`；
4. tie-breakers 依次为 canonical JSON exact、normalized edge exact、pointer exact、assistant token NLL、较早 epoch；
5. 选中 checkpoint 后，再以同一底座构造 General vs Adapted 配对评价；在评价结果出来前不允许正向论文声明或 M3 接入。

本记录不授权上述评价执行，只证明训练阶段已完整结束并到达该治理闸门。
