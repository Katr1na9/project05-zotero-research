# Project05 受证据约束的 LLM 辅助 APT 溯源研究设计 v0.1

日期：2026-07-15
状态：设计审阅稿；尚未授权模型下载或正式实验
文档优先级：本文件只定义新 LLM 主线，不改写既有冻结实验事实。用户审阅通过后，才进入实施计划与代码修改。

## 1. 研究定位

Project05 的新主线是**受证据约束的大语言模型辅助 APT 溯源**。LLM 不再只是未来可接入的解释器，而是需要被独立评估的核心实证模块。现有调查控制、成本治理、信息隔离、显式 STOP 和支持上限继续作为 LLM 的安全执行层。

工作论文主张应被写成待检验命题，而不是预设结论：

> LLM 能否把 CTI、日志与 provenance 子图编译成带精确来源指针的结构化证据，并在可审计控制层约束下改善攻击路径重建和后续序贯调查，同时减少自由 LLM 的无支撑断言与过度归因。

论文主终点是攻击行为链、阶段、跨来源证据路径、证据缺口和可支撑结论粒度。actor/campaign 识别只在独立外部真值完整时开放；当前 C07–C12 没有这样的真值，因此不能把内部 G3、厂商标签或案例名称重新解释为 actor accuracy。

建议工作标题：

> 受证据约束的大语言模型辅助 APT 溯源：异构安全证据编译与序贯调查控制

## 2. 当前事实基线

设计开始时的仓库事实如下：

1. C04–C06 有 26 条开发 evidence claims；C07–C12 有 32 条冻结测试 claims、6 个独立案例或攻击链。
2. 现有 `llm_compiler` 支线只生成了 C07–C09 的 14 条 pilot，其中 10 条为原子主样本，4 条为上下文依赖对照。
3. 尚未下载 LLM 权重，尚未运行任何模型推理；现有 M2、M3a、Logistic、XGBoost、AFA 和 Depth-2 结果均不包含 LLM 因果贡献。
4. 当前机器为 RTX 2080 Ti 11 GB，硬件上适合 7B 级 4-bit 推理；当前 Codex Python 运行时未安装 `torch`、`transformers`、`accelerate`、`bitsandbytes`、`jsonschema` 或结构化生成依赖。
5. `run_mvp.py` 已有公开 `planner_state_view`、`planner_action_views` 和外部 `action_selector` 接口；既有 runtime contract 已禁止规划器读取隐藏恢复集合、mask、seed、实际通道状态和 Oracle。
6. 现有 pilot 把 `sample_id` 设置为 gold `claim_id`，且提示要求模型原样返回该 ID。与此同时，当前状态构造器使用 `required_claim_ids` 判断 CTI 节点是否满足。直接将 pilot 输出接入规划器会产生答案键泄漏：模型可在语义错误时仅凭复制 ID 被误算为覆盖节点。新主线必须先修复这一结构问题。

## 3. 研究问题与可证伪假设

### RQ1：结构化证据编译

通用 LLM 或安全领域 LLM 能否比确定性规则编译器更准确地把可见安全记录转换为符合 schema、可回指来源的原子 evidence claims？

- H1a：至少一种 LLM 在 claim existence 或字段 macro-F1 上超过规则编译器。
- H1b：LLM 的收益不以更高 unsupported-claim rate、无效来源指针或更高人工修正成本为代价。
- 失败条件：LLM 只改善文本流畅度，或字段指标改善但无支撑断言、指针错误明显增加。

### RQ2：领域模型的增量

在底座、量化和生成配置尽量匹配时，安全领域指令训练是否相对通用模型带来可复核的证据编译收益？

- H2：安全领域模型在至少一个预注册主要语义指标上优于同底座通用模型，且不恶化来源支撑和下游安全指标。
- 失败条件：收益只存在于个别记录、只存在于技术重复，或由不同底座/提示/上下文长度混淆。

### RQ3：端到端影响

不同编译条件产生的 claims 是否实质改变攻击路径状态、动作选择、达到目标的成本、STOP 或结论上限？

- H3：LLM 编译相对规则编译改善至少一个案例级端到端指标，或在不降低结果质量时减少人工编译工作量。
- 失败条件：抽取指标变化无法传导到规划；或传导只体现为越界、过早停止和错误动作。

### RQ4：受约束 LLM 动作选择

只读取公开状态和候选动作的 LLM selector，能否在不读取答案键、不增加结论越界的情况下改善调查成功或成本？

