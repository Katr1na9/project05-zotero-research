# Project05 Zotero Research Workspace

本目录用于集中管理 Project05 的 Zotero 文献、精读笔记、撞题扫描、研究想法、专利草稿和实验设计。

## 研究线布局

Project05 现在按“共享工作区 + 独立论文线”管理，入口见 [Research Lines](10-research-lines/README.md)。

| 研究线 | 核心内容 | 当前状态 |
|---|---|---|
| [P05-L1](10-research-lines/01-incomplete-evidence-investigation-control/) | 不完整证据下、信息边界约束的 APT 调查控制 | 论文 v0.5；C11 已作为独立外部效度压力并入 |
| [P05-L2](10-research-lines/02-multimodal-threat-attribution/) | IPv4/IPv6/MPLS/Geo/SCION 异构路径下的行为追溯与意图感知，暂定 | Stage 1；初筛完成，W1 amber，P0 精读待进行 |

共享 SOP、单篇精读、模板和 Zotero 导出继续使用根目录的稳定路径，所有权规则见 [Shared Workspace](10-research-lines/00-shared-workspace/README.md)。

## P05-L1 既有论文线

截至 2026-07-13，已完成 C07-C10 四个 G3 主案例、AFA/敏感性实验、Reviewer major revision，以及 C11 第三种数据封装的独立 G2 外部效度评估。当前主线为：

> 不完整证据下、信息边界约束的 APT 调查控制。

项目不直接提出新的 actor attribution 分类器，也不把 M3a、XGBoost、AFA 或 DQN 写成新 SOTA。当前贡献是把部分对齐转化为可更新证据缺口状态，在规划器不可读取动作实际恢复集合的条件下完成采集、反馈、STOP 和结论粒度截断。

该主线把“CTI 侧攻击行为图与本地日志 / provenance / IOC / 样本证据的对齐结果”作为证据状态，进一步解决：

- 当前证据最多能支撑到哪一层调查结论；
- 哪些证据缺口阻止归因粒度继续提升；
- 在成本约束下，下一步最值得获取哪类证据；
- 何时停止取证并输出粒度受控的结论或降级原因。

当前权威文档和实验入口见：[AUTHORITATIVE-DOCUMENTS-20260713.md](08-writing/AUTHORITATIVE-DOCUMENTS-20260713.md)。论文母本为：[paper-main-draft-v0.5-c11-external-validity-20260713.md](08-writing/paper-main-draft-v0.5-c11-external-validity-20260713.md)。

当前 G1 通过版 RQ 见：[topic-rq-brief-v2.1-g1-final-20260706.md](03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md)

本轮重扫报告见：[project-rescan-increment-20260706.md](04-progress/project-rescan-increment-20260706.md)

## 使用原则

- 当前 workflow 见：[project05-skill-driven-workflow-v2.md](01-sop/project05-skill-driven-workflow-v2.md)
- 多研究线治理见：[project05-multi-line-workspace-sop-v0.1.md](01-sop/project05-multi-line-workspace-sop-v0.1.md)
- 研究线总入口见：[10-research-lines/README.md](10-research-lines/README.md)
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
- `10-research-lines/`: 共享资产治理、既有论文线入口和多模态新论文线。

## 当前下一步

1. P05-L2：按 [reading queue](10-research-lines/02-multimodal-threat-attribution/02-literature-notes/reading-queue.md) 精读 P0 五篇，验证 W1 能否区别于 SecTracer、Forensic Coverage、ID-INT 和 P4Prime。G1 前不选模型、不写论文。
2. P05-L1：C07-C11 v0.2 双人盲标包仍为 `awaiting_annotations`。27/27 Claim 来源摘录已就绪，下一步是确认两名独立标注者并启动三任务盲标。
3. P05-L1：C11 的 D1-D5 已完成；外部效度应优先增加自然发生或更接近运营现场的独立 engagement。
4. P05-L1：根据目标 venue 决定是否补官方 AFA 实现；专利继续完成权属、公开日和代理师审查。

## P05-L1 当前红线

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
