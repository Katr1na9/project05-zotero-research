# Project05 LLM 证据编译层：正式 QLoRA 训练与配对评估实施计划 v0.1

日期：2026-07-19

状态：`draft_for_user_review_plan_only`

当前权威：`authority-lock-v0.21.json`

适用路线：Project05 主线前端语义建图层，不再作为独立 Paper B

当前授权：仅允许编写、审阅和提交本 Markdown；**不授权正式训练、正式推理、C07–C12 模型运行或 M3 接线**

## 0. 裁决先行

本计划把已经通过的本地单步 QLoRA smoke 推进为一个可审阅、可硬停的正式训练与配对评估协议。计划通过后仍需另行授权，才可执行正式训练。

后续方法链固定为：

```text
当前可见日志 / CTI / provenance
  -> 确定性来源适配、分包和候选构造
  -> QWEN-GENERAL 或 QWEN-ADAPTED 对候选证据边进行来源约束判定与规范化
  -> schema / pointer / hash / surface / scope / ceiling 机械准入
  -> EvidenceClaim[] + EntityBinding[] + ClaimNodeLink[]
  -> 冻结的 alignment state
  -> M3 / 调查控制器：可溯源性、最低成本取证顺序与 STOP
```

这条路线中的科学问题不是“Qwen 或 QLoRA 是否新颖”，而是：

> 带来源指针、可拒收、可弃权的语义编译层，能否在不突破证据上限的前提下，把异构安全证据转化为可供成本约束调查控制使用的溯源图；若使用任务适配，是否相对同一底座的原版模型产生可重复的增量。

正式比较必须同时保留 `RULE-STRONG`、`REUSE-HYBRID`、`QWEN-GENERAL` 和 `QWEN-ADAPTED`。不得只报告表现最好的一条路线。

## 1. 权威来源与优先级

出现冲突时按下表从上到下解释；后来的、范围更窄的合同优先于历史愿景稿。

| 优先级 | 工件 | 本计划继承内容 |
|---:|---|---|
| 1 | `contracts/authority-lock-v0.21.json` | 本地单步 smoke 已通过；primary training、formal inference、C07–C12、M3 仍关闭；服务器路线废止 |
| 2 | `contracts/authority-lock-v0.16.json` | 1,500 条正式候选对与独立 token Gate 的组合终态为 `formal_data_gate_passed=true` |
| 3 | `contracts/qwen-paired-fairness-contract-v0.1.json` | General/Adapted 唯一允许差异为 adapter state；独立单位为 case/attack chain |
| 4 | `llm-evidence-compiler-qwen25-paired-route-amendment-v0.1-20260718.md` | 恢复固定 Qwen2.5 同底座对照；正式数据门槛提高为 1,200/300 与 4+2 来源族 |
| 5 | `llm-evidence-compiler-label-blind-pair-construction-amendment-v0.2-20260719.md` | Zeek N1/N2/N3 配额修订，不改变 validation 总量与家族隔离 |
| 6 | `llm-evidence-compiler-mainline-integration-design-v0.1-20260717.md` | 主线接口、E0/E1/E2 评价边界、G0–G4 和 M3 传导逻辑 |
| 7 | `llm-apt-phase1-implementation-plan-v0.2-qwen25-qlora-20260716.md` | 训练参数、adapter-only、24 GPU 小时和 30 GB 等可兼容约束 |

历史 v0.2 实施计划中的 `400/100` 只保留为 smoke 下限，**不再是正式训练门槛**。正式训练必须使用后续修订的 `1,200/300`。

### 1.1 数据 Gate 状态解释

`candidate_pairs_v0.2/generated/data-gate-audit-v0.2.json` 是 pair 构造时的非 token 审计，所以其自身仍写有 `formal_data_gate_passed=false` 和 `token_gate_status=pending_independent_full_audit`。这不是当前终态。

独立 token 审计随后由 `tokenizer_gate_v0.2/generated/token-length-audit-v0.2.json` 完成，组合裁决记录在 `authority-lock-v0.16.json`：

