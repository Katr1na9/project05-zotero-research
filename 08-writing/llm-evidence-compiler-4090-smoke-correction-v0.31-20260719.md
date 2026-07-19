# Project05 单卡 4090 smoke 实现纠错记录 v0.31

日期：2026-07-19
状态：实现修复与本地验证进行中；纠正后的 smoke 重跑尚待单独授权

## 1. 已完成且仍有效的准备 Gate

- 运行边界仍为 `/home/myy/project05-qwen25-4090-v0.1`，未访问或写入其他服务器目录。
- 固定模型仍为 `Qwen/Qwen2.5-7B-Instruct`，revision 为 `a09a35458c702b33eeacc393d103063234e8bc28`。
- 14 个 allowlisted 文件均已按合同核验字节数及 Git blob SHA-1 / LFS SHA-256。
- 模型仓库总量为 15,242,807,270 bytes，其中权重为 15,231,271,888 bytes。
- Python 3.11.9、PyTorch 2.3.1+cu121、bitsandbytes 0.43.1、PEFT 0.13.2 等固定运行时通过，NF4 CUDA 探针通过。
- prepare 的运行时、缓存与模型资源占用为 27,853,931,104 bytes，低于 34,000,000,000 bytes 上限。
- Hugging Face 官方端点在该服务器网络不可达；`hf-mirror.com` 仅作为传输端点。固定 repository、revision、allowlist 和逐文件内容哈希均未改变。

## 2. smoke 失败边界

第一次启动 smoke 后，四片量化模型被加载，但程序在构造 LoRA 模块清单审计记录时抛出：

```text
KeyError: 'passed'
```

根因是 `summarize_target_module_inventory()` 返回字段 `all_target_families_present`，而 4090 执行器误读为 `passed`。

失败发生于数据编码、forward、backward 和 optimizer step 之前。因此：

- forward calls：0
- backward calls：0
- optimizer steps：0
- adapter/checkpoint 写入：0
- 正式训练输出目录：未创建
- 服务器 `server-output` 中仅存在已通过的 `preparation-audit-v0.1.json`
- GPU 2 已完全释放，回到 24,094 MiB free / 18 MiB used

该失败不是 OOM，不反映模型质量、数据质量或训练稳定性，也不能作为 smoke 结果。

## 3. 实现纠错

纠错仅包括：

1. 将执行器读取字段从 `module_gate["passed"]` 改为 `module_gate["all_target_families_present"]`；
2. 增加纯函数级回归测试，锁定共享 preflight schema 与 4090 audit schema 的映射；
3. 新合同显式接受原 prepare 合同 SHA-256，仅用于复用已经逐文件复核的同一模型快照；执行器仍会重新调用 `verify_snapshot()` 复核全部 14 个文件；
4. 不修改训练数据、序列化、token 长度、模型 revision、NF4 配置、LoRA rank/alpha、batch、梯度累积、学习率、优化器、scheduler、epoch、225-step 或 seed。

## 4. 重跑 Gate

原权威文件禁止自动重试。尽管本次失败未产生任何模型计算或优化器状态，纠正后的 smoke 仍不得静默启动。

需要新的显式授权仅覆盖：

- 在同一运行根、同一固定模型快照和同一科学配置下，执行一次纠正后的最长 16 序列 smoke；
- smoke 仍仅允许 1 个 optimizer step，且不得保存 adapter；
- 仅在纠正后的 smoke 全部通过后，原先获批的一次 3 epochs / 225-step primary 才可继续；
- 不授权第二次 primary、自动 resume、超参调整、多卡、正式推理或下游 M3 接入。
