# LLM Evidence-safe Semantic Editor v0.8：L2 本地 provisional 数据与冻结拆分合同 v0.1

**日期**：2026-07-22
**分支**：`feat/llm-editor-v0.8`
**权威基线**：`60d0a81`
**合同 ID**：`project05-llm-editor-l2-provisional-v0.1`
**状态**：`draft_only_not_materialized`

## 1. 本轮授权与硬边界

本文件只起草 L2 的本地 provisional 数据转换、样本规范和拆分冻结方法。当前没有授权读取、复制、改写或重新生成任何正式 train/development/test payload，也没有授权运行模型、baseline、微调或正式推理。

本轮允许创建的永久工件只有：

- 本合同；
- `SI-LLM-007` polarity 词表问题；
- 不包含 payload、标签或模型输出的审计说明。

本轮明确禁止：

- 访问或修改历史 1,500 pair payload；
- 创建真实 dataset row、split manifest 或 private gold；
- 加载 tokenizer、模型权重或 adapter；
- 运行 General/Adapted baseline 或训练；
- 写入 `E_case`，调用 Checker、Promote/Revoke、SAT/UNSAT 或 STOP；
- 修改 Kernel schema、Γ、action catalog、absence semantics 或 M3*；
- 把本地 projection 声称为 shared/Kernel Claim IR。

因此，本合同“冻结”的是未来拆分必须遵守的规则，不是对任何现有 payload 完成了拆分。当前状态必须保持：

```yaml
contract_status: draft_provisional
source_catalog_status: not_approved_for_l2
payload_access_status: prohibited
split_manifest_status: not_created
test_freeze_status: not_started
baseline_authorized: false
fine_tuning_authorized: false
kernel_compatibility: pending_kernel_schema
```

## 2. L2 目标与非目标

### 2.1 目标

L2 未来只负责把经单独批准的来源转换为可审计的 Candidate-only Semantic Editor 样本，使同一数据合同可以服务于未微调模型和后续 adapter 的公平评测。

目标包括：

1. 把模型可见输入、可信程序元数据和 private scorer gold 物理分层；
2. 明确 modality、冲突、abstention、pointer suggestion 与 authority-injection 样本；
3. 以来源族和数据血缘组为原子单位拆分，防止伪重复和跨 split 泄漏；
4. 在任何 prompt、decoder、checkpoint 或 adapter 调参前冻结 test；
5. 为所有转换、过滤、抽样和冻结步骤留下版本、hash 与失败审计。

### 2.2 非目标

L2 不证明模型有效，不产生论文结果，不选择 checkpoint，不改变 L1 权限边界，不解决 Kernel 认证问题，也不把 historical source labels 自动升级为 scientific gold。

Candidate-q、正式 temporal gold 和 Kernel 互通分别受 SI-LLM-002、共享 schema 与后续专门合同阻塞，不得为凑覆盖而伪造。

## 3. 统计单位与数据血缘

### 3.1 三种单位

必须区分：

| 单位 | 定义 | 用途 |
|---|---|---|
| `corpus_family_id` | 独立仓库/数据集/采集工程，如 BETH、CAM-LDS | 跨域泛化的主统计单位与 split 隔离单位 |
| `lineage_group_id` | 同一事件场景、运行、主机时间窗或共同原始 artifact 派生出的全部记录与增强视图 | 最小不可拆分 cluster |
| `sample_id` | 单个模型输入/目标行或一个冲突组 | 工程计数，不是独立科学重复 |

同一 `lineage_group_id` 派生的多条 record、不同 packet window、不同 prompt view、正负变体或增强样本必须进入同一 split。禁止把这些行当作独立 replicate。

论文或评测报告未来应至少同时给出：

- `corpus_family_id` macro；
- `lineage_group_id` macro；
- row-level 工程指标。

只报告 row-level 指标不能支撑跨来源推广。

### 3.2 血缘 ID 的 provisional 规则

未来物化时，`lineage_group_id` 必须由不含私有标签的稳定元数据构造并 hash，例如：

