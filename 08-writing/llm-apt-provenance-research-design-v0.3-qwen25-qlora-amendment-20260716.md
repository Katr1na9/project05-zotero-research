# Project05 受证据约束的 LLM–APT 溯源研究设计 v0.3

## Qwen2.5 同底座 QLoRA 领域适配修订稿

日期：2026-07-16  
状态：`superseded_no_qwen_execution_authority`  
取代文件：`llm-evidence-compiler-open-base-finetuning-amendment-v0.1-20260718.md`  
说明：用户于 2026-07-18 明确否决 Qwen；本文件只作历史设计证据，不得用于下载、安装、训练或正式推理授权。  
修订对象：`llm-apt-provenance-research-design-v0.2-20260715.md` 的模型选型、微调非目标、运行时与磁盘预算  
不变边界：Paper A、Phase 2/3、C07–C12 冻结测试、G0/G1/G2、GPS/UCR 与标题 Gate 均保持独立和未解锁状态

---

## 1. 修订结论

v0.3 建议停止原来的 `Qwen1.5-7B-Chat + SEVENLLM-Qwen1.5-7B` 双 checkpoint 路线，不下载两者权重，也不把旧模型元数据记录当作实验结果。

新路线只使用一份固定底座：

1. **General**：冻结的 `Qwen/Qwen2.5-7B-Instruct`；
2. **APT-adapted**：完全相同的 Qwen2.5 checkpoint，加装 Project05 自行训练的 QLoRA adapter；
3. **Rule**、General structured、General direct、G0/G1/G2 和全部声明 Gate 保持 v0.2 的语义；
4. 只保存 adapter，不合并或复制第二份完整模型。

核心对照由“两个来源、许可和训练历史不同的模型”改成：

> 在底座权重、架构、量化、prompt、解码和可见证据相同的前提下，Project05 的 APT 证据编译 QLoRA 是否产生可复核的增量？

本设计不预设微调一定有效。若 adapter 未通过预注册 Gate，应报告持平或负结果，不追加模型、扩大测试集或使用测试失败样本救场。

---

## 2. “使用 Qwen”在本项目中的准确含义

Qwen2.5 由 Alibaba Cloud/Qwen 团队发布，发布方是商业公司；本修订明确接受这一事实。项目使用的是可本地运行的固定开放权重，不调用收费闭源 API，也不向模型提供方发送 Project05 私有数据。

本稿不把 Qwen2.5 称为“完全开源模型”，而采用更准确的表述：

- 固定 checkpoint 的 Hub metadata 与仓库 `LICENSE` 均标为 Apache-2.0；
- 权重、配置和 tokenizer 可被版本锁定并在本地运行；
- 官方公开了模型卡和总体训练说明，但未公开足以逐条重建全部预训练/后训练语料的完整清单；
- 因而许可证可审计，不等于能够证明测试案例从未进入训练材料；
- 污染状态无法证实时必须写 `unknown`。

使用商业公司发布的开放权重不等于研究变成商业模型调用。真正进入论文方法学审计的是许可证、固定 revision、数据边界、污染限制和同底座公平比较。

---

## 3. 对 v0.2 的修改范围

| v0.2 项目 | v0.3 修订 | 状态 |
|---|---|---|
| General 模型 | Qwen1.5 改为 Qwen2.5-7B-Instruct | 待审阅冻结 |
| Security 模型 | SEVENLLM 改为同底座 Project05 QLoRA adapter | 待审阅冻结 |
| “不做微调” | 撤销；只允许 observation-compiler QLoRA | 待审阅授权 |
| RQ1 | Rule / General / APT-adapted compiler | 不扩展 RQ 数量 |
| RQ5 | 同一 General Qwen 的 structured vs direct | 不变 |
| G0/G1/G2 | 训练标签不能替代 G2 | 不变 |
| 正式测试 | C07–C12、64 packets、6 cases | 已构建，继续字节冻结 |
| Phase 2/3 | 端到端传导与 selector | 继续未授权 |
| Paper A | 调查控制与参数治理 | 禁止混写 |
| 文档形式 | 先 Markdown 审阅 | 不生成 DOCX/PPT/PDF |

已经完成的 v0.2 public/private 分包、ID 泄漏修复、Rule 开发集冻结和 null construction audit 保留为只读前置证据。v0.3 不重新抽取 C07–C12，也不因更换模型修改测试 packet。

