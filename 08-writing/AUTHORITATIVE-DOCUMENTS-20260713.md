# Project05 当前权威文件索引

日期：2026-07-13

状态：论文 v0.7 为唯一母本；专利 v0.5 已同步 C11/C12、来源核验与外部 AFA/MDP 边界

## 1. 唯一写作入口

| 用途 | 当前权威文件 | 说明 |
|---|---|---|
| 论文主稿 | `paper-main-draft-v0.7-c12-operational-stress-20260713.md` | 唯一论文母本；C11 G2、C12 G1 分层报告，均不与 G3 主均值混算 |
| 论文写作记录 | `paper-main-authoring-record-v0.7-20260713.md` | 一句话论点、术语、C12/AFA 主张—证据和未完成项 |
| 贡献边界 | `contribution-boundary-and-results-brief-v0.2-20260711.md` | 任何摘要、答辩、论文和专利说明均应服从此文件 |
| 论文/专利共同叙事 | `paper-patent-narrative-freeze-v0.2-20260711.md` | 统一技术核心及两类成果的不同表达 |
| 论文主图/表契约 | `paper-main-figure-contract-v0.4-20260713.md` | 图 1—3 保持；C11/C12 使用独立正文表，不重绘主图聚合 |
| 引文审计 | `paper-main-citation-audit-v0.2-20260711.md` | 新增 AFA 近邻的直接支撑边界 |
| Reviewer 回复 | `reviewer-response-major-revision-v0.3-20260713.md` | 已记录 C12 两级 Gate、外部源码审计和仍未关闭的人工/终点门槛 |
| 修订后严谨性审计 | `paper-main-rigor-review-v0.5-20260713.md` | 已纳入 C12 与外部 AFA 边界；二线 Borderline / 顶会 Weak Reject |
| 专利主稿 | `patent-main-draft-v0.5-20260713.md` + `patent-package-v0.5/` | 12 项权利要求与 v0.4 一致；说明书同步 C11/C12 和来源 Gate |
| 专利一致性附录 | `patent-v0.5-paper-v0.7-alignment-addendum-20260713.md` | 说明论文增量、权项冻结、FTR-010 和正式申请待办 |
| 中国专利逐项补检 | `chinese-patent-claim-chart-v0.2-20260711.md` + `patent-claim-collision-matrix-v0.3-20260713.md` | 加入 AFA/MDP 与 C11/C12 边界；仍不是法律意见 |
| FTR-002 改写候选 | `patent-ftr002-claim-amendment-options-v0.1-20260711.md` | 供代理师选择；尚未替换 v0.4 权利要求 |

## 2. 权威实验结果

| 结果 | 文件/目录 | 当前结论 |
|---|---|---|
| C07-C10 序贯比较 | `../09-experiments/results/xgboost_c01_c06_train_c07_c10_test/` | M2 180/180 达标，均成本 4.5333；XGBoost 未超过 M2 |
| AFA-VOI 同接口比较 | `../09-experiments/results/afa_voi_c07_c10_v0.1/` | 两种适配均达标，但比 M2 多 0.4389 成本；不是 NOCTA/WinRegRL 官方复现 |
| M2/粒度敏感性 | `../09-experiments/results/m2_sensitivity_v0.1/` | 16 个单权重扰动局部稳定；C07-C10 每节点单 claim，OR/AND 不可识别 |
| 真实 Depth-2 | `../09-experiments/results/nonmyopic_real_v0.1/` | 180/180 达标但成本不降，冻结升级门槛未通过 |
| 合成非短视 Gate | `../09-experiments/results/nonmyopic_dqn_gate_v0.1/` | Gate A 通过、Gate B 不通过；不启动 DQN 主模型 |
| C11 数据接入协议 | `c11-otrf-apt29-day1-intake-protocol-v0.1-20260712.md` | 内部冻结 D1-D5、AND 多 claim、初始 G3 目标和失败保留/降级规则 |
| C11 OTRF AND 主结果 | `../09-experiments/results/c11_holdout_v0.1/` | 4/5 节点通过双 provider Gate；自然缺口使目标降至 G2；M2 success 1.0、cost 3.6667，但不是最低成本 |
| C11 OR 敏感性 | `../09-experiments/results/c11_or_sensitivity_v0.1/` | 仅改 AND→OR 后，M2 cost 降至 1.0222；证明覆盖语义会实质改变成本 |
| C11 结果简报 | `c11-otrf-apt29-day1-results-v0.1-20260712.md` | C11 是第三种数据封装与单个仿真链，不是未知 actor 归因 benchmark |
| C11 增量复核 | `c11-increment-audit-v0.1-20260713.md` | 原始回指、冻结结果、语义边界与 v0.5 整合决定 |
| C11 冻结策略迁移 | `../09-experiments/results/c11_extended_policies_v0.1/` | XGBoost/Logistic cost 3.0667，AFA-Myopic 3.5556，Depth-2 success 0.9778；单案例排序反转 |
| C11 策略迁移简报 | `c11-frozen-policy-transfer-results-v0.1-20260713.md` | 冻结约束、配对结果、离线—序贯指标分离及写作红线 |
| 外部 AFA 源码/接口映射 | `external-afa-baseline-mapping-protocol-v0.1-20260713.md` + `../09-experiments/results/external_afa_baseline_audit_v0.1/` | 三个冻结仓库通过；任务不等价，禁止称官方同任务复现 |
| C12 元数据/事件 Gate | `../09-experiments/results/c12_witfoo_screen_v0.1/` + `../09-experiments/results/c12_witfoo_event_audit_v0.1/` | 13,119→5→2；剔除产品标签多源、实际 stream 单源候选 |
| C12 冻结 G1 结果 | `c12-natural-operational-engagement-results-v0.1-20260713.md` + `../09-experiments/results/c12_holdout_v0.1/` + `../09-experiments/results/c12_extended_policies_v0.1/` | 单个生产 SOC incident；Depth-2 与 Oracle cost 0.8889，M2 1.4222；无 actor truth，不并入既有均值 |
| 双人盲标协议 | `human-annotation-evaluation-protocol-v0.2-20260712.md` | C07-C11、114 个 item；先一致性、后裁决、再对工程代理校准 |
| 双人盲标包 | `../09-experiments/annotation/c07_c11_v0.2/` | A/B 与裁决模板均为空，状态必须保持 `awaiting_annotations`，不得生成或代填人工结果 |
| Claim 来源摘录包 | `../09-experiments/annotation/source_excerpts/c07_c11_v0.1/` | 27/27 canonical excerpts 已在当前工作站生成；Git 只保存构建器与哈希清单 |
| A/B 本地分发包 | `../09-experiments/annotation/distribution/c07_c11_v0.2_distribution_v0.1/` | 两个隔离 ZIP 已生成；不含 admin key、对方 CSV、规划结果或人工标签 |
| Claim 来源访问台账 | `human-annotation-source-access-ledger-v0.2-20260713.md` | 来源 Gate 已关闭；人工标签仍为零，尚未启动 A/B 标注 |

