# Route B 构念 Gate 执行协议 v0.1

**日期**：2026-07-14  
**状态**：预注册草案；在重新发放标注包前冻结  
**适用对象**：Claim 支持度、预执行动作目标、可支撑结论粒度  
**不适用对象**：新规划器、DQN、LLM Agent、新数据源

## 1. 目标

本协议用于修复并重新验证 Project05 的三个状态构念，同时保留 Round 1 的负结果。它不以“把指标做高”为目标，而要回答：这些字段能否按公开 codebook 被独立分析员复现；若不能，哪些字段只能作为版本化工程合同继续存在。

## 2. 不可撤销的历史记录

1. Round 1 Claim：27 项，加权 kappa `-0.1455`，原始一致率 `0.7407`，判定失败。
2. Round 1 预执行动作目标：27 项，exact `0.0741`，mean Jaccard `0.3673`，micro-F1 `0.4878`，判定失败。
3. Round 1 粒度：60 项的 A/B 文件 SHA-256 与自由文本相同，来源独立性无法证明，全部作废；不报告任何一致性数值。
4. 第三人裁决只产生裁决标签，不修改上述 Round 1 指标。

## 3. 三阶段执行顺序

### 3.1 R1-GR：粒度独立重标

该阶段只补齐 Round 1 中失效的粒度任务，不称为 Round 2。

- 使用冻结的 60 个 `GRN-*` 公开项目，不增删困难项目。
- A、B 分别接收不同的 package ID、annotator code 和交付目录。
- 每个 CSV 行必须包含 `package_id` 与 `annotator_code`，使两份回收文件字节级可区分。
- 管理员分别记录包生成、交付、回收的 UTC 时间；A、B 不共享目录，不查看对方答案。
- 回收后先计算原始文件 SHA-256，再复制到项目归档；不得先规范化再哈希。
- 若两份回收文件再次相同，任务仍判定无效，不进入统计。

### 3.2 R1-ADJ：Claim 与动作目标裁决

- 裁决者只接收 7 个 Claim 分歧项和 25 个动作目标分歧项。
- 裁决包不得包含 A/B 身份、答案顺序、管理员映射或编译标签。
- 裁决标签用于 human-vs-proxy 校准和错误分类，不用于重算双人 IAA。
- 输出必须保留 `adjudication_reason`、所依据证据指针和裁决者提交时间。

### 3.3 R2：修订构念后的新验证

Round 2 必须在 codebook v2、schema v2 和阈值冻结后开始，并在论文中明确写成“修订构念后的新验证”。

- 主验证集优先使用尚未进入 Round 1 的 C12 项，以及从 C07-C11 现有案例生成但未在 Round 1 展示的新状态；不增加新数据源。
- Round 1 的典型分歧项可以作为重复诊断层，但不与新项目混合计算主 Gate。
- 试标只用于发现说明书歧义，试标人员和项目不进入正式 Round 2 统计。
- 正式 A、B 继续独立盲标，裁决仅在 IAA 计算完成后进行。

## 4. Codebook v2 最低修订

### 4.1 Claim 支持度

- 将 `direct` 限定为原始事件字段直接编码主体、客体、动作和时间关系。
- 将 `partial` 限定为至少一个核心关系需由上下文、报告或跨事件拼接补足。
- 为 `unsupported` 与错误来源指针加入强制负例，避免标签全部集中于 `partial` 或来源指针全部为 `yes`。
- 对 compound node 明确“支持一个子行为”与“支持整个节点”的差异。

### 4.2 预执行动作目标

- 不再要求标注者猜测动作执行后会恢复哪些节点。
- 定义为“仅根据动作请求、通道能力和调查问题，在执行前声明该动作试图回答的最小调查问题集合”。
- 明确最小直接目标与宽候选集合的取舍规则，并提供正例、反例和边界例。
- 若分析员仍无法稳定重建，则将该字段固定为版本化系统合同，不再主张人工语义真值。

### 4.3 可支撑粒度

- 每一级都给出必要证据和禁止越级条件，而不是要求标注者复刻数值阈值。
- 明确 `G1_technique` 是行为/技术层结论，不等于正确 ATT&CK ID。
- 明确 `G2_tactic_intent` 不允许仅凭单一 TTP 推导行为体。
- 明确 `G3_campaign` 需要跨阶段关系和可回指锚点，不能由产品标签或报告标题单独触发。

## 5. 预注册指标与 Gate

| 构念 | 主指标 | 通过条件 |
|---|---|---|
| Claim 支持度 | quadratic-weighted Cohen's kappa | `>= 0.70`；`>= 0.80` 记为 strong |
| 来源指针 | Cohen's kappa + 混淆矩阵 | 必须包含正负例；不能只报告 raw agreement |
| 预执行动作目标 | micro-F1 + mean Jaccard | F1 `>= 0.80` 且 Jaccard `>= 0.70` |
| 可支撑粒度 IAA | quadratic-weighted kappa + 相差不超过一级比例 | kappa `>= 0.70` |
| 人工粒度 vs 编译代理 | weighted kappa + over-granularity rate | kappa `>= 0.70` 且越级率 `<= 0.10` |

任一构念未通过时，不得以后验删除项目、修改阈值或只报告 raw agreement 的方式改写结论。

## 6. Planner-visible 变更与重跑 Gate

### 6.1 不触发重跑

- 论文中将“公开意图”改称“预执行公开目标”，但底层字段值和策略输入完全不变。
- 专利仅收缩人工一致性和技术效果表述。
- 新增裁决结果，但裁决标签不写回运行时状态、动作或粒度规则。
- 修正文档、引用、拼写或展示顺序。

### 6.2 必须触发 C07-C12 全策略重跑

- `intended_cti_nodes` 的节点集合、生成规则或可见性发生变化。
- Claim 到 CTI 节点的映射、支持标签或来源过滤影响 `planner_state_view`。
- G0-G3 阈值、OR/AND 组合语义、关键节点或 `support_ceiling` 发生变化。
- 动作成本、通道先验、零收益反馈或 STOP 条件发生变化。
- 新字段进入 `planner_action_view` 或 `planner_state_view`。

触发后必须同时运行 Coverage、CMI、M1、M2、M3a、Logistic、XGBoost、AFA-VOI Myopic、AFA-VOI Rollout-H3、Depth-2 Public、DP/Oracle 等冻结矩阵；不得只重跑受益策略。

## 7. 重跑前后的版本要求

每次全矩阵重跑必须保存：

1. schema、codebook、案例配置和策略代码的 Git commit；
2. C07-C12 输入文件 SHA-256；
3. planner-visible schema diff；
4. 随机种子、重复次数和命令行；
5. 原始 episode 输出、聚合结果和与旧版本的 paired diff；
6. ceiling violation、premature STOP 和 zero-yield 审计。

## 8. 当前触发判定

2026-07-14 的论文 v0.9 与专利 v0.8 只进行了定位和术语收缩，没有修改 `intended_cti_nodes`、Claim 映射、G0-G3 规则、动作成本、通道反馈或 planner-visible schema。因此**当前不触发 C07-C12 重跑**。一旦 codebook v2 导致任何上述运行字段变化，本判定自动失效并转为强制全矩阵重跑。

## 9. 构念 Gate 关闭前禁止项

- 不实现或训练 DQN、Dueling DQN 或其他 RL planner。
- 不把 LLM Agent 接入在线动作选择。
- 不引入新的大体量数据源或以新增案例回避构念失败。
- 不把裁决标签、Round 2 结果或 IAA 写入专利技术效果。
