# Claim、公开意图与可支撑粒度人工标注协议 v0.2

日期：2026-07-12
状态：标注前冻结；尚无人工标签
案例范围：C07-C11

## 1. 目的与边界

本协议独立评价三个由项目规范或脚本编译、但尚未获得人工效度证据的环节：

1. evidence claim 是否被引用来源直接支持，是否存在语义越界；
2. `intended_cti_node_ids` 是否能由动作请求和公开 CTI 图在执行前复现；
3. 人工判断的最高可支撑调查粒度是否与当前 G0-G3 工程代理一致。

结果用于校准 schema、公开意图和粒度代理，不用于回头修改 C07-C11 的冻结规划器输出。内部 success 仍不等于 actor/campaign 归因准确率。

## 2. 样本与统计单位

| 任务 | 入组规则 | Item 数 |
|---|---|---:|
| Claim 支持度与来源指针 | C07-C11 全部 evidence claims | 27 |
| 公开动作意图 | C07-C11 全部非 STOP 动作 | 27 |
| 可支撑粒度 | 每案例去重并分层抽取最多 12 个可见 claim 状态 | 60 |

合计 114 个标注 item。独立案例数为 5，其中 C11 是一个 APT29 adversary-emulation 链，不能写成自然事件或未知 actor benchmark。Item、mask、seed 和 annotator 数均不得重计为独立攻击样本。

## 3. 标注者与盲法

- 至少两名具备安全日志、CTI 或事件响应知识的独立标注者 A、B。
- 第一轮不得讨论答案，也不得访问对方 CSV、管理员 key、规划器结果或论文中的案例结论。
- 公开包使用随机 blind ID，不显示 `case_id`、真实 `claim_id`、`action_id`、代码计算粒度或动作恢复集合。
- intended 标注者不得访问 `recoverable_claim_ids`。
- granularity 标注者只能读取当前可见 claims 和公开 CTI 图，不能读取隐藏 claims、support ceiling 或代码标签。
- 首轮一致性计算完成后，第三名裁决者只处理 A/B 分歧；裁决者仍不得访问管理员 key。
- 管理员 key 只在裁决完成后用于聚合校准，不向任何标注者开放。

## 4. 来源访问 Gate

Claim 任务开始前，每个 source pointer 必须满足以下二选一：

1. 标注者能够访问指针指向的原始记录；或
2. 管理员提供 hash 锚定的 canonical excerpt，保留 artifact ID、record ID、时间、provider/event type 以及判断 subject-predicate-object 所需的原始字段。

项目 `notes`、motif report 和 claim 编译说明只是待审对象的上下文，不能替代独立来源记录。若标注者实际无法读取所指记录，必须标为 `U_unassessable` 和 `source_pointer_valid=unassessable`；但管理员已知来源不可用时，不应故意启动 Claim 任务来制造大量 U 标签。

当前来源状态见 `human-annotation-source-access-ledger-v0.1-20260712.md`：C11 的 8 条记录本地可回查；C07-C10 的 19 条精确原始记录当前不在本地工作区。因此：

- 公开意图和粒度任务已具备启动条件；
- Claim 任务仍需先补 C07-C10 原始记录或 canonical excerpts；
- 未通过来源 Gate 前，不得声称 27 条 claims 已获得人工验证。

## 5. Codebook

### 5.1 Claim 支持度

评价完整的 subject-predicate-object、限定语、技术映射和 notes 中的行为含义：

- `2_direct`：来源直接支持原子 claim，主体、客体、行为和限定范围均未越过可观察事实；
- `1_partial`：核心事件存在，但对象、因果、攻击含义、技术映射或范围有部分过度表述；
- `0_unsupported`：来源不支持、与 claim 冲突，或指针定位到无关记录；
- `U_unassessable`：来源记录不可访问、损坏或缺少完成判断所需字段。

`source_pointer_valid` 单独标记：

- `yes`：能够按 artifact/record locator 唯一定位到被引用记录；
- `no`：定位失败、定位到其他记录或 locator 不唯一；
- `unassessable`：对应数据源不可访问。

