# Project05 Research Lines

本目录是 Project05 的多论文线总入口。它负责研究线注册、共享资产边界和阶段状态，不复制已有论文、实验或文献文件。

机器可读状态见 [`workspace-manifest.json`](workspace-manifest.json)。

## 当前研究线

| ID | 工作名称 | 目录 | 当前阶段 | 权威状态 |
|---|---|---|---|---|
| P05-L1 | 不完整证据下、信息边界约束的 APT 调查控制 | [`01-incomplete-evidence-investigation-control/`](01-incomplete-evidence-investigation-control/) | 论文 v0.4；C11 与盲标 v0.2 已完成工程准备 | 既有论文线 |
| P05-L2 | 多模态威胁归因与调查，暂定名 | [`02-multimodal-threat-attribution/`](02-multimodal-threat-attribution/) | ARS Stage 0 Inbox；RQ 未冻结 | 新论文线 |

## 共享工作区

共享资产入口见 [`00-shared-workspace/`](00-shared-workspace/)。为保持既有路径、引用、Zotero 导出和实验哈希稳定，共享资产的物理目录暂时保留在仓库根部：

- `01-sop/`：跨研究线 SOP；
- `02-literature-notes/`：单篇精读笔记的唯一来源；
- `06-templates/`：通用模板；
- `07-zotero-exports/`：Zotero/RIS/BibTeX/PDF 导入记录；
- `docs/`：跨研究线图示和辅助文档。

## 文件归属规则

1. 单篇论文的事实型精读笔记只保留一份，写入共享 `02-literature-notes/`。
2. 某条论文线的主题综合、撞题矩阵、RQ、实验、草稿和审稿记录写入该研究线目录。
3. 可复用 SOP 和模板进入共享区；只服务一条论文线的流程留在线内。
4. 每条研究线必须有独立 Dashboard、Idea Inbox、Progress、Logs、Writing、Experiments 和 Material Passport。
5. 新论文线未通过 RQ Gate 前，不创建方法主张、实验结果或论文正文。

## 迁移策略

当前采用兼容迁移：建立清晰的所有权和入口，但不批量移动既有 517 个文件。原因是既有实验脚本、预注册 SHA-256、Markdown 相对链接和 Git 历史依赖当前路径。后续只有在路径审计、链接重写和全量测试均可通过时，才考虑物理迁移 P05-L1。