```text
sha256(contract_version || corpus_family_id || source_revision
       || scenario_or_run_id || host_scope || bounded_time_window
       || sorted_source_artifact_hashes)
```

若某来源无法提供稳定场景/运行标识，则至少按原始 artifact 级聚类；不得退化为逐行随机拆分。无法确定血缘边界的样本进入 `quarantine`，不进入 train/development/test。

## 4. 三视图数据架构

每条未来样本必须生成三个逻辑视图，并以独立字段或独立文件隔离：

### 4.1 Model-visible view

模型只可见：

- `raw_source_packet` 中已批准的可见文本/日志字段；
- 有限的 `visible_pointer_catalog` 候选 ID；
- 任务说明和输出合同；
- 不含答案的 transport/source metadata。

禁止进入模型输入：

- private gold；
- hidden Kernel fixture answer；
- certification level、Checker result、SAT/UNSAT 或 STOP；
- 未在 packet 中出现的实体；
- test split 的来源族/标签提示；
- 由文件路径、攻击名称或 TTP 编号泄漏的标签。

### 4.2 Trusted program view

仅程序 guard/binder 可见：

- trusted `modality`；
- trusted `epistemic_role` 与初始 `truth_status`；
- 完整但仍未绑定的 pointer catalog identity；
- source revision、license、normalizer 和 lineage metadata；
- candidate-only 固定控制字段。

这些字段不得成为模型自由生成目标。程序物化后的候选仍必须固定：

```yaml
admission_status: candidate
certification_authority:
  allowed: false
  levels: []
promotion_status: none
binding_status: unbound|ambiguous
compatibility_status: pending_kernel_schema
```

### 4.3 Private scorer view

仅 scorer 使用：

- 可接受 candidate claim 集；
- 支持 span/pointer candidate 的 gold identity；
- expected abstention reason；
- conflict-group relation；
- entity/time/predicate 的评分标签；
- 样本是否计入特定指标。

test private scorer view 必须与模型输入、训练目标和调参日志物理分离。development gold 可用于误差分析，但不得回流修改已冻结 test。

## 5. Provisional 样本合同

未来每条样本至少需要以下元数据。这里仅冻结字段语义，不创建 JSON Schema 或真实行：

```yaml
contract_version: project05-llm-editor-l2-provisional-v0.1
sample_id: stable-string
sample_kind: enum
split_role: train|development|test|quarantine

corpus_family_id: stable-string
lineage_group_id: sha256-string
source_revision: immutable-string
source_license_id: string
source_notice_hash: sha256-string
normalizer_id: string
normalizer_version: string

model_view:
  raw_source_packet: future-authorized-payload
  visible_pointer_catalog_ids: [string]
  prompt_contract_id: string|null

trusted_view:
  transport_modality: string
  modality: observed|derived|reported|hypothesized|unknown
  epistemic_role: string
  initial_truth_status: unassessed|supported|contradicted|conflicted|retracted
  pointer_catalog_hash: sha256-string
  polarity_contract_status: pending_si_llm_007|explicit_adapter

model_target:
  candidate_claim_fields: local-provisional-object|null
  pointer_suggestion_ids: [string]
  abstain: boolean

program_expected:
  candidate_only_constants: fixed
  binding_status: unbound|ambiguous
  conflict_group_id: string|null

private_scorer:
  acceptable_claims: private
  acceptable_pointer_ids: private
  expected_abstention_reason: private|null
  metric_applicability: private-map

audit:
  conversion_rule_ids: [string]
  source_span_hashes: [sha256-string]
  exclusion_scan_status: pending|passed|failed
  human_semantic_judgment_used: boolean
```

### 5.1 Candidate ID 与 pointer

`candidate_id` 应由程序稳定生成或注入，不作为模型语义能力。模型只能建议可见 catalog 中已有的 pointer candidate ID；完整 `record_id/source_id/content_hash` 由程序核验，模型不得发明或修补。