## 3. 当前冻结判断

1. 论文主线仍是“不完整证据下、信息边界约束的 APT 调查控制”，不是新的 actor attribution 分类器。
2. C11 关闭了“第三种数据封装”和“真实可识别多 provider claim”两个工程缺口，但只增加一个 APT29 仿真链，不能声称广泛外部泛化。
3. C11 的 Host 与 Zeek 时间窗不重叠；Zeek 不构成事件级 corroboration。
4. 预锁定 N01 无事件支持并被原样保留；由此得到的 G3→G2 降级是可审计结果，不是数据清洗失败。
5. M2 在 C07-C10 上是冻结对照内最佳折中；C11 中 XGBoost/Logistic 和 AFA-Myopic 成本更低，Depth-2 发生一次退化。任何排序都不得写成全局最优或新 SOTA。
6. C11 的 45 个 mask/intensity/seed 条件是重复测量，不是 45 个独立攻击。
7. LLM/agent 仍只保留为待独立验证的离线编译或解释接口，不进入当前因果贡献。
8. C11 的协议与结果同批提交，只称内部冻结记录；N02/N05 claims 只证明 collection，不证明网络 exfiltration。
9. C12 是 1 个生产 SOC 多 stream incident 的 G1 压力；45 个条件是重复测量，GraphML 为厂商投影，`Disrupted` 不等于独立 actor truth。
10. 外部 AFA 源码与动作映射已完成，但 AFABench/AACO/WinRegRL 与 Project05 的状态、端点和转移语义不等价；当前不允许“官方同任务复现”表述。
11. 专利 v0.5 只把 C12 两级来源 Gate 写为可选实施例；FTR-010 在完成中国专利补检和代理师审查前不得升级为独立必要特征。

## 4. 历史文件处理规则

`AUTHORITATIVE-DOCUMENTS-20260711.md`、论文 v0.6 及更早稿、旧 reviewer/rigor review、早期 contribution brief、C07-C09 协议和早期 M3a 结果均保留为研究过程档案，不删除、不改写其阶段性事实，但不得继续承担当前状态索引或下一步计划的功能。

## 5. 当前未完成门槛

1. 由两名独立标注者完成 claim、公开意图和粒度盲标，并报告一致性、裁决及代理校准结果；27/27 来源摘录已经就绪，不再以恢复数据作为前置待办。
2. C12 已提供一个更接近运营现场的独立 incident，但仍需更多组织/incident 或分析师效用端点才能主张外部泛化；重复 mask/seed 不得重计为独立攻击。
3. 若主张真实归因能力，必须增加 actor/campaign 正确性或分析师效用终点；当前内部 success 不等于归因准确率。
4. AFA 源码/任务映射已完成；正式投稿若要求数值复现，必须先冻结 endpoint contract，并将跨任务复现或 adapter 与主结果分表。
5. 专利正式提交前由代理师复核中国专利补检，确认 FTR-002 改写方案、权利要求 9 和 FTR-010 的处理，并完成权属、公开日、发明人/申请人确认和逐项审查。
