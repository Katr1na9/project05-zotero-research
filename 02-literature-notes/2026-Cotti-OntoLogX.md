# OntoLogX: Ontology-Guided Knowledge Graph Extraction from Cybersecurity Logs with Large Language Models

## 1. 基本信息

- 中文译名：OntoLogX：基于本体引导和大语言模型的网络安全日志知识图谱抽取
- 作者：Luca Cotti; Idilio Drago; Anisa Rula; Devis Bianchini; Federico Cerutti
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2510.01409
- Zotero key：LY4IMACH（PDF：ZE85UFBV）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Log-to-KG / Ontology / ATT&CK Tactic Classification

## 2. 一句话总结

OntoLogX 通过混合检索、结构化生成和 SHACL 纠错，把每条异构日志转为本体合规的微型事件 KG，并用会话 KG 预测 ATT&CK tactics。它与本课题的日志侧图构建高度相关，但作者明确不连接各事件图，也没有 PCAP、统一跨源事件图、攻击链或意图候选。

## 3. 研究问题

- LLM 能否把异构日志稳定转换为 ontology-compliant KG？
- KG 中间表示能否改善会话级 ATT&CK tactic 分类？

## 4. 核心贡献

1. 以 `Event` 为中心的轻量本体，并映射 PROV-O/W3C Time。
2. Neo4j 向量+全文混合检索、MMR few-shot、结构化输出和最多 3 次 SHACL 纠错。
3. 多模型三元组/实体/关系质量评测。
4. 在真实 Cowrie 蜜罐会话上验证 tactic 分类。

## 5. 方法框架

```text
raw log + optional context
  -> hybrid retrieval + MMR
  -> LLM structured KG generation
  -> SHACL validation/correction
  -> persist micro-KG with source log
  -> aggregate session representations
  -> ATT&CK tactic classification
```

- 节点包括 Source、Timestamp、Application、Process、Command、NetworkAddress、File、User 等。
- 每个 KG 只表示一条日志事件；论文明确排除图间语义连接和完整攻击叙事。
- ontology 是 schema；ATT&CK 在下游是标签列表，不等于背景 KG。

## 6. 数据集与实验

- KG 实验：AIT RussellMitchell 候选日志，70 条异构样本；10 few-shot、10 validation、50 test。
- 蜜罐：两个 `/28` 网络，2025-08-04 至 08-14；1 示例、2 开发、161 测试会话，人工标注 6 tactics。
- Claude Sonnet 4：baseline F1 0.283，full retrieval 0.786；populated database 达成功率 1.000、SHACL 违规率 0.008、P/R/F1 0.845/0.820/0.832。
- Qwen3 Coder populated-database F1 0.762。
- 过高 G-Eval 可与低图 F1 同时出现，例如一配置 G-Eval 0.912、F1 0.460。

## 7. 关键知识点

- 本体合规、三元组正确和自然语言“看起来合理”必须分别评价。
- 单事件微图是统一证据图的构件，不是完整事件图。
- 单事件来源日志伴随存储可作为 provenance 起点，但 tactic 结论还需逐证据绑定。

## 8. 优点

- 日志到图的 schema、验证、纠错和质量指标较完整。
- 明确保存来源日志，支持单事件回查。
- 证明结构化中间表示对复杂 tactics 有帮助。

## 9. 局限

- 单源蜜罐，高攻击密度与企业环境差异明显。
- 图与图之间不连接，无法重构链。
- tactic 标注部分依赖标注者对行为目的的判断。
- 无流量侧、跨源实体解析、端到端证据路径、意图或行为体归因。

## 10. 对我选题的启发

- 可直接借鉴日志侧 ontology、SHACL 纠错和多层图质量指标。
- 需要新增 `Observation/Event/Entity/Claim/SourceAnchor` 分层及跨事件/跨源边。
- 将 HFish Session、Credential、URL、Command、File 与 PCAP flow/frame 对齐。

## 11. 可转化的研究问题

1. 如何把独立微图合并为保持来源与不确定性的统一事件图？
2. PCAP 流和日志事件的实体共指与时间连接如何验证？
3. tactic/intent 结论如何保存支持路径、反证路径和拒答条件？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AttacKG | CTI 文本到 technique KG；OntoLogX 是日志到微型事件 KG |
| EXTRACTOR | 报告到系统行为图；本课题可用共同中间表示衔接 |
| FuseChain | 后者直接构建跨源时间异构事件图并做阶段恢复 |

## 13. 论文写作可引用句式

- 本体约束和结构校验能够改善日志图抽取质量，但跨事件攻击链仍依赖显式实体解析和时序/因果连接。

## 14. 我的批注与疑问

- 论文所称配置数与附录表格存在 6/7 的口径差异。
- 不应因标题含 Knowledge Graph 就把它误写为完整攻击知识图谱。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
