# Project05 主线 LLM 证据编译层：Qwen2.5 同底座配对路线恢复修订案 v0.1

日期：2026-07-18  
状态：`approved_model_route_design_only`  
用户裁决：恢复 Qwen 路线；正式比较原版 Qwen 与同 checkpoint 的 Project05 QLoRA 适配版  
上游主设计：`llm-evidence-compiler-mainline-integration-design-v0.1-20260717.md`  
当前授权：**允许冻结设计、准备离线合同/数据审计/测试；不授权安装或变更模型运行环境、下载 tokenizer/权重、训练、正式推理、C07–C12 模型运行或 M3 接线**

## 0. 裁决先行

1. **Qwen2.5 恢复为唯一正式 LLM 底座。** 使用固定 revision 的 `Qwen/Qwen2.5-7B-Instruct`，不再以 OLMo 2 作为当前候选。
2. **原版与微调版必须同时保留。** `QWEN-GENERAL` 关闭 adapter；`QWEN-ADAPTED` 在完全相同底座上启用 Project05 QLoRA adapter。不能只报告表现较好的一方。
3. **不是全参数微调。** 底座参数冻结，只训练 attention/MLP 线性层中的低秩参数，trainable parameters 必须 `<1%`；仅保存 adapter，不生成或保存合并后的第二份完整模型。
4. **LLM 是主线前端，不是独立 Paper B。** 它把日志、CTI 文本与 provenance records 编译为带来源指针的 observation、实体绑定与候选链接；M3 继续负责可支持溯源粒度、成本约束取证动作和 STOP。
5. **选择以预注册结果为准。** adapter 过 Gate 才进入主系统；若持平、退化或不稳定，则主系统采用原版 Qwen、`REUSE-HYBRID` 或强规则条件，不能为保住微调叙事调整阈值。
6. **模型不是创新点。** 候选创新仍是“逐边来源约束、可弃权的语义编译如何进入成本约束调查控制闭环”，不是 Qwen、LoRA 或 QLoRA 本身。

本修订案只取代 `llm-evidence-compiler-open-base-finetuning-amendment-v0.1-20260718.md` 的 OLMo 模型选择，以及主设计 §16 中“只有通用模型失败后才考虑 QLoRA”的顺序约束。它不撤销主线融合架构、public/private 隔离、来源指针 Gate、C07–C12 测试隔离、成本规范化或 M3 独立冻结要求。历史文件保留原状态，不回写成从未发生过。

## 1. 统一方法链

```text
当前可见的日志 / CTI / provenance
  -> 确定性来源适配与 packet 构建
  -> QWEN-GENERAL 或 QWEN-ADAPTED 候选编译
  -> schema / pointer / hash / literal / scope / ceiling 机械准入
  -> EvidenceClaim[] + EntityBinding[] + ClaimNodeLink[]
  -> 冻结的 Project05 alignment state
  -> M3：可支持溯源粒度 + 最低成本取证动作 + STOP
```

LLM 只能输出候选 evidence sidecar。未通过准入的内容不得进入控制器；在 compiler contract 与选定 M3 interface 完成独立冻结及合并审查前，LLM 输出继续保持 `controller_eligible=false`。

## 2. 固定模型与 adapter 身份

### 2.1 唯一底座

| 字段 | 冻结值 |
|---|---|
| Model ID | `Qwen/Qwen2.5-7B-Instruct` |
| Resolved revision | `a09a35458c702b33eeacc393d103063234e8bc28` |
| 发布方 | Alibaba Cloud / Qwen Team |
| Hub license metadata | `apache-2.0` |
| 部署方式 | 本地离线；正式运行固定 `local_files_only=true` |
| 训练/推理量化 | 4-bit NF4；RTX 2080 Ti 上的实际 compute dtype 由 runtime smoke 冻结 |
| 训练序列候选 | 1024 tokens，必须先过正式 tokenizer 长度 Gate |

Qwen 是商业公司发布的开放权重模型，不得在论文中写成“非商业模型”或“完全开源训练链”。许可证、revision、4-bit 限制及公开预训练污染状态 `unknown` 均须准确披露。

### 2.2 Project05 适配器

| 字段 | 冻结值 |
|---|---|
| 公开名称 | `Project05 Evidence-Compiler Adapter` |
| 运行时 key | `project05_obs_compiler` |
| 方法 | causal SFT + 4-bit QLoRA |
| 底座状态 | 全部冻结 |
| 可训练参数 | `<1%` |
| LoRA 候选 | `r=16`, `alpha=32`, dropout `0.05` |
| 候选模块 | `q_proj,k_proj,v_proj,o_proj,gate_proj,up_proj,down_proj`；须由 module inventory smoke 复核 |
| 保存策略 | adapter-only；禁止 `merge_and_unload()` 后保存完整权重 |

