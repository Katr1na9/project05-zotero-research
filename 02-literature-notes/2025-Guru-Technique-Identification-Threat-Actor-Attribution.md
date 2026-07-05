# On Technique Identification and Threat-Actor Attribution using LLMs and Embedding Models

## 1. 基本信息

- 英文题名：On Technique Identification and Threat-Actor Attribution using LLMs and Embedding Models
- 中文译名：使用大语言模型与嵌入模型进行技术识别和威胁行为体归因
- 作者：Kyla Guru; Robert J. Moss; Mykel J. Kochenderfer
- 年份：2025
- Venue：arXiv preprint
- DOI / arXiv / URL：https://arxiv.org/abs/2505.11547
- 代码：https://github.com/kylag/ttp_attribution
- 本地 PDF：`../07-zotero-exports/pdfs_20260705/Guru_2025_Technique_Identification_Threat_Actor_Attribution.pdf`
- 本地文本：`../07-zotero-exports/pdf_text_20260705/Guru_2025_Technique_Identification_Threat_Actor_Attribution.txt`
- 阅读日期：2026-07-05
- 阅读优先级：必读
- 所属主题：LLM-CTI / TTP Identification / Threat Actor Attribution / Embedding Model / Baseline

## 2. 一句话总结

这篇论文做了一个从原始 CTI 文档到 TTP，再到 threat actor ranking 的端到端 proof-of-concept；结论很克制：GPT-4 和 embedding search 生成的 TTP 与 MITRE 人工标注差异很大、噪声明显，但仍能训练出优于随机基线的 attribution ranking，因此 LLM 更适合作为辅助决策工具，而不是自动归因系统。

## 3. 研究问题

- 论文要解决什么？
  - 自动从 CTI/forensic documentation 中抽取 threat actor 的 TTP。
  - 用抽取出的 TTP profile 对新的攻击文档进行 threat actor attribution。
- 为什么重要？
  - 手工从密集报告中抽取行为指标很慢，重大事件后会造成归因延迟。
  - 对国家级事件，归因延迟会影响外交和地缘政治响应。
- 和 Project05 的关系是什么？
  - 它是最直接的“CTI 文档 -> TTP -> actor”的 LLM/embedding baseline。
  - 它证明 TTP-only attribution 可做，但不够可靠。
  - 它支撑 Project05 不应只做 TTP 抽取或 TTP profile 匹配。

## 4. 核心贡献

1. 评估 off-the-shelf GPT-4 做 TTP extraction 的效果。
2. 评估 text-embedding-3-large 做基于向量相似度的 TTP identification。
3. 构建从 raw CTI documents 到 threat actor prediction 的端到端 pipeline。
4. 用 MITRE ATT&CK Groups 中 human-generated TTPs 作为 proxy ground truth。
5. 证明自动 TTP profile 虽然噪声高，但仍能产生 above-baseline actor ranking。

## 5. 方法框架

### 任务 1：TTP Identification

两条路线：

1. GPT-4 prompt：
   - 输入 actor 相关报告；
   - 要求输出 MITRE ATT&CK technique / sub-technique ID。
2. Vector embedding search：
   - 对 MITRE technique description 预先 embedding；
   - 对 CTI 文档每 3 行做 embedding；
   - 用 cosine similarity 取 top TTP。

### 任务 2：Threat Actor Attribution

- 为每个 actor 构建 TTP count / weight matrix；
- 对新文档抽取 TTP；
- 用 dot product / ranking 得到候选 actor；
- 输出 top-r ranked threat actors。

### 方法流程

```text
MITRE actor references / CTI docs
  -> GPT-4 or vector embedding TTP extraction
  -> actor-TTP profile matrix
  -> new document TTP extraction
  -> ranked actor attribution
```

## 6. 数据集与实验

- 数据来源：
  - MITRE ATT&CK Groups 页面；
  - 每个 group 的 cited references / raw post-incident reports；
  - MITRE 对 actor 的 TTP 标注作为 human-generated proxy ground truth。
- LLM：
  - GPT-4。
- Embedding：
  - OpenAI text-embedding-3-large。
- 主要评价：
  - TTP Jaccard similarity；
  - set difference；
  - actor attribution average rank；
  - random baseline：29 个 actor 时平均 rank 约 15。

### 主要结果

- GPT-4 TTP vs MITRE：
  - 平均 Jaccard similarity 约 0.39 +/- 0.12。
- Vector embedding TTP vs MITRE：
  - 平均 Jaccard similarity 约 0.18 +/- 0.0739。
- GPT-4 漏掉 MITRE TTP：
  - 平均约 41%。
- GPT-4 额外生成 MITRE 未标注 TTP：
  - general case 约 66%；
  - 加 sub-technique 后约 76%。
- VE 漏掉 MITRE TTP：
  - 平均约 42%。
- VE 额外生成 TTP：
  - 平均约 77%。
- GPT-4 生成不存在于 MITRE taxonomy 的 hallucinated TTP：
  - 约 0.76%，共 46 个 case。
- Attribution：
  - random baseline 平均 rank 约 15/29；
  - uniform prior 下平均 rank 约 10.96 或 10.68；
  - 加 expert prior 后最佳平均 rank 约 7.55。

## 7. 关键发现

- GPT-4 生成的 TTP 与 MITRE 人工标注差异很大，但频率分布与 MITRE 有正相关。
- VE search 比 GPT-4 更透明，因为可以看到相似度排名，但自身也有大量噪声。
- 对 TTP profile 独特的 actor，attribution ranking 效果更好。
- 对 Lazarus、menuPass 这类 TTP 与其他 actor 高度重叠的 actor，归因更困难。
- 作者明确说：off-the-shelf models are not sufficient as an automated tool for high-stakes attribution。

## 8. 局限

- 依赖 MITRE actor page 和 references，ground truth 只是 proxy。
- 主要依赖 TTP，不融合 IOC、malware、infrastructure、provenance 等证据。
- 不做 evidence sufficiency 判断。
- 不做 confidence calibration 或 refusal。
- 不处理 unknown actor / false flag。
- 没有生成可审计的证据链，只是 actor ranking。

## 9. 对 Project05 的影响

### 撞掉的方向

- “用 LLM 从 CTI 抽 TTP，再根据 TTP 做 actor attribution”已经有人做了。
- “TTP profile + embedding ranking”不能作为主创新。

### 留下的空间

1. TTP 只是弱证据，不能直接升级为 actor attribution。
2. 需要把 TTP 与 IOC、sample、provenance、历史 actor profile 共同建模。
3. 需要评估 TTP overlap 下的 evidence sufficiency。
4. 需要在 actor 相似度高时输出低置信或拒答。
5. 需要解释“哪些 TTP 是区分性证据，哪些只是常见 TTP”。

## 10. 可转化的选题问题

> 当 TTP-only attribution 只能达到 moderate ranking 时，如何利用证据充分性、证据区分度和可拒答机制，避免 LLM 把高重叠 TTP 错误解释为强 actor 证据？

## 11. 相关工作位置

| 相关文献 | 关系 |
|---|---|
| TechniqueRAG / Multi-Step Pipeline | 它们做 TTP extraction 更系统；Guru 把 TTP 接到 actor ranking |
| AURA | AURA 比 Guru 更进一步，加入 RAG、agent 和 explanation |
| High Stakes | 支撑 TTP/高层 IOC 归因不充分 |
| APT-MMF | APT-MMF 使用更丰富的 report-IOC graph 做 closed-set actor classification |
| Project05 | 应把 Guru 作为 baseline，而不是创新点 |

