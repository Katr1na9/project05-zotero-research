# Project05 当前权威文件索引

> 历史索引：当前状态与下一步请转至 `AUTHORITATIVE-DOCUMENTS-20260712.md`。本文件仅保留 2026-07-11 Reviewer major revision 后的阶段快照。

日期：2026-07-11

状态：Reviewer major revision 后冻结

## 1. 唯一投稿入口

| 用途 | 当前权威文件 | 说明 |
|---|---|---|
| 论文主稿 | `paper-main-draft-v0.4-major-revision-20260711.md` | 以“信息边界约束的调查控制框架”为贡献，不主张新归因器或新规划器 SOTA |
| 论文写作记录 | `paper-main-authoring-record-v0.4-20260711.md` | 一句话论点、术语、主张—证据和未完成项 |
| 贡献边界 | `contribution-boundary-and-results-brief-v0.2-20260711.md` | 任何摘要、答辩、论文和专利说明均应服从此文件 |
| 论文/专利共同叙事 | `paper-patent-narrative-freeze-v0.2-20260711.md` | 统一技术核心及两类成果的不同表达 |
| 论文主图契约 | `paper-main-figure-contract-v0.2.md` | 图 1—3 的证据、统计单位和视觉红线 |
| 引文审计 | `paper-main-citation-audit-v0.2-20260711.md` | 新增 AFA 近邻的直接支撑边界 |
| Reviewer 回复 | `reviewer-response-major-revision-v0.1-20260711.md` | 逐条记录已处理、部分处理和未处理事项 |
| 修订后严谨性审计 | `paper-main-rigor-review-v0.2-20260711.md` | 二线 Borderline / 顶会 Weak Reject；未完成人工效度不作包装 |
| 专利主稿 | `patent-main-draft-v0.4-20260711.md` + `patent-package-v0.4/` | 权利要求链不因论文负结果改写 |
| 专利一致性附录 | `patent-v0.4-review-alignment-addendum-20260711.md` | 说明第 9 项、LLM 和正式申请待办 |
| 中国专利逐项补检 | `chinese-patent-claim-chart-v0.2-20260711.md` + `patent-claim-collision-matrix-v0.2-20260711.md` | 权利要求级技术比较；不是法律意见 |
| FTR-002 改写候选 | `patent-ftr002-claim-amendment-options-v0.1-20260711.md` | 供代理师选择；尚未替换 v0.4 权利要求 |

## 2. 权威实验结果

| 结果 | 文件/目录 | 当前结论 |
|---|---|---|
| C07-C10 序贯比较 | `results/xgboost_c01_c06_train_c07_c10_test/` | M2 180/180 达标，均成本 4.5333；XGBoost 未超过 M2 |
| AFA-VOI 同接口比较 | `results/afa_voi_c07_c10_v0.1/` | 两种适配均达标，但比 M2 多 0.4389 成本；不是 NOCTA/WinRegRL 官方复现 |
| M2/粒度敏感性 | `results/m2_sensitivity_v0.1/` | 16 个单权重扰动局部稳定；OR/AND 在真实四例不可识别，在开发多 claim 案例显著改变内部 success |
| 真实 Depth-2 | `results/nonmyopic_real_v0.1/` | 180/180 达标但成本不降，冻结升级门槛未通过 |
| 合成非短视 Gate | `results/nonmyopic_dqn_gate_v0.1/` | Gate A 通过、Gate B 不通过；不启动 DQN 主模型 |
| 双人盲标 | `annotation/c07_c10_v0.1/` | 空模板，状态必须保持 `awaiting_annotations`，不得生成或代填人工结果 |

## 3. 历史文件处理规则

`contribution-boundary-and-results-brief-v0.1.md`、`paper-patent-narrative-freeze-v0.1-20260711.md`、C07-C09 协议和早期 M3a 结果均保留为研究过程档案，不删除、不改写其阶段性实验事实，但不得继续承担“当前主线”“当前案例数”或“下一步计划”的功能。

## 4. 当前未完成门槛

1. 两名独立标注者完成 claim、公开意图和粒度盲标，并报告一致性及校准结果。
2. 增加第三数据家族或更多独立 engagement；重复 mask/seed 不得重计为独立攻击。
3. 若主张真实归因能力，必须增加 actor/campaign 正确性或分析师效用终点；当前内部 success 不等于归因准确率。
4. AFA 结果仅是同接口领域适配；正式投稿若要求严格外部复现，应补官方实现或等价公开代码的任务映射。
5. 专利正式提交前由代理师复核已完成的中国专利补检，确认 FTR-002 改写方案，并完成权属、公开日、发明人/申请人确认和逐项审查。
