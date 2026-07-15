# Project05 专利 DOCX 模板执行契约

## Reference

- 主参考：`C:\Users\35393\Desktop\浙大项目\年度报告\一种融合根源语义信息的高级持续性威胁检测与溯源方法-9-24-reviewed.docx`
- SHA-256：`D5D1E41421F973BDBCEE432A45C5CE0F5B7635BFCE4DE609200BEB10477ADBB1`
- Word 保存属性：16 页；167 个 document paragraphs；12,363 个去空白字符；9,794 个 CJK 字符；4 个 section；5 个 inline images；0 个 table。
- 佐证参考：`C:\Users\35393\Desktop\浙大项目\年度报告\一种基于系统溯源图的高级持续威胁检测与识别方法-完成版9-24-reviewed.docx`
- 佐证 SHA-256：`39385740D39856C9CB0E1E717E3A3CD9E9973FA70FA30722AF553E2759698082`
- 佐证 Word 保存属性：11 页；160 个 document paragraphs；11,591 个去空白字符；9,225 个 CJK 字符；4 个 section；6 个 inline images；0 个 table。
- 结构证据：`ref1/inspection.json`、`ref2/inspection.json`、`ref1/style.json`、`ref2/style.json`。
- 渲染证据：当前打包环境未找到 LibreOffice/soffice，标准渲染器在 DOCX→PDF 阶段返回 WinError 2；最终输出必须改用本机 Word 导出 PDF 后再做逐页视觉检查，或明确记录未完成视觉 QA。

## Page system

- A4 纵向，8.268 × 11.693 英寸。
- 四个 section 均从新页开始。
- 页边距：左 1.25 英寸，右 1.25 英寸，上 1.00 英寸，下 1.00 英寸。
- 页眉距 0.591 英寸，页脚距 0.689 英寸。
- 不启用首页不同或奇偶页不同。
- 四个 section 页眉分别为“摘要”“权利要求书”“说明书”“说明书附图”，左对齐、无页码字段；页脚为空。

## Typography

- Normal：中文东亚字体宋体，12 pt；西文默认 Calibri，但参考正文多数 run 直接设 Times New Roman；两端对齐。
- “论文正文”：基于 Normal；西文 Times New Roman，10.5 pt；首行缩进 24 pt；1.25 倍行距。参考稿仅在部分长段落使用，新的申请文本优先统一使用 Normal 以避免混用。
- 参考稿正文主要 direct formatting：中文承接宋体 12 pt，西文 Times New Roman，1.5 倍行距，正文首行缩进约 28 pt（约 2 个汉字）。
- 四个 section 正文首段标题“摘要”“权利要求书”“说明书”“说明书附图”居中、12 pt、1.5 倍行距。
- 说明书中的发明名称居中；“技术领域”“背景技术”“发明内容”“附图说明”“具体实施方式”使用 Normal、12 pt、1.5 倍行距、不缩进。参考未使用 Word Heading 样式，也无自动目录。
- 权利要求和说明书正文采用 1.5 倍行距；普通段落首行缩进约 28 pt。步骤行与章节标题不缩进或按参考段落角色设置。

## Lists, tables, and figures

- 参考没有表格；申请正文不使用审计表、证据矩阵或 Markdown 风格表格。
- 权利要求编号为正文中的真实数字文本 1–n，不使用自动目录；独立项内部步骤可用连续分号段落，必要时使用 S1、S2 等分步表达。
- 附图为 inline images，参考宽度约 5.75–5.77 英寸；不使用浮动环绕。
- 图名“图1”等居中置于对应图前或后，沿用参考结构；说明书“附图说明”逐行列出。

## Content flow

1. Section 1 摘要：居中“摘要” + 单段摘要，随后新页分节。
2. Section 2 权利要求书：居中“权利要求书” + 连续方法权利要求，随后新页分节。
3. Section 3 说明书：居中“说明书” + 居中发明名称 + 技术领域 + 背景技术 + 发明内容 + 附图说明 + 具体实施方式，随后新页分节。
4. Section 4 说明书附图：居中“说明书附图” + 图1–图N。

## Slot map

- Section 1 heading：保留“摘要”；摘要正文必须改写为 Project05 方法，不保留参考技术内容。
- Section 2 heading：保留“权利要求书”；全部权利要求替换为 v0.9 的 1 项独立方法权利要求和 10 项从属方法权利要求。
- Section 3 heading：保留“说明书”；发明名称和全部五个说明书模块替换为 Project05 内容。
- Section 4 heading：保留“说明书附图”；参考图片不得复制为本发明附图。只可插入 Project05 自有、与说明书一致的图。
- 页眉：按 section 替换为四个固定名称；页脚保持空白。
- 不把文件状态、提交红线、P/E/F/C 映射、实验审计表或作者待办放入申请正文；这些内容保留在独立研发附件。

## Package preservation

- 主参考不含 comments 部件、tracked insertions/deletions 或 Word fields，适合作为样式参考。
- 参考的 styles、theme、page geometry 和基本 header/footer pattern 为 preserve-derived。
- 参考正文、图片、媒体关系和旧发明名称不属于 preserve-only 内容，必须全部替换，不得带入交付文件。
- 不复制 ref1 的 comments.xml/commentsExtended.xml。
- 输出文件必须使用新文件名，主参考保持字节级不变并在最终核对时复算 SHA-256。

## Capacity and length target

- 两份参考的申请正文（不含空白）约 11,591–12,363 字符、9,225–9,794 个 CJK 字符。
- Project05 v0.9 当前申请核心为 8,588 个去空白字符、7,227 个 CJK 字符；其中权利要求约 2,059 个 CJK 字符、说明书约 4,597 个、摘要约 325 个，低于两份参考，不需要因“29 KB 文件大小”机械删减。
- 最终 DOCX 目标约 10–14 页；若附图另占页，可适当增加，但正文不加入研发审计附件。

## Fidelity gates

- 四个新页 section、A4 几何、四类页眉、空页脚必须与参考一致。
- 申请正文不得出现证据矩阵、提交红线、`all_experiments_complete`、Markdown heading 标记或内部路径。
- 权利要求仅为方法；独立项不得出现 LLM、DQN、XGBoost、DARPA、OpTC 或具体案例编号。
- 所有图片必须来自 Project05，不得残留参考专利图片。
- DOCX 生成后先做 section/style/image/field audits；再用 Word 导出 PDF并逐页检查无裁切、重叠、乱码、错误分页和旧内容残留。

## Final build record

- 最终文件：`08-writing/patent-package-v0.9-zju-reference/Project05_调查取证动作规划方法-浙大参考格式.docx`。
- 结构结果：4 个 section、11 项方法权利要求、5 幅 inline image、0 个 table、0 个 field、0 个 tracked change、0 个 comment part。
- 长度结果：6,966 个去空白可见字符，其中 6,324 个 CJK 汉字。
- 渲染结果：标准 LibreOffice 渲染器因本机缺少 soffice 返回 WinError 2；已改用 Microsoft Word 导出 PDF，并将 18 页全部栅格化后逐页检查通过。
