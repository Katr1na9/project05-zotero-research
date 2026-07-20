# Project05 General Qwen vs epoch-2 QLoRA 单次配对执行修订 v0.42

日期：2026-07-20

状态：`single_training_validation_paired_execution_authorized`

## 1. 执行范围

用户设定的当前目标明确要求在完成模型无关实现和哈希 Gate 后，继续在 4090 上执行 General Qwen 与 selected epoch-2 QLoRA 的配对评测。本修订据此只开放一次 Stage P1 training-validation 原子运行：

- 16 条冻结面板；
- 每条 `QWEN-GENERAL` 与 `QWEN-ADAPTED` 各一次；
- 总计 32 次确定性 greedy 调用；
- 生成完成后在服务器侧一次性评分；
- 仅回收脱敏 metrics、generation audit、score audit 和非敏感日志。

本授权不开放 train、development/test、C07–C12、M3 或正式论文结论。

## 2. 固定身份

- Base：`Qwen/Qwen2.5-7B-Instruct`
- Revision：`a09a35458c702b33eeacc393d103063234e8bc28`
- General：adapter disabled
- Adapted：`project05_obs_compiler` epoch 2 enabled
- Optimizer step：150
- Adapter SHA-256：`D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11`
- Tokenizer/quantization：同一 snapshot，NF4 + double quantization + FP16
- Decode：`do_sample=false`，`max_new_tokens=256`，invalid 不 repair

epoch 1/3 不得加载；不得重新选择 checkpoint。

## 3. 服务器边界

唯一允许远端根目录：

`/home/myy/project05-qwen25-4090-v0.1`

固定使用物理 GPU 2：

- UUID：`GPU-b0302acd-64e2-8218-7b5c-07a152007357`
- 预检空闲显存：约 24,094 MiB

不得查看、创建、修改或删除远端其他目录。不得安装、升级或下载 runtime、Qwen、tokenizer 或 adapter。

## 4. 冻结输入预检

2026-07-20 的只读预检确认：

| 输入 | SHA-256 |
|---|---|
| preparation audit | `12F73CE159E72F08C08533B8CA8A79BBF79ECAF7FEF118CB24F702FA1BDDC38A` |
| epoch-2 adapter weights | `D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11` |
| training-validation payload | `7607F79387CD2139640B2DB323C45C87815D2E8780B84D979092432ADAFBF552` |

固定 runtime：

- torch `2.3.1+cu121`
- transformers `4.45.2`
- peft `0.13.2`
- bitsandbytes `0.43.1`

目标输出 `server-output/paired-general-adapted-v0.41` 在预检时不存在。

## 5. 运行和失败规则

launcher 必须依次：

1. 调用 hash-locked paired runner；
2. runner 完整锁定 32 条 raw generation；
3. scorer 校验 generation audit 与 raw file SHA-256；
4. scorer 才读取同一 frozen panel 的 training-validation labels；
5. 写出 sanitized metrics 与 aggregate score audit；
6. 硬停。

若任何一步失败：

- 写 failure audit；
- 不自动重试、不 resume；
- 不更换 GPU、checkpoint、prompt、parser、阈值或面板；
- 不进入 development/test；
- 报告失败并等待新裁决。

## 6. 回收边界

允许下载：

- `paired-generation-audit-v0.1.json`
- `paired-sanitized-metrics-v0.1.jsonl`
- `paired-score-audit-v0.1.json`
- detached 非敏感日志和失败审计（若有）

禁止下载：

- `paired-raw-generations-v0.1.jsonl`
- adapter/checkpoint/base/tokenizer cache
- raw training-validation pair
- 服务器上的 prompt、target 或其他原始 payload

## 7. 结果裁决

本轮必须如实报告 supported-class collapse、invalid、pointer、coverage proxy、ceiling 与 family-macro F1。若 Adapted 诊断 Gate 失败：

- 不换 checkpoint；
- 不改 Gate；
- Adapted 不得被表述为已改善；
- 后续按预注册路线降级为负面对照或放弃 adapter。

即使诊断 Gate 通过，也只代表 training-validation 原子面板通过，不等于 C07–C12 正式 test 增益。