旧 Qwen1.5/SEVENLLM runtime draft 只保留为选型否决记录。它不能改名冒充 Qwen2.5 lock，也不能授权旧权重下载。

---

## 4. 推荐 checkpoint 的冻结候选信息

### 4.1 General 与 adapter 共用底座

- Model ID：`Qwen/Qwen2.5-7B-Instruct`
- Requested revision：`main`
- 2026-07-16 解析到的不可变 commit：`a09a35458c702b33eeacc393d103063234e8bc28`
- 发布方：Alibaba Cloud / Qwen Team
- Hub metadata license：`apache-2.0`
- 仓库 `LICENSE`：Apache License 2.0
- 仓库总量：15,242,807,270 bytes（约 15.24 GB / 14.20 GiB）
- 权重总量：15,231,271,888 bytes
- 官方参数规模：7.61B
- 架构：`Qwen2ForCausalLM`
- 配置 dtype：`bfloat16`
- 原生 `max_position_embeddings`：32768
- 当前计划训练序列：1024 tokens
- RTX 2080 Ti 实际计算 dtype 候选：`float16`

四份权重的 Hub LFS SHA-256：

| 文件 | bytes | LFS SHA-256 |
|---|---:|---|
| `model-00001-of-00004.safetensors` | 3,945,441,440 | `a1333e6293854747c481288ea83b348226af178dd565c49b6f9495ba1966aba7` |
| `model-00002-of-00004.safetensors` | 3,864,726,352 | `f5d25a2772cb825164a2a2c0fb6d51a87e282abf21e4dd75bc5cfb3cd0ea6185` |
| `model-00003-of-00004.safetensors` | 3,864,726,424 | `8efdec4c1bc12317ae1a38dc42b595ce777738a64deea3fcb8a0a91381bcdfd5` |
| `model-00004-of-00004.safetensors` | 3,556,377,672 | `1a72d403cdf0c1ec3cb7f289f17b394a01e64394c2e9b3c0f94dbce3faf879bd` |

固定元数据证据：

- [模型卡](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/README.md)，SHA-256 `f366f33bbf6bcadbb7d87f0a21a7b65584a56b8d58b0743c77c88bee625b93a6`；
- [LICENSE](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/LICENSE)，SHA-256 `832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e`；
- [config.json](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/config.json)，SHA-256 `7463bb0ea78315365e6c6b74de4e73bbcc8359dfb0c5a737584e077d42c0b03c`；
- [tokenizer_config.json](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/a09a35458c702b33eeacc393d103063234e8bc28/tokenizer_config.json)，SHA-256 `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583`。

这些是审核期元数据，不代表权重已经下载。正式实施计划仍须把 resolved commit、每个文件 hash、许可证 hash 和下载后本地校验写入不可变 runtime lock。

### 4.2 为什么不采用 Llama-3.1-8B-Instruct

Llama-3.1-8B-Instruct 同样来自商业公司，而且使用自定义 Llama 3.1 Community License，不比本 checkpoint 的 Apache-2.0 更符合当前许可治理目标。其 8B 规模还会进一步压缩 11 GB 显存余量。

因此 Llama 不进入本轮候选矩阵，也不在看到 Qwen 测试输出后作为备用赢家。若 Qwen 在许可证、后端或显存 Gate 失败，本轮停止并形成新设计版本。

---

## 5. Project05 QLoRA 的任务定义

`Project05-Qwen2.5-Observation-Compiler-LoRA-v0.1` 是暂定 adapter 名称，运行时 adapter key 固定为 `project05_obs_compiler`。它不是新的完整大模型，也不是强化学习模块；该名称只表示 observation/schema 任务适配，不声称模型获得普遍 APT 领域知识。

底座参数保持冻结。训练仅更新插入 attention/MLP 线性层的小型低秩矩阵，使模型学习一个窄任务：

```text
可见日志、CTI 或 provenance records
  -> 选择来源直接支持的 observation
  -> 输出原子 subject–predicate–object
  -> 绑定 packet 内 source_pointer
  -> 证据不足时 abstain
```

它不学习：

- actor 或 campaign 归因；
- tactic/technique、恶意性、intent 或 confidence；
- planner action、策略选择或在线控制；
- Paper A 的成本 profile 或实验答案；
- C07–C12 私有 gold。