### 5.2 公开意图

标注者只依据 action type、channel、target、natural-language request 与公开 CTI 图，选择该动作在执行前合理希望补充的节点集合：

- 允许空集合；
- 允许多节点；
- 只标公开请求可推断的宽意图，不猜测执行后会实际恢复什么；
- 多节点在 CSV 中以 `|` 分隔。

### 5.3 可支撑粒度

- `G0_unknown`：当前证据不足以稳定确认具体攻击技术或调查方向；
- `G1_technique`：至少能支持具体行为/技术，但不足以形成跨阶段战术意图；
- `G2_tactic_intent`：多个证据能支持战术目的、攻击意图或跨阶段局部链，但关键缺口仍阻止 campaign 级结论；
- `G3_campaign`：关键攻击阶段和关系形成连贯、来源可支撑的 campaign 级调查叙事。

标注者按证据含义判断，不复刻代码中的覆盖率阈值。`key_missing_evidence` 用简短文本写明阻止进入下一粒度的最关键缺口；该字段用于定性分析，不进入首轮 kappa。

## 6. 随机化与冻结

- packet：`c07_c11_v0.2`
- 随机种子：`20260712`
- blind ID 与 v0.1 不复用。
- 三类 item 独立随机排列。
- 每个公开文件和 C07-C11 三个来源 case 文件的 SHA-256 固定在 `packet_manifest.json`。
- 首轮标签只追加不覆盖。Codebook 若修改，必须新建 round 2/pilot，不得删除困难 item 提高指标。

## 7. 分析顺序

1. A、B 独立填写各自三个 CSV，逐行将 `reviewed` 设为 `yes`。
2. 运行一致性分析；该步骤不读取 admin key。
3. 仅把分歧 item 交给第三名裁决者，写入 `adjudicator/` 对应行。
4. 裁决完成后，管理员在隔离环境运行代理校准；输出只含聚合指标，不导出 item 映射或 `recoverable_claim_ids`。

命令：

```powershell
python 09-experiments/scripts/analyze_annotation_agreement.py 09-experiments/annotation/c07_c11_v0.2
python 09-experiments/scripts/analyze_annotation_calibration.py 09-experiments/annotation/c07_c11_v0.2
```

## 8. 预注册指标与判定

### A/B 一致性

- claim：排除 U 后的 quadratic-weighted Cohen's kappa、原始一致率、U 比例；
- source pointer：Cohen's kappa、原始一致率；
- intended：exact match、mean Jaccard、micro precision/recall/F1；
- granularity：quadratic-weighted kappa、相差不超过一级比例、混淆矩阵。

阈值：weighted kappa >= 0.80 为 strong，0.70-0.79 为 acceptable，低于 0.70 需修订 codebook；intended micro F1 >= 0.80 且 mean Jaccard >= 0.70 为 acceptable；U 超过 20% 表示来源包不足。

### 人工对工程代理校准

- claim：人工 `2_direct` 接受率、direct-or-partial 比例、source pointer 可验证率；
- intended：最终人工节点集与编译 intended 的 exact/Jaccard/micro F1；
- granularity：最终人工标签与代码代理的 weighted kappa、exact match、过粒度率、欠粒度率和混淆矩阵。

粒度代理通过条件预锁定为：weighted kappa >= 0.70 且 `compiled_over_granularity_rate <= 0.10`。未通过时应调整规则或收缩论文主张，不得通过删 item 或后验改阈值救结果。

## 9. 产物

- packet generator：`09-experiments/scripts/build_annotation_packets.py`
- agreement analyzer：`09-experiments/scripts/analyze_annotation_agreement.py`
- adjudication/calibration analyzer：`09-experiments/scripts/analyze_annotation_calibration.py`
- 盲标包：`09-experiments/annotation/c07_c11_v0.2/`
- 来源台账：`08-writing/human-annotation-source-access-ledger-v0.1-20260712.md`
- 结果模板：`08-writing/human-annotation-evaluation-results-template-v0.2-20260712.md`
