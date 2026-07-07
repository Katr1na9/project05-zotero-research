# Project05 Workflow Status

## 2026-07-06 第五次更新：US12530469 权利要求原文补读剔除

根据用户决策，US12530469 的“权利要求原文补读”不再作为当前 workflow 的 G2/G4 阻塞项。该专利仍作为摘要级红线材料保留，用于提醒 Project05 避免写成泛化的“LLM 告警调查 + 置信不足追加上下文 + 循环收敛”。

当前剩余补洞修正为：

1. CLIProv 全文；
2. APT-CGLP 全文；
3. TAA-EPLMR 复核；
4. 中文专利侧与证据采集/取证规划相关检索。

下一步仍优先起草 `08-writing/experiment-plan-v0.1-20260706.md`。

## 2026-07-06 第四次更新：G1 正式通过

已新增 `03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md`，作为当前主线的 Stage 1 / RQ Scoping 通过版。

当前状态修正为：

> G1 通过；G2 剩余补洞与 G5 实验设计 v0.1 并行推进。

下一步优先级：

1. 起草 `08-writing/experiment-plan-v0.1-20260706.md`，先验证这条主线能不能跑起来。
2. 继续补 CLIProv/APT-CGLP/TAA-EPLMR 全文；US12530469 权利要求原文补读已剔除。
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
2. 补 CLIProv、APT-CGLP、TAA-EPLMR 正文；US12530469 仅保留摘要级红线。
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
- APT-ATT、APTChaser、GAPT、AARGS 全文仍需补齐。

## 下一步任务

1. 导入 `07-zotero-exports/zotero-import-candidates-20260706-deep-scan.ris`。
2. 获取 APT-ATT、APTChaser、GAPT、AARGS 正文。
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