在 `r=16` 且覆盖 Q/K/V/O 与 gate/up/down projection 的候选配置下，预计可训练参数约 40.4M，约占 7.61B 的 0.53%。实际数量必须由 smoke 后的 `print_trainable_parameters()` 记录，且 `<1%` 才能继续。

---

## 6. 同底座实验条件

| 条件 | 底座 | 可训练参数 | Phase 1 用途 |
|---|---|---:|---|
| Rule compiler | 无 | 0 | 冻结非 LLM 基线 |
| Qwen-General compiler | 固定 Qwen2.5 commit | 0 | 通用模型基线 |
| Project05-Qwen-ObsCompiler | 同一 commit + QLoRA adapter | `<1%` | 检验任务适配增量 |
| Qwen-General structured | 同一 General 模型 | 0 | RQ5 受约束结论 |
| Qwen-General direct | 同一 General 模型 | 0 | RQ5 direct 对照 |

RQ5 仍只使用 General Qwen 做 structured/direct 配对。APT adapter 首轮只参加 compiler 条件，避免同时扩张“领域微调”和“控制层”的研究问题。

G2 每位标注者仍评 24 packets × 4 条件 = 96 项：

1. Rule compiler；
2. Qwen-General compiler claims + structured conclusion；
3. Project05-Qwen-ObsCompiler；
4. Qwen-General direct。

Null construction audit 与 G2 仍是两项不同工作：前者确认负 packet 构造，已经完成；后者在模型输出生成后盲评来源支持度，尚未开始。QLoRA 训练标签不能代替 G2。

---

## 7. 微调数据边界

### 7.1 独立单位与物理隔离

训练/验证划分的独立单位是**来源家族、报告或事件集合**，不是 packet 行。同一事件流、同一 CTI 报告或同一攻击复现的切片不得跨 train/training-validation/test，以免将近重复片段当成独立样本。

拟建目录必须与正式测试物理分离：

```text
09-experiments/llm_finetuning_v0.3/
  public_sources/
  generated/train/
  generated/training-validation/
  frozen/source-license-manifest.json
  frozen/train-manifest.json
  frozen/training-validation-manifest.json

09-experiments/llm_compiler_v0.2/generated/test/
  public/
  private/
```

训练进程只能访问 `llm_finetuning_v0.3/`。已冻结的 v0.2 test、G2、旧模型 draft 与 Paper A 结果路径不得挂载到训练命令。

### 7.2 明确排除

以下内容禁止进入训练、checkpoint 选择或 prompt 选择：

- C07–C12 的任何 raw record、packet、gold、case/report 名称、UUID、时间戳或命令串；
- C07–C12 所属来源家族的镜像、翻译或近重复文本；
- G2 人工标签；
- 正式测试模型输出或根据测试失败生成的补充样本；
- actor、campaign、tactic、technique、恶意性、confidence 等非目标标签；
- 由待评估 Qwen 根据 C07–C12 生成的伪标签。

数据冻结前必须执行：原始文件 SHA-256、规范化文本 hash、MinHash/片段近重复检查，以及关键实体、UUID、时间戳和命令串扫描。任一测试来源命中即阻止训练冻结。

### 7.3 最低数据充分 Gate

正式 QLoRA 前最低要求：

- train `>=400` packets，来自 `>=4` 个独立来源家族；
- training-validation `>=100` packets，来自 `>=2` 个未进入 train 的来源家族；
- 正/null 比例各处于 40%–60%；
- 至少 50% 正 packet 包含同来源干扰记录或多记录选择；
- 每项具备来源许可证、原始文件 hash、转换脚本 hash 和审阅状态；
- observation 标签只含来源直接可观察的 SPO 与 pointer；
- 标签可由规则/模板预编译，但必须逐项作者核验；无需双人盲标，也不能称为 G2 人类共识 gold。

作者审核可按每批不超过 50 项分批冻结，但不得因工作量降低 train 400 / training-validation 100 门槛。可按固定 seed `2026071605`、来源家族和正/null 分层抽取 10% 供第二人复核，作为标签质量诊断；该抽检不替代 G2，也不改变 G2 Gate。

达不到数量或来源家族 Gate 时，只允许做 QLoRA 管线 smoke，不得把领域微调作为 Paper B 核心条件。

### 7.4 标签格式

训练目标与正式 compiler schema 对齐：