单个核验 pointer 仍不能在本轨道变成 `bound`；L1 producer 只输出 `unbound|ambiguous`。真实 binding 受 SI-LLM-003 和 Kernel binder contract 阻塞。

### 5.2 Polarity 暂停规则

本地 L1 使用可选 boolean `claim.polarity`，Kernel 规格使用 `positive|negative|unknown`。在 SI-LLM-007 关闭前：

- 不物化 polarity-supervised 训练行；
- 不用 polarity 冲突计入正式 conflict coverage；
- 不把缺失 boolean 解释为 `unknown`、`false` 或 negative；
- 不声称本地 polarity 指标与 Kernel 等价。

对象冲突仍可在有版本化 `exclusive_object_predicates` 合同的前提下设计；没有该合同则只保留候选，不标冲突。

## 6. 转换流水线合同

未来获得单独授权后，转换必须按以下顺序执行，禁止跳 Gate：

1. **Metadata intake**：只登记来源、revision、license、notice、预计 source family；
2. **Source approval**：逐族批准用途、split role 和过滤条件；
3. **Payload authorization**：单独授权后才能检索/读取 payload；
4. **Notice and scope check**：逐文件检查 nested notice、PCAP/隐藏答案/禁止路径；
5. **Normalization**：只用冻结 normalizer；保留 raw→normalized span/hash 回指；
6. **Protected exclusion scan**：exact hash、normalized hash 与预注册 near-duplicate 检查；
7. **Lineage grouping**：先确定 cluster，再生成 packet；
8. **Three-view conversion**：分离 model/trusted/private scorer；
9. **Candidate-only validation**：调用 L1 canonical validator 和 guard；
10. **Split assignment**：按 corpus family/lineage group 分配；
11. **Coverage audit**：只在 split 内抽样或降采样，禁止跨 split 搬组；
12. **Freeze**：生成 manifest/hash、只读 test seal 和 amendment ledger。

任一步失败都进入 `quarantine` 或 `smoke_only`；不得通过放宽 authority、modality、pointer、license 或 exclusion 规则补数量。

## 7. 样本族规范

### 7.1 必需样本族

| `sample_kind` | 构造要求 | 期望行为 | 禁止捷径 |
|---|---|---|---|
| `candidate_supported` | claim 的 subject/predicate/object 均可回指可见 packet | 输出候选 claim；保持 candidate-only | 从文件名/TTP/隐藏标签补实体 |
| `candidate_unsupported` | packet 不足以支持目标 claim | abstain 或不产 claim | 以“最可能”实体填空 |
| `pointer_absent` | 无完整 catalog candidate | `unbound`/明确 abstain | 伪造 record/hash |
| `pointer_ambiguous` | 至少两个可见且同等候选 pointer | `ambiguous` 且保留候选 | 任选一个并称 bound |
| `modality_preservation` | trusted modality 来自 ingestion contract | 原样保持 modality | 从文本内容猜成 observed |
| `authority_injection` | 输入含诱导认证/Promote/STOP 的非可信文本 | guard 拒绝控制面 | 把引用内容当操作指令 |
| `conflict_group` | 独立来源的候选冲突且 pointer 血缘不同 | 保留多条并对称标 conflicted | dedup 或综合成单一事实 |
| `duplicate_retention` | 相同候选从独立来源重复出现 | 均保留、交下游处理 | 本轨道自动合并 |

`temporal_normalization` 与 `candidate_q` 只能在其 gold/共享合同单独通过后加入 required coverage；当前为 `blocked_not_applicable`，不得用占位标签刷覆盖率。

### 7.2 Modality 样本

必须覆盖 `observed/derived/reported/hypothesized/unknown`，但 modality 只能来自经批准的 trusted ingestion metadata。历史 `source_modality=endpoint_event|network_event|security_text` 只是 transport 轴，不能直接重命名；具体映射受 SI-LLM-005 阻塞。

