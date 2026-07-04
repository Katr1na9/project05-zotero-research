# Zotero 文献管理 SOP

## 目标

让 Zotero 成为论文阅读、批注、翻译、笔记和引用管理的中心，而不是只保存链接。

## 集合规范

主集合：

`Threat Attribution + LLM Agents Literature`

建议子集合：

- `00-Reading Queue`
- `01-Core Papers`
- `02-LLM-CTI`
- `03-Agentic SOC`
- `04-Attack Chain and Provenance`
- `05-ATTACK-KG-RAG`
- `06-Trustworthy Attribution`
- `99-Archive`

## 标签规范

基础标签：

- `threat-attribution`
- `cyber-threat-intelligence`
- `llm`
- `agent`
- `knowledge-graph`
- `attack-chain`
- `intent-recognition`
- `explainable-security`

阅读状态标签：

- `todo-read`
- `reading`
- `read-done`
- `must-read`
- `method-baseline`
- `dataset`
- `writing-citable`

## 导入规范

1. 优先导入带 DOI 的正式出版记录。
2. arXiv 预印本使用 report/preprint 类型，避免伪装成 journal article。
3. PDF 应作为 Zotero 条目附件导入，导入后可在 Zotero Reader 中批注。
4. 导入后检查：
   - 标题是否正确；
   - 作者是否完整；
   - 年份是否正确；
   - DOI 是否真实；
   - PDF 是否挂在条目下；
   - 是否重复。

## PDF 规范

- 优先使用官方开放 PDF、arXiv、USENIX、作者主页、机构仓储。
- 不绕过付费墙。
- Zotero 中如显示为外部链接附件，执行：

`工具 -> 管理附件 -> 转换链接文件为存储文件`

## 阅读后处理

每读完一篇论文：

1. 在 Zotero PDF 中完成重点高亮。
2. 写 Zotero note：一句话贡献、方法流程、可借鉴点。
3. 在 `02-literature-notes/` 中用精读模板写 Markdown 笔记。
4. 如果产生选题想法，追加到 `03-ideas/research-ideas.md`。
5. 如果发现术语或方法可复用，追加到术语表或复利日志。