- H4：受约束 selector 至少保持安全指标，并在部分独立案例上改善成功、成本或动作路径。
- 失败条件：优势只来自无效动作被人工修正、隐藏字段泄漏、技术重复计数，或 selector 在案例级不稳定。

### RQ5：自由推理与受控推理

自由 LLM 直接归因是否比结构化编译加确定性控制更容易产生无来源结论和越级归因？

- H5：`LLM-direct` 的 unsupported claim、无引用结论或 over-attribution 高于受约束条件。
- 失败条件：两者没有差异；此时不能声称控制层缓解了 LLM 风险。

## 4. 系统架构与职责边界

主数据流如下：

```text
可见 CTI / 日志 / provenance 子图 / IOC 上下文
    -> LLM evidence compiler
    -> schema 与来源验证
    -> 公开 CTI 节点语义链接
    -> evidence state
    -> M2 / AFA / XGBoost / 受约束 LLM selector
    -> 执行采集或 STOP
    -> 新证据
    -> 重新编译、验证、链接与状态更新
    -> 带来源的攻击路径和受支持结论
```

### 4.1 LLM evidence compiler

编译器只读取当前允许可见的证据 packet、公开 CTI 节点目录和 schema。一个 packet 包含同一案例、同一有限时间窗或同一 provenance 邻域内的若干记录，其中可以包含无关记录。编译器输出零个或多个原子 candidate claims，内容包括 source type、claim type、subject–predicate–object、时间范围、来源支持的 tactic/technique、从 packet 中选择的 source pointer、candidate-to-node 映射及理由；没有可支持 claim 时必须显式弃权。

编译器不得输出或读取 actor 真值、隐藏恢复集合、Oracle、mask、seed、实际通道状态、gold claim 或节点的隐藏 required claim IDs。

### 4.2 验证与准入层

验证器依次执行 JSON/schema、请求与来源身份、来源存在性与哈希、字段来源支撑、公开节点语义映射、重复/冲突/支持上限检查。机械校验不能替代语义支撑判断；正式 unsupported-claim 指标必须使用冻结 gold 与来源盲审，不得使用另一个 LLM 作为最终裁判。

### 4.3 调查控制器

经过准入的 claims 进入现有 evidence state。M2、AFA、XGBoost、Logistic 和前瞻规划器保持冻结，用来隔离“输入表示改变”与“规划算法改变”。成本 profile、通道 prior、mask 和随机种子在条件间配对。

### 4.4 受约束 LLM selector

LLM selector 只读取新的 LLM runtime contract 生成的公开状态与动作视图，并返回一个公开候选 `action_id`、引用的公开 claim/node ID、简短理由，或者显式 STOP/abstain。执行器按 `action_id` 回查完整动作，随后才读取真实恢复集合。未知动作、引用隐藏对象或非法输出不得自动修正为有效动作。

### 4.5 `LLM-direct` 安全对照

自由 LLM 读取相同可见证据后直接输出攻击路径、当前归因结论和缺失证据。它不进入正式执行器，不影响 gold 或案例配置。该条件只用于测量无来源断言、过度归因与弃权行为。

## 5. 身份分离与答案键防护

### 5.1 三类 ID 必须分离

- `request_id`：模型请求的随机或哈希化公开标识；
- `candidate_claim_id`：由请求哈希和输出序号派生的候选标识；
- `gold_claim_id`：只存在于私有评分包中的 canonical 标识。

模型请求不得包含 `gold_claim_id`，不得要求模型复制 canonical claim ID。修改 gold 文件必须不改变模型请求字节或请求哈希。

### 5.2 公开 CTI 节点语义目录

现有 `required_claim_ids` 只适合冻结模拟器，不适合直接接受 LLM 输出。新实验为每个 CTI 节点建立独立版本化的公开语义目录，只包含调查前可知的 node ID、阶段、自然语言调查需求、允许的 claim/source 类型、必要实体或关系约束、corroboration 要求和禁止事项。

目录不得包含 `recoverable_claim_ids`、gold claim ID、实际通道状态或动作答案。其来源必须记录为 CTI schema、调查请求或预先冻结的人工定义。

### 5.3 新的语义覆盖模式

LLM 端到端实验不能沿用“candidate ID 是否命中 `required_claim_ids`”作为覆盖判断。需要新增 model-agnostic semantic-link 模式：只有通过来源验证且符合公开节点语义目录的 candidate claim 才能支持节点。

