# Project05 Zotero Research Workspace

本目录用于集中管理 Project05 的 Zotero 文献、精读笔记、撞题扫描、研究想法、专利草稿和实验设计。

## 当前主线

截至 2026-07-06，全项目重扫后，当前推荐主线为：

> 面向 APT 归因的对齐感知证据状态建模与主动取证规划。

旧主线“证据不完整场景下的 APT 归因粒度门控、可拒答解释与缺失证据生成”已经被降级为模块，不再单独作为主创新。原因是它更像给已有归因系统增加保护层，贡献强度不足。

新的主线把“CTI 侧攻击行为图与本地日志 / provenance / IOC / 样本证据的对齐结果”作为证据状态，进一步解决：

- 当前证据最多能支撑到 technique、intent、campaign、actor 哪一层归因粒度；
- 哪些证据缺口阻止归因粒度继续提升；
- 在成本约束下，下一步最值得获取哪类证据；
- 何时停止取证并输出粒度受控的归因结论。

当前 G1 通过版 RQ 见：[topic-rq-brief-v2.1-g1-final-20260706.md](03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md)

本轮重扫报告见：[project-rescan-increment-20260706.md](04-progress/project-rescan-increment-20260706.md)

## 使用原则

- 当前 workflow 见：[project05-skill-driven-workflow-v2.md](01-sop/project05-skill-driven-workflow-v2.md)
- 项目总览和当前任务见：[research-dashboard.md](00-dashboard/research-dashboard.md)
- 每篇论文使用：[paper-intensive-reading-template.md](06-templates/paper-intensive-reading-template.md)
- 周进展写入：[research-progress.md](04-progress/research-progress.md)
- 可复用经验写入：[compound-learning-log.md](05-logs/compound-learning-log.md)
- 踩坑和配置问题写入：[pitfall-log.md](05-logs/pitfall-log.md)
- Zotero 导出文件、RIS、BibTeX、PDF 导入包放入 `07-zotero-exports/`

## 目录结构

- `00-dashboard/`: 项目总览、当前任务、关键决策。
- `01-sop/`: 固定流程，包括文献检索、Zotero 管理、论文精读、选题推进。
- `02-literature-notes/`: 单篇论文精读笔记、专利红线和高风险相关工作记录。
- `03-ideas/`: 科研灵感、问题意识、可行选题池、RQ brief。
- `04-progress/`: 周进展、撞题扫描、待办、阻塞、阶段状态。
- `05-logs/`: 复利日志、踩坑日志、决策记录。
- `06-templates/`: 可复用模板。
- `07-zotero-exports/`: Zotero/RIS/BibTeX/PDF 导入包。
- `08-writing/`: 开题报告、综述、论文草稿、专利草稿、实验设计。

## 当前下一步

1. 已完成 `08-writing/experiment-plan-v0.1-20260707.md`，下一步进入案例清单和数据 schema。
2. CLIProv、APT-CGLP、APT-ATT 已升级为全文精读；TAA-EPLMR 已完成新主线复核，继续保留 APTChaser、GAPT 正文获取待办。
3. 设计 `evidence_claim / alignment_state / acquisition_action` 三个 schema。
4. 根据最小可行实验结果判断是否重写专利 `v0.3`，不要继续扩写旧的 `v0.2`。

## 当前红线

以下方向不能再作为 Project05 的宽泛主创新：

- 多源证据融合 APT 归因；
- LLM-based APT attribution framework；
- KG/RAG/GraphRAG 辅助归因；
- CTI 图 / provenance graph 对齐或威胁狩猎匹配；
- TTP 相似度或技术画像驱动 actor ranking；
- 单独的 confidence score、information gap、hunting recommendation；
- 单独的归因粒度门控、拒答解释、缺失证据 list。

更安全的表述是：

> 将 CTI-local evidence alignment 的输出建模为部分可观测证据状态，在归因粒度收益与取证成本约束下进行主动证据获取规划。
