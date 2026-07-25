# LLM Evidence-safe Semantic Editor v0.8：L2 配额修订 v0.1

**日期**：2026-07-22
**基线合同**：`project05-llm-editor-l2-provisional-v0.1`
**库存依据**：`llm-editor-v0.8-l2-source-inventory-metadata-only-v0.1-20260722.json`
**状态**：`registered_not_satisfied`

## 1. 修订目的

本修订把 L2 草案中的 `quota_status=unresolved` 改为可检查的 provisional 最低配额。配额用于阻止单一来源、单一运行或大量重复视图伪装成有效样本量；它不是统计功效证明，也不能支持“普遍有效”声明。

本修订只使用已提交的计数、revision、license、hash 和来源审计。没有读取 payload、private gold 或模型输出。

## 2. 当前容量裁断

历史审计记录：

- 4 个 train candidate family，历史 pair 1,200；
- 2 个 development candidate family，历史 pair 300；
- 0 个独立 test family；
- Splunk 过滤后仅 2 条记录，不计 family quota；
- 全部 family 的 v0.8 `lineage_group_id` 容量和 sample-kind 容量仍未知。

因此当前只能注册配额，不能判通过。旧 pair 行数不能替代 lineage group 或 v0.8 样本覆盖。

## 3. Split 级配额

| 项 | train | development | test |
|---|---:|---:|---:|
| 独立 `corpus_family_id` | ≥4 | ≥2 | ≥2 |
| 每 family 独立 `lineage_group_id` | ≥4 | ≥4 | ≥4 |
| split 总独立 lineage groups | ≥16 | ≥8 | ≥8 |
| row 总量 | 800–1,600 | ≥192 | ≥192 |
| 单一 family row 占比上限 | 35% | 60% | 60% |
| 单一 lineage group row 占比上限 | 10% | 10% | 10% |

这些是 pilot 的操作下限。family 或 lineage 数低于下限时，不得通过增加同一组的 packet window、模板、prompt view 或重复行来补数。

当前状态：

| Split | Family 配额 | Lineage 配额 | Row 配额 | 裁断 |
|---|---|---|---|---|
| train | metadata 上恰有 4 个候选 | 未知 | 历史 1,200，不可继承 | `pending` |
| development | metadata 上恰有 2 个候选 | 未知 | 历史 300，不可继承 | `pending` |
| test | 0/2 | 0/8 | 0/192 | `failed_hard_stop` |

## 4. 结果平衡配额

对于 `train`，可产生候选与应 abstain/reject 的主结果各占 40%–60%。此比例只用于机制学习，不代表真实世界 prevalence。

对于 development/test，冻结 challenge panel 同样维持 40%–60% 主结果覆盖，并必须另行报告原始来源可达分布。禁止全 abstain 刷 safety，也禁止全 supported 刷 recall。

`primary_outcome` 只能取：

- `candidate_emitted`；
- `abstained_or_rejected`。

冲突组内多条 claim 仍只计一个 sample group，不能重复计入 class balance。

## 5. Sample-kind 配额

下表适用于 development 和 test；同一行可同时覆盖多个正交安全属性，但必须在 manifest 中逐项声明，不能靠事后解释。

| Sample kind / slice | 每个 evaluative split 最低量 | 独立性要求 |
|---|---:|---|
| `candidate_supported` | 48 rows | ≥8 lineage groups，≥2 corpus families |
| `candidate_unsupported` | 48 rows | ≥8 lineage groups，≥2 corpus families |
| `pointer_absent` | 24 rows | ≥4 lineage groups |
| `pointer_ambiguous` | 24 rows | ≥4 lineage groups |
| `authority_injection` | 24 rows | ≥4 lineage groups，≥2 corpus families |
| `conflict_group` | 12 groups | 每组 ≥2 个独立来源 lineage；总计 ≥2 family-pair 类型 |
| `duplicate_retention` | 12 groups | 每组保留全部候选，不计冲突 |

Train 中每个已启用 sample kind 至少 40 rows 且覆盖 ≥4 lineage groups。Train 总量和比例仍受第 3、4 节约束。

## 6. Modality 配额

每个 evaluative split 对下列 trusted modality 各要求至少 12 rows、3 个 lineage groups：

- `observed`；
- `derived`；
- `reported`；
- `hypothesized`；
- `unknown`。

modality 必须来自经批准的 ingestion mapping。SI-LLM-005 未关闭时，无法可靠映射的来源固定为 `unknown`，不得为了满足 observed/reported 配额而人工洗白。

Train 对每个已启用 modality 至少 40 rows、4 个 lineage groups；不能达到的 modality 明确标 `not_trainable`，不能跨 split 借用。

## 7. 暂停计数项

以下配额注册为 0 且状态为 `blocked_not_applicable`，不能用占位样本填充：

| 项 | 阻塞原因 |
|---|---|
| polarity-supervised rows | SI-LLM-007 未关闭 |
| polarity-based conflict groups | SI-LLM-007 未关闭 |
| candidate-q rows | SI-LLM-002 未关闭 |
| formal temporal-normalization rows | gold/时间合同未冻结 |
| Kernel-compatible Claim IR rows | SI-LLM-001/003 等未关闭 |

## 8. 技术重复上限

为防止伪重复：

- 同一 raw record 最多生成 4 个模型视图；
- 同一 `lineage_group_id` 的全部视图保持在同一 split；
- 指标必须先在 lineage 内聚合，再做 family macro；
- row-level 结果只能作为工程诊断；
- 增强视图不增加 lineage group 计数；
- 一个 conflict group 无论包含多少 claim，只贡献一个 group-level replicate。

## 9. 冻结与 amendment 规则

真正物化前必须生成 `quota-capacity-audit.json`，按 family × lineage × sample kind × modality 报告：available、selected、quarantined 和 reason。任何最低配额未满足时：

1. 保持 L2 Gate 失败；
2. 可新增经批准的独立来源族；
3. 可缩小指标或论文主张；
4. 不得降低配额来适配已看到的模型结果；
5. 若科学上确需修改，必须在模型调用前发布新 amendment 并说明理由。

## 10. 当前 Gate

```yaml
quota_contract_registered: true
metadata_inventory_complete_for_known_families: true
lineage_capacity_known: false
sample_kind_capacity_known: false
train_quota_passed: false
development_quota_passed: false
test_quota_passed: false
baseline_authorized: false
fine_tuning_authorized: false
```

下一步仍只能申请 metadata-only lineage/sample-kind capacity inventory 和新 test-family 候选调研。未获得独立授权前，不得读取 payload 来计算这些容量。
