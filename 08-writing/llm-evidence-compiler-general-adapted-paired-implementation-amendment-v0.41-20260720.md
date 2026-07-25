# Project05 General Qwen vs epoch-2 QLoRA 配对评测实施修订 v0.41

日期：2026-07-20

状态：`implementation_frozen_model_execution_closed`

适用路线：Project05 主线前端证据编译层

## 1. 本轮裁决

checkpoint 选择已完成，唯一后续 Adapted 条件为 epoch 2、optimizer step 150：

- adapter SHA-256：`D29F2BE6DF4310B22535FE8FB0D59BEDB23BF7CDCC431D3BBDD6882F4FA3DF11`；
- 选择数据仅为 300 条 training-validation；
- 三个 checkpoint 的两个来源族 `supported` 类 F1 均为 0；
- epoch 2 只是冻结选择规则下的相对最优版本，不是有效性结论。

本修订只授权冻结配对合同、实现 model-lazy runner/scorer、哈希链和模型无关测试。它不授权模型执行、development/test、C07–C12、M3 或正向论文主张。

## 2. 本轮要回答的问题

第一步只回答：

> 在相同底座、相同输入、相同 prompt/tokenizer/量化/greedy 解码、相同硬件与相同 scorer 下，仅切换 adapter off/on 时，两个条件能否完成可审计的配对运行；Adapted 在冻结 training-validation 原子面板上是否仍出现 supported 类塌缩或更差的 invalid/pointer/ceiling 行为？

该 16 条面板是技术和风险诊断，不是独立测试，不能直接选择主线模型，也不能进入论文 test 表。

## 3. 唯一允许的模型差异

```text
QWEN-GENERAL
  base = Qwen2.5-7B-Instruct@a09a3545…
  adapter = disabled

QWEN-ADAPTED
  same loaded base process
  adapter = project05_obs_compiler:epoch-2 enabled
```

必须相同：

- base snapshot、tokenizer snapshot、4-bit NF4 与 FP16 compute；
- 单一加载进程、单一 RTX 4090；
- public input、prompt、最大上下文和 `max_new_tokens=256`；
- `do_sample=false`、无 temperature/top-p 调参；
- 首轮 invalid 不 repair、不续写、不重试；
- parser、admission/scorer 版本和失败计数；
- 输入、prompt、decode、runtime 与硬件哈希记录。

不得换 epoch 1/3，不得重跑 checkpoint 选择，不得根据输出改 prompt、Gate 或样本。

## 4. 原子面板冻结

来源仍是 300 条 training-validation，正式运行前不读取原始行：

- Loghub 150、Zeek 150；
- 每个来源族 supported 75、unsupported-by-bound-pointer 75；
- 按 seed `2026072001` 在四个 family × decision 分层内各取 4 条；
- 总计 16 条；两条件各 16 次，共 32 次模型调用；
- panel ID 与 raw generation 仅留服务器；
- 条件顺序在每个分层内按 seed `2026071801` 精确平衡，避免总是由同一条件先运行。

看到输出后不得重选面板。

## 5. 两层 Gate

### 5.1 技术 Gate

必须同时满足：

- 16 条样本均有 General/Adapted 两行，共 32 行；
- 每对共享 public-input/prompt/base/tokenizer/runtime/quantization/decode/hardware 哈希；
- condition position 为 0/1，且每层 General-first 与 Adapted-first 数量相等；
- 仅 adapter state 不同；
- 无 OOM、无缺行、无静默 repair、无自动重试；
- raw generation 仅服务器保存；
- sanitized metrics 不含 raw generation；
- 所有输出 `controller_eligible=false`。

技术 Gate 失败时写 failure audit 并停止，不自动重试。

### 5.2 Adapter 诊断 Gate

为防止只看 macro-F1 掩盖类别塌缩，必须同时报告：

- family-macro support-decision F1；
- overall 与逐来源族 supported-class F1；
- unsupported-class F1；
- invalid rate；
- pointer exact；
- normalized-edge exact；
- supported-output rate；
- bound-pointer ceiling violation。

预注册诊断护栏：

- Adapted overall 与两个来源族的 supported-class F1 都必须严格大于 0；
- Adapted family-macro F1 不低于 General；
- invalid rate 与 ceiling violation 不高于 General；
- pointer exact 不低于 General；
- unsupported-class F1 与 supported-output rate 相对 General 的下降均不得超过 0.05。

该 Gate 失败时，Adapted 不得作为“已改善”路线；它只能作为后续独立评测中的负面对照，或按最终结果降级。该 Gate 通过也不等于通过六案例正式 Gate。

## 6. 统计和措辞边界

- 原子面板来自 checkpoint 选择所用 training-validation，不是独立样本；
- 16 个 pair、32 次调用不能扩大论文样本量；
- 本阶段不能声称“减少幻觉”“提高 APT 溯源准确率”或“适配器有效”；
- 允许结论仅为技术连通性、机械指标诊断与类别塌缩是否仍存在；
- 最终 Adapter 主线 Gate 仍须在冻结 C07–C12 的 6 个 case/attack chain 上按 case-macro 检验 0.05、4/6、coverage 和安全护栏。

## 7. 数据与产物边界

允许提交：

- 本修订、合同、配置、runner/scorer、测试；
- 后续完成后回收的 sanitized metrics、aggregate audit 和 progress。

禁止提交或下载：

- raw generation、raw prompt、raw training-validation pair；
- adapter/checkpoint/optimizer/scheduler；
- base 权重或 tokenizer cache；
- development/test、C07–C12、M3 数据；
- Paper A 正向结果。

服务器操作若后续获批，仍只能发生在：

`/home/myy/project05-qwen25-4090-v0.1`

## 8. 当前硬停

v0.41 完成后只允许：

1. 运行 model-free tests；
2. 校验实现、合同和哈希；
3. 提交并推送 sanitized 实现。

模型执行必须有一个新的、引用本修订全部精确 SHA-256 的 authority lock，且最多授权一次 16 条 training-validation 配对运行。未出现该 authority 前，runner 必须 fail closed。
