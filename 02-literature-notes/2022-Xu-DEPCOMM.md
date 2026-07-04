# DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation

## 1. 基本信息

- 英文题名：DEPCOMM: Graph Summarization on System Audit Logs for Attack Investigation
- 中文译名：DEPCOMM：面向攻击调查的系统审计日志图摘要方法
- 作者：Zhiqiang Xu; Pengcheng Fang; Changlin Liu; Xusheng Xiao; Yu Wen; Dan Meng
- 年份：2022
- Venue：IEEE Symposium on Security and Privacy, S&P 2022
- DOI / arXiv / URL：10.1109/SP46214.2022.9833632 / https://doi.org/10.1109/SP46214.2022.9833632
- Zotero key：待核验
- 阅读日期：2026-07-04
- 阅读优先级：必读
- 所属主题：Attack Chain / Provenance Graph / Attack Investigation / Graph Summarization

## 2. 一句话总结

DEPCOMM 解决的是系统审计日志因果分析产生的 dependency graph 过大、难以人工调查的问题。它把大规模依赖图划分为 process-centric communities，压缩社区内部重复边，并用跨社区信息流路径 InfoPaths 生成社区摘要，从而让安全分析员用更少的事件理解攻击过程。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - causality analysis 能从系统审计日志生成 dependency graph，但图通常包含大量节点和边，分析员难以手动检查。
  - DEPCOMM 目标是保留系统活动语义，同时把依赖图压缩成可调查的 summary graph。
- 这个问题为什么重要？
  - 攻击调查需要理解攻击链上下文，而不是只看单个告警。
  - 大规模 dependency graph 存在 dependency explosion，可能超过 100K edges。
  - 自动检测技术仍可能遗漏或误报，因此人工调查仍不可替代。
- 之前方法哪里不够？
  - 传统 causality analysis 生成图太大。
  - 自动过滤方法可能依赖启发式规则或系统 profile，存在残余风险。
  - 通用图摘要方法没有考虑系统安全图的异构实体、时间因果和攻击语义。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 它不直接做威胁归因或 ATT&CK 标注，但提供日志侧攻击调查证据压缩方法。
  - 它可以作为后续 LLM/RAG/Agent 的输入预处理：把原始审计图压缩成可读 InfoPaths。
  - 它和 Kairos 共同构成“系统日志 -> 攻击摘要图/证据链”的基础。

## 4. 核心贡献

1. 任务贡献：提出面向攻击调查的 dependency graph summarization 问题，强调压缩图的同时保留系统活动语义。
2. 方法贡献：提出 process-centric community detection，把 intimate processes 及其访问资源组成社区。
3. 方法贡献：提出 community compression，通过 process-based patterns 和 resource-based patterns 合并重复节点/边。
4. 方法贡献：提出 InfoPaths，用社区输入输出之间的信息流路径作为社区摘要，并按攻击相关性/系统活动重要性排序。
5. 实验贡献：在 6 个实验室真实攻击和 8 个 DARPA TC 攻击上评估，覆盖约 150M audit events。
6. 系统贡献：可与 HOLMES 等自动调查技术结合，突出 attack-related communities。

## 5. 方法框架

### 输入

- 数据类型：
  - 系统审计日志；
  - process events；
  - file events；
  - network events。
- 输入格式：
  - 系统事件三元组：`<subject, operation, object>`；
  - 给定 POI event 后，通过 backward causality analysis 构建 dependency graph。
- 先验知识：
  - POI event，例如 IDS 告警、可疑下载、可疑外联；
  - 系统事件时间戳、主体、客体、操作类型；
  - process lineage tree。

### 输出

- 预测结果：不是分类预测，而是摘要图。
- 图结构：
  - process-centric communities；
  - compressed communities；
  - top-ranked InfoPaths。
- 标签：无 ATT&CK 标签。
- 报告：无自然语言报告，但 InfoPaths 可作为调查摘要。
- 证据链：跨社区信息流路径，可视为日志侧证据链雏形。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Dependency Graph Generation | 从 POI event 出发，做 backward causal analysis，生成依赖图 | 适合把安全告警扩展为上下文证据图 |
| Pre-processing | 合并平行边、过滤 read-only file nodes | 减少不影响调查的重复审计事件 |
| Process-centric Community Detection | 识别 intimate processes 并聚类为社区 | 从“进程协作完成任务”的角度切分攻击图 |
| Hierarchical Walk Schemes | 结合局部邻居和全局 process lineage 生成进程表示 | 比通用 random walk 更适合系统安全图 |
| Community Compression | 用 process-based / resource-based patterns 合并重复节点和边 | 可减少 LLM/RAG 输入长度 |
| InfoPath Generation and Ranking | 从社区输入节点到输出节点生成信息流路径并排序 | 可作为攻击步骤、意图识别、证据链的候选输入 |
| HOLMES Cooperation | 与自动调查系统结合，映射 attack-related communities 到 Kill Chain steps | 说明图摘要可服务上层安全语义分析 |

