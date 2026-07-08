# Project05 Workflow Status

## 2026-07-08 第九次更新：C01 toy MVP 已跑通

已新增 C01 小样例和最小模拟器：

1. `09-experiments/examples/C01/case_config.json`
2. `09-experiments/examples/C01/evidence_claims.json`
3. `09-experiments/examples/C01/acquisition_actions.json`
4. `09-experiments/scripts/run_mvp.py`
5. `09-experiments/results/c01_mvp_results.csv`
6. `09-experiments/results/c01_mvp_summary.json`
7. `09-experiments/results/c01_mvp_traces.json`

当前状态修正：

> G5 从“Phase 0/1 草案完成，待小样例与模拟器验证”推进为“C01 toy MVP 跑通，待 C02/C03 扩展验证”。

当前 C01 结果仅作为工程闭环验证：`project05_m1` 平均达到 G3 成本为 3.0，低于 `coverage_greedy` 的 3.4 和 `fixed_order` 的 6.2667。该结果还不能作为论文实验结论。

下一步：

1. 构造 C02/C03。
2. 增加 mask intensity 20% / 40% / 60%。
3. 增加统计汇总脚本和结果表模板。

## 2026-07-08 第八次更新：实验案例清单与 schema 已完成

已新增实验设计 Phase 0/1 产物：

1. `08-writing/experiment-case-inventory-v0.1-20260708.md`
2. `09-experiments/README.md`
3. `09-experiments/data_schema/evidence_claim.schema.json`
4. `09-experiments/data_schema/alignment_state.schema.json`
5. `09-experiments/data_schema/acquisition_action.schema.json`

当前状态修正：

> G5 从“草案完成，待案例清单和 schema 验证”推进为“Phase 0/1 草案完成”；2026-07-08 已进一步跑通 C01 toy MVP。

下一步：

1. 已构造 C01 最小样例数据。
2. 已实现 evidence ablation + action recovery 模拟器。
3. 已跑 random / fixed-order / coverage-greedy / Project05-M1 / full-evidence 五个最小 baseline。

## 2026-07-07 第七次更新：缺口精读笔记已补齐

已新增/升级 8 篇核心精读笔记：

1. `2019-Milajerdi-POIROT.md`
2. `2021-Wei-DeepHunter.md`
3. `2024-Aly-MEGR-APT.md`
4. `2025-Li-CLIProv.md`（由摘要级占位升级）
5. `2025-Qiu-APT-CGLP.md`（由摘要级占位升级）
6. `2025-NOCTA-Non-Greedy-Objective-Cost-Tradeoff-Acquisition.md`
7. `2025-ExCyTIn-Bench-Cyber-Threat-Investigation.md`
8. `2026-Adaptive-Malware-Detection-Sequential-Feature-Selection-DDQN.md`

当前状态修正：

> CLIProv / APT-CGLP 已不再是待补全文项。对齐谱系红线与主动取证理论/baseline 侧材料已补齐到可支撑下一步实验案例清单。

下一步：

1. 已完成 `08-writing/experiment-case-inventory-v0.1-20260708.md`。
2. 已完成 `evidence_claim / alignment_state / acquisition_action` 三个 schema。
3. 仅保留 APTChaser、GAPT 作为后续高风险全文待办；APT-ATT 已于 2026-07-07 获取并精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

## 2026-07-07 第六次更新：实验方案 v0.1 已完成

已新增 `08-writing/experiment-plan-v0.1-20260707.md`。实验路线采用 evidence ablation：从完整攻击案例出发，遮蔽部分证据，模拟不完整证据场景；不同策略通过取证动作逐步恢复证据，比较达到目标归因粒度的成本、步数、过度归因率和解释证据回指质量。

当前状态：

> G5 从“未通过”推进到“草案完成”；2026-07-08 已进一步完成案例清单和 schema，待小样例与模拟器验证。

下一步：

1. 已建立 `08-writing/experiment-case-inventory-v0.1-20260708.md`。
2. 已设计 `evidence_claim / alignment_state / acquisition_action` 三个 schema。
3. MVP 已暂定先评估 G1-G3，即 technique / intent / campaign 粒度。

## 2026-07-06 第五次更新：US12530469 权利要求原文补读剔除

根据用户决策，US12530469 的“权利要求原文补读”不再作为当前 workflow 的 G2/G4 阻塞项。该专利仍作为摘要级红线材料保留，用于提醒 Project05 避免写成泛化的“LLM 告警调查 + 置信不足追加上下文 + 循环收敛”。

当前剩余补洞修正为：

1. 中文专利侧与证据采集/取证规划相关检索；
2. APTChaser / GAPT 正文获取；APT-ATT 已于 2026-07-07 获取并精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。

下一步仍优先起草 `08-writing/experiment-plan-v0.1-20260706.md`。

## 2026-07-06 第四次更新：G1 正式通过

已新增 `03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md`，作为当前主线的 Stage 1 / RQ Scoping 通过版。

当前状态修正为：

> G1 通过；G2 剩余补洞与 G5 实验设计 v0.1 并行推进。

下一步优先级：

