# Liwa 单族 source-role review v0.1

**分支 / 评审基线**：`feat/llm-editor-v0.8` @ `221e94656018e5bcacdbc9d622a5ac30b21459d7`

**候选**：`liwa_ad_endpoint_telemetry_30run_2026`

**评审方式**：只使用已提交的 metadata、冻结合同和脱敏 bounded-audit 结果；未重新打开 archive，未查询外部来源。

## 1. 裁断

> **有条件批准为 provisional train candidate（review-only）**

Liwa 可以作为两个空缺 train-family slot 之一的候选进入下一道 catalog-role application Gate。这个裁断不是正式角色变更，不授予 family、lineage 或 sample 配额，也不授权样本物化、baseline、微调或训练。

当前仍保持：

```yaml
catalog_role_change_applied: false
train_source_admitted: false
family_quota_credit: 0
lineage_quota_credit: 0
sample_quota_credit: 0
train_materialization_authorized: false
l2_gate_passed: false
```

## 2. 为什么可以进入 provisional train 候选

Liwa 已闭合以下最低证据链：

| 项目 | 证据 |
|---|---|
| 身份与许可 | Zenodo revision 7；DOI `10.5281/zenodo.20618083`；CC-BY-4.0；单一 archive 的 size/MD5 已钉死并验证 |
| Archive 安全 | 86 members；unsafe path=0；duplicate path=0；nested notice conflict=false |
| 原始证据形态 | 31/31 bounded CSV probes 具有 raw-event schema |
| Pointer 潜力 | 31/31 probes 具有 timestamp + record-id/host/provider 组合 |
| 非纯汇总 | detector-only member=0 |
| Source-native grouping | 30 个稳定 run group 通过，最低要求为 4；另有 1 个 member 无稳定 run token而不计数 |
| 负面边界 | statistical independence、null/benign lineage、temporal normalization 均未被声明为已验证 |

这使 Liwa 与此前被停损的 specification、fixture 或单 collection 来源不同：它至少提供了可程序回指的、执行产生的 endpoint telemetry 结构和多个 source-native run group。

## 3. 为什么仍是 high-risk conditional approval

### 3.1 Forbidden-supervision 共址

Bounded probe 识别到 1,884 次 forbidden-supervision 字段出现。虽然这些字段值没有进入本次审计结论、监督或模型输入，但未来转换器必须证明它们被字段级物理隔离，不能进入：

- model-visible packet；
- target；
- pointer hint；
- validator 或 admission；
- null、unsupported 或 abstention 构造。

在该隔离 Gate 通过前，Liwa 只能是角色候选，不能生成训练行。

### 3.2 Protected-family exclusion 尚未执行

Liwa 尚未针对 E3、E5、OpTC、OTRF 和 WitFoo 完成 exact、normalized 和预注册 near-duplicate exclusion。该检查必须先于 normalization 与 packet construction；不过线则进入 quarantine，不能通过换阈值补救。

### 3.3 不能提供负例和拒答配额

来源没有已验证 benign/null lineage。禁止把“没有报警”“某规则未触发”或 attack/path label 转换成：

- `candidate_unsupported`；
- benign/null；
- abstention gold；
- hard negative。

因此 Liwa 当前只能贡献正向 candidate-supported 潜力；train 的 40%–60% outcome balance 必须由其他独立来源补足。

### 3.4 30 个 group 不是统计独立性证明

30 个通过项只是 bounded source-native run groups。它们来自单一生产者、三个 attack type 和配对 logging conditions，不得写成 30 次跨环境独立重复，也不得据此主张泛化。

### 3.5 时间与 modality 未闭合

本次 probe 没有形成可解析的 day-level timestamp 范围，因此 Liwa 不得贡献 formal temporal-normalization samples。Trusted modality 在 SI-LLM-005 或等价 ingestion mapping 通过前固定为 `unknown`，不能因为来源看起来像 endpoint logs 就人工写成 `observed`。

## 4. 冻结角色限制

若未来另行批准 catalog role，Liwa 必须遵守：

1. 仅可申请 `train_candidate`，不能同时进入 development/test；
2. 一个 family 最多贡献一份 family credit；当前 credit 仍为 0；
3. native、Windows Security、Sysmon、Wazuh 或 enhanced 等同一 execution 的视图保持同一个 lineage；
4. 同一 run group 的所有记录、窗口与增强视图留在同一 split；
5. 模型可见 family/lineage ID 全部 opaque；
6. 文件名、目录、attack/technique 名和条件标签不得进入监督或 pointer hint；
7. 未来若录取，Liwa rows 不超过 train 的 35%，单一 lineage 不超过 10%；
8. 不得从 Liwa 生成 null、benign、unsupported、abstention、conflict、temporal、candidate-q 或 polarity 配额，除非另有独立合同和证据；
9. Pointer 仍由程序 binder 校验，模型输出只能保持 `unbound|ambiguous`；
10. `certification_authority.allowed=false`，`promotion_status=none` 永远不由模型改变。

## 5. 角色应用前的硬 Gate

以下全部完成后，才可另行申请把 review verdict 写入 effective source catalog：

1. 字段级 forbidden-supervision isolation contract 与测试；
2. protected-family exact/normalized/near-duplicate exclusion；
3. 冻结 normalizer、source-span hash 与 pointer-catalog builder；
4. family × run group × sample kind × trusted modality 的 capacity audit；
5. CC-BY-4.0 attribution 与 notice hash 进入派生 manifest；
6. 单独的用户 catalog-role application 授权。

即使角色应用完成，也必须等完整 L2 schema、authority/modality/pointer、split 与 coverage Gate 全部通过后，才能申请 baseline 或微调。

## 6. 严谨性评分

| 维度 | 分数 / 5 | 摘要 |
|---|---:|---|
| Evidence relevance | 4 | 31/31 raw-event + pointer-capable，直接对应 editor 输入需求 |
| Falsifiability | 5 | 预注册拒绝条件清晰，且 AInception 负结果证明 Gate 未被放宽 |
| Scope calibration | 4 | 只批准 provisional candidacy，不宣称独立性、负例或训练资格 |
| Argument coherence | 4 | metadata → acquisition → schema/pointer → lineage → role 限制链条一致 |
| Exploration integrity | 4 | 高风险、forbidden-field、temporal 与 AInception 失败均被保留 |
| Methodological rigor | 3 | exclusion、字段隔离、capacity、temporal 和统计独立性仍未闭合 |

平均分 4.0，语义严谨性等级为 `Accept`；角色裁断仍是 `conditional_approve_as_provisional_train_candidate_review_only`。

## 7. AInception 状态

AInception 不属于本轮正向角色评审，继续保持 fail-closed：

- 两个 SL700 archive 在 notice cap 16 处阻断；
- SL100/SL300 bounded probe 均未发现 pointer-capable schema；
- 禁止静默重跑、扩大 notice cap、增加 probe 或换 archive；
- 不进入 catalog-role application。

## 8. 下一道授权点

下一步不是生成训练数据，而是二选一的独立授权：

- 仅把 Liwa 的 provisional train-candidate verdict 应用到 effective source catalog，同时保持 quota=0；或
- 先起草并评审字段隔离 + protected exclusion 合同，再决定是否应用角色。

本报告不执行任何角色变更，也不触发 train、baseline、微调、L2 Gate 或 Git push。

机器可检裁断见：`llm-editor-v0.8-l2-liwa-source-role-review-v0.1-20260722.json`。