### 方法流程

```text
System audit logs + POI event
  ↓
Backward causality analysis
  ↓
Dependency graph
  ↓
Pre-processing：edge merge + read-only file filtering
  ↓
Process-centric community detection
  ↓
Community compression：process/resource patterns
  ↓
InfoPath generation：input nodes -> output nodes
  ↓
InfoPath ranking
  ↓
Summary graph for attack investigation
```

## 6. 数据集与实验

- 数据集：
  - 6 个实验室攻击；
  - 8 个 DARPA Transparent Computing attacks。
- 数据规模：
  - 总计约 150M system audit events；
  - 生成 dependency graphs 平均 1,302.1 nodes 和 7,553.4 edges；
  - 原始攻击案例依赖图可达到数十万到数百万 edges。
- 攻击案例：
  - Email Penetration；
  - Compile Crash；
  - Files Tamper；
  - Data Exfiltration；
  - Password Crack；
  - VPN Filter；
  - DARPA Phishing Email、Firefox Backdoor、Browser Extension、Pine Backdoor 等。
- 标注方式：
  - attack-related events / communities 用于评价社区检测和调查效果；
  - 与 HOLMES 结合时，评估 attack-related communities 到 Kill Chain steps 的覆盖。
- Baseline：
  - 9 个 state-of-the-art community detection algorithms；
  - HOLMES 作为自动调查技术协作对象。
- 指标：
  - community detection F1-score；
  - compression rate；
  - nodes/edges reduction；
  - attack-related community recall；
  - turnaround performance；
  - top-n InfoPaths 的调查有效性。
- 主要结果：
  - DEPCOMM 平均生成 18.4 communities，约比原图小 70 倍。
  - 每个 community 平均 43.1 nodes 和 248.5 edges。
  - community detection F1-score 达到 94.1%，平均比 9 个对比算法高 2.29 倍。
  - community compression 平均压缩率 44.7%。
  - 压缩后每个 community 平均 15.7 nodes 和 32.1 edges，节点减少 63.6%，边减少 87.1%。
  - top-2 InfoPaths 通常足以支持攻击调查，只需查看约 12.7% 的 InfoPaths。
  - 与 HOLMES 合作时，attack-related communities recall 为 96.2%。
- 消融实验：
  - 评估 community detection；
  - 评估 community compression；
  - 评估 top-ranked InfoPaths；
  - 评估处理性能。
- Case study：
  - DARPA D5 Browser Extension 案例中，原始图 37,109 events，DEPCOMM 通过 summary graph 让分析员只需检查 25 events 即可识别攻击相关行为。

## 7. 关键知识点

### 概念

- **Dependency graph**：从系统审计日志通过因果分析生成的有向图，节点为进程、文件、网络连接等系统实体，边为系统事件。
- **Dependency explosion**：因果分析把大量相关和弱相关事件纳入图中，导致图规模膨胀，影响调查。
- **Process-centric community**：以一组紧密协作的进程为核心，加上这些进程访问的资源构成的社区。
- **Intimate processes**：存在父子关系、兄弟关系或通过资源形成数据依赖的紧密进程组。
- **InfoPath**：社区内从输入节点到输出节点的信息流路径，用于摘要社区的关键系统活动。
- **POI event**：Point-Of-Interest event，通常是告警或可疑事件，作为因果分析起点。

### 技术路线

- DEPCOMM 不是先做异常检测，而是从 POI 出发生成依赖图，再进行安全语义驱动的图摘要。
- 它不是通用 community detection，而是使用系统安全图的结构特征：
  - process lineage；
  - process-resource dependencies；
  - system event time；
  - input/output information flow。
- 它的摘要单位不是单个节点或边，而是 community + top-ranked InfoPaths。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| dependency graph | 依赖图 | 系统实体与事件构成的因果图 |
| dependency explosion | 依赖爆炸 | 因果分析导致图过大 |
| process-centric community | 进程中心社区 | DEPCOMM 核心结构 |
| intimate processes | 紧密进程组 | 共同完成系统活动的一组进程 |
| InfoPath | 信息路径 | 保留英文也可 |
| POI event | 关注事件 / 兴趣点事件 | Point-Of-Interest event |
| graph summarization | 图摘要 |  |
| community compression | 社区压缩 |  |
| process lineage tree | 进程谱系树 |  |

## 8. 优点

- 非常贴近真实安全调查问题：不是“检测到了什么”，而是“如何让人看懂庞大的日志证据图”。
- 相比通用图摘要，DEPCOMM 明确利用进程、文件、网络连接和时间因果关系，安全语义更强。
- InfoPath 是很好的中间表示，适合后续作为 LLM/RAG 的输入。
- 能与 HOLMES 等自动调查工具协作，说明它可插入现有安全分析流水线。
- 实验规模较大，覆盖实验室攻击和 DARPA TC 数据。