1. 起草 `08-writing/experiment-plan-v0.1-20260706.md`，先验证这条主线能不能跑起来。
2. 继续补剩余高风险全文；US12530469 权利要求原文补读已剔除，CLIProv/APT-CGLP 已于 2026-07-07 升级为全文精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。
3. 旧专利 v0.2 继续冻结，等 experiment-plan-v0.1 通过后再进入 v0.3。

## 2026-07-06 第三次更新：全项目重扫后的当前状态

当前阶段修正为：

> Stage 1 / RQ Scoping 基本通过，正在进入 Stage 2 / Deep Collision Scan 的剩余补洞，以及 Stage 5 / Experiment Design 的 v0.1 草案。

本轮重扫确认旧的“归因控制层”方向偏弱，已经降级为模块。当前主线为：

> 对齐感知证据状态建模 + 面向归因粒度提升的主动取证规划。

关键判断：

- CTI graph 与 provenance/local evidence 对齐本身已经拥挤，不能作为单独主创新。
- CLIProv、APT-CGLP、US12530469 是新红线材料。
- AFA / POMDP 是当前最重要的理论基座。
- 当前 RQ v2 见 `03-ideas/topic-rq-brief-v2-20260706.md`。
- 本轮重扫报告见 `04-progress/project-rescan-increment-20260706.md`。

下一步任务：

1. 导入 `07-zotero-exports/zotero-import-candidates-20260706-alignment.ris`。
2. 补剩余高风险全文；US12530469 仅保留摘要级红线，CLIProv/APT-CGLP 已于 2026-07-07 升级为全文精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。
3. 起草 `08-writing/experiment-plan-v0.1-20260706.md`。
4. 暂停扩写旧专利 v0.2，等实验计划成型后再重写 v0.3。

日期：2026-07-06

## 当前所处阶段

当前处于：

> Stage 6：Collision Matrix 功能级撞题  
> 正在向 Stage 7：Patent Due Diligence 过渡，但尚未通过 G4。

## 已完成

- 主线文献第一轮沉淀。
- 2026 H1 补读。
- TAA-EPLMR / LLMAPT 已纳入精读。
- 二次深度撞题扫描。
- 新增 13 份精读/风险精读笔记。
- `patent-claims-draft-v0.1` 已标记为偏宽草案。

## 当前红线

以下方向不得作为 Project05 主创新：

1. 多源证据融合 APT 归因。
2. LLM-based APT attribution framework。
3. KG/RAG/GraphRAG 归因。
4. IOC/KG/HIN/GNN/RGCN 图归因。
5. TTP 相似度/加权归因。
6. open-set / abstention 单点创新。
7. provenance graph + LLM 攻击摘要。
8. confidence score / information gap / hunting recommendation。

## 当前白名单

仍可推进的组合：

```text
证据充分性画像
  + 归因粒度门控
  + 可拒答解释
  + 缺失证据生成
  + LLM 受控表达
```

必须注意：每个单点都不新，只有组合成“归因控制层”才可能保留空间。

## 未通过的 Gate

### G4：专利权利要求可防守性

未通过原因：

- v0.1 题名仍含“多源安全证据自适应融合”，太宽；
- 独立权利要求仍容易被 US12368730B2、TAA-EPLMR、TRAIL、APT-scope、HG-CTA、AARGS 等压缩；
- 需要把“多源融合”降级为输入条件。

### G5：实验可执行性

未通过原因：

- 数据集未最终确定；
- baseline 未最终确定；
- 缺失证据生成的评价方式未确定；
- APTChaser、GAPT、AARGS 全文仍需补齐；APT-ATT 已于 2026-07-07 获取并精读。

## 下一步任务

1. 导入 `07-zotero-exports/zotero-import-candidates-20260706-deep-scan.ris`。
2. 获取 APTChaser、GAPT、AARGS 正文；APT-ATT 已于 2026-07-07 获取并精读。
3. 把摘要级风险精读升级为全文精读。
4. 已完成：重写 `08-writing/patent-claims-draft-v0.2-20260706.md`。
5. 下一步：起草 `experiment-plan-v0.1`。

## 2026-07-06 更新

- 缺全文项已转入 `04-progress/fulltext-todo-20260706.md`，不再阻塞主线推进。
- 最终撞题边界已整理为 `04-progress/collision-matrix-final-20260706.md`。
- 专利权利要求草案已推进到 `08-writing/patent-claims-draft-v0.2-20260706.md`，但仍标记为 incomplete draft。

## 2026-07-06 第二次更新：G3 回退生效

- 用户判定"归因控制层"组合偏弱，触发 G3 回退条件（白名单只剩"给别人系统加保护层"）。
- 当前阶段修正为：**Stage 1：RQ Scoping（主线转向中）**。
- Stage 6/7 的撞题矩阵与专利 v0.2 保留为历史资产；v0.2 暂停扩写，待新主线确定后决定是否重写为 v0.3。
- 候选主线分析见 `04-progress/mainline-pivot-candidates-20260706.md`。
- 新增待核查专利：US12530469（置信度驱动的 LLM 多阶段告警调查循环）。
