# Project05 Multi-Line Workspace SOP v0.1

日期：2026-07-12

## 1. 目标

在同一 Project05 仓库中并行推进多篇论文，同时保持文献共享、论证隔离、实验可复现和 Git 历史连续。

## 2. 目录层级

- `10-research-lines/`：论文线注册和入口；
- `10-research-lines/00-shared-workspace/`：共享资产治理；
- `10-research-lines/01-incomplete-evidence-investigation-control/`：P05-L1 入口；
- `10-research-lines/02-multimodal-threat-attribution/`：P05-L2 独立工作区。

## 3. 新研究线创建规则

每条新线至少创建：

1. `00-dashboard/`：当前阶段、Gate、阻塞项；
2. `01-sop/`：该线的阶段化流程；
3. `02-literature-notes/`：只存线内综合，不复制共享精读；
4. `03-ideas/`：原始 idea、Socratic 记录、RQ Brief；
5. `04-progress/`：进度、检索日志、碰撞扫描；
6. `05-logs/`：复利、踩坑、决策；
7. `06-templates/`：共享模板入口和线内专用模板；
8. `07-zotero-exports/`：该线候选清单，正式元数据仍由共享区去重；
9. `08-writing/`：Material Passport、综合、草稿和审稿；
10. `09-experiments/`：预注册、数据、代码、结果和测试。

## 4. ARS Gate

| Stage | 必须产物 | Gate |
|---|---|---|
| 0 Inbox | 原始 idea、问题清单、Material Passport | 工作区完整 |
| 1 RQ Scoping | Socratic 记录、RQ Brief、FINER、边界 | G1 RQ 可回答 |
| 2 Deep Search | 检索协议、候选语料、来源验证 | G2 覆盖足够 |
| 3 Synthesis | WHY/HOW/WHAT、主题综合、撞题矩阵 | G3 仍有白名单 |
| 4 Method/Experiment | 方法蓝图、数据、baseline、指标 | G4/G5 可执行 |
| 5 Pilot | 预注册 pilot 与失败条件 | Pilot Gate |
| 6 Paper | 主张—证据台账、草稿 | Integrity Gate |
| 7 Review | 独立审稿、伦理和反方检查 | Revision Gate |
| 8 Finalize | 最终完整性、复现包 | Release Gate |

未过 Gate 不得用文件数量或模型复杂度代替研究进展。

## 5. 共享原则

- 事实型精读进入共享 `02-literature-notes/`；
- 论文线只保留本线的综合、判断和引用用途；
- 同一 DOI/RIS 条目只在共享 Zotero 导出中维护一个规范版本；
- 共享代码前先清除论文线答案键、私有路径和结论标签。

## 6. 版本与记忆

- 每条线独立维护 Material Passport、Dashboard、Progress 和三类日志；
- 重大边界变化必须写 Decision Log；
- 失败实验不得删除，必须写 Pitfall/Negative Result；
- 权威文件必须在该线 README 与 Dashboard 同时登记。

## 7. Git 规则

- 研究线使用目录隔离，不自动等同于 Git branch；
- 原始大数据、PDF、管理员 key、密钥和本地 trace 不入库；
- 大规模物理迁移前必须先做链接审计、哈希审计和全量测试；
- 每个可复现阶段形成独立 commit，提交信息包含研究线和阶段。
