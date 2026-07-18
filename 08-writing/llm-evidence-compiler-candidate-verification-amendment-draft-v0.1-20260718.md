# Project05 LLM evidence compiler：候选边验证训练修订草案 v0.1

状态：`draft_non_authorizing_pending_review`  
日期：2026-07-18  
依据：`train-null-alternative-source-literature-audit-v0.1-20260718/`  
影响范围：仅拟修订 Qwen2.5 General vs QLoRA 的训练单位和 data-gate；不修改 M3、`run_mvp.py`、冻结案例或旧结果

## 1. 修订目的

现有 QLoRA 计划把训练 packet 分为 observation/null，并要求 40%–60% 平衡。证据审查表明：对“从日志中抽取所有可支撑 observation”的无条件任务，良性日志仍包含大量合法关系；继续补 `packet=null` 会制造错误标签或来源模态 shortcut。

本修订拟将 adapter 的监督单位改为“候选边是否被一个绑定来源指针支持”。LLM 的角色仍是语义建图：把异构字段和文本归一为主线图 schema，并拒绝来源不支持的候选边。

## 2. 不变项

- 底座仍为固定 revision 的 `Qwen/Qwen2.5-7B-Instruct`。
- 比较仍为同底座 adapter off/on；基础权重冻结，QLoRA 参数占比 `<1%`，只保存 adapter，不 merge full model。
- 正式测试仍只挂载 public input；private gold 不进入 prompt、validator 或第二阶段输入。
- Rule-Strong、Qwen-General、Qwen-Adapted、Reuse-Hybrid 与 General-Direct 条件保持可区分。
- Paper A/M3 冻结结果不被重写；本模块只是主线证据建图层。
- G2 与训练真值分离；训练标签不能靠 G2 或单人主观意见创建。

## 3. 新统计单位

### 3.1 输入

```json
{
  "source_record": "visible normalized record",
  "source_pointer": {
    "artifact_id": "...",
    "record_id": "...",
    "record_sha256": "..."
  },
  "candidate": {
    "subject_type": "...",
    "subject_value": "...",
    "predicate": "...",
    "object_type": "...",
    "object_value": "...",
    "event_time": "..."
  }
}
```

### 3.2 输出

```json
{
  "support_decision": "supported | unsupported_by_bound_pointer | abstain",
  "normalized_edge": "object or null",
  "pointer": "exactly echoed pointer or null",
  "reason_code": "frozen enum"
}
```

只有 `supported` 可带 `normalized_edge`；`unsupported_by_bound_pointer` 和 `abstain` 必须为 `null`。模型不得修复或猜测缺失 subject/object/time。

## 4. G0 正例合同

正例只能来自 source-specific field map 可逐字段验证的记录：

1. subject、predicate、object、time 的每个 target 字段都绑定显式 source field 或冻结的纯机械规范化；
2. 不允许从文件名、目录名、ATT&CK/TTP 标签、actor 名、scenario 名或模型输出生成 target；
3. `record_sha256`、artifact/pointer 和 source license 必须完整；
4. 任一字段需要作者语义补全时，该记录不得进入 G0 正例池；
5. 正例 admission 不读取 validation/test gold。

因此不再要求用户逐条“创造”训练标签；真值来自公开记录字段与可测试 mapping。可保留确定性抽样的人工质量诊断，但它不改变标签、不过 Gate，也不承担学术外部效度。

## 5. 负例生成合同

负例标签只表示：

> `candidate` 不被 `source_pointer` 所绑定的这一条记录支持。

它不表示事件在真实世界不存在，不表示主机良性，也不表示整个 packet 没有其他 observation。

### N1：same-type object swap

- 从同 packet 另一条记录取同类型 object；
- 保持 subject 和 predicate；
- 要求替换值不等于、且不出现在 bound record 的 object field/span；
- 记录原正例与替换来源 pointer。

### N2：pointer swap

- 保持一个 G0 正例 candidate；
- pointer 改指同 packet 的另一条记录；
- 新 bound record 的冻结字段不得逐字段支持该 candidate；
- 不允许跨 source family，避免格式 shortcut。

### N3：predicate-field incompatibility