adapter 只学习四类窄任务：

1. `observable extraction`：从可见来源抽取带精确 pointer 的原子 observation/SPO；
2. `entity binding`：在 host/process/time/session 作用域内规范化实体；
3. `target linking`：在公开 target catalog 内提出受支持的候选链接；
4. `abstain`：来源不足、指针不成立或语义上限不允许时明确弃权。

禁止训练 actor/campaign/intent 判定、TTP 标签生成、planner action、成本、预期收益、恢复集合或 STOP。

## 3. 正式对照条件

| 条件 | 模型状态 | 用途 |
|---|---|---|
| `RULE-STRONG` | 无 LLM | 冻结的确定性强基线 |
| `QWEN-GENERAL` | 固定 Qwen，adapter off | 原版模型基线 |
| `QWEN-ADAPTED` | 同一 Qwen，`project05_obs_compiler` on | 检验 Project05 任务适配增量 |
| `REUSE-HYBRID` | 已准入复用组件 + 规则 | 检验是否根本不需要新增微调 |
| `GENERAL-CONSTRAINED` | 原版 Qwen，经 compiler/admission/controller | 架构安全条件 |
| `GENERAL-DIRECT` | 同一原版 Qwen，直接结构化结论 | 仅作安全负对照，不进入控制器 |

`QWEN-GENERAL` 与 `QWEN-ADAPTED` 的唯一预期模型差异是 adapter 状态。两者必须共享：

- 同一底座 snapshot、tokenizer、量化配置与加载进程；
- 同一 public packet、prompt、schema、最大上下文与解码参数；
- 同一运行顺序随机化/阻塞方案、硬件和软件环境；
- 同一机械 admission 与 scorer；
- 同一冻结测试集，且测试输出不能反向影响 prompt、训练数据、超参数或 checkpoint。

独立统计单位是 `case/attack chain`（测试 `n=6`），同一 packet 的重复生成只是技术重复，不得当成独立样本扩大显著性。

## 4. 数据与泄漏 Gate

恢复 Qwen 不自动恢复旧独立 Paper B 的训练授权，也不把历史 proposal labels 变成 gold。允许复用的只有经过逐项复验的许可、notice、source hash、规范化规则和 exclusion audit。

正式 adapter 数据冻结最低要求：

- train `>=1,200` packets，来自 `>=4` 个独立来源族；
- training-validation `>=300` packets，来自不进入 train 的 `>=2` 个来源族；
- observation/null 各占 `40%–60%`；
- 多记录干扰 packet `>=50%`；
- C07–C12、E3/E5、OpTC、OTRF、WitFoo、private gold、G2 表单及模型输出不得进入训练；
- exact hash 与固定 5-gram Jaccard `0.85` exclusion scan 必须通过；
- 按 source family × role × predicate 分层抽检至少 `20%`，作者接受率 `>=95%`；失败 stratum 扩展为 100% 审核。

只达到旧 `400/100` 下限时，仅允许训练 smoke adapter，不能据此写“微调有效”。作者审核是训练数据质量控制，不是 G2，也不是人类共识 gold；本路线不要求为了机械指标重新启动全量双人审计。

### 4.1 Token Gate

只有在 tokenizer 下载另获授权后，才能用固定 Qwen revision 的正式 chat template 统计完整 `system + user/evidence + assistant target`：

- train/validation 分别记录 p50、nearest-rank p95、pre-exclusion max、超长数量和 final max；
- `p95_tokens <=1024`；
- 任一 `>1024` packet 必须在冻结前显式排除，随后重算数量、来源族、角色比和干扰比例；
- 最终 `max_tokens <=1024`；
- 禁止 tokenizer/collator 静默截断；失败即 `smoke_only` 或另提 amendment。

## 5. 训练和运行 Gate

本修订案不直接授权以下动作。顺序必须是：