人工 gold、规则编译、通用 LLM 和安全 LLM 必须经过同一个公开 linker。旧 ID-based 模式保持不变，确保历史结果逐字节可复现。

允许另设明确标注的 `gold-admission diagnostic`：使用隐藏 gold 判断 candidate 是否语义等价，并决定是否映射 canonical ID。该诊断只能测量错误传播上界，不能被写成可部署端到端结果。

## 6. 数据、切分与实验单位

### 6.1 开发与冻结测试

- 开发：C04–C06，26 条 claims。用于 prompt、节点语义目录格式、schema、拒收规则和运行器调试。
- 冻结测试：C07–C12，32 条 claims、6 个独立案例。测试输出不得用于修改 prompt、目录、阈值或模型配置。
- 现有 14 条 pilot：只用于数据隔离、模型加载、显存和输出解析冒烟测试，不能代替完整冻结测试。

正式编译评估分为两层：

1. `atomic-diagnostic`：沿用单条代表记录，检查模型加载、基本字段抽取和严格 JSON。由于输入已经提供唯一 source pointer，该层的 pointer exact match 只是接口完整性指标，不能被解释为模型具备来源定位能力。
2. `context-packet-primary`：每个正 packet 含一个或多个相关记录及同窗/同邻域干扰记录，模型必须选择实际支持 claim 的 pointer；另加入按案例和来源类型匹配的 null packet，要求输出空列表/弃权。

冻结测试主任务包含 32 个正 context packets 和 32 个匹配 null packets，共 64 个 packets。开发集相应包含 26 个正 packets 和 26 个匹配 null packets。负例由冻结的确定性抽样规则产生，并在模型运行前由来源盲审确认不存在可接受的目标 claim；不得根据模型输出重新挑选“更容易”的负例。

这组负例用于估计 false positive、hallucination 和正确弃权。上下文 packet 中的多记录选择用于估计真正的 source-pointer 定位；原子任务不承担这些主结论。

### 6.2 实验单位

- 编译层观测单位是 evidence packet，packet 嵌套于案例；同一原始记录若进入多个 packet，其共享性必须在 manifest 中记录，分析时不得假定完全独立。
- 端到端与 selector 的独立单位是案例或攻击链，共 6 个。
- 同一记录的五次生成是技术重复，不增加独立样本量。
- 270 个 mask × intensity × seed 条件是 6 个案例内配对重复，不是 270 次独立攻击。

主要结论必须按案例报告或使用尊重嵌套结构的分析；记录级或 episode 级结果只能作为条件内精度描述。

### 6.3 Gold 与盲审

`model_input` 与 `private_gold` 必须物理分文件、分目录。推理运行器只获得 public package 路径；scorer 在推理结束后单独读取 private package。正式来源支撑与 unsupported 判断使用冻结 gold 加来源记录，必要时由两名盲审者独立判断并记录裁决；模型或项目代码标签不得冒充人工标签。

## 7. 模型与实验条件

### 7.1 主要模型对照

- 通用模型：`Qwen/Qwen1.5-7B-Chat`，4-bit；
- 安全领域模型：`Multilingual-Multimodal-NLP/SEVENLLM-Qwen1.5-7B`，4-bit；
- 非 LLM：冻结确定性规则编译器；
- 上界：人工复核 gold。

正式下载前必须确认仓库可访问性、许可、完整 revision 和权重哈希。若任一模型不可复现，不得静默替换；模型变更需要新设计版本。可增加一个现代通用 7B 模型作为敏感性对照，但不能用它替代同底座领域训练主比较。

首轮不进行微调，避免把模型选择、训练数据、超参数和编译接口同时改变。只有零/少样本推理失败且数据规模足以支持时，才单独设计微调研究。

### 7.2 生成配置

主要配置为 temperature 0、`do_sample=false`、固定 max tokens、五次重复推理。所有重复记录 raw bytes、解析结果、延迟和显存。若底层算子仍非确定，报告一致性而不是把重复平均成独立样本。

结构化约束分为 `first-pass-strict` 主分析与独立的 `schema-repair` 附加条件。修复后成功不得回填为 first-pass 成功。

### 7.3 编译对照

每条冻结记录配对运行 Rule compiler、General LLM、Security LLM 和 Human gold。另运行 `LLM-direct` 作为安全负对照，但不把其自由文本强制伪装成 evidence claim。

## 8. 指标与分析

### 8.1 编译层主要指标

