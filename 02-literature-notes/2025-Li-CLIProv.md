# CLIProv: A Contrastive Log-to-Intelligence Multimodal Approach for Threat Detection and Provenance Analysis

## 1. 基本信息

- 英文题名：CLIProv: A Contrastive Log-to-Intelligence Multimodal Approach for Threat Detection and Provenance Analysis
- 中文译名：CLIProv：面向威胁检测与溯源分析的日志-情报对比多模态方法
- 作者：Jingwen Li, Ru Zhang, Jianyi Liu, Wanguo Zhao
- 年份：2025
- Venue：arXiv preprint
- DOI / arXiv / URL：https://arxiv.org/abs/2507.09133
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：必读
- 所属主题：Log-to-intelligence alignment / Contrastive learning / Provenance analysis / TTP identification
- 阅读状态：全文精读；由原“摘要级红线占位”升级

## 2. 一句话总结

CLIProv 直接覆盖了“本地 provenance/log 与威胁情报语义对齐”的关键空间：它把 provenance logs 和 TTP threat intelligence 投影到共享语义空间，用对比学习将威胁检测转化为语义搜索，并输出 TTP 识别和攻击场景。

## 3. 研究问题

- 高层 TTP intelligence 难以直接转化为低层系统日志中的 actionable security policies。
- Query graph 方法需要手工构造模板，且面对行为变体和大规模日志时效率有限。
- 日志是低层、结构化、微观数据；CTI 是高层、自然语言、宏观描述，两者存在语义层级和结构差异。

## 4. 核心贡献

1. 提出 provenance log representation learning，将日志序列与威胁情报放入共享语义空间。
2. 用 contrastive learning 对齐 log sequence 与 threat intelligence，避免依赖精确 query graph。
3. 将 threat detection 转化为 semantic search：搜索与日志序列最相似的威胁情报。
4. 输出 TTP 识别与完整、简洁的 attack scenario。
5. 在 CADETS、THEIA、ATLAS、CICAPT-IIoT 四个数据集上评估。

## 5. 方法框架

### 输入

- Provenance logs / system audit logs。
- MITRE ATT&CK threat intelligence / TTP descriptions。
- 训练时的正负样本对。

### 输出

- 攻击行为检测结果。
- 相关 TTP。
- 高层 attack scenario summary。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| Graph construction and reduction | 从 provenance logs 构建并压缩行为图 | 不是我方创新点 |
| Subgraph partitioning / sequence construction | 将 provenance graph 转成系统行为序列 | 可作为 evidence unit 生成方式 |
| Intelligence augmenting | 用 GPT-3 增广威胁情报文本 | LLM 数据增强已有先例 |
| Log/text encoders | RoBERTa 编码日志和情报文本 | 语义统一/对齐已被覆盖 |
| Contrastive training | 拉近同一攻击模式的日志与情报表示 | 主红线 |
| Semantic search | 检索最相似 TTP/情报 | 可作为上游 baseline |

### 方法流程

```text
provenance logs
  -> graph construction/reduction
  -> subgraph partitioning
  -> log sequence construction
ATT&CK intelligence
  -> text augmentation
log sequence + intelligence
  -> contrastive representation learning
  -> semantic search
  -> TTP identification + attack scenario
```

## 6. 数据集与实验

- 数据集：CADETS、THEIA、ATLAS、CICAPT-IIoT。
- 情报库：MITRE ATT&CK，包含 14 tactics、177 techniques、10358 threat intelligence。
- 模型：RoBERTa 作为 log encoder 和 text encoder；projection layer；100 epochs。
- Baseline：POIROT、ProvG-Searcher，以及 anomaly-based detection methods。
- 结果摘记：
  - CADETS/THEIA/ATLAS graph-level precision/recall 均报告为 100/100。
  - CICAPT-IIoT graph-level precision 约 60.96，recall 约 86.21。
  - 与 POIROT/ProvG-Searcher 比较时，搜索时间明显低于 POIROT，接近或优于 ProvG-Searcher。
  - 运行开销：预处理约 13.9 分钟，训练约 8.72 小时，威胁搜索与调查约 19.15 秒。

## 7. 关键知识点

### 概念

- Log-to-intelligence alignment：把低层日志行为与高层情报文本对齐。
- Semantic search threat hunting：把检测变成“日志序列找相似情报”。
- Attack scenario reconstruction：根据检索出的 TTP 与日志子图生成高层攻击过程。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| log-to-intelligence | 日志-情报 | CLIProv 核心关键词 |
| multimodal alignment | 多模态对齐 | 在此指日志/图结构与文本 |
| attack scenario reconstruction | 攻击场景重构 | 它已覆盖“场景总结” |

## 8. 优点

- 非常直接地补上了 POIROT/DeepHunter/MEGR-APT 的语义鸿沟问题。
- 不依赖手工 query graph，直接利用自然语言情报。
- 实验跨四个数据集，且明确与 query graph 系方法比较。
- 输出 TTP 与攻击场景，对“LLM 总结攻击过程”构成红线压力。

## 9. 局限

- 任务仍是检测、TTP 识别和 provenance analysis，不是 actor/campaign attribution。
- 没有 evidence sufficiency / attribution granularity gate。
- 没有主动取证规划；对齐或检索不足时不会决定下一步该获取什么证据。
- 讨论了假情报和噪声情报风险，但没有把 CTI trustworthiness 纳入闭环取证。

## 10. 对我选题的启发

- 强红线：Project05 不能把“LLM/语义模型统一 CTI、IOC、日志语义表达”作为主创新，也不能把“日志到 TTP 语义提升”作为主创新。
- 可作为上游：CLIProv 的输出可被 Project05 接收为 alignment state，例如 log-text similarity、TTP candidates、attack scenario fragments。
- 差异点必须明确：Project05 不优化 semantic alignment 本身，而优化对齐结果之后的 evidence sufficiency 判断和 next evidence action planning。

## 11. 可转化的研究问题

1. 当 CLIProv 给出多个相似 TTP 但置信度接近时，哪些附加证据最能提升归因粒度？
2. 当 graph-level recall 足够但 node-level precision 较低时，系统是否应避免高粒度归因？
3. 如何把 semantic search 分数、TTP 覆盖和攻击场景完整度转成 evidence state？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| POIROT | CLIProv 避免手工 query graph 和昂贵图匹配 |
| DeepHunter / ProvG-Searcher | CLIProv 与其共享 representation matching 思路，但转向文本语义对齐 |
| APT-CGLP | 两者都覆盖跨模态对齐；APT-CGLP 更进一步做 graph-language pre-training |
| Project05 | CLIProv 是上游对齐基座，不是最终研究目标 |

## 13. 论文写作可引用句式

- Recent log-to-intelligence systems have demonstrated that provenance logs and threat intelligence can be aligned in a shared semantic space for TTP identification and attack scenario reconstruction; however, they do not decide whether the aligned evidence is sufficient for a target attribution granularity or which evidence should be acquired next.

## 14. 我的批注与疑问

- 这是目前对我们“语义统一”想法杀伤力最大的一篇之一。
- 如果专利还写“LLM 将 CTI/日志/IOC 统一成规范语义表达”，必须把它降级为前处理或可选模块，不能放在独立权利要求核心。
- 应进一步复核它是否开源；若可复现，MVP 可以把它简化成 baseline alignment module。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