- formal data Gate：通过；
- train：1,200；training-validation：300；
- train 来源族 4 个；training-validation 来源族 2 个，族间无重叠；
- supported / unsupported-by-bound-pointer：750 / 750；
- protected exact / near match：0 / 0；
- token overall p50 / p95 / max：589 / 881 / 1021；
- train p95：897；training-validation p95：580；
- `>1024`：0；截断或改写：0。

后续 v0.3 pair contract 将早期笼统的“多记录干扰 packet”要求操作化为同 packet 的来源绑定 hard-negative：门槛为同 packet negative fraction `>=0.75`，实际审计为 `1.0`，且 train 中 N1–N4、validation 中 N1–N3 均有表示。这个结果证明的是绑定指针条件下的候选判别压力，**不等于**已经证明模型能抵抗任意长窗口中的多记录干扰；后者仍须由 full compiler 的 development/test component bench 检验。

任何后续脚本都必须读取 v0.16 的组合裁决，不得仅凭早期 data-gate JSON 的中间状态错误地重开或关闭 Gate。

## 2. 当前已经证明与尚未证明

### 2.1 已证明的工程可行性

本地 RTX 2080 Ti 单步 smoke 已证明：

- 固定 `Qwen/Qwen2.5-7B-Instruct` revision `a09a35458c702b33eeacc393d103063234e8bc28` 可在本地加载；
- 4-bit NF4、double quantization、FP16 compute 可运行；
- LoRA `r=16`、`alpha=32`、7 个 attention/MLP projection 的 trainable ratio 为 `0.9189% < 1%`；
- 16 个 microbatch、1 个 optimizer step 的 loss 全部有限；
- adapter-only 保存及重载成功；
- peak reserved VRAM 为 `10.417969 GiB`，低于 `10.5 GiB` 上限；
- 未读取 development/test、C07–C12 或 M3 运行数据。

### 2.2 尚未证明

单步 smoke **不能**证明：

- adapter 改善编译质量；
- 3 epoch 训练能稳定完成；
- General/Adapted 公平切换与正式生成能在同一进程中完成；
- LLM 优于 `RULE-STRONG` 或 `REUSE-HYBRID`；
- 编译增量会传导到 M3 的路径质量、取证成本或 STOP；
- “幻觉减少”或人类验证的语义正确性；
- 对其他模型、精度、硬件或 APT 数据集的普遍泛化。

### 2.3 训练数据的精确能力边界

冻结的 1,500 条数据监督以下任务：

1. 判断候选边是否被当前绑定的来源记录支持；
2. 输出规范化边；
3. 输出可回指来源指针；
4. 对不被绑定记录支持的候选明确输出 `unsupported_by_bound_pointer`。

因此该 adapter 是证据编译层中的**来源约束判定与规范化子模块**。它不单独证明“任意原始日志/CTI 一步生成完整溯源图”。完整编译能力必须在相同 public packet 上，把候选构造、adapter、机械 admission、实体/link 输出作为一条管线评估。

## 3. 本计划的目标与非目标

### 3.1 目标

1. 训练唯一一个 primary `Project05 Evidence-Compiler Adapter`；
2. 只用 training-validation 选择 checkpoint；
3. 冻结 adapter、训练、数据、runtime 和选择 manifest；
4. 在相同输入上配对比较 `RULE-STRONG`、`REUSE-HYBRID`、`QWEN-GENERAL`、`QWEN-ADAPTED`；
5. 先过 training-validation/atomic 和 development Gate，再单独申请 C07–C12 正式测试；
6. 只有组件 Gate 通过且 compiler/M3 接口分别冻结后，再申请只读 M3 接线；
7. 失败时保留可发表的负结果或工程接口结论，不改变阈值救场。

### 3.2 非目标

- 不进行 full fine-tuning、RLHF、DPO、GRPO 或 selector 训练；
- 不做多底座搜索、多组 LoRA rank、学习率或 epoch 调参；
- 不重新获取训练语料，不改变 4+2 来源族或 1,200/300 配额；
- 不把来源标签、攻击叙事、actor、tactic、technique 或测试 gold 加入训练；
- 不使用 C07–C12 选择 prompt、阈值、checkpoint 或超参数；
- 不修改 `run_mvp.py`、冻结 real cases、旧 CSV/summary/trace、cost profile、Paper A 或专利；
- 不连接 4090 服务器；不查看、创建或删除服务器文件；
- 不上传 adapter/权重到 Hub；不保存 merge 后完整模型；
- 不生成 DOCX、PPT 或 PDF。