- schema-valid rate；
- correct abstention 与 false abstention；
- claim existence precision、recall、F1；
- claim/source type、subject、predicate、object、time、stage/technique 的准确率或 macro-F1；
- context packet 上的 source-pointer exact match、可定位率和哈希一致率；atomic diagnostic 的 pointer 复制率单独报告；
- unsupported-claim/hallucination rate；
- candidate-to-node 链接准确率；
- 五次生成一致性；
- 延迟、峰值显存、输出 tokens；
- 人工修正字段数与修正时间。

模型比较先在记录内配对，再按案例 macro 汇总，不能让 claims 较多的案例自动主导结论。

### 8.2 端到端指标

- 攻击路径/节点/阶段的 precision、recall、F1；
- 与 gold state 的一致率；
- 达到案例可支撑目标的比例；
- action top-1 与完整动作序列一致率；
- cost-to-target 和相对 gold regret；
- zero-yield、premature STOP；
- ceiling violation、over-attribution、abstention；
- 编译错误到状态、动作和结论的传播类型。

成本至少分别报告 legacy、uniform 和已冻结的 rubric/measured profile；若后两者仍未完成，只能标记为开放 Gate，不能用代理值补齐。

### 8.3 Selector 指标

比较 M2、通用 LLM selector、安全领域 LLM selector、`LLM-direct` 和 Oracle 上界：valid-action rate、公开证据引用率、success、cost、regret、premature/invalid STOP、ceiling violation、同状态重复选择一致性和对隐藏字段扰动的请求不变性。

### 8.4 统计口径

- 六个案例是端到端推断的独立单位，episode 嵌套于案例。
- 主要表逐案例报告方向和幅度，并提供 case-macro 汇总。
- 区间估计采用以案例为最高层的分层 bootstrap 或明确的混合效应模型；不得对 270 个 episode 做独立样本 t 检验。
- 小样本下不以单一显著性阈值代替效应方向、案例异质性和失败分析。

## 9. 成功、失败与声明 Gate

LLM 只有同时满足以下条件，才能进入论文标题与核心贡献：

1. 相对规则编译器改善结构化语义质量，或在不降低质量的情况下减少人工修正；
2. unsupported claim、来源错误和 ceiling violation 不增加；
3. 编译差异对端到端攻击路径或调查规划产生可复核影响；
4. 安全领域模型相对同底座通用模型的收益可在案例级解释；
5. 受约束 selector 不牺牲信息边界与安全指标，并在至少部分独立案例改善成功、成本或动作路径。

下列结果必须按负结果报告：LLM 仅改善可读性、LLM 编译弱于规则、领域模型与通用模型持平、抽取 F1 提升但 unsupported/越界/下游成本恶化、selector 只在案例内重复上看似更优，或自由 LLM 与受约束系统在过度归因上没有差异。

当前没有 external actor/campaign truth，因此无论内部结果如何，都不得声称提高 actor attribution accuracy、跨组织泛化或 SOTA。

## 10. 运行契约与审计产物

### 10.1 建议文件组织

```text
09-experiments/
  llm_compiler/
    README.md
    compiler-experiment-v1.0.json
    prompts/
      evidence-compiler-v1.0.txt
      constrained-selector-v1.0.txt
      direct-attribution-v1.0.txt
  data_schema/
    llm_compiler_input.schema.json
    llm_compiler_result.schema.json
    llm_selector_result.schema.json
    llm_run_manifest.schema.json
    public_cti_node_catalog.schema.json
  governance/contracts/
    llm-compiler-contract-v0.1.json
    llm-selector-runtime-contract-v0.1.json
  scripts/
    build_llm_evaluation_dataset.py
    run_llm_compiler.py
    validate_llm_compiler_output.py
    score_llm_compiler.py
    link_candidate_claims.py
    run_llm_end_to_end.py
    llm_action_selector.py
    summarize_llm_experiments.py
  tests/
    test_llm_dataset_separation.py
    test_llm_compiler_contract.py
    test_llm_output_validation.py
    test_candidate_claim_linker.py
    test_llm_selector_contract.py
    test_llm_end_to_end.py
```

现有 v0.1 pilot、prompt 和结果保留，不覆盖。

### 10.2 正式运行 manifest

每次运行至少记录：

