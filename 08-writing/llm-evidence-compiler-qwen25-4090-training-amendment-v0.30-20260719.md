# Project05 Qwen2.5 QLoRA：RTX 4090 迁移与正式训练修订 v0.30

日期：2026-07-19

状态：`user_authorized_4090_migration_smoke_then_primary_training`

适用范围：Project05 主线前端 LLM evidence compiler 的 Qwen2.5-7B-Instruct QLoRA。本文只重开单卡 RTX 4090 执行路线，不改变 Paper A、C07–C12、M3、正式推理或论文正向结论的权限。

## 1. 裁决

用户已明确要求把本地训练迁移到 4090 服务器并持续推进。因此，本修订覆盖 `authority-lock-v0.28.json` 中“服务器路线关闭”的旧状态，但不改写 v0.25、v0.27、v0.28 的历史结果：

- 本地 RTX 2080 Ti 的正式训练尝试仍是容量 Gate 失败；
- v0.27 最长序列预检仍按当时的 `peak_reserved <= 10.5 GiB` 合同判失败；
- 新执行是不同硬件上的一次全新运行，不是本地失败的续训或事后改判。

## 2. 唯一允许的训练配置

迁移不改变科学配置：

| 项目 | 冻结值 |
|---|---|
| 底座 | `Qwen/Qwen2.5-7B-Instruct` |
| revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| 量化 | 4-bit NF4、double quant、FP16 compute |
| LoRA | r16、alpha32、dropout 0.05、bias none |
| target | q/k/v/o/gate/up/down projections |
| 序列 | 1024 tokens，禁止截断 |
| 数据 | train 1,200；training-validation 300；4+2 来源族 |
| batch | microbatch 1；accumulation 16 |
| 优化 | PagedAdamW8bit；lr 2e-4；cosine；warmup 7 |
| 训练 | 3 epochs；225 optimizer steps；seed 2026071601 |
| 产物 | 每 epoch adapter-only checkpoint；禁止 merge / Hub upload |

4090 只提供更宽松的物理容量和更快执行，不授权增加 epoch、rank、上下文、训练数据或进行超参数搜索。

## 3. 服务器边界

唯一远端根目录为：

`/home/myy/project05-qwen25-4090-v0.1`

必须满足：

1. 代码 bundle、pair 数据、Python、依赖、cache、模型、checkpoint、日志和审计均位于该根目录；
2. 不读取、创建、移动或删除 `/home/myy` 之外的任何文件；
3. 不复用登录环境中异常膨胀的 `PATH` / `LD_LIBRARY_PATH`；launcher 必须从最小环境启动；
4. 运行前重新检查磁盘和全部 GPU，只绑定一张当时空闲的 RTX 4090；
5. GPU 用 UUID 绑定，禁止假定固定编号长期空闲；
6. 输出目录必须全新，禁止覆盖、自动 resume 或失败后自动换配置重跑。

## 4. 分阶段权限

### S0：隔离环境和固定权重

允许：

- 在唯一远端根内准备 Python 3.11 隔离环境；
- 安装冻结版本依赖；
- 下载固定 revision 的 14 个 allowlisted 模型文件；
- 逐文件核验 size 与 Git blob/LFS SHA-256；
- 复制已冻结的 1,200/300 pair 数据和最小执行 bundle。

S0 不执行 forward、backward、optimizer step 或 generation。

### S1：4090 最长序列 smoke

S0 通过后，唯一一次 S1 执行：

- 从 train 中按冻结 tokenizer 长度选择最长 16 条；
- 完成 16 个 microbatches 和 1 个 optimizer step；
- 不保存 adapter/checkpoint，不 generation；
- 每个 backward 后和 optimizer step 前后同步记录 allocated、reserved、driver free memory。

S1 同时满足下列条件才通过：

1. 16/16 microbatches、1/1 optimizer step 完成；
2. loss 与 gradient norm 全部有限；
3. 七类 target 完整，trainable ratio `<1%`；
4. 无 CUDA OOM；
5. `peak allocated <= 22 GiB`；
6. 所有同步采样点 `free memory >= 1 GiB`；
7. 运行前设备总显存不少于 23 GiB，且绑定设备为 RTX 4090；
8. 清理后 reserved `<=256 MiB`；
9. 无 adapter、checkpoint、generation、development/test、C07–C12 或 M3 访问。

`peak_reserved` 完整记录但仅作诊断。该规则与 v0.29 的度量构念一致，并针对 24 GiB 4090 保留至少 1 GiB 物理余量。

### S2：三轮正式训练

仅当 S1 同一合同审计为 passed 时自动放行一次 S2：

- 从头初始化底座、LoRA、optimizer 和 scheduler；不得继承 smoke 参数；
- 执行 3,600 microbatches / 225 optimizer steps；
- 每一步继续应用 `allocated <=22 GiB`、`free >=1 GiB`、无 OOM 和有限数值 Gate；
- epoch 1/2/3 各保存一个 adapter-only checkpoint，以及恢复所需 optimizer/scheduler/RNG state；
- 训练失败立即写脱敏 failure manifest，禁止自动重启、resume 或换配置。

训练完成只证明 adapter 已按冻结配置生成。checkpoint selection、training-validation generation、General-vs-Adapted 配对评价、正式推理和 M3 接线仍是后续独立 Gate。

## 5. 资源 Gate

- S0 开始前远端根所在文件系统可用空间至少 32,000,000,000 bytes；
- runtime、cache、模型、checkpoint 和输出的唯一物理字节总量不得超过 34,000,000,000 bytes；
- 正式训练最长 24 小时；
- 任何资源 Gate 失败均保留已完成的脱敏审计，不自动删除证据或改阈值。

## 6. 结论边界

允许的结论：

> 固定 Qwen2.5-7B-Instruct revision 的 task/schema-adapted QLoRA 已在一张 RTX 4090 上按预注册数据、序列、adapter 和资源 Gate 执行（仅在相应 Gate 实际通过后）。

禁止的结论：

- adapter 已优于原版 Qwen；
- LLM 已提升 C07–C12 溯源质量或 M3 调查控制；
- 这是“APT 领域大模型”训练；
- 4090 训练通过即可写入论文标题或正向摘要；
- 本次迁移抹除了本地 2080 Ti 的容量失败。
