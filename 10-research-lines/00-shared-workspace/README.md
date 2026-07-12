# Project05 Shared Workspace

本目录定义跨论文线共享资产的唯一来源。它是治理入口，不复制根目录中的既有文件。

## Canonical Assets

| 资产 | 唯一物理目录 | 使用规则 |
|---|---|---|
| 通用科研 SOP | [`../../01-sop/`](../../01-sop/) | 所有研究线继承；线内只写差异化补充 |
| 单篇论文精读 | [`../../02-literature-notes/`](../../02-literature-notes/) | 一篇论文只保留一份事实型精读笔记 |
| 通用模板 | [`../../06-templates/`](../../06-templates/) | 精读、选题、周进展等可复用模板 |
| Zotero 导出 | [`../../07-zotero-exports/`](../../07-zotero-exports/) | 统一去重；线内可维护自己的候选清单 |
| 图示与辅助文档 | [`../../docs/`](../../docs/) | 只有跨线可复用内容进入此处 |

## Shared Versus Line-Specific

共享区保存可重复使用的事实和方法；研究线保存该论文的判断和论证。

- 共享：论文元数据、精读事实、通用术语、通用 SOP、模板。
- 线内：研究问题、WHY/HOW/WHAT 综合、撞题判断、方法假设、数据方案、实验、草稿、审稿意见。

同一材料若同时服务两条论文线，应在共享笔记中保持事实中立，再由各研究线分别写“与本线的关系”，不得复制并形成两个漂移版本。

详细所有权矩阵见 [`ASSET-OWNERSHIP.md`](ASSET-OWNERSHIP.md)。

## 工作区级记忆

- [`decision-log.md`](decision-log.md)：研究线注册、迁移和共享边界决策；
- [`compound-learning-log.md`](compound-learning-log.md)：跨论文线可复用的组织经验；
- [`pitfall-log.md`](pitfall-log.md)：目录、引用、哈希和版本治理踩坑。