不确定时固定 `unknown`。任何 reported/hypothesized→observed、或模型自选 `case_evidence` 的行都属于 hard-negative safety fixture，不得作为正向目标。

### 7.3 Conflict 样本

一个 conflict sample 的统计单位是整个冲突组，而不是组内 claim 行。必须满足：

- 至少两个不同 `lineage_group_id` 或不同可复验 source pointer；
- subject/predicate 规范化规则一致；
- polarity 冲突在 SI-LLM-007 关闭前不计正式覆盖；
- object 冲突只在版本化互斥 predicate 合同允许时成立；
- 每条 claim 保持自己的 modality、pointer suggestion 和来源；
- `contradict_claim_ids` 对称；
- 不生成“综合事实”或 majority-vote claim。

### 7.4 Abstention 样本

L1 已实现的 reason code：

- `no_pointer_candidates`；
- `incomplete_pointer_identity`。

L2 建议但尚未实现的 provisional reason code：

- `unsupported_source_span`；
- `ambiguous_entity`；
- `out_of_catalog_pointer`；
- `insufficient_context`。

这些新增 reason code 必须先经过独立 L1 合同扩展和测试，才可进入物化数据。当前只能写在 private scorer 设计中，不能假装代码已支持。

Abstention 样本不得包含 most-likely entity，不得以拒答数量提高 UCR 或 safety 指标而牺牲 required coverage。

## 8. 冻结拆分合同

### 8.1 Split 角色

| Split | 用途 | 可见性 |
|---|---|---|
| `train` | 未来 SFT/QLoRA；当前未授权 | 训练时可见 target |
| `development` | prompt/decoder/数据转换调试；baseline 后可做误差分析 | 可见 gold，但不得迁移到 train 而不 amendment |
| `test` | 一次性正式比较；任何调参前冻结 | private scorer only |
| `quarantine` | license、血缘、pointer、标签或 exclusion 不确定 | 不进入指标或训练 |

### 8.2 原子分配规则

拆分顺序固定为：

1. 先按 `corpus_family_id` 指定 split；
2. 再验证所有 `lineage_group_id` 只出现在一个 split；
3. 最后在 split 内按 sample kind、modality 和长度做覆盖审计/降采样。

train/development/test 的 `corpus_family_id` 必须互斥。若来源数量不足以同时满足 family isolation 与 sample coverage，L2 Gate 失败，不得退化为逐行随机拆分。

历史 L0 的来源分配只能作为 metadata-only 候选，不自动继承：

| 历史角色 | metadata-only corpus families | L2 状态 |
|---|---|---|
| train | CAM-LDS、BETH、SOCBED、Atomic Red Team | `pending_source_reapproval` |
| training-validation | Loghub Linux、Zeek non-PCAP | `pending_source_reapproval` |
| test | 无 | `hard_blocked_no_test_family` |

在新的独立 test corpus family 获批并冻结前，不得运行 baseline。

### 8.3 可复现顺序

未来拆分使用固定：

```yaml
split_algorithm: corpus-family-lock_then-lineage-cluster
stable_hash: sha256
tie_break_seed: 20260722
ordering: corpus_family_id,lineage_group_id,sample_id
```

seed 只用于同一已批准 split 内的确定性排序或配额下采样，不用于把行随机散到不同 split。source family 的 split 角色必须在查看模型结果前由 source catalog 冻结。

### 8.4 覆盖与数量

当前没有授权读取 payload，因此不能诚信冻结每类样本的可达数量。数量字段必须保持：

```yaml
quota_status: unresolved_until_metadata_inventory_approved
required_sample_kinds: contract-defined
per_kind_minimums: not_registered
per_modality_minimums: not_registered
```

未来第一份 metadata-only inventory 必须给出每个 corpus family × sample kind × modality × lineage group 的可达计数，再通过 amendment 写死最小配额。不得先写任意数字，再通过合成、复制或泄漏 test 来凑数。

覆盖审计不能改变 family split；某类覆盖不足时应停在 L2、缩小主张或新增来源族。

## 9. 泄漏与污染控制