```json
{
  "status": "completed",
  "candidate_claims": [
    {
      "source_type": "local_log",
      "subject": {"entity_type": "process", "value": "literal value"},
      "predicate": "executed",
      "object": {"entity_type": "file", "value": "literal value"},
      "source_pointer": {"artifact_id": "...", "record_id": "..."}
    }
  ]
}
```

模型不学习 `candidate_claim_id`；该 ID 仍由 runner 根据 request、condition、attempt 和 output index 确定性绑定。Null 训练目标固定为：

```json
{"status":"abstain","candidate_claims":[]}
```

---

## 8. QLoRA 候选配置

本节参数尚待实施计划审阅，不是已冻结命令。

### 8.1 候选运行时

- Python 3.11；
- `torch==2.3.1+cu121`；
- `transformers==4.45.2`；
- `accelerate==0.34.2`；
- `bitsandbytes==0.43.1`；
- `peft==0.13.2`；
- `datasets==3.0.1`；
- `huggingface-hub==0.25.2`；
- `safetensors==0.4.5`；
- `numpy==1.26.4`；
- `jsonschema==4.23.0`。

Qwen config 记录 `transformers_version=4.43.1`；候选运行时取其后的稳定版本。正式 lock 必须由隔离环境解析结果产生，不得因安装方便静默换包。

需新建 `.venv-llm-phase1-qwen25`，不得覆盖旧探测环境。模型加载固定 `trust_remote_code=false`；正式推理固定 `local_files_only=true`。Windows wheel、Qwen2 架构、NF4 或 adapter 保存/重载任一 smoke 失败即停止并修订。

### 8.2 主训练候选

