# An Automated Attack Investigation Approach Leveraging Threat-Knowledge-Augmented Large Language Models

## 1. 基本信息

- 系统名：ANANKE（仓库/旧稿中亦见 Themis）
- 中文译名：基于威胁知识增强大语言模型的自动化攻击调查方法
- 作者：Rujie Dai et al.
- 年份：2025
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2509.01271
- Zotero key：NCKE7SCH（PDF：DFR5B4JB）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Knowledge-Augmented LLM / Provenance / Attack Investigation

## 2. 一句话总结

ANANKE 从历史标注攻击日志构建阶段化 Kill Chain 知识单元，再从 IDS 告警出发，让 LLM 检索知识并在审计 provenance 图上逐跳扩展恶意节点、生成报告。它已覆盖“知识层+事件图+LLM 链调查”，但仍是日志单源、强依赖完整日志与历史标签，缺少确定性验证、主张级 ID、意图和行为体归因。

## 3. 研究问题

- 如何在数日海量审计日志中从告警锚点提取攻击子图并重构多阶段链？
- 如何用历史攻击知识指导局部扩图以控制上下文和成本？

## 4. 核心贡献

1. 阶段化历史攻击序列知识库。
2. 平台中立 subject-action-object provenance 本体。
3. 一跳邻域检索、LLM 节点判断、可疑队列反馈与推理缓存。
4. 跨 Windows/Linux 的 15 场景评测。

## 5. 方法框架

```text
historical labeled attack logs
  -> LLM Kill Chain phase segmentation + behavior units
  -> Milvus knowledge base

target audit logs + IDS alert
  -> provenance graph
  -> one-hop ordered event sequence
  -> retrieve top threat unit
  -> LLM judges new malicious nodes / causal expansion
  -> feedback queue + reasoning cache
  -> attack report
```

- 知识层是阶段化序列/向量库，不是严格 KG。
- 事件层是审计 provenance 图；Socket/Website/IP 节点不代表独立 PCAP/flow 模态。
- `evidence_set` 出现在提示词中，但最终报告未强制稳定 event ID。

## 6. 数据集与实验

- 15 场景、4.3M+ 事件、7.2GB：10 个 ATLAS Windows、2 个 EternalBlue/Gamaredon、3 个 Linux DepImpact。
- 平均 TPR/FPR 97.1%/0.2%，ATLAS 对照 79.2%/29.1%。
- S1--S4 Balanced Accuracy 99.5%--100%；EB-P1/P2 为 90.3/94.8%；Linux 三场景为 89.5/98.3/95.8%。
- 平均调查 1.9 小时、247.6K tokens；S1--S4 完整系统约 1 小时、145K tokens。
- 指标主要是恶意事件 TPR/FPR，未验证链边、顺序、阶段或报告主张正确性。

## 7. 关键知识点

- 背景知识层与现场事件证据层应分离。
- 检索到相似历史 TTP 不等于当前事件真实发生，必须有独立证据验证。
- 节点分类准确率不能替代攻击链结构和报告忠实度评价。

## 8. 优点

- 局部扩图和推理缓存适合长日志调查。
- 阶段知识单元和平台中立本体可复用。
- 跨 Windows/Linux 验证并给出效率对比。

## 9. 局限

- 依赖完整、准确且防篡改日志，排除内核攻击。
- 背景库依赖已知恶意实体标签；主实验场景隔离协议不够清楚，可能有知识泄漏。
- LLM 同时做分类和因果裁决，无确定性物理验证。
- 无双源、原始证据 ID 契约、意图候选、行为体归因和校准。

## 10. 对我选题的启发

- ANANKE 应作为“单源 provenance + knowledge-RAG + LLM”强基线。
- 本课题必须加入流量/日志双源验证、知识/观测分层和 observed/derived/inferred 边。
- 实验需独立报告事件节点、链边、阶段、意图、证据忠实度和成本。

## 11. 可转化的研究问题

1. 双源对齐能否降低 LLM 单独裁决节点时的误扩图？
2. 如何让历史攻击知识只生成候选，而不污染现场事实层？
3. 从 Kill Chain 阶段如何上升到带证据和校准的攻击意图候选？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| HunterAgent | 同样知识增强补链，但后者有确定性验证和反取证威胁模型 |
| AttacKG / EXTRACTOR | 可提供 ATT&CK/行为知识层；ANANKE 使用历史日志序列知识 |
| PROVSEEK | 后者强调 node/edge ID 验证和负证据 |

## 13. 论文写作可引用句式

- 历史攻击知识可以提高 provenance 图的局部调查效率，但若缺少现场证据验证，知识相似性可能被误当成事件事实。

## 14. 我的批注与疑问

- 旧名 Themis 与 ANANKE 需在引用中说明版本关系。
- 论文中“same attack intent”只是分段提示，不是被评测的意图识别任务。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