## 9. 局限

- 依赖 POI event；如果没有合适告警或兴趣点事件，构图起点可能不稳定。
- 主要解决图压缩和调查辅助，不直接输出 ATT&CK technique、攻击意图或威胁行为体归因。
- InfoPath 排序仍是启发式/特征打分，无法保证 top paths 总是包含全部关键攻击语义。
- 需要系统审计日志和 causality analysis 基础设施，复现成本高于纯 CTI 文本方法。
- 对 LLM/RAG 时代的自然语言解释、证据引用和置信度没有覆盖。

## 10. 对我选题的启发

- 可以直接借鉴：
  - `POI -> dependency graph -> community -> InfoPath` 的证据压缩流程；
  - InfoPath 作为“日志侧证据链”的中间表示；
  - process-centric community 作为 attack summary graph 的结构单元。
- 可以改进：
  - 将 InfoPaths 映射到 ATT&CK techniques / tactics；
  - 用 LLM/RAG 为 InfoPaths 生成自然语言攻击解释；
  - 对 InfoPath 是否足以支撑某个 attack intent 做证据充分性判断；
  - 将 CTI 文本侧 attack graph 与日志侧 InfoPaths 对齐。
- 可以作为 baseline：
  - 如果做日志侧 evidence summarization，DEPCOMM 是关键 baseline。
  - 如果做 LLM 解释攻击图，DEPCOMM 可作为输入摘要图生成方法。
- 可以用于研究动机：
  - 原始日志图太大，必须先压缩为人和模型都能处理的证据结构。
  - 安全调查的目标不是只检测异常，而是恢复可理解的攻击故事。
- 可以用于实验设计：
  - 用 attack step coverage、evidence precision/recall、summary size、human inspection effort 评价图摘要到解释的质量。

## 11. 可转化的研究问题

1. 如何将 DEPCOMM 的 InfoPaths 自动映射到 MITRE ATT&CK techniques 和 tactics？
2. LLM 能否基于 InfoPaths 生成可验证的攻击调查叙事，并引用具体节点/边作为证据？
3. CTI 文本中的 attack behavior graph 是否能和 DEPCOMM 的 process-centric communities / InfoPaths 对齐？
4. InfoPath 是否可以作为攻击意图识别的证据单位？
5. 如何评估 summary graph 是否保留了足够的攻击语义，而不只是压缩率高？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Kairos | Kairos 从异常检测出发生成 attack summary graph；DEPCOMM 从 POI 依赖图出发做 process-centric community summarization |
| EXTRACTOR | EXTRACTOR 从 CTI 文本抽取 provenance query graph；DEPCOMM 从系统日志抽取并压缩 dependency graph |
| AttacKG | AttacKG 做 CTI 文本到 ATT&CK 技术知识图谱；DEPCOMM 做日志侧图摘要，缺少 ATT&CK 语义层 |
| HERCULE | HERCULE 较早用 community discovery 做 attack story reconstruction；DEPCOMM 更系统地处理 dependency graph summarization |
| HOLMES | DEPCOMM 可与 HOLMES 协作，用 HOLMES 高层场景图突出 attack-related communities |
| POIROT | POIROT 用 query graph 匹配日志；DEPCOMM 关注从日志图中生成调查摘要 |
| TechniqueRAG | TechniqueRAG 标注 CTI 文本中的 ATT&CK technique；DEPCOMM 的 InfoPaths 可作为未来 technique annotation 的非文本输入 |

## 13. 论文写作可引用句式

- 系统审计日志的因果分析能够重建攻击上下文，但由此生成的依赖图往往过大，难以直接用于人工调查。
- 面向攻击调查的图摘要不仅要压缩图规模，还必须保留系统活动语义和攻击相关信息流。
- Process-centric communities 和 InfoPaths 为从底层系统事件到高层攻击故事之间提供了可解释的中间结构。
- 日志侧攻击摘要图本身并不等价于 ATT&CK 技术标注或威胁归因，还需要进一步的语义映射与证据推理。

## 14. 我的批注与疑问

- DEPCOMM 对我的方向非常关键，因为它给出了“日志侧证据压缩”的另一种方案。
- Kairos 更像“异常检测 + 攻击摘要图”，DEPCOMM 更像“POI 驱动的因果图摘要”。两者可以并列作为日志侧证据底座。
- InfoPath 很适合被序列化输入给 LLM：

```text
input node -> process -> file -> process -> network output
```

  这种结构比完整审计图更短，也比自然语言日志更保留因果关系。
- 真正值得往下想的问题不是“如何再压缩图”，而是：
  - 压缩后的 InfoPath 如何变成 ATT&CK / intent？
  - LLM 生成解释时如何引用路径中的节点和边？
  - 如果 InfoPath 不足以支撑结论，系统如何表达不确定性？

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是