- 模型 ID、revision、许可入口和权重 SHA-256；
- 量化方法、bits、compute dtype；
- Python、torch、transformers、量化后端、CUDA、驱动版本；
- GPU 型号和峰值显存；
- prompt、schema、contract、公开输入和 private gold manifest 的哈希；
- temperature、seed、max tokens 和重复编号；
- 每条原始输出、解析结果、验证状态和拒收原因；
- 运行开始/结束时间、退出状态和输出文件哈希；
- 是否为 first-pass、repair、compiler、selector 或 direct 条件。

正式结果目录必须为空；禁止覆盖或混写旧结果。模型输出缓存以完整请求哈希为键，缓存命中必须写入 manifest。

## 11. 失败处理

统一状态：

```text
ok
abstain_null
invalid_json
schema_invalid
source_pointer_invalid
unsupported_claim
node_link_invalid
unknown_action
generation_timeout
out_of_memory
model_error
```

处理原则：

1. 主分析不自动修复非法输出。
2. 未知动作、无引用动作或隐藏字段引用记为 selector 失败，不偷偷回退到 M2。
3. 若研究部署回退，单独设 `LLM+M2 fallback` 条件。
4. OOM、超时、模型缺失或下载失败不能自动换模型。
5. 原始失败输出必须保留，不能只保留成功样本。
6. 部分运行不得写成完整正式结果；resume 必须基于请求哈希并记录。

## 12. 验证要求

### 12.1 数据隔离测试

- gold 不出现在 prompt、模型工作目录或请求对象；
- 修改 gold 不改变请求字节和哈希；
- request、candidate 和 gold ID 分离；
- public CTI node catalog 不含 canonical/recoverable claim IDs。

### 12.2 信息边界测试

- 修改隐藏恢复集合、mask、seed、Oracle 或实际通道状态不改变 selector 请求；
- selector 只能返回公开候选动作；
- 递归禁止字段扫描覆盖嵌套对象和列表；
- 公开成本与 prior profile ID、版本和哈希进入请求 manifest。

### 12.3 功能与回归测试

- dataset builder、schema、validator、scorer、linker、selector 和 end-to-end runner 均有单元测试；
- 使用 stub model 完成无 GPU 的全链路测试；
- 真实模型测试单独标记，不能让缺模型掩盖纯代码失败；
- 新 semantic-link 模式不改变旧 ID-based 模式；
- legacy 主实验 CSV、summary 和 traces 在默认参数下逐字节不变；
- manifest 和所有正式输出有独立验证器。

## 13. 实施顺序

设计通过后按以下顺序实施：

1. 修复 ID 泄漏：建立 public/private 数据包、三类 ID 和公开节点语义目录。
2. 冻结 compiler/selector schema、contract、prompt 和 manifest 格式。
3. 实现 stub 后端、validator、scorer、semantic linker 和测试。
4. 实现本地 Hugging Face 4-bit 后端，先跑 14 条 pilot，验证显存和输出链路。
5. 冻结模型 revision 后运行 C07–C12 完整编译对照。
6. 运行 claim 条件到冻结规划器的端到端实验。
7. 实现并运行公开状态 LLM selector 与 direct 安全对照。
8. 完成案例级分析、失败审计和实验 manifest。
9. 根据真实结果更新论文 Markdown；不得预写正向结果。
10. 用户审阅 Markdown 通过后，才转换 DOCX/PDF 或专利正式格式。

## 14. 非目标

本轮不做：

- 伪造 external actor/campaign ground truth；
- 把 G3 等同于命名攻击者准确率；
- 训练 DQN 或把任务重新包装为强化学习；
- 同时微调 LLM、改变状态定义、改变成本并更换规划器；
- 以 LLM judge 替代来源真值和人工盲审；
- 在实验前把 LLM 正向结果写进论文结论；
- 在 Markdown 审阅前生成完整 DOCX/PPT/PDF。

## 15. 设计审阅清单

- [x] LLM 是核心受测模块，不是未来工作装饰。
- [x] 通用、安全领域、规则和人工 gold 四类对照完整。
- [x] 编译、端到端和 selector 三层评价分离。
- [x] request/candidate/gold ID 分离，避免复制 claim ID 泄漏答案。
- [x] 新 semantic-link 模式不改写旧冻结结果。
- [x] 记录级、重复生成、episode 和案例级统计单位区分清楚。
- [x] actor/campaign 真值缺失被保留为硬边界。
- [x] 失败、弃权和负结果不会被自动修复或隐藏。
- [x] 用户要求的 Markdown-first 工作流已纳入实施 Gate。
