# OCR-APT: Reconstructing APT Stories from Audit Logs using Subgraph Anomaly Detection and LLMs

## 1. 基本信息

- 中文译名：OCR-APT：利用子图异常检测和 LLM 从审计日志重构 APT 故事
- 作者：Ahmed Aly; Essam Mansour; Amr Youssef
- 年份：2025
- Venue：ACM CCS 2025 author extended version / arXiv
- DOI：10.1145/3719027.3765219
- arXiv：https://arxiv.org/abs/2510.15188
- Zotero key：IPYYVJRP（PDF：NQ5BNSP2）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Provenance Graph / APT Story / LLM

## 2. 一句话总结

OCR-APT 在审计 provenance 图上用 OCRGCN 与 one-class SVM 检测异常节点和子图，再让 LLM 提取 IOC、映射阶段、生成攻击故事并回查关键上下文。它已强占“事件证据子图+LLM 攻击叙事”，但明确不处理独立网络流量，且 IOC 字符串校验无法消除语义幻觉。

## 3. 研究问题

- 如何在 8000 万级审计事件中检测未知 APT 并生成可读攻击叙事？
- 攻击者可用 zero-day 和 low-and-slow 行为，但训练日志须干净，audit/kernel logging 被信任。

## 4. 核心贡献

1. RDF provenance 图与类型特定 RGCN/OCRGCN 异常检测。
2. 异常节点邻域与路径构成子图，必要时 Louvain 分割。
3. LLM 分阶段 IOC 提取、报告生成、关键 IOC 选择和图数据库回查。
4. DARPA TC3、OpTC、NODLINK 上与 KAIROS、THREATRACE、MAGIC、FLASH 等比较。

## 5. 方法框架

```text
audit logs -> RDF provenance graph
  -> OCRGCN embeddings + one-class SVM
  -> anomalous nodes/subgraphs
  -> time-ordered edge serialization
  -> LLM IOC extraction and lexical validation
  -> stage summaries + combined APT story
  -> key IOC selection and graph-context retrieval
```

- 主体/客体为 process/file/network-flow entity，边为 read/write/execute/connect 等系统动作。
- network-flow entity 属于主机审计图，不是独立 PCAP/Zeek 模态。
- GPT-4o-mini 负责报告，Llama3-8B 用于本地部署对照。

## 6. 数据集与实验

- 超过 80M system events；平均恶意节点比例低于 0.01%。
- 多数主机检测 F1 为 0.94--1.00；OpTC 51 与 NODLINK WS12 为 0.82，OpTC 51 低于 FLASH 的 0.93。
- GPT-4o-mini 在六个主要场景恢复的 IOC/stage 分别为 11/16 & 5/6、6/7 & 4/4、5/7 & 5/6、5/6 & 5/7、7/11 & 5/8、8/10 & 4/6。
- 严格取消二跳邻居放宽后，CADETS/TRACE/THEIA F1 为 1.00/0.93/0.99。

## 7. 关键知识点

- IOC 出现在源子图只能证明词法存在，不能证明 LLM 对阶段、因果或目的的解释正确。
- 异常子图压缩是连接图检测与 LLM 推理的关键中间层。
- 默认宽松邻居真值会高估节点检测，需要严格指标复核。

## 8. 优点

- 真实规模 provenance 图、异常检测和 LLM 报告组合完整。
- 支持关键 IOC 回查、交互式问答和本地模型。
- 报告了 IOC/阶段覆盖而不只看检测 F1。

## 9. 局限

- 训练必须无攻击；对未见良性行为易误报。
- 不处理独立网络流量，作者明确列为未来工作。
- 多攻击共享实体时可能合并；解析缺失会破坏链。
- 最终报告无逐句 raw event ID；附录出现把标准库加载/组播解释为攻击的语义幻觉。
- 无意图候选、行为体归因、校准和分析员实证。

## 10. 对我选题的启发

- “provenance subgraph + LLM report”本身已不足以构成创新。
- 必须增加独立 PCAP/flow 线、跨源对齐置信度和逐结论 evidence path。
- 应把词法 IOC 校验升级为结构/语义蕴含验证与反证检查。

## 11. 可转化的研究问题

1. 独立流量证据能否补齐 lateral movement 和 C2 并纠正日志叙事？
2. 如何评价每个生成句子的 evidence precision 和 entailment？
3. 多攻击共享实体时如何解缠候选链和意图？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| ANANKE | 都在日志 provenance 图上用 LLM 扩图/报告 |
| PROVSEEK | 后者的 claim-node/edge ID 绑定更严格 |
| StageFinder | 后者双源早融合做阶段分类，不生成叙事 |

## 13. 论文写作可引用句式

- 字符串级 IOC 校验可以减少实体捏造，却不能验证阶段判断、因果关系和攻击叙事的语义忠实度。

## 14. 我的批注与疑问

- 这是本支线必须正面比较的强基线。
- 需要核验公开代码能否导出稳定 event/edge IDs。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
