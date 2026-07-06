# Workflow Status Supplement - 2026-07-06

## 本轮完成

1. 重新核查 APTChaser。
   - Springer 页面确认题名、作者、页码、DOI 和摘要。
   - 该章节为订阅内容，本轮下载到的本地文件实际是 HTML 错误页，不是可解析 PDF。
   - 已新增摘要级精读笔记：`02-literature-notes/2025-Zhang-APTChaser-Attack-Technique-Modeling.md`。

2. 重新核查 GAPT。
   - 目前只在 2026 APT knowledge graph correlation 论文参考文献中看到线索。
   - 未检索到可独立验证的 DOI、IEEE 页面或全文。
   - 已重写为“二级引用风险项”：`02-literature-notes/2024-Chen-GAPT-Temporal-Relation-Embeddings.md`。

3. 新增 MLDSJ。
   - 这是 2026 卷开放全文，直接研究 multi-level feature + DS evidence fusion + APT group attribution。
   - 已新增精读笔记：`02-literature-notes/2026-Duan-MLDSJ-Multi-Level-Feature-Joint-Attribution.md`。
   - 判断为红色风险项。

4. 新增撞题补充矩阵。
   - 文件：`04-progress/collision-matrix-supplement-20260706.md`。
   - 结论：Project05 必须从“多源证据融合归因”收缩到“证据充分性门控/归因粒度控制/可拒答解释”。

5. 新增 Zotero RIS 补充导入文件。
   - 文件：`07-zotero-exports/zotero-import-candidates-20260706-supplement.ris`。

## 当前未解决

- APT-ATT 正文仍未获得。
- APTChaser 正文仍未获得。
- GAPT 的独立存在性、DOI 与全文仍待验证。
- IEEE `A Multi-Source Feature Fusion-Based Knowledge Graph for APT Attribution` 需要继续找全文或至少补齐 DOI/会议元数据。

## 当前决策

不建议现在写宽题专利。

可以开始写的应是窄题 v0.2：

> 一种面向证据不完整与攻击者混淆场景的 APT 归因粒度门控与可拒答解释方法

独立权利要求应避免“多源证据融合模块”为核心，而应把输入表述为“来自既有归因模型、证据融合模型或安全分析系统的候选归因结果及证据画像”，核心限定在：

1. 证据充分性画像；
2. actor-specific distinctiveness；
3. long-tail / time drift / mimicry / missing-feature 风险检测；
4. 归因粒度门控；
5. 拒答或降级输出；
6. LLM 受控生成解释与缺失证据清单。
