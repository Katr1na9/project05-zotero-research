# P05-L2 Multimodal Research Workflow v0.1

日期：2026-07-12

本流程继承 Project05 的 Gate、Zotero、精读、复利日志和可复现原则，并按 academic-research-suite 从宽 idea 推进到论文。

执行状态（2026-07-15）：用户授权先完成 Project03 审计、全量纳入精读和二次撞题检索，再提交候选题人工选择。当前 Stage 2/3 已完成，G2 通过、G3 条件通过；G1 仍等待用户从候选 A/B/C 中冻结单一 RQ。此顺序是本轮明确授权的 scope-reset 流程，不允许据此跳过用户决策后所需的 FINER/G1。

## Stage 0: Inbox

输入：原始 idea、潜在模态、已有论文线可复用资产。

产物：

- `03-ideas/idea-inbox.md`
- `03-ideas/rq-scoping.md`
- `08-writing/MATERIAL-PASSPORT.md`

禁止：提前指定模型、题名、SOTA 主张或实验结果。

## Stage 1: Socratic RQ Scoping

使用 `deep-research / socratic`。先回答任务、模态、数据、增益机制和评价终点，再形成 RQ Brief。

G1 必须同时满足：

1. 只有一个主要问题；
2. 输入和输出明确；
3. 多模态是解决机制，不是装饰；
4. 有现实可获得的数据路径；
5. FINER 平均至少 3/5，且无单项低于 2/5；
6. 明确与 P05-L1 的不同贡献。

## Stage 2: Deep Search

在 RQ 冻结后才建立检索式，覆盖：

- 多模态 CTI / threat attribution / incident investigation；
- 文本与图像的攻击知识图构建；
- 日志、网络、provenance 与 CTI 跨模态对齐；
- multimodal RAG / VLM / multimodal graph learning；
- 缺失模态、冲突模态、证据 grounding 和校准；
- 2025-2026 最新论文、预印本、benchmark 和专利。

G2：来源存在性核验、搜索日志完整、核心材料进入共享 Zotero/精读区。

## Stage 3: Synthesis And Collision

本线只保存主题综合，不复制单篇精读。固定输出：

- WHY/HOW/WHAT 矩阵；
- 模态—任务—数据—指标矩阵；
- 功能级撞题矩阵；
- 已覆盖红线与剩余白名单。

G3：至少保留一个不是“加模态/换模型”的可证伪研究缺口。

## Stage 4: Method And Experiment Blueprint

必须显式定义：

- 每种模态提供的独立信息；
- 配对、时间、实体和语义对齐条件；
- 缺失/冲突模态处理；
- 单模态和简单融合 baseline；
- modality ablation 与 leakage audit；
- 任务指标、evidence-grounding 指标和 calibration 指标。

G4/G5：数据可获取、baseline 可运行、指标可计算、失败条件已预注册。

## Stage 5-8: Pilot To Paper

1. 小样例预注册与可行性 pilot；
2. 参数锁定实验；
3. 主张—证据台账；
4. academic-paper 写作；
5. integrity、reviewer、ethics、devil's advocate；
6. 最多两轮修订，剩余问题进入 acknowledged limitations。

## 多模态专属红线

- 不把“VLM/多模态/Agent”写成创新本身；
- 不用同一事件的重复字段冒充独立模态证据；
- 不在训练/检索语料中泄漏 actor/campaign 标签；
- 不用报告图片中的文字 OCR 与正文文本形成伪多模态增益；
- 不忽略模态缺失率、时间错位和实体错配；
- 不只报告平均准确率，必须分析证据支撑与错误归因风险。