## 4. 冻结输入与新工件

### 4.1 必须按 SHA-256 读取的输入

| 输入 | 作用 |
|---|---|
| `candidate_pairs_v0.2/local-data/train.jsonl.gz` | 1,200 条正式训练数据，Git-ignored |
| `candidate_pairs_v0.2/local-data/training-validation.jsonl.gz` | 300 条 checkpoint 选择/训练诊断数据，Git-ignored |
| `candidate_pairs_v0.2/generated/data-gate-audit-v0.2.json` | 非 token 数量、家族、proof、pointer、exclusion 审计 |
| `candidate_pairs_v0.2/generated/determinism-audit-v0.2.json` | byte-identical 重建审计 |
| `tokenizer_gate_v0.2/generated/tokenizer-lock-v0.2.json` | tokenizer identity 与四文件 hash |
| `tokenizer_gate_v0.2/generated/token-length-audit-v0.2.json` | 正式完整 prompt+target token 分布 |
| `contracts/qwen-paired-fairness-contract-v0.1.json` | adapter off/on 公平性合同 |
| `results/qwen25-qlora-local-smoke-result-v0.2.json` | 本地硬件与显存上界证据 |

训练脚本启动时须重新计算上述已跟踪文件及本地 pair 文件 SHA-256，并与 v0.16/v0.21 锁对比。任一不一致均 fail closed。

### 4.2 计划通过后拟新增的跟踪工件

以下仅是文件规划，当前不创建：

```text
09-experiments/llm_evidence_compiler_mainline/
  contracts/
    qwen25-primary-training-contract-v0.1.json
    qwen25-primary-checkpoint-selection-contract-v0.1.json
    qwen25-component-paired-evaluation-contract-v0.1.json
  qlora_primary_v0.1/
    training-config-v0.1-local.json
    run-local-primary-v0.1.ps1
  results/
    qwen25-primary-training-result-v0.1.json
    qwen25-primary-adapter-manifest-v0.1.json
    qwen25-training-validation-selection-v0.1.json
    qwen25-component-pilot-result-v0.1.json
09-experiments/scripts/
  train_qwen_qlora_primary.py
  select_qwen_qlora_checkpoint.py
  run_llm_evidence_compiler_paired.py
  score_llm_evidence_compiler_paired.py
09-experiments/tests/
  test_qwen_qlora_primary.py
  test_llm_evidence_compiler_paired.py
04-progress/
  llm-evidence-compiler-primary-training-result-YYYYMMDD.md
  llm-evidence-compiler-paired-pilot-result-YYYYMMDD.md
```

adapter、optimizer、scheduler、raw generation、训练数据与模型权重只写入仓库内 Git-ignored 本地运行根，不进入 Git。

## 5. 正式训练配置

除非发生书面 amendment，下表不允许执行中修改。