| 参数 | 预注册候选值 |
|---|---|
| 方法 | 4-bit QLoRA / causal SFT |
| 量化 | NF4 + double quantization |
| compute dtype | FP16 |
| LoRA rank / alpha | `r=16`, `alpha=32` |
| dropout | `0.05` |
| target modules | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` |
| sequence length | 1024 |
| micro batch | 1 |
| gradient accumulation | 16 |
| effective batch | 16 sequences |
| epochs | 最多 3 |
| learning rate | `2e-4` |
| scheduler / warmup | cosine / 3% |
| optimizer | paged AdamW 8-bit |
| gradient checkpointing | enabled |
| max grad norm | 1.0 |
| primary seed | `2026071601` |
| checkpoint selection | 冻结 training-validation packet agreement，附 coverage 护栏；不读取 test |
| artifact | adapter + base/tokenizer reference；禁止保存 merged full weights |

只对 assistant response 计算 loss；system/user/source packet tokens 全部 mask。训练顺序按来源家族和正/null 角色平衡后，用固定 seed 随机化。

Checkpoint 选择规则在训练前冻结：优先 training-validation packet agreement；并列时优先较低的 invalid-pointer/unsupported-proxy；仍并列则选更早 checkpoint。不得读取 v0.2 development/test 模型结果决定 checkpoint。

### 8.3 Token 长度 Gate

数据冻结必须使用固定 commit 的 Qwen2.5 tokenizer，对最终 chat template 的完整 `system + user/source packet + assistant target` 计数，不得用字符数代理，也不得启用 tokenizer truncation。Train 与 training-validation 分别记录 token p50、nearest-rank p95、pre-exclusion max、超长数量和 final max。

- `p95_tokens <=1024` 才能进入正式训练；
- 任一 `>1024` packet 必须在冻结前标记并排除，然后重新计算 400/100、4+2 家族、正/null 比和干扰比例；
- 排除后所有正式 packet 的 `max_tokens <=1024`；
- 任一重新计算后的数据 Gate 失败，状态降为 `smoke_only`；
- 禁止在 collator 或 tokenizer 中静默截断，也不得在看到测试输出后改变 1024 阈值。

### 8.4 OOM、时间与随机性 Gate

正式训练前先运行不超过 20 个 training packets 的 smoke，只检验：

- Qwen2 模块名与 LoRA 注入正确；
- trainable parameters `<1%`；
- forward/backward loss 有限；
- 峰值显存 `<=10.5 GiB`；
- adapter 可保存和重载；
- 固定输入与配置的生成链可复现；
- 训练进程没有读取 C07–C12 路径。

若 1024 tokens OOM，不自动缩为 768；先提交 amendment，重新评估截断和信息损失。Primary adapter 预计或实际超过 24 GPU 小时时停止，不减少来源家族或只保留容易样本。

只训练一个预注册 primary seed。若 primary 完整训练时间 `<=6` GPU 小时，可增加 `2026071602/03` 两个预注册 seed 作为训练随机性诊断；三者全部报告，不按测试表现选择 seed。额外 seed 不增加独立测试案例数。

---

## 9. 正式评估与声明 Gate

### 9.1 APT adapter 相对 General

只有同时满足以下条件，才能写“Project05 APT 微调优于同底座 General”：

- APT adapter 的 6-case macro GPS 比 General 高至少 0.05；
- 至少 4/6 案例方向不劣；
- unsupported-claim、invalid-pointer 和 ceiling-violation rate 均不高于 General；
- positive-packet coverage 不得比 General 低 0.05 以上；
- 改善不能仅由提高弃权率取得；
- G2 kappa `>=0.70` 且 unassessable `<=20%`。

### 9.2 Rule 与 structured/direct Gate

v0.2 的 Gate 继续原样生效：

- “LLM 优于 Rule”仍需 GPS `+0.05`、至少 4/6 案例不劣，并通过错误率和拒答护栏；
- “structured 优于 direct”仍需 UCR 至少降低 0.05、至少 4/6 案例有利，并通过 coverage 护栏；
- 标题或核心贡献中的正向 grounding 措辞仍需 G2、Rule 和 structured/direct 三个 Gate 全部通过。

### 9.3 无合格 G2 时

只能报告：

- schema-valid；
- pointer/hash/literal checks；
- `project_gold_packet_agreement`；
- abstention、coverage、拒答和错误状态；
- 相对作者锁定 observation gold 的差异。

不得使用 GPS/UCR，不得写“减少幻觉”“提高真实 APT 溯源准确率”或“领域微调已获人类验证”。

### 9.4 负结果路径

Adapter 若未过 Gate：

- 不调换 Qwen 规模或改用 Llama；
- 不用测试输出增加训练数据；
- 不启动 Phase 2/3 救场；
- Paper B 可降级为同底座领域适配的负结果/证据约束接口 pilot；
- Paper A 继续不写 LLM 正向结果。

---

## 10. 调用预算与一致性条件

正式推理条件数不因微调增加，v0.2 最大预算保持：

| 项目 | 调用数 |
|---|---:|
| General + APT-adapted compiler first-pass | 128 |
| General structured conclusion | 64 |
| General direct conclusion | 64 |
| 12-packet repeat panel | 192 |
| 最大正式调用 | 448 |

Repeat panel 的四个完整条件明确为：

1. General compiler；
2. APT-adapted compiler；
3. General structured（每次重复绑定完整 compiler + conclusion 两阶段哈希）；
4. General direct。

Atomic pilot 为 14 packets × 2 compiler conditions = 28 次调用：同一 Qwen 底座分别禁用/启用 adapter，用于验证 JSON、显存、延迟和 adapter 切换。Pointer copying 仍不构成科学定位结果。

QLoRA 训练计算与 448 次推理分开报告。若推理预计超过 24 GPU 小时，按 v0.2 规则取消 repeat panel，保留 256 次 first-pass；不得删除 APT-adapted 条件或只运行表现较好的模型。

---

## 11. 磁盘与工件治理

新路线只需一份 15.24 GB 仓库 snapshot 和小型 adapter，理论上可保持在 30 GB model/cache Gate 内：

- 只使用 Hugging Face cache snapshot，不复制到第二个 `local_dir`；
- adapter 单独保存，实际大小写入 manifest；
- 不执行 `merge_and_unload()` 后保存完整模型；
- 训练 checkpoint 只保存 adapter、optimizer 和 scheduler 状态；
- 限制 checkpoint 数并记录删除策略，但不得删除最终选择依据与日志；
- 每次训练前后记录 cache、adapter、checkpoint 和输出目录字节数；
- 任一时刻模型/cache/checkpoint 合计超过 30,000,000,000 bytes 即停止。

旧 Qwen1.5/SEVENLLM 元数据查询缓存不含权重，可以保留为审计记录。正式 lock 必须证明磁盘上不存在旧 checkpoint 重复占用。

---

## 12. 污染、语言与外推限制

正式报告必须：

1. 固定引用 Qwen 模型卡、许可证和可获得的训练说明；
2. 对 C07–C12 案例名、报告名、UUID、时间戳、命令和局部事件串执行记忆探针；
3. 对 Project05 训练数据执行 source-family hash 隔离；
4. 分开报告公开文本记忆与原始事件记录编译；
5. 无法证明未污染时写 `contamination_status="unknown"`；
6. 不把 Apache-2.0 或开放权重写成“确认没有测试污染”。

Qwen 具备中英文能力，但首轮仍固定英文 system/schema，并保留原始字段值。中文翻译只用于人工审阅，不把双语能力引入 RQ1/RQ5。

所有结论限定于指定 Qwen2.5-7B-Instruct checkpoint 的 4-bit 本地条件。不得外推到 FP16、其他参数规模、闭源前沿模型或普遍 APT 归因能力。

---

## 13. 新硬顺序

1. 用户审核本文的 Qwen2.5 选型、开放权重表述、数据 Gate 和 QLoRA 参数。
2. 生成并审核独立的 v0.3 实施计划；旧 v0.1 实施计划不能自动授权微调。
3. 新建 `llm_finetuning_v0.3` 和 v0.3 runtime/output 工件，不覆盖 v0.2 冻结测试与 Rule 证据。
4. 先实现训练/test 物理隔离、source-license manifest、近重复检测和泄漏测试。
5. 构建训练/training-validation packet，并通过最低数据充分 Gate。
6. 冻结 prompt、schema、训练配置、seed、checkpoint 选择规则和 adapter 名称。
7. 只有上述测试全绿后，才单独请求安装 Qwen2.5 隔离运行时和下载固定 commit。
8. 运行 20-packet QLoRA smoke；通过后再次提交正式训练授权。
9. 训练 primary adapter，只用 training-validation 选择 checkpoint。
10. 冻结 adapter SHA-256、训练日志、依赖、GPU 与数据 manifest。
11. 跑 28-call atomic pilot；通过 24 小时/显存 Gate 后才运行 64-packet Phase 1。
12. 完成独立 G2，判定 GPS/UCR 与标题 Gate。
13. 先写 Markdown 结果稿，审阅后再考虑正式格式。

---

## 14. 非目标

v0.3 仍不做：

- full-parameter fine-tuning；
- RLHF、DPO、GRPO 或在线强化学习；
- selector、DQN 或 Phase 2/3；
- actor/campaign 监督；
- 使用 C07–C12 调 prompt、训练数据、超参数或 checkpoint；
- 同时比较多个新底座或选择测试集赢家；
- 上传模型/adapter 或进行产品部署；
- 修改 Paper A、`run_mvp.py`、冻结 real cases、成本 profile 或旧结果；
- 在 Markdown 审阅前生成 DOCX/PPT/PDF。

---

## 15. 审阅人应重点裁决的问题

| 编号 | 待裁决事项 | 推荐判定 |
|---|---|---|
| V3-A1 | 是否接受商业公司发布、Apache-2.0 的 Qwen2.5 开放权重作为本地底座 | 接受并准确披露来源 |
| V3-A2 | 是否接受训练语料不可完全重建、污染状态只能为 unknown 的限制 | 接受并强制披露 |
| V3-A3 | 是否以同一 checkpoint + Project05 adapter 构成严格同底座对照 | 接受 |
| V3-A4 | 是否接受 train 400 / validation 100、来源家族隔离的最低 Gate | 接受；不足则降级 smoke/pilot |
| V3-A5 | 是否允许 observation-compiler QLoRA 成为唯一新增训练任务 | 接受 |
| V3-A6 | 是否保持 RQ1+RQ5、G2 与标题 Gate，不扩展 selector/端到端 | 接受 |
| V3-A7 | 是否接受一个 primary seed，额外 seed 只作有条件诊断 | 接受并声明限制 |
| V3-A8 | 是否继续执行 30 GB、24 GPU 小时和 2080 Ti 11 GB Gate | 接受 |

---

## 16. 当前授权状态

本文生成不构成模型下载或训练授权。当前状态为：

- Qwen2.5 + Project05 QLoRA 研究路线：**用户原则同意，待本文审核**；
- Qwen1.5/SEVENLLM 权重下载：**禁止**；
- Qwen2.5 权重下载：**禁止**；
- 新隔离运行时安装：**禁止**；
- 微调数据构建和作者核验：**待本文及实施计划批准**；
- QLoRA smoke/正式训练：**禁止**；
- atomic/formal inference：**禁止**；
- Paper A、Phase 2/3、论文正向声明：**禁止修改或提前写入**。

用户批准本文后的下一步是编写 v0.3 详细实施计划，不是直接下载权重或开始训练。
