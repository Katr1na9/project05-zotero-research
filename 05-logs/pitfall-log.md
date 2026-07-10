# 踩坑日志：科研版

## 目的

记录所有浪费过时间的问题，避免重复踩坑。

## 记录格式

### YYYY-MM-DD：问题标题

- 场景：
- 表现：
- 原因：
- 解决：
- 预防：
- 影响：

## 初始记录

### 2026-07-10：从 recoverable 抄 intended 造成答案键

- 场景：为 M3a 增加公开 `intended_cti_node_ids`。
- 表现：通道在线时 M3a 近乎 Oracle；`intended` 与 `OR(recoverable)` 节点集完全一致（C01–C06）。
- 原因：编译时用隐藏恢复集合反推公开意图；通道门控只覆盖离线 seed。
- 解决：P0-#1 通道门控 + `intended≠OR` 标注规范与 CI；C07 过宽意图合规；C01–C06 暂列 allowlist。
- 预防：禁止脚本从 `recoverable_claim_ids` 生成 `intended`；新案例必须过 `test_intended_not_recoverable_or`。
- 影响：高——直接威胁“表示假设”实验的可辩护性。

### 2026-06-30：Zotero 翻译源 CNKI 证书错误

- 场景：Zotero Reader 中选中文本，Translate for Zotero 调用 CNKI 翻译。
- 表现：`SSL_ERROR_BAD_CERT_DOMAIN`，无法翻译。
- 原因：CNKI/dict.cnki.net 安全连接证书问题，不是 PDF 或 Zotero 本体损坏。
- 解决：将翻译源切换为 Bing，并开启自动划词翻译与弹窗。
- 预防：后续优先使用 GPT/Gemini/DeepL，并配置网络安全术语 prompt。
- 影响：通用翻译术语质量仍可能不稳定。

### 2026-06-30：RIS 导入 Zotero 只生成链接而非 PDF 附件

- 场景：导入 RIS/BibTeX 后，Zotero 条目只有 URL，需要手动找 PDF。
- 表现：不能直接在 Zotero Reader 中批注。
- 原因：普通 RIS 只包含元数据和 URL，不包含本地 PDF 附件字段。
- 解决：生成带 `L1 - file:///...pdf` 的 RIS，并下载公开可获取 PDF。
- 预防：以后导入前优先生成 `with_PDF` RIS。
- 影响：付费墙或无开放 PDF 的论文仍需手动获取。

