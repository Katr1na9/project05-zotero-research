# Project05 专利交付包 v0.4

日期：2026-07-11
状态：技术与格式审阅稿；发明人、权属、公开日和代理师审查未完成，不可直接提交。

## 文件

- `Project05_归因取证动作规划-权利要求书.docx`
- `Project05_归因取证动作规划-说明书.docx`
- `Project05_归因取证动作规划-说明书摘要.docx`
- `Project05_归因取证动作规划-摘要附图.docx`
- `Project05_归因取证动作规划-完整审阅稿.docx`
- `Project05_归因取证动作规划-完整审阅稿.pdf`
- `Project05_归因取证动作规划-figures/figure-1..5.{svg,png}`
- `Project05_归因取证动作规划-结构化草稿.json`

## 自动校验

- `validate_patent_draft.py`：PASS，0 error / 0 warning。
- `audit_claims.py`：仅保留权利要求10 `NO_REFERENCE` warning；该项是预期的第二独立权利要求（系统权利要求），不是从属引用缺失。
- 12 项权利要求编号连续；全部具有证据映射；独立权利要求不包含 LLM、DQN、XGBoost、DARPA 或 OpTC 限定。
- 摘要已压缩到 300 字门槛内。
- 五幅附图均通过节点、边、可达性、末端结果和附图说明校验。

## DOCX QA

- 已修复生成器默认 `w:zoom` 缺少 `w:percent` 的 OOXML 问题。
- 五个 DOCX 均通过 `python-docx` 打开，并逐个解析内部 XML/relationships。
- Office XML 验证器不再报告文档结构错误；其剩余 GBK 解码信息来自验证器在中文 Windows 上读取 UTF-8 XML 的本地编码缺陷。
- 已用 Microsoft Word 无界面导出 18 页 PDF，并生成 `qa-pages/contact-sheet.png` 做视觉检查。
- 权利要求、说明书、公式、摘要和摘要附图均可见；图1在独立页面可读。完整审阅稿中图2-5为紧凑总览，正式代理稿应优先使用 `figures/` 下的独立 SVG 分页插入。

## 提交前阻塞项

1. 确认发明人贡献、申请人和权属。
2. 确认 GitHub、论文、汇报或代码的首次公开日期。
3. 由中国专利代理师复核现有技术、单一性、支持性、清楚性和客体适格性。
4. 确认是否保留权利要求9的轻量非短视规划从属保护层。
5. 将图1-5按代理机构模板分页排版并复核图号/附图说明。