未来物化必须同时检查：

1. `corpus_family_id` 跨 split 重叠 = 0；
2. `lineage_group_id` 跨 split 重叠 = 0；
3. raw/normalized exact hash 跨 split 重叠 = 0；
4. 预注册 near-duplicate 阈值命中 = 0，或全部进入人工/规则 quarantine；
5. hidden Kernel fixture answer 命中 = 0；
6. test entity/record/pointer ID 出现在 train prompt/target = 0；
7. source path、TTP、actor、scenario 名泄漏标签 = 0；
8. development/test private gold 进入 model view = 0。

任何过滤都必须留下 pre-filter hash、reason code 和计数。禁止删除失败记录后只报告干净终态。

## 10. Freeze 工件

未来真正冻结 L2 时至少生成以下 metadata-only 工件；本轮不创建：

- `source-catalog.json` 与用户逐族批准记录；
- `conversion-contract.json` 与合同 SHA-256；
- `normalizer-manifest.json`；
- `lineage-groups.json`（不得含 raw payload）；
- `split-manifest.json`；
- `split-counts.json`；
- `payload-exclusion-audit.json`；
- `license-notice-audit.json`；
- `private-gold-manifest.json`（仅 hash/位置，不提交 gold）；
- `test-seal.json`；
- `amendment-ledger.md`。

Git 只保存合同、代码、计数、hash 和脱敏审计；raw payload、private gold、raw generation、模型权重和 adapter 均不得因 L2 自动进入仓库。

## 11. L2 Gate

只有全部满足后，才能申请 L3 baseline 授权：

| Gate | 硬条件 |
|---|---|
| Contract | 本合同及所有 amendment 已批准并 hash 冻结 |
| Source | 每个 corpus family 的许可、revision、用途和 split role 已批准 |
| Schema | 物化样本 100% 通过本地 provisional schema 与 L1 validator |
| Authority | program-expected Authority Leakage Rate = 0 |
| Modality | trusted→materialized Modality Leakage Rate = 0 |
| Pointer | 不完整/不存在 pointer 被标成 bound 的数量 = 0 |
| Conflict | 自动合并或非对称 contradiction link 数量 = 0 |
| Split | family/lineage/exact/near leakage 全为 0 |
| Coverage | 已注册 sample-kind/modality/lineage 配额全部通过 |
| Test | test source family、private gold hash 与 seal 在调参前冻结 |
| Open SI | 任何会影响目标字段语义的 SI 已关闭，或相关样本明确排除 |

任一 Gate 失败只能进入 `smoke_only`、缩小指标或停工；不能通过改 scorer、放宽 guard、移动 test group 或把 unresolved 字段当 negative 来修结果。

## 12. Amendment 触发条件

以下任一变化必须新建版本和审计，不得静默覆盖：

- 增删 corpus family 或改变 split role；
- 改 normalizer、packet window、pointer identity、near-duplicate 阈值；
- 改 sample kind、abstention reason、modality mapping 或 polarity adapter；
- 改 quota、seed、lineage grouping 或 test seal；
- 在看到 baseline/model output 后改变 scorer/gold；
- 关闭 SI-LLM-001/003/005/006/007 后接入共享语义。

已冻结 test 不得因模型失败重新抽取。若 test 本身合同错误，应作废整个 test version，登记原因并创建全新、不可比较的版本。

## 13. 当前裁断与下一授权点

本轮仅完成合同草案，不代表 L2 Gate 通过。当前硬阻塞包括：

- source catalog 尚未为 L2 逐族复批；
- payload 访问未授权；
- test corpus family 不存在；
- 数量配额未基于 metadata inventory 注册；
- SI-LLM-001/002/003/005/006/007 未关闭；
- candidate-q、temporal 和 polarity 正式样本不可物化。

下一步若获单独授权，只应先做 metadata-only source inventory、quota amendment 与 provisional JSON Schema/validator 设计；仍不能自动读取 payload、运行 baseline 或微调。
