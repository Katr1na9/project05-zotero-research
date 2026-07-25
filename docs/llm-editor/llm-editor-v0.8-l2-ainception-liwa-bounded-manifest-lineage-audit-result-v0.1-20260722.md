# AInception + Liwa 有界 manifest / lineage 审计结果 v0.1

**分支 / 执行基线**：`feat/llm-editor-v0.8` @ `4b7ed5086a441d61bfdb9749e04eab3a96276074`

**冻结合同**：`project05-llm-editor-l2-ainception-liwa-bounded-acquisition-audit-contract-v0.1`

**合同 SHA-256**：`EA94D1ADE408FFDE870E940AC42C58BF38F91B400CF14E48522A00F424F7D245`

**审计日期**：2026-07-22

**总体状态**：`blocked_no_authority_transition`

## 1. 裁断

本次技术审计按冻结合同完成到 fail-closed 终点。Liwa 的 bounded source-native lineage evidence Gate 通过，可进入单独授权的 `source-role review`；AInception Gate 不通过，不得进入角色审查、训练或配额计算。

整体 `technical_audit_completed=false`，原因是两个 SL700 archive 的 notice 候选数超过冻结上限 16。审计器在 notice 阶段阻断，没有放宽上限、没有替换 archive，也没有对失败对象继续进行 schema/pointer probe。

本结果没有改变 family role，没有授予 family、lineage 或 sample 配额，没有批准 train source，也没有开启 L2、baseline 或微调。

## 2. 执行顺序与边界

执行顺序严格为：

1. 对每个 archive 重新校验 exact byte size 与 MD5；
2. 只读 ZIP central directory，生成聚合 manifest；
3. 按冻结的 notice 数量与单成员字节上限执行 nested-rights scan；
4. 仅对通过前序 Gate 的允许文本成员执行 bounded schema/pointer probe；
5. 生成不可逆路径哈希、聚合计数和 fail-closed 结论。

没有解压 archive 到磁盘；没有持久化 raw member path、事件值、主机名、用户、IP、命令、文件/注册表值或 payload excerpt。

## 3. Archive 结果

| Archive | 终态 | Manifest / notice | Bounded probe | Lineage 结论 |
|---|---|---|---|---|
| `SL100.zip` | completed | 25 members；unsafe=0；duplicate=0；notice=2、无冲突；eligible raw=9 | 8 members / 6,145,115 bytes；raw-event schema=0；pointer-capable=0 | 仅结构性 source-native candidate；不证明统计独立性 |
| `SL300_variant_7.zip` | completed | 184 members；unsafe=0；duplicate=0；notice=2、无冲突；eligible raw=10 | 8 members / 6,525,795 bytes；raw-event schema=0；pointer-capable=0 | 仅结构性 source-native candidate；不证明统计独立性 |
| `SL700_variant_f_a.zip` | blocked | notice candidate count 超过冻结上限 16 | 未执行 | 不计 lineage candidate |
| `SL700_variant_b_a.zip` | blocked | notice candidate count 超过冻结上限 16 | 未执行 | 不计 lineage candidate |
| Liwa revision-7 archive | completed | 86 members；unsafe=0；duplicate=0；notice=2、无冲突；eligible CSV=31 | 31 members / 3,380,462 bytes；raw-event schema=31；pointer-capable=31；detector-only=0 | 30 个稳定 run group 通过；1 个成员无稳定 run token；只通过 future role-review evidence Gate |

两个被阻断的 SL700 archive 的实际 notice 数量没有持久化；结果只保留“超过 16”这一 fail-closed 事实，避免为事后放宽上限提供内容导向的调参依据。

## 4. AInception 结论

机器结果记录：

- 选择的 archive 数：4；
- bounded source-native lineage candidate：2；
- 需求：4；
- 已完成两份 archive 的 manifest signature 不相同，bounded identity Jaccard 为 0；
- 两份 SL700 在 notice Gate 阻断；
- `future_role_review_evidence_gate_passed=false`；
- `counts_toward_train_or_lineage_quota=false`。

除 notice 阻断外，SL100 与 SL300 的 bounded probe 均未发现 pointer-capable schema 或 raw-event schema。SL100 的探针只识别到 timestamp 类字段且没有 record-id；SL300 在冻结样本中没有识别到可用的 pointer 字段组合。因此，当前证据不足以把 AInception 当作 Candidate Claim IR pointer 训练来源。

本轮不得通过扩大 notice 上限、增加 probe 成员、替换 archive 或改写字段词表来挽救 AInception。任何后续动作都需要新的、独立的 amendment 与用户授权。

## 5. Liwa 结论

Liwa archive 通过 manifest、notice、bounded schema 和 source-native run grouping：

- 31 个允许 CSV 均呈现 raw-event 与 pointer-capable schema；
- 30 个稳定 run group 通过冻结的 bounded lineage 条件，超过最低要求 4；
- 1 个 CSV member 无稳定 run token，不计 lineage；
- 没有 detector-only member；
- 没有 nested notice conflict；
- `future_role_review_evidence_gate_passed=true`。

Probe 识别到 1,884 次 forbidden-supervision 字段出现；这些字段的值未用于 lineage、schema 决策、监督生成或任何模型输入，结果只保留字段类别计数。所有时间字段在本次 bounded probe 中均未形成可解析的 day-level 范围，因此 temporal normalization 能力仍未验证。

Liwa Gate 只表示“有足够证据进入下一道 source-role review”，不表示：

- train source 已批准；
- 30 个 group 具有统计独立性；
- 可贡献 null/benign lineage；
- 可计入 family、lineage 或 sample 配额；
- 已通过 L2 Gate。

## 6. 安全与权限核对

| 项目 | 结果 |
|---|---|
| label / ground-truth values 用于审计 | false |
| raw member paths 持久化 | false |
| raw payload values 持久化 | false |
| supervision / normalization 生成 | false |
| family role 改变 | false |
| train / lineage quota 授予 | false |
| train admission | false |
| baseline / fine-tuning | false |
| CERT / IoT-23 下载 | false |
| Kernel / M3* 工作 | false |
| L2 Gate 通过 | false |
| Git push | false |

## 7. 下一道 Gate

允许的下一步仅是：对 Liwa 发起单独授权的 `source-role review`，审查它是否应作为 provisional train/dev 候选及其角色限制。

AInception 保持 fail-closed，不自动进入 source-role review。若要继续，必须先另开 amendment，明确处置 notice-cap 阻断和 pointer-capability 缺失；不得静默重跑本审计。

## 8. 工件

- 机器结果：`llm-editor-v0.8-l2-ainception-liwa-bounded-manifest-lineage-audit-result-v0.1-20260722.json`
- 人类报告：`llm-editor-v0.8-l2-ainception-liwa-bounded-manifest-lineage-audit-result-v0.1-20260722.md`
- 冻结合同：`llm-editor-v0.8-l2-ainception-liwa-bounded-acquisition-audit-contract-v0.1-20260722.json`

以上工件只提供 source-role review 的证据，不产生任何自动权限迁移。