1. 冻结本修订案、authority lock 和无模型依赖的负向测试；
2. 复验旧训练来源许可/hash/exclusion 状态并形成主线 data-readiness；
3. 单独授权后，建立隔离环境并只下载固定 Qwen tokenizer/snapshot；
4. 运行 20-packet QLoRA smoke：module inventory、loss、显存、adapter 保存/重载、无测试路径访问；
5. 用户再次授权后训练唯一 primary adapter；只用 training-validation 选择 checkpoint；
6. 冻结 adapter SHA-256、数据、runtime、GPU、prompt、解码和运行 manifest；
7. 同一加载进程切换 adapter off/on，先跑 development/atomic pilot；
8. 通过时间/显存 Gate 且再次获授权后，才运行 C07–C12 正式比较；
9. 只有 compiler 与 M3 interface 各自冻结后才进行只读 adapter 接线与端到端评估。

任何一步 OOM、非有限 loss、adapter 无法准确重载、训练读取测试路径、运行环境漂移或磁盘超过 30,000,000,000 bytes，均硬停。不得通过降低来源族、删除困难样本、查看测试后改超参或换更大模型救场。

## 6. 选择 Gate 与论文解释

### 6.1 Adapter 相对原版 Qwen

`QWEN-ADAPTED` 只有同时满足以下条件，才允许被选择为主线 LLM 条件：

- 测试 6-case macro reference claim+link F1 相对 `QWEN-GENERAL` 提高至少 `0.05`；
- 至少 `4/6` 案例方向不劣；
- invalid-pointer、surface-unsupported 和 ceiling-violation rate 均不高于 General；
- admitted coverage 相对 General 的下降不超过 `0.05`；
- 效果不是由单一来源族、单一 predicate 或全拒答造成；
- adapter/off 与 adapter/on 的 base、prompt、input、decode、runtime hash 均通过公平性校验。

### 6.2 最终采用规则

| 结果 | 主系统决定 |
|---|---|
| Adapted 通过全部增量 Gate | 采用 `QWEN-ADAPTED` 进入后续 M3 闭环候选 |
| Adapted 与 General 持平 | 采用 `QWEN-GENERAL`，不承担不必要的训练维护成本 |
| Adapted 更差或不稳定 | 弃用 adapter，报告负结果 |
| `REUSE-HYBRID >= QWEN-ADAPTED` | 优先复用混合方案，LLM 微调降为可选接口 |
| 所有 LLM 条件未过 compiler Gate | 主线回退 `RULE-STRONG/REUSE-HYBRID`，不得让 LLM 进入标题或正向摘要 |

即使 adapter 通过组件 Gate，也不能单独证明整条论文主线成立。只有在相同控制器、预算和成本 profile 下进一步通过端到端 Pareto/STOP/ceiling Gate，才能声称编译增益传导到成本约束溯源。

## 7. 人工审计边界

本路线的核心机器可判指标包括 schema-valid、pointer/hash/literal/scope、admitted coverage、reference claim/link 一致性、ceiling violation，以及对 M3 路径与成本的传导。它们不要求全量双人盲审。

只有论文拟使用“减少幻觉”“人类验证的来源支持”“语义正确性显著提高”等强语义措辞时，才另行触发最小、来源盲化的双人语义抽检及一致性 Gate。若该 Gate 不做或失败，删除强语义措辞，不阻塞机械指标和端到端控制实验。

## 8. 当前授权矩阵

| 动作 | 当前状态 |
|---|---|
| 恢复 Qwen 为唯一底座 | **已批准** |
| 原版 Qwen vs QLoRA Qwen 配对设计 | **已批准** |
| 新增本修订案、authority lock、离线负向测试 | **已授权** |
| 复验已存在的来源元数据/hash/排除审计 | **允许，不获取新语料** |
| 获取新训练语料 | **未授权** |
| 安装/变更模型运行环境 | **未授权** |
| 下载 Qwen tokenizer 或权重 | **未授权** |
| 训练 smoke/primary adapter | **未授权** |
| C07–C12 模型推理或 M3 接线 | **未授权** |
| 修改 `run_mvp.py`、冻结案例或旧结果 | **禁止** |
| 生成 DOCX/PPT/PDF | **不做；Markdown 审阅后另议** |

## 9. 下一交付 Gate

本修订冻结后，下一项无模型执行工作是生成 `QWEN-GENERAL/QWEN-ADAPTED` 公平性合同与训练数据复验报告，回答：

1. 当前已批准来源是否在主线合同下达到 `1,200/300`、`4+2`、正/null 和干扰比例；
2. 哪些样本只能用于 smoke，哪些可以进入正式训练候选；
3. exclusion lock 是否仍覆盖 C07–C12 及五个被阻断测试族；
4. adapter on/off 是否被机器合同限制为唯一模型差异。

该报告通过后，再向用户单独申请 tokenizer/runtime/权重 Gate；不把“继续推进”解释为无限制下载或训练授权。
