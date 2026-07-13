# Project05 当前权威文件索引

日期：2026-07-13

状态：论文 v0.5 已吸收 C11 外部效度增量

## 1. 唯一写作入口

| 用途 | 当前权威文件 | 说明 |
|---|---|---|
| 论文主稿 | `paper-main-draft-v0.5-c11-external-validity-20260713.md` | 唯一论文母本；C11 独立进入外部效度小节，不与 G3 主均值混算 |
| 论文写作记录 | `paper-main-authoring-record-v0.5-20260713.md` | 一句话论点、术语、主张—证据和未完成项 |
| 贡献边界 | `contribution-boundary-and-results-brief-v0.2-20260711.md` | 任何摘要、答辩、论文和专利说明均应服从此文件 |
| 论文/专利共同叙事 | `paper-patent-narrative-freeze-v0.2-20260711.md` | 统一技术核心及两类成果的不同表达 |
| 论文主图/表契约 | `paper-main-figure-contract-v0.3-20260713.md` | 图 1—3 保持，新增 C11 独立表格红线 |
| 引文审计 | `paper-main-citation-audit-v0.2-20260711.md` | 新增 AFA 近邻的直接支撑边界 |
| Reviewer 回复 | `reviewer-response-major-revision-v0.1-20260711.md` | 逐条记录已处理、部分处理和未处理事项 |
| 修订后严谨性审计 | `paper-main-rigor-review-v0.3-20260713.md` | 已纳入 C11；二线 Borderline / 顶会 Weak Reject，未完成人工效度不作包装 |
| 专利主稿 | `patent-main-draft-v0.4-20260711.md` + `patent-package-v0.4/` | 权利要求链不因论文负结果改写 |
| 专利一致性附录 | `patent-v0.4-review-alignment-addendum-20260711.md` | 说明第 9 项、LLM 和正式申请待办 |
| 中国专利逐项补检 | `chinese-patent-claim-chart-v0.2-20260711.md` + `patent-claim-collision-matrix-v0.2-20260711.md` | 权利要求级技术比较；不是法律意见 |
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
| 双人盲标协议 | `human-annotation-evaluation-protocol-v0.2-20260712.md` | C07-C11、114 个 item；先一致性、后裁决、再对工程代理校准 |
| 双人盲标包 | `../09-experiments/annotation/c07_c11_v0.2/` | A/B 与裁决模板均为空，状态必须保持 `awaiting_annotations`，不得生成或代填人工结果 |
| Claim 来源访问台账 | `human-annotation-source-access-ledger-v0.1-20260712.md` | C11 8 条可回查；C07-C10 19 条精确记录待恢复，完整 Claim 标注尚未启动 |

## 3. 当前冻结判断

1. 论文主线仍是“不完整证据下、信息边界约束的 APT 调查控制”，不是新的 actor attribution 分类器。
2. C11 关闭了“第三种数据封装”和“真实可识别多 provider claim”两个工程缺口，但只增加一个 APT29 仿真链，不能声称广泛外部泛化。
3. C11 的 Host 与 Zeek 时间窗不重叠；Zeek 不构成事件级 corroboration。
4. 预锁定 N01 无事件支持并被原样保留；由此得到的 G3→G2 降级是可审计结果，不是数据清洗失败。
5. M2 在 C07-C10 上是冻结对照内最佳折中，在 C11 上不是最低成本；不得写成全局最优或新 SOTA。
6. C11 的 45 个 mask/intensity/seed 条件是重复测量，不是 45 个独立攻击。
7. LLM/agent 仍只保留为待独立验证的离线编译或解释接口，不进入当前因果贡献。
8. C11 的协议与结果同批提交，只称内部冻结记录；N02/N05 claims 只证明 collection，不证明网络 exfiltration。

## 4. 历史文件处理规则

`AUTHORITATIVE-DOCUMENTS-20260711.md`、早期 contribution brief、C07-C09 协议和早期 M3a 结果均保留为研究过程档案，不删除、不改写其阶段性事实，但不得继续承担当前状态索引或下一步计划的功能。

## 5. 当前未完成门槛

1. 先恢复 C07-C10 的 19 条精确来源记录或 hash 锚定 excerpts；随后由两名独立标注者完成 claim、公开意图和粒度盲标，并报告一致性、裁决及代理校准结果。
2. 若要进一步加强外部效度，增加自然发生或更接近运营现场的独立 engagement；重复 mask/seed 或同一仿真 replay 不得重计为独立攻击。
3. 若主张真实归因能力，必须增加 actor/campaign 正确性或分析师效用终点；当前内部 success 不等于归因准确率。
4. AFA 结果仅是同接口领域适配；正式投稿若要求严格外部复现，应补官方实现或等价公开代码的任务映射。
5. 专利正式提交前由代理师复核中国专利补检，确认 FTR-002 改写方案，并完成权属、公开日、发明人/申请人确认和逐项审查。
