# AttacKG+: Boosting Attack Knowledge Graph Construction with Large Language Models

## 1. 基本信息

- 英文题名：AttacKG+: Boosting Attack Knowledge Graph Construction with Large Language Models
- 中文译名：AttacKG+：使用大语言模型增强攻击知识图谱构建
- 作者：Yongheng Zhang; Tingwen Du; Yunshan Ma; Xiang Wang; Yi Xie; Guozheng Yang; Yuliang Lu; Ee-Chien Chang
- 年份：2024
- Venue：arXiv preprint；本地 PDF 显示 Computers & Security 相关版本待核验
- DOI / arXiv / URL：https://arxiv.org/abs/2405.04753
- 本地 PDF：`../07-zotero-exports/pdfs_20260705/AttacKG_plus_2024.pdf`
- 本地文本：`../07-zotero-exports/pdf_text_20260705/AttacKG_plus_2024.txt`
- 阅读日期：2026-07-05
- 阅读优先级：重点
- 所属主题：Attack Knowledge Graph / LLM-CTI / ATT&CK Technique Identification / Evidence Structuring

## 2. 一句话总结

AttacKG+ 用 LLM 把 CTI 文本转成多层攻击知识图谱：behavior graph、MITRE TTP labels、state summary；它把“LLM 构建攻击图”这条路线推进得很实，因此 Project05 不能再把“用 LLM 从 CTI 构图”作为主创新，只能把它作为上游证据结构化模块。

## 3. 研究问题

- 论文要解决什么？
  - 传统 CTI attack KG construction 泛化能力有限，难以识别新型实体、关系和攻击场景。
  - 传统模型需要专家设计 ontology、规则、NLP pipeline 或 graph matching threshold。
  - 作者希望用 LLM 的语义理解和 zero-shot 能力自动构建 attack knowledge graph。
- 为什么重要？
  - CTI 报告是自然语言，直接读报告难以做攻击链重构和 TTP 分析。
  - attack graph 是后续归因、狩猎、检测和安全分析的基础表示。
- 和 Project05 的关系是什么？
  - 它提供了 CTI 文本侧 evidence unit 的强基线。
  - Project05 可以复用其三层表示，但不能把构图本身当创新。

## 4. 核心贡献

1. 提出全自动 LLM-based AttacKG+ 框架。
2. 四个模块：
   - Rewriter；
   - Parser；
   - Identifier；
   - Summarizer。
3. 升级 attack knowledge schema，把一次 cyber attack 表示为 temporally unfolding event。
4. 每个 temporal step 包含：
   - behavior graph；
   - MITRE TTP labels；
   - state summary。
5. 构建两个数据集：
   - Re-CTI；
   - CTI-TE。
6. 在实体、关系和 technique identification 上显著优于 EXTRACTOR / AttacKG。

## 5. 方法框架

### 输入

- CTI report text；
- MITRE ATT&CK tactic / technique templates；
- entity and relation type prompts。

### 输出

- threat behavior graph：
  - subject-action-object triplets；
  - entity-entity relations；
  - temporal relations；
- ATT&CK tactic / technique labels；
- stage state summary。

### 方法流程

```text
CTI report
  -> Rewriter: filter background and split tactic stages
  -> Parser: extract entities, actions, relations
  -> Identifier: match behavior to ATT&CK technique templates
  -> Summarizer: generate state summary per stage
  -> AttacKG+ multilayer attack graph
```

## 6. 数据集与实验

- 数据来源：
  - 500 篇真实 CTI reports；
  - 来源包括 Cisco Talos、Microsoft Security Intelligence Center 等。
- 评估标注：
  - 15 篇 APT activity reports 手工标注 entities、relations、techniques。
- 对比：
  - EXTRACTOR：实体/关系抽取；
  - AttacKG：technique identification。
- 指标：
  - Precision；
  - Recall；
  - F1。

### 主要结果

| 任务 | 对比方法 F1 | AttacKG+ F1 |
|---|---:|---:|
| Entity extraction | EXTRACTOR 0.039 | 0.698 |
| Relation extraction | EXTRACTOR 0.301 | 0.623 |
| Technique identification | AttacKG 0.258 | 0.566 |

AttacKG+ technique identification 的 precision 0.545，recall 0.588，F1 0.566。作者指出 AttacKG 会产生较多 false positives，平均每篇约 14.4 个，而 AttacKG+ 更稳定。

## 7. 局限

- 只处理文本输入，没有处理 CTI 图像、流程图、表格、截图等多模态信息。
- 依赖 prompt 和商业 LLM，对要求理解不稳定。
- evaluation 手工标注样本只有 15 篇。
- 输出是 attack graph / TTP / summary，不做 actor attribution。
- 不做证据充分性、置信度、拒答和 unknown actor 判断。
- state summary 是语义摘要，不等同于可审计归因解释。

## 8. 对 Project05 的影响

### 撞掉的方向

- “用 LLM 自动构建 CTI attack graph”已经被 AttacKG+ 基本覆盖。
- “CTI report -> behavior graph -> ATT&CK labels”也已经成熟。

### 留下的空间

1. 把 AttacKG+ 产物作为 evidence unit，而不是最终贡献。
2. 将 behavior graph / TTP / state summary 进一步提升到 intent / actor hypothesis。
3. 引入 evidence sufficiency：哪些 graph/TTP 足以支撑 actor-level attribution？
4. 与日志侧 provenance graph 对齐，这是 AttacKG+ 没有覆盖的。
5. 将 graph evidence 绑定到 refusal / confidence calibration。

## 9. 可转化的选题问题

> 在 AttacKG+ 已经能从 CTI 文本构建攻击图后，如何判断这些攻击图证据是否足以支持更高层的 intent / actor attribution，并在证据不足时拒绝归因？

## 10. 相关工作位置

| 相关文献 | 关系 |
|---|---|
| AttacKG | AttacKG 是原始 graph alignment/TTP identification 路线 |
| EXTRACTOR | AttacKG+ 在实体和关系抽取上显著超过 EXTRACTOR |
| TechniqueRAG | TechniqueRAG 更专注 ATT&CK annotation，AttacKG+ 更专注 graph construction |
| MM-AttacKG | MM-AttacKG 是 AttacKG+ 的多模态扩展 |
| Project05 | AttacKG+ 可作为 CTI 文本侧结构化证据模块 |

