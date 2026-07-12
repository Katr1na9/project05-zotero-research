# Project05 Workspace Decision Log

## 2026-07-12：采用共享区与独立论文线结构

- 决策：注册 P05-L1 和 P05-L2，并建立 `10-research-lines/` 总入口。
- 共享资产：根目录 `01-sop/`、`02-literature-notes/`、`06-templates/`、`07-zotero-exports/` 和 `docs/`。
- P05-L1：现有文件保持原位，通过 `01-incomplete-evidence-investigation-control/` 建立权威映射。
- P05-L2：在 `02-multimodal-threat-attribution/` 建立独立 `00-09` 工作区。
- 原因：物理搬迁会同时影响大量相对链接、脚本根路径、预注册 SHA-256 和 Git 历史；当前先完成职责隔离。
- 复审条件：只有路径审计、自动重写、哈希保护和全量测试均通过，才考虑移动 P05-L1。