| 字段 | 冻结值 |
|---|---|
| Base | `Qwen/Qwen2.5-7B-Instruct` |
| Revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| Method | causal SFT + 4-bit QLoRA |
| Quantization | NF4 + double quantization |
| Compute dtype | FP16 |
| Base parameters | 全部冻结 |
| LoRA target | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj` |
| LoRA rank / alpha / dropout | 16 / 32 / 0.05 |
| Trainable ratio | `<1%`，启动后实测复核 |
| Sequence length | 1024 |
| Truncation | 禁止 |
| Microbatch | 1 |
| Gradient accumulation | 16 |
| Effective batch | 16 |
| Train examples | 1,200 |
| Epochs | 3，单一 primary run |
| Microbatches | 3,600 |
| Optimizer steps | 225（每 epoch 75） |
| Optimizer | `paged_adamw_8bit` |
| Learning rate | `2e-4` |
| Scheduler | cosine |
| Warmup | 7 steps（`ceil(225 × 0.03)`，显式写死） |
| Weight decay | 0.0 |
| Max gradient norm | 1.0 |
| Gradient checkpointing | true |
| Primary seed | `2026071601` |
| Shuffle | 每 epoch 按 primary seed 派生、可复现；不按标签重排 |
| Loss mask | 只计算 assistant target token |
| Checkpoints | 每个 epoch 末保存 adapter + optimizer/scheduler/RNG state |
| Model save | adapter-only；禁止 merged model |

### 5.1 不允许的隐式补救

发生 OOM、非有限 loss、磁盘或时间失败时，不得静默：

- 把 1024 降到 768；
- 降低 rank 或移除 target module；
- 删除较长/困难样本；
- 减少来源族或只训练某一来源；
- 改用更大 GPU、服务器或更大模型；
- 改 microbatch/accumulation 来改变有效 batch；
- 重跑多个 seed 后选择最好结果；
- 查看 C07–C12 后修改任何训练配置。

这些动作均需要新的书面 amendment 与用户授权。

## 6. 本地资源与硬停

### 6.1 运行位置

- 仅在当前仓库工作树内执行；
- 复用已通过 smoke 的 `.local-qwen25-smoke/local-runtime/venv` 与现有固定 revision cache；
- primary 输出放到 `.local-qwen25-smoke/local-output/primary-v0.1/`；
- 不复制第二份 15.24 GB base snapshot；
- `TEMP/TMP/HF_HOME/TRANSFORMERS_CACHE/PIP_CACHE_DIR` 继续锁定在 `.local-qwen25-smoke/local-cache/`；
- `CUDA_VISIBLE_DEVICES=0`。

### 6.2 资源 Gate

| Gate | 阈值 | 失败动作 |
|---|---:|---|
| Peak reserved VRAM | `<=10.5 GiB` | 立即停止；不自动改 seq/rank/data |
| 当前 smoke 余量 | 约 84 MiB | 视为高风险，不视为充裕余量 |
| 总 model/cache/checkpoint/output | `<30,000,000,000 bytes` | 写 manifest 后停止 |
| Primary train + checkpoint selection | `<=24 GPU h` | 在最近完整 checkpoint 停止并标记 incomplete；不得进入正式评估 |
| Adapter 单文件 | `<1,000,000,000 bytes` | 停止并调查是否错误保存完整权重 |
| Loss | 每 microbatch 有限 | 立即停止，不跳过该 batch |

单步 smoke 用时约 82.8 秒。以 225 step 线性外推约 5.2 小时，但这只是容量估计，不包含全部 validation generation、checkpoint I/O 与热漂移，不能作为完成保证。正式训练前必须给出总墙钟上界估计；预计超过 24 小时则不启动。

### 6.3 窄显存余量下的操作纪律

允许的稳定性措施仅限不改变科学配置的实现细节：

- 在训练开始前确认无其他占用目标 GPU 的 Project05 进程；
- 保持 gradient checkpointing；
- optimizer step 后及时释放不再引用的临时 tensor；
- checkpoint/validation 边界调用 Python/CUDA 垃圾回收并记录前后显存；
- validation 使用 batch size 1；
- validation 前后不得重载不同量化或不同底座。

任何需要改变模型、数据、序列、batch 或训练目标的“优化”不属于实现细节。

## 7. Checkpoint 选择协议

### 7.1 可见数据边界

checkpoint 选择器只能读取：

- 300 条 training-validation candidate pairs；
- 三个 epoch checkpoint；
- 冻结 tokenizer、prompt、schema 与 scorer；
- 训练日志和资源 telemetry。

它不得读取 C04–C12、E1 private reference、G2/E2 表单、M3 输出或任何 formal test generation。

### 7.2 选择指标

对 epoch 1/2/3 的 adapter 在全部 300 条 training-validation 上做确定性生成。每条 invalid JSON、schema invalid、字段缺失、输出超长均按错误计，不做修复重试。

主选择指标：

1. 先在每个 held-out source family 内计算 supported / unsupported-by-bound-pointer 的 macro-F1；
2. 再对 Loghub 与 Zeek 两个 family 等权平均，得到 `family_macro_support_decision_f1`。

并列规则按顺序固定为：

1. 更高 full canonical JSON exact-match rate；
2. 更高 normalized-edge exact-match rate；
3. 更高 pointer exact-match rate；
4. 更低 assistant-token NLL；
5. 更早的 epoch。

不以 train loss 最低、单一来源最好或输出更长作为选择依据。选择后写入 adapter SHA-256 和完整选择表，其他 checkpoint 不得在正式测试中轮流尝试。

### 7.3 Checkpoint 资格硬门槛

被选 checkpoint 还必须满足：

- adapter-only 保存且重载后输出哈希在允许的确定性范围内复现；
- base snapshot、tokenizer、quantization、prompt/schema、data 和 runtime hash 与合同一致；
- trainable ratio `<1%`；
- 无 test/development/M3 路径访问；
- 无非有限 loss、OOM、静默截断或 batch 跳过；
- 训练完整完成 225 optimizer steps；
- 资源 Gate 全部通过。

任何资格门槛失败均判 primary training 失败，不选择“次优但不合规”的 checkpoint。

## 8. 配对评估条件

### 8.1 四个主条件

| 条件 | 实现 | 目的 |
|---|---|---|
| `RULE-STRONG` | 冻结 source parser + entity normalization + rule target linking | 最强确定性基线 |
| `REUSE-HYBRID` | 冻结可复用组件 + deterministic adapter + verifier | 检查现有组件包装是否已足够 |
| `QWEN-GENERAL` | 固定 Qwen，adapter off，经过同一 admission | 原版底座基线 |
| `QWEN-ADAPTED` | 同一加载进程、同一 Qwen，`project05_obs_compiler` on | 任务适配增量 |

`GENERAL-DIRECT` 只保留为后续安全诊断，不参与 primary adapter 选择，也不得进入控制器。

### 8.2 General/Adapted 公平性

两条件必须共享：

- 同一 base snapshot 与 tokenizer；
- 同一 4-bit 量化配置和 compute dtype；
- 同一加载进程与 GPU；
- 同一 public packet、候选、prompt、schema、max context 和 decode config；
- 同一 admission 与 scorer；
- 同一条件顺序区组计划；
- 同一失败与 JSON repair policy（首轮不 repair）；
- 同一 runtime/package/environment manifest。

唯一允许的模型差异是：

```text
QWEN-GENERAL: adapter disabled
QWEN-ADAPTED: project05_obs_compiler enabled
```

每次调用记录 adapter state、base hash、adapter hash、input hash、prompt hash、decode hash、raw output hash、admission result、latency、tokens 和 peak VRAM。

### 8.3 解码与重复

- primary first-pass 使用确定性 greedy decode：`do_sample=false`；
- `temperature/top_p` 不作为可调参数；
- `max_new_tokens=256`，输出超限按失败，不续写、不修复；
- 条件顺序按 `condition_order_seed=2026071801` 在 case × packet-role × modality 区组内平衡；
- 如后续运行非确定性重复，最多 3 次且只作稳定性诊断；
- 重复、packet、claim 和模型调用不是独立统计样本。

## 9. 评价阶段与授权边界

### Stage T0：计划与合同代码

当前只允许本 Markdown。用户批准计划后，可单独授权实现合同、trainer、runner 和纯 fake-module/fixture 测试；这仍不等于正式训练授权。

### Stage T1：正式训练预检

在不进行 optimizer step 前完成：

1. 校验 v0.16/v0.21 与全部输入 hash；
2. 重新验证 1,200/300、4+2、50/50、proof、pointer 和 protected scan；
3. 加载固定 base，复核 module inventory 与 trainable ratio；
4. 估算 225 step + 3 次 validation 的总墙钟；
5. 校验磁盘、GPU、cache 单副本和输出路径；
6. 证明训练进程无 development/test/C07–C12/M3 路径能力；
7. 生成 preflight audit 后硬停。

### Stage T2：Primary QLoRA training

仅在用户显式授权正式训练后执行一个 seed、三个 epoch。完成后立即进行 checkpoint 选择并冻结 adapter manifest；不开始 C04–C12 推理。

### Stage P1：Training-validation atomic pilot

在选中 adapter 后，使用 training-validation 的冻结小面板验证：

- adapter off/on 在同一进程切换；
- 结构化 JSON、指针和 admission 端到端连通；
- latency、tokens、显存和预计正式调用时间；
- 不把 training-validation 指标写成科学 test 结果。

面板、数量和抽样 seed 必须在第一次运行前写入合同；看到输出后不得换样本。

### Stage P2：C04–C06 development 配对 pilot

需要新的显式授权。只用于冻结 full compiler 的 request builder、matching、decode、admission 与 failure policy。可比较四个主条件，但不得用于论文 test 效应量。

### Stage E1：C07–C12 正式组件比较

需要再次显式授权。formal runner 只挂载 public root，不挂载 private reference。四个条件读取相同 frozen packet/visibility panel；输出完成并锁定后，scorer 才读取 E1 private reference。

### Stage M1：M3 只读接线与端到端评估

不在本计划自动授权。只有：

1. 组件 G0/G1 通过；
2. 选定的 compiler condition 通过 G2 或被明确接受为工程输入适配器；
3. compiler contract 与 M3 interface 分别冻结；
4. 合并冲突和 hash 审计完成；

才能申请把 controller-eligible sidecar 只读输入 M3。LLM 不选择 action、不产生 cost、不覆盖 STOP。

## 10. 统计单位与指标

### 10.1 独立单位

正式测试独立单位是 `case/attack chain`，C07–C12 为 `n=6`。所有指标先在 case 内聚合，再对 6 案例等权 macro。

以下均不能扩大 n：

- 同一 case 的 packet；
- supported/unsupported candidate；
- claim 或 link；
- 三次生成重复；
- token；
- action step；
- 不同 condition 的同一 case 观测。

条件是同一 case 上的配对观测。主要报告每 case 原始值、配对差值、case-macro、median 和 range；bootstrap/精确配对置换仅作探索性诊断，并明确 n=6 的力度有限。

### 10.2 组件主指标

1. `frozen-reference claim+link F1`：相对 E1 冻结作者参考的一致性，不称为人类共识真值；
2. `invalid-or-surface-unsupported rate`：pointer 不可解析、来源不可见、关键 surface 不可复现或 predicate 非法的比例；
3. `admitted coverage`：防止全拒答刷安全指标。

诊断：schema valid、pointer resolvable、entity binding、target link、abstain/reject、duplicate、per-modality、latency、tokens、VRAM、OOM/refusal。

### 10.3 Adapter 进入主线的机械 Gate

`QWEN-ADAPTED` 只有同时满足以下条件才可优先于 `QWEN-GENERAL`：

- 6-case macro frozen-reference claim+link F1 提高 `>=0.05`；
- 至少 `4/6` 案例差值非负；
- invalid-pointer、surface-unsupported、ceiling-violation 均不升高；
- admitted coverage 下降不超过 `0.05`；
- 不是全拒答、单一来源族或单一 predicate 驱动；
- 公平性 manifest 证明 adapter state 是唯一模型差异。

### 10.4 四条件最终选择

| 结果 | 主线处置 |
|---|---|
| Adapted 通过全部 adapter Gate 且优于其他自动条件 | 作为 M3 候选输入层；仍需端到端 Gate |
| Adapted 与 General 持平 | 采用 General，避免不必要训练维护成本 |
| Adapted 更差/不稳定 | 废弃 adapter，保留负结果 |
| Reuse-Hybrid 等于或优于 LLM 条件 | 优先 Reuse-Hybrid，LLM 降为可选接口 |
| 所有自动条件不优于 Rule-Strong | 采用 Rule-Strong；停止模型扩展 |

不允许在测试后改变 `0.05`、`4/6`、coverage 或安全护栏。

## 11. 人工审计边界

本计划的核心 E0/E1 指标不要求全量或双人审计：

- schema、pointer、hash、visibility、surface、scope、predicate、coverage、ceiling 均由机器判定；
- E1 只称“相对冻结作者参考的一致性”；
- training labels 不是 G2/E2，也不是人类共识 gold；
- 不要求用户逐条审核 1,500 条训练对。

只有论文拟使用“减少幻觉”“人类验证的来源支持”“语义正确性显著提高”等强措辞时，才另行预注册最小 E2：只审参与最终路径或触发 STOP 的去重 claim-link，两人来源盲化独立判断。E2 不做或失败时，删除强措辞，不阻塞 E0/E1 与 M3 机器实验。

## 12. 训练和评估实现任务

以下任务按顺序执行；每个带有独立硬停。

### Task 1：冻结 primary training 合同与负向测试

拟创建：

- `qwen25-primary-training-contract-v0.1.json`
- `training-config-v0.1-local.json`
- `test_qwen_qlora_primary.py`

先写测试，要求：

- 非 v0.16/v0.21 输入拒绝；
- 训练路径出现 development/test/C07–C12/M3 即拒绝；
- seq !=1024、truncation=true、seed 不符、train !=1200 或 validation !=300 即拒绝；
- base revision、7 个 target module、r/alpha/dropout 不符即拒绝；
- output root 逃逸仓库或非 Git-ignored 即拒绝；
- merged save、Hub upload、第二份 base snapshot 即拒绝。

**HARD STOP T1-A：** 代码/测试完成后只提交 diff，不运行正式训练。

### Task 2：实现正式 trainer

从 smoke trainer 提取已验证的加载、assistant-only mask、显存审计和 adapter-only 保存逻辑，不复制另一套不一致实现。

trainer 必须：

- 记录每 step loss、grad norm、LR、VRAM、wall time；
- 每 epoch 保存可恢复 checkpoint；
- 保存 RNG、optimizer、scheduler state；
- 每次保存后重载 adapter 校验；
- 遇到非有限 loss/OOM/hash 漂移立即停止；
- 不捕获异常后跳过 batch；
- 不生成或提交 raw payload/output。

**HARD STOP T1-B：** fake module、fixture 与无模型单元测试全绿后，等待 formal preflight 授权。

### Task 3：运行 formal preflight

只加载和检查，不做 optimizer step。输出：输入 hash、runtime、GPU、VRAM baseline、disk、预估时间、路径访问 allowlist 和拟运行命令。

**HARD STOP T1-C：** 用户审阅 preflight 后决定是否授权 primary training。

### Task 4：执行唯一 primary training

显式授权后执行 225 optimizer steps。任何中断先保存失败 manifest；只有合同允许且状态完整的 checkpoint 才可按原 seed 恢复。不得从头多跑并选择更好的一次。

**HARD STOP T2：** 训练完成后只运行 training-validation checkpoint 选择；不访问 development/test。

### Task 5：冻结 adapter 与选择记录

写出：

- 三个 checkpoint 的完整 validation 表；
- 选择规则逐项裁决；
- selected adapter 文件清单和 SHA-256；
- base/tokenizer/data/runtime/GPU/config hash；
- 训练完整性、显存、时间、磁盘和失败 telemetry；
- `controller_eligible=false`。

**HARD STOP T3：** 提交 aggregate result Markdown/JSON 供用户审阅；不自动运行 atomic pilot。

### Task 6：实现四条件 paired runner/scorer

先用 fake backend 验证：

- 每个 packet 四条件齐全；
- General/Adapted 同一 base 进程且唯一差异为 adapter state；
- condition order 可复现且区组平衡；
- raw candidate 永不进入 controller；
- private mutation 不改变 public input hash；
- invalid output 不被 repair 成 first-pass；
- scorer 在所有 generation 锁定后才读取 private reference；
- case-macro 而非 packet-level n。

**HARD STOP P0：** 纯测试通过后请求 atomic pilot 授权。

### Task 7：training-validation atomic pilot

只验证运行完整性、adapter toggle、JSON/admission、显存、延迟与调用预算。其分数只作诊断，不进入论文 test 表。

**HARD STOP P1：** 用户审阅后才申请 C04–C06 development。

### Task 8：C04–C06 development pilot

冻结 full compiler prompt、matching、decode、admission 与 failure policy；完成后 hash lock。若任一 G0/G1 失败，不得申请 C07–C12。

**HARD STOP P2：** 提交开发集快照与预计 formal wall time。

### Task 9：C07–C12 正式组件评估

需单独授权。一次完成冻结四条件 first-pass；测试输出不得反馈训练、prompt、规则、阈值或 checkpoint。

**HARD STOP E1：** 输出与 scorer 分离冻结，提交 E0/E1 结果和所有 Gate；不自动接 M3。

### Task 10：M3 只读接线与端到端实验

需新计划、新 authority lock 和独立合并审计。只传入 controller-eligible sidecar；保持 cost profile、controller、budget、actions、initial visibility 和 STOP 不变。

## 13. 负结果与恢复路径

| 失败点 | 允许结论 | 后续动作 |
|---|---|---|
| Primary training OOM/超时/非有限 | 本地正式训练在冻结配置下不可行 | 停止；不降配置救场 |
| Adapter validation 无增量 | QLoRA 未提供 held-out family 增量 | 可继续保留 General/Rule/Reuse 评估，adapter 不进主线 |
| Atomic/development G0/G1 失败 | LLM 接口未达到安全准入 | 不运行 C07–C12 |
| Adapted 未过 adapter Gate | 微调无有效增量 | 采用 General/Reuse/Rule |
| General/Adapted 均不优于 Rule | LLM 对本合同无编译增量 | 主线使用 Rule 或 Reuse，报告负结果 |
| 组件 G2 过、M3 G3 不过 | 编译层工程有效但未改善成本约束调查 | 不声称端到端价值 |
| 未做 E2 | 无人类共识语义结论 | 仅写机械可回指和冻结参考一致性 |

任何负结果都不得通过 Phase 2/3、selector、多模型、额外 seed 或测试后阈值修改来补救。

## 14. 提交、隐私与仓库纪律

允许提交：

- 合同、配置、代码、测试；
- aggregate 审计、hash manifest、资源统计；
- Markdown 计划与结果记录。

禁止提交：

- base 权重、tokenizer cache 副本；
- adapter/optimizer/scheduler 二进制；
- raw train/validation pair；
- raw model generation；
- private E1/E2 reference 或审计表；
- Kaggle 凭据、密码、环境缓存；
- DOCX/PPT/PDF。

禁止使用 `git add .`。每次提交前必须检查 staged file list、`git diff --check` 和 forbidden-path diff。

## 15. 计划通过后的授权阶梯

| 阶段 | 计划通过是否自动授权 |
|---|---|
| 创建训练合同、trainer 和无模型测试 | 否；建议作为下一次最小授权 |
| 创建 paired runner/scorer 和无模型测试 | 否；建议在 adapter 冻结后另行授权 |
| 正式 preflight（零 optimizer step） | 否 |
| 225-step primary training | **否，必须显式授权** |
| training-validation atomic pilot | 否 |
| C04–C06 development 模型运行 | 否 |
| C07–C12 正式模型运行 | **否，必须再次显式授权** |
| M3 接线与端到端实验 | **否，需独立计划和合并审计** |
| 论文正向结论 | 否，取决于实际 Gate |

## 16. 审阅者检查清单

- [ ] 是否同意 QLoRA 只定位为来源约束判定/规范化子模块，而不夸大为端到端完整建图？
- [ ] 是否接受唯一 primary seed、3 epoch、225 step、无超参搜索？
- [ ] 是否接受 checkpoint 只由 300 条 training-validation 和冻结并列规则选择？
- [ ] 是否接受 84 MiB 显存余量属于硬风险，失败后不静默降 seq/rank/data？
- [ ] 是否接受四条件必须同时保留，且 Reuse/Rule 胜出时主线不用 LLM？
- [ ] 是否接受 case/attack chain 为独立单位、测试 n=6、重复不扩样本量？
- [ ] 是否接受无 E2 时禁止“减少幻觉/人类验证语义正确”措辞？
- [ ] 是否确认计划审阅通过仍不等于正式训练、C07–C12 或 M3 授权？

## 17. 本轮交付结论

本轮只交付本实施计划。它不会修改任何训练/评估 authority lock，不会启动正式训练或模型推理。

若计划通过，建议下一授权严格限制为：

> 实现 Tasks 1–2 的训练合同、trainer 骨架与无模型负向测试，完成后停在 HARD STOP T1-B；不实现 paired runner，不运行 formal preflight、optimizer step、development/test 或 M3。
