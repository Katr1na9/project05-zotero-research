# Project05 全项目重扫增量报告 - 2026-07-06

## 扫描结论

本次重扫确认：Project05 已经出现明显增量，而且这些增量改变了当前主线。

原来的“归因粒度门控 / 可拒答解释 / 缺失证据 list”方向已经被用户判断为偏弱。随后新增的深度撞题扫描、AFA 综述精读和 RQ v2 文件显示，项目已经转向：

> 对齐感知证据状态建模 + 面向归因粒度提升的主动取证规划。

这条主线比“产出缺失证据 list”更强，因为它把缺失证据从解释性输出提升为可优化的取证动作序列，并可以用成本、收益、停止条件和归因粒度提升来评价。

## 新增文件

### 文献笔记

- `02-literature-notes/2025-Aronsson-AFA-Survey.md`
- `02-literature-notes/2025-Li-CLIProv.md`
- `02-literature-notes/2025-Qiu-APT-CGLP.md`
- `02-literature-notes/2026-Varonis-US12530469-LLM-Alert-Investigation.md`
- `02-literature-notes/2025-Au-Multi-Source-Feature-Fusion-HKG-APT-Attribution-IDS.md`

2026-07-07 补充：CLIProv、APT-CGLP 已由摘要级占位升级为全文精读，并新增 POIROT、DeepHunter、MEGR-APT、NOCTA、ExCyTIn-Bench、D3QN 恶意软件顺序特征选择精读笔记。

### 主线和撞题文件

- `03-ideas/topic-rq-brief-v2-20260706.md`
- `04-progress/deep-collision-scan-alignment-20260706.md`
- `04-progress/mainline-pivot-candidates-20260706.md`
- `04-progress/collision-matrix-final-20260706.md`
- `04-progress/fulltext-todo-20260706.md`
- `04-progress/project05-current-conclusion-brief-20260706.md`

### Zotero / 写作

- `07-zotero-exports/zotero-import-candidates-20260706-alignment.ris`
- `08-writing/patent-claims-draft-v0.2-20260706.md`

## 新主线为什么出现

深度扫描发现，“CTI 图与本地日志 / provenance / IOC 证据对齐”本身已经不是安全空白。相关工作从 POIROT、DeepHunter、MEGR-APT 到 2025-2026 的 CLIProv、APT-CGLP、ProHunter，已经覆盖了 CTI report 与 provenance graph / log evidence 的匹配、对齐、图语言预训练和威胁狩猎。

因此 Project05 不能把“我也做一个对齐器”作为主线。更稳的位置是：

1. 复用或抽象已有对齐器的输出；
2. 把对齐结果变成证据状态；
3. 判断当前证据能支撑的归因粒度；
4. 估计不同取证动作的期望粒度收益；
5. 在成本约束下规划下一步取证；
6. 迭代更新证据状态，直到达到目标粒度或预算终止。

## 新增红线

| 红线 | 影响 |
|---|---|
| CLIProv | 日志 / provenance 到威胁情报语义对齐不能作为核心创新 |
| APT-CGLP | CTI report 与 provenance graph 的 graph-language pre-training 已有覆盖 |
| US12530469 | 宽泛的“LLM 告警调查 + 置信不足拉取更多上下文 + 循环收敛”有专利风险 |
| APT-MMF / Au HKG | 多源 CTI / IOC / HKG / feature fusion / actor attribution 已高度拥挤 |

## 新增理论基座

`A Survey on Active Feature Acquisition Strategies` 将 Project05 的新问题落到了 Active Feature Acquisition / POMDP 框架：

- 当前证据状态 = 部分观测特征；
- 取证动作 = 获取一个或一类证据；
- 取证成本 = 日志窗口、样本分析、基础设施富集、人工调查等成本；
- 任务收益 = 归因粒度提升、错误归因降低、拒答正确性提升；
- STOP 动作 = 当前证据足够支撑目标粒度，或预算耗尽。

Project05 与常规 AFA 的差异在于：证据不是扁平表格特征，而是 CTI-local alignment state；输出不是分类标签，而是归因粒度、候选 actor 分布、缺口解释和取证策略。

## 当前最重要 RQ

见 `03-ideas/topic-rq-brief-v2-20260706.md`。核心问题是：

> 在证据不完整的 APT 归因场景中，如何以“CTI 侧攻击行为图与本地观测证据的对齐状态”为证据画像，估计各候选取证动作对归因粒度可提升性的期望增益，并在成本约束下规划取证动作序列，使系统通过“对齐-评估-补证-再对齐”闭环，以最小取证成本达到证据可支撑的最高归因粒度？

## 状态不一致点

重扫发现这些索引文件仍有旧主线残留，已在本轮修正：

- `README.md`
- `00-dashboard/research-dashboard.md`
- `02-literature-notes/README.md`
- `04-progress/research-progress.md`
- `04-progress/workflow-status-20260706.md`

## 当前待办

1. 已根据 `08-writing/experiment-plan-v0.1-20260707.md` 建立案例清单和数据 schema；下一步构造小样例与模拟器。
2. 保留 APTChaser、GAPT 正文获取待办；APT-ATT 已于 2026-07-07 获取并精读，TAA-EPLMR 已于 2026-07-08 完成新主线复核。
3. 继续中文专利侧与证据采集/取证规划相关检索。
4. 把 POIROT/DeepHunter/MEGR-APT/CLIProv/APT-CGLP/TAA-EPLMR 写入相关工作和 baseline 设计。
5. 在 experiment plan 后续验证通过后，再判断是否重写专利 `v0.3`。

注：US12530469 权利要求原文补读已按用户决策从当前 workflow 剔除；该材料仅作为摘要级专利红线保留。
