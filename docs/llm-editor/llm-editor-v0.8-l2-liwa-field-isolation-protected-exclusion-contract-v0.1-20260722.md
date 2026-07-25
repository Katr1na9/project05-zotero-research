# Liwa 字段隔离与 protected-exclusion 合同 v0.1

**日期**：2026-07-22  
**状态**：`draft_frozen_not_execution_authority`  
**适用候选**：`liwa_ad_endpoint_telemetry_30run_2026`

## 裁断边界

Liwa 已在 effective catalog 中登记为 `train_candidate`，但 family、lineage、sample 以及所有专项配额仍为 **0**。本合同只冻结未来隔离与排除步骤，**不授权执行**，也不授权额外读取 payload、构造样本、baseline、微调或通过 L2。

角色登记的含义仅是：Liwa 有资格继续接受 fail-closed 检查。它不等于一个有效训练族，更不等于已获训练许可。

## 为什么必须隔离

既有 bounded audit 对 31 个 CSV 成员进行了有限 probe：31/31 呈现 raw-event 且 pointer-capable 的结构，形成 30 个稳定 source-native run group；但同时识别到 1,884 次 forbidden-supervision 字段出现。若让 label、attack/technique、detector rule、score 或文件路径进入模型视图，模型可能学习数据集答案或场景命名，而不是从原始安全证据进行语义编辑。

因此数据面必须分成三个隔离区：

1. **control plane**：保留 archive/member/run/record 的哈希身份与审计计数；
2. **program binder**：仅程序使用 archive digest、member-path hash、member hash 与 record/span hash；
3. **model view**：只接收经显式映射、隔离和 protected-exclusion 后的 raw-event 字段。

原始目录名、文件名、member path、attack/TTP/condition/logging-view 标签、ground truth、detector summary、截图、图、规则、配置与统计报告不得进入 prompt、target、pointer hint、validator、admission 或训练记录。

## 字段隔离

未来实现必须先读 header 编译 field-action map，再物化任何行值。每个字段只能归入：

- `forbidden_supervision`；
- `detector_summary`；
- `binder_only`；
- `candidate_raw_event`；
- `unknown`。

deny 规则优先；`unknown` 直接 fail closed。被拒字段的值不得实例化到任何模型相关对象中，也不得进入日志。路径只允许在 control plane 中用于分组和哈希，不能成为目标、提示或 learned feature。

隔离针对字段身份，而不是对合法事件文本做关键词审查。若一个真实命令行或事件消息自然包含攻击名称，不得因为这个字符串“像标签”就选择性删除。若它与 protected material 命中，则隔离的是整条记录及其所有派生 packet，而不是删词后放行。

## 程序化 pointer

LLM 不生成或绑定可信 pointer。未来 binder 必须使用以下元素确定性重算：

- 冻结 archive digest 与 record revision；
- member path 的 SHA-256，而不是把 raw path 暴露给模型；
- member content hash；
- 稳定 record id，或在其缺失时使用 zero-based row index 与 raw-record hash；
- admitted source span hash。

身份缺失、重复或不可重算时只能输出 `unbound` / `ambiguous`。不能写入 E_case，不能 Promote，也不能取得 certification authority。

## Protected exclusion

保护集合保持为 E3、E5、OpTC、OTRF 与 WitFoo。未来执行只能使用已冻结且不含 raw private gold/test payload 的 signature lock：

- 文件：`09-experiments/llm_evidence_compiler_mainline/wp4/generated/retrieval-v0.1/protected-signature-lock-v0.1.json`
- 文件 SHA-256：`0BFFA67783368DFD91101E737BCC5E2D869A8D9818FD220E6DC4C21C1CEF9E30`
- 语义 lock：`597A167723C2A7306D49E95C2D449548EFAD9799190C893A586255CBFAD45A7F`
- normalized hashes：2,535
- near-duplicate signatures：1,177

检查顺序冻结为：

1. 验证 signature lock；
2. archive/member exact hash；
3. 对隔离后的 model-visible scalar 与 deterministic record serialization 做 `NFKC+casefold+whitespace-collapse` normalized SHA-256；
4. 对长度至少 16 的文本做 normalized character 5-gram Jaccard；阈值固定为 `>=0.85`；
5. 任一命中即 quarantine 整条 record 及其派生 packet；
6. quarantine 后复扫，剩余 exact/normalized/near 必须全部为 0。

观察结果后禁止提高阈值、改变 n-gram、弱化 normalizer、缩小 quarantine 单元或选择性删词。预过滤命中只保留 candidate hash、计数与 reason code，不能持久化命中文本或恢复 protected payload。

## 未来执行前测试

至少需要证明：

- forbidden 字段 canary 在 model view、target、prompt、pointer hint、validator、admission、日志和训练序列中均为 0；
- 路径中的 attack/condition token 无法影响 learned feature 或标签；
- 合法 raw-event 中自然出现的 attack-like 字符串保持原样；
- unknown header 和 deny/allow 冲突在物化行值前 fail closed；
- binder pointer 可由冻结输入完全重算且模型看不到 raw path；
- exact、normalized-exact、阈值处 near-duplicate 均会 quarantine，低于阈值的对照不会误杀；
- lock、normalization、阈值或 n-gram 被改动时硬失败；
- 所有输出仍为 candidate-only，authority leakage 与 modality override 均为 0。

## 成功也不会自动发生什么

即便未来独立授权执行并通过，本合同也只证明隔离与 protected-exclusion 合格。Liwa 的 quota 仍为 0；还需独立的 capacity/lineage/source-role admission review，才能决定是否物化样本。baseline、微调与 L2 Gate 仍须后续单独授权。

机器可检合同见同名 JSON。