- candidate subject/object 保持；
- predicate 改为 source schema 明确不由该字段组合表达的 predicate；
- incompatibility 必须来自冻结 schema table，不得由模型判断。

### N4：explicit time mismatch

- 仅用于带显式 event time 的记录；
- candidate time 改为同 packet 另一条记录的不同时间；
- 负标签只针对 `pointer × time` 不匹配。

## 6. Proof object

每条负例必须保存独立 proof：

```json
{
  "proof_version": "pointer-bounded-negative-v1",
  "generator": "N1 | N2 | N3 | N4",
  "positive_record_sha256": "...",
  "bound_record_sha256": "...",
  "candidate_before": "...",
  "candidate_after": "...",
  "field_map_id": "...",
  "mechanical_checks": {
    "candidate_not_supported_by_bound_record": true,
    "world_false_claim_made": false,
    "path_or_scenario_supervision_used": false
  }
}
```

proof 任何字段缺失或 check 非 `true/false` 预期值，样本 fail closed。

## 7. 拟议 data-gate

这是草案阈值，批准前没有执行效力：

| 项目 | 拟议要求 |
|---|---:|
| train candidate pairs | ≥1200 |
| training-validation candidate pairs | ≥300 |
| train source families | ≥4 |
| validation source families | ≥2，且与 train family-disjoint |
| supported 比例 | 40%–60% |
| unsupported/abstain 比例 | 40%–60% |
| negative generator families | ≥3 |
| 任一 negative generator 占比 | ≤50% |
| same-packet negative | ≥75% |
| positive/negative source-modality match | 100% |
| proof validator pass | 100% |
| exact/near test leakage | 0 |
| token p95/final max | ≤1024；禁止截断 |

旧 `packet_role=null` 数量不迁移、不重命名；新 Gate 使用 `candidate_support_role`，版本号和 report schema 必须变化。

## 8. 数量可行性与失败条件

历史排除审计后有 2394 条 train observation proposals，但它们尚不等于 G0 positives。只有 source-specific field maps 全部通过后才能重算。

若至少 600 条 proposal 成为 G0 positive，每条配 1 条机械证明负例即可达到 1200 pair 的平衡下界。若严格 mapping 后不足 600，必须：

- 降级为 smoke-only；或
- 另行批准同模态、同真值合同的来源。

禁止放宽字段 mapping、使用模型自证、使用 benign/path 标签或 validation 数据追数量。

## 9. 与正式推理的衔接

```text
raw evidence
→ deterministic high-recall entity/pointer proposal
→ Qwen semantic normalization + candidate support decision
→ deterministic schema/hash/pointer admission
→ executable provenance graph
→ M3 traceability decision and minimum-cost acquisition planning
```

若 deterministic proposal recall 在 development 上不足，adapter 不得靠自由生成绕过 pointer contract；应保留 Reuse-Hybrid 或 General compiler 作为失败路径。

## 10. 可证伪主张

本修订若获批准，QLoRA 增益只允许表述为：

- 在同底座、同 prompt、同 decoding 下，task/schema adapter 是否提高 candidate-edge support decision 与 pointer-grounded normalization；
- 是否在不降低可接受 edge 覆盖率的条件下降低 pointer-unsupported admission。

不得表述为：

- 已证明真实世界事件不存在；
- 已完成人类验证的“幻觉减少”；
- APT-domain model；
- 端到端 APT attribution SOTA。

## 11. 开工前必须新增的依赖无关工件

1. `candidate_edge_training.schema.json`；
2. `pointer-bounded-negative-proof.schema.json`；
3. 四类 source-specific field map 与 hash lock；
4. negative generator 的正/反例单元测试；
5. source-modality balance 与 family split validator；
6. 新旧 Gate 不可混读测试；
7. amendment authority lock。

完成以上工件仍不自动授权 tokenizer、权重、环境或训练；需要单独展示 non-token data-gate 可行性并再次授权。

## 12. 当前裁决

`recommended_for_user_review_not_authorized`

推荐原因：它与文献中的候选 claim/triple verification 形态一致，同时把 Project05 负标签限制在一个可机械验证的来源指针范围，消除了“benign=无 observation”和“未入库=事实为假”两类核心错误。
