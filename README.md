# Project05 Zotero Research Workspace

本目录用于集中管理 Project05 的 Zotero 文献、精读笔记、撞题扫描、研究想法、专利草稿和实验设计。

## 当前主线

截至 2026-07-11，完成四案例、AFA/敏感性实验和 Reviewer major revision 后，当前主线为：

> 不完整证据下、信息边界约束的 APT 调查控制。

项目不直接提出新的 actor attribution 分类器，也不把 M3a、XGBoost、AFA 或 DQN 写成新 SOTA。当前贡献是把部分对齐转化为可更新证据缺口状态，在规划器不可读取动作实际恢复集合的条件下完成采集、反馈、STOP 和结论粒度截断。

该主线把“CTI 侧攻击行为图与本地日志 / provenance / IOC / 样本证据的对齐结果”作为证据状态，进一步解决：

- 当前证据最多能支撑到哪一层调查结论；
- 哪些证据缺口阻止归因粒度继续提升；
- 在成本约束下，下一步最值得获取哪类证据；
- 何时停止取证并输出粒度受控的结论或降级原因。

当前权威文档和实验入口见：[AUTHORITATIVE-DOCUMENTS-20260711.md](08-writing/AUTHORITATIVE-DOCUMENTS-20260711.md)。论文母本为：[paper-main-draft-v0.4-major-revision-20260711.md](08-writing/paper-main-draft-v0.4-major-revision-20260711.md)。

当前 G1 通过版 RQ 见：[topic-rq-brief-v2.1-g1-final-20260706.md](03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md)

本轮重扫报告见：[project-rescan-increment-20260706.md](04-progress/project-rescan-increment-20260706.md)

## 使用原则

- 当前 workflow 见：[project05-skill-driven-workflow-v2.md](01-sop/project05-skill-driven-workflow-v2.md)
- Project05 学习路线见：[project05-ml-learning-roadmap.md](01-sop/project05-ml-learning-roadmap.md)
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
- `09-experiments/`: 实验 schema、配置、脚本和后续小样例。

## 当前下一步

1. 完成双人盲标和粒度校准；当前模板仍为 `awaiting_annotations`，不得以模型标签代替人工结果。
2. 根据目标 venue 决定是否补官方 AFA 实现；现有 Myopic/Rollout-H3 只是同接口领域适配。
3. 增加第三数据家族或更多独立 engagement，优先引入多 claim 证据组合。
4. 专利以 `patent-main-draft-v0.4-20260711.md` 为母本，完成中文补检、权属、公开日和代理师审查。

## 当前红线

以下方向不能再作为 Project05 的宽泛主创新：

- 多源证据融合 APT 归因；
- LLM-based APT attribution framework；
- KG/RAG/GraphRAG 辅助归因；
- CTI 图 / provenance graph 对齐或威胁狩猎匹配；
- TTP 相似度或技术画像驱动 actor ranking；
- 单独的 confidence score、information gap、hunting recommendation；
- 单独的归因粒度门控、拒答解释、缺失证据 list。

当前安全表述是：

> 将 CTI-local evidence alignment 的输出建模为受信息边界约束的证据缺口状态，在成本、通道反馈和可支撑结论粒度下执行可审计的调查控制。
