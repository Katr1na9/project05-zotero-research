# APT-MMF: An Advanced Persistent Threat Actor Attribution Method Based on Multimodal and Multilevel Feature Fusion

## 1. 基本信息

- 英文题名：APT-MMF: An advanced persistent threat actor attribution method based on multimodal and multilevel feature fusion
- 中文译名：APT-MMF：基于多模态与多层级特征融合的高级持续性威胁行为体归因方法
- 作者：Nan Xiao; Bo Lang; Ting Wang; Yikai Chen
- 年份：2024
- Venue：Computers & Security
- DOI / URL：10.1016/j.cose.2024.103960；https://www.sciencedirect.com/science/article/pii/S0167404824002657
- Zotero key：2N9ATPHK；PDF attachment：CNQYPZ7W
- 阅读日期：2026-07-05
- 阅读优先级：重点读
- 所属主题：APT Actor Attribution / CTI / IOC Heterogeneous Attributed Graph / Graph Attention / Baseline

## 2. 一句话总结

APT-MMF 把 APT CTI 报告及其 IOC 信息建成 heterogeneous attributed graph，融合 attribute type、BERT text、Node2vec topology 三类节点特征，再通过 IOC type-level、metapath-based neighbor node-level、metapath semantic-level 三层 attention 学习 report node 表示，最终把报告分类到 21 个 APT actor。

## 3. 研究问题

- 论文要解决什么问题？
  - 现有 CTI-based APT actor attribution 常只使用单一特征：ATT&CK tactic/technique、报告文本，或同质图拓扑。
  - 这些方法忽略 IOC 的类型、属性和异构关系，难以充分利用 CTI 报告中的多源证据。
  - 报告节点本身没有结构化属性，需要从报告包含的 IOC 邻居中补全表示。
- 为什么重要？
  - Project05 需要明确 actor attribution 的传统强基线，避免把“LLM 直接读报告猜 actor”当作唯一方案。
  - APT-MMF 提供了一个可解释的结构化归因路线：报告、IOC、属性、关系、metapath、attention weight。
- 和 CTI、ATT&CK、RAG、provenance、intent 的关系是什么？
  - 它位于 CTI report -> actor attribution 层，不处理系统日志 provenance graph。
  - ATT&CK tactics/techniques 被作为 IOC 类型和属性纳入图。
  - 它可作为 LLM/RAG attribution 的非 LLM 对比基线，也可作为 Opinion Pools 中的 graph/IOC attributor。
  - 它不做 attack intent recognition，也不判断证据充分性或未知 actor。

## 4. 核心贡献

1. Schema 贡献：设计面向 APT actor attribution 的 heterogeneous attributed graph schema，以 APT report 为中心连接多类 IOC。
2. 多模态贡献：融合 attribute type features、natural language text features 和 topological relationship features。
3. 多层级贡献：设计 triple attention，包括 IOC type-level attention、metapath-based neighbor node-level attention 和 metapath semantic-level attention。
4. 数据贡献：基于多源 CTI 构建包含 1,300 篇报告、21 个 APT group、24,694 个节点和 40,335 条关系的异构属性图数据集。
5. 实验贡献：在多分类 actor attribution 上达到 Micro-F1 0.8321、Macro-F1 0.7051，优于传统 ML 和 GNN baselines。

## 5. 方法框架

### 输入

- APT CTI reports；
- 从报告中抽取的 IOC entities；
- ATT&CK、CVE、VirusTotal、Avclass2 等外部知识或分析结果；
- APT group label，作为 report node 的分类标签。

### 输出

- 对每个 APT report node 的 threat actor classification；
- attention weights，可用于解释 IOC type、相邻报告和 metapath 的相对贡献。

### 图 Schema

- 中心节点：
  - APT report node，本身无属性。
- IOC node types：
  - malware；
  - tactics；
  - techniques；
  - vulnerabilities；
  - IPs；
  - domains；
  - URLs；
  - filenames；
  - file paths；
  - registries；
  - emails。
- 关系类型：
  - report 与 IOC 的 inclusion；
  - IP 与 domain 的 resolution；
  - IP 与 malware 的 association；
  - domain 与 malware 的 association；
  - malware 与 malware 的 homology。

### 多模态节点特征

| 特征 | 含义 | 方法 | 维度 |
|---|---|---|---:|
| Attribute type feature | 节点/属性类型的类别信息 | ordinal encoding / ID encoding | 64 |
| Natural language text feature | 属性文本语义 | BERT + fully connected layer | 64 |
| Topological relationship feature | 节点关系结构 | Node2vec | 128 |

### 三层 Attention

| 层级 | 作用 | 直觉 |
|---|---|---|
| IOC type-level attention | 利用一阶/二阶 IOC 邻居补全 report node 的稀疏表示 | 不同 IOC 类型对归因贡献不同，例如 malware/domain 通常强于 filename |
| Metapath-based neighbor node-level attention | 在某一 metapath 下聚合相邻 report nodes | 通过共享 IOC 或 IOC 关系找到相似报告 |
| Metapath semantic-level attention | 聚合不同 metapath 的语义贡献 | 不同 metapath 对 actor attribution 的区分力不同 |

### 方法流程

```text
APT CTI reports
  -> Entity extraction: tactics/techniques via TRAM; other IOCs via IOC-Finder
  -> Entity cleaning: whitelist, VirusTotal, invalidation handling
  -> Entity attribute and relationship expansion: ATT&CK, CVE, Avclass2, VirusTotal
  -> Build heterogeneous attributed graph
  -> Extract multimodal node features: attribute type + BERT text + Node2vec topology
  -> IOC type-level attention completes sparse report node features
  -> Metapath-based neighbor node-level attention aggregates report neighbors
  -> Metapath semantic-level attention aggregates metapaths
  -> Fully connected classifier
  -> APT actor attribution result
```

### Metapaths

- 一阶 metapath：report-filename-report、report-malware-report、report-URL-report、report-domain-report、report-IP-report、report-tactic-report 等。
- 二阶 metapath：report-IP-malware-report、report-domain-malware-report、report-malware-malware-report。
- 三阶 metapath：report-IP-malware-IP-report、report-IP-domain-IP-report、report-domain-IP-domain-report、report-malware-domain-malware-report、report-malware-IP-malware-report。
- 四阶 metapath：report-IP-malware-malware-IP-report、report-domain-malware-malware-domain-report。

## 6. 数据集与实验

### 数据集构建

- 数据来源：
  - APTNotes；
  - Symantec、FireEye/Trellix、Kaspersky、Qianxin、Nsfocus 等安全厂商威胁情报；
  - CVE、ATT&CK；
  - VirusTotal、Avclass2。
- 报告筛选：
  - 优先选择 2015 年后的报告；
  - 人工筛选具有明确唯一 APT actor 归因、且包含丰富 IOC 信息的报告。
- 规模：
  - 1,300 reports；
  - 21 APT groups；
  - 24,694 nodes；
  - 40,335 relationships；
  - 15,540 nodes 直接从报告抽取；
  - 其余节点由 VirusTotal 扩展。
- 划分：
  - 对每个 APT group 下的 report nodes 按 8:1:1 划分 train/validation/test。

### 实体抽取与清洗

- tactics / techniques：
  - 使用 TRAM 映射到 ATT&CK；
  - 仅保留 100% confidence 的分类结果。
- 其他 IOC：
  - 使用 IOC-Finder，并改进正则以减少 IP false positive、filepath false negative 和 registry 抽取不完整。
- IP/domain/URL 清洗：
  - whitelist filtering；
  - VirusTotal static analysis；
  - URL invalidation handling，如 `[.]` 或 `hxxp`；
  - URL 若 VirusTotal 中超过 10 个引擎判定恶意，则保留为 malicious。

### Baselines

- 传统 ML：
  - Naive Bayes；
  - KNN；
  - Decision Tree；
  - SVM；
  - Random Forest；
  - XGBoost；
  - MLP。
- GNN：
  - GCN；
  - GAT；
  - HAN；
  - HGNN-AC。

### 主要结果

| 方法 | Micro-F1 | Macro-F1 |
|---|---:|---:|
| Naive Bayes | 0.4379 | 0.3972 |
| KNN | 0.4598 | 0.3367 |
| Decision Tree | 0.4744 | 0.2707 |
| SVM | 0.5401 | 0.3825 |
| Random Forest | 0.6788 | 0.5540 |
| XGBoost | 0.7372 | 0.5929 |
| MLP | 0.7445 | 0.4869 |
| GCN | 0.7518 | 0.5693 |
| GAT | 0.7737 | 0.6641 |
| HAN | 0.7810 | 0.6838 |
| HGNN-AC | 0.8029 | 0.6871 |
| APT-MMF | 0.8321 | 0.7051 |

相对最佳传统 ML baseline MLP，APT-MMF 的 Micro-F1 提升 8.76%，Macro-F1 提升 11.82%。

### Ablation：多模态特征

| Node Features | Micro-F1 | Macro-F1 |
|---|---:|---:|
| MAT | 0.4672 | 0.2775 |
| MAT + OAT | 0.5912 | 0.4105 |
| MAT + OAT + NLT | 0.7518 | 0.6189 |
| MAT + OAT + NLT + TR | 0.8321 | 0.7051 |

结论：其他属性、自然语言文本特征和拓扑关系特征逐步加入后均显著提升性能。

### Ablation：三层 Attention

| Attention | Micro-F1 | Macro-F1 |
|---|---:|---:|
| Metapath-based neighbor node level | 0.7445 | 0.5868 |
| + Metapath semantic level | 0.7810 | 0.6838 |
| + IOC type level | 0.8321 | 0.7051 |

结论：IOC type-level attention 对 report node feature completion 很关键，因为 report node 本身无属性。

### Ablation：Metapaths

| Metapaths | Micro-F1 | Macro-F1 |
|---|---:|---:|
| First order | 0.7956 | 0.6919 |
| First + Second order | 0.8029 | 0.6928 |
| First + Second + Third order | 0.8102 | 0.6997 |
| First + Second + Third + Fourth order | 0.8321 | 0.7051 |

结论：更高阶 metapath 能补充异构语义，但也可能增加 schema 设计负担。

### 可解释性分析

- 以 Lazarus group 的 R562 报告为例：
  - 该报告涉及 ThreatNeedle malware cluster；
  - 包含 55 malware nodes、44 URL nodes、30 domain nodes、30 technique nodes、7 filepath nodes、2 registry nodes。
- IOC type-level attention：
  - domain、URL、malware 对 R562 的表示补全最重要；
  - technique 更常跨组共享，filepath/registry 更易变化或较少报告，因此权重较低。
- Metapath neighbor attention：
  - report-domain-report 下，R562 与多个 Lazarus 相关报告相连。
- Metapath semantic attention：
  - MP2 report-malware-report、MP13 report-malware-malware-report、MP5 report-domain-report 权重较高。

## 7. 关键知识点

### 概念

- Heterogeneous attributed graph：同时包含多类型节点、多类型边和节点属性的图。
- Attributeless report node：报告节点自身无结构化属性，需要由包含的 IOC 节点补全表示。
- IOC type-level attention：按 IOC 类型学习不同邻居对报告归因的贡献。
- Metapath：在异构图中定义的类型路径，用于表达“两个报告因何种证据相似”。
- Macro-F1：对类别不均衡更敏感，APT-MMF 的 Macro-F1 仍明显低于 Micro-F1，说明少数 actor 类别仍较难。

### 和现有主线的关系

```text
CTI text extraction:
  TTPXHunter / TechniqueRAG / Multi-Step Pipeline
    -> extract ATT&CK/TTP/atomic actions

CTI graph attribution:
  APT-MMF
    -> report + IOC heterogeneous attributed graph
    -> actor classification

可信融合:
  Opinion Pools
    -> treat APT-MMF as one attributor
    -> combine with text/RAG/provenance/local-context attributors

日志侧 evidence:
  UNICORN / THREATRACE / PROGRAPHER / Kairos / DEPCOMM
    -> local behavioral evidence
    -> can be aligned with CTI graph evidence
```

## 8. 优点

- 直接面向 APT actor attribution，比多数 TTP extraction 方法更贴近 Project05 的归因主线。
- 明确把 IOC 类型、属性和关系作为归因证据，而不是只看报告文本。
- attention weights 提供一定可解释性，能说明哪些 IOC 类型、相邻报告和 metapath 更重要。
- 与 Opinion Pools 很兼容：APT-MMF 可以作为结构化 CTI/IOC attributor。
- 实验覆盖传统 ML、同质 GNN、异构 GNN，baseline 组合相对完整。

## 9. 局限

- 本质仍是 closed-world actor classification：训练和测试都来自已知 21 个 APT groups。
- 未来工作才提到 unknown APT actors，当前方法不能自然处理新 actor、混合 actor 或 false flag。
- 数据集依赖人工筛选“明确唯一归因”的报告，可能天然排除了现实中最困难的不确定样本。
- TRAM 仅保留 100% confidence 的 ATT&CK 映射，提升精度但可能降低覆盖率。
- 使用 VirusTotal、Avclass2、ATT&CK、CVE 做扩展，复现依赖外部服务与知识库状态。
- 注意力权重只能提供局部解释，不等于因果证据或可审计归因证明。
- Zotero 元数据摘要提到对 incomplete/noise information 的鲁棒性，但本地 PDF 正文只呈现四组实验，没有看到完整鲁棒性表；写作时不要把鲁棒性作为强结论。

## 10. 对我选题的启发

- 可以直接借鉴：
  - 用 report-IOC heterogeneous graph 组织 CTI 证据；
  - 用 metapath 表达“两个事件/报告为什么相似”；
  - 把 actor attribution 拆成多证据 attributor，而不是让 LLM 一步到位。
- 可以改进：
  - 加入 provenance evidence：把日志侧 anomalous node / InfoPath / attack summary graph 映射到 IOC 或 ATT&CK 节点；
  - 加入 evidence sufficiency：当 IOC 证据过泛或跨组共享时，输出低置信或拒答；
  - 加入 unknown actor detection：不要强制归入 21 个已知 actor；
  - 用 LLM 生成可审计解释，但要求引用 report sentence、IOC edge、ATT&CK node 或 provenance evidence。
- 可以作为 baseline：
  - CTI/IOC graph-based actor attribution baseline；
  - 与 CTIBench 的 CTI-TAA、Opinion Pools、High Stakes 形成 attribution evaluation 对比。

## 11. 可转化的研究问题

1. 如何将 APT-MMF 的 report-IOC heterogeneous graph 与日志侧 provenance evidence 对齐？
2. 如何把 attention-based explanation 转换为可审计证据链，而不是只给权重可视化？
3. 如何在 actor classification 外增加 unknown actor / insufficient evidence / false flag 检测？
4. LLM 能否作为 attribution explanation generator，但受 APT-MMF 的图证据和 Opinion Pool 概率约束？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| A survey of cyber threat attribution | APT-MMF 是 survey 中 automated APT attribution 的代表方法之一。 |
| CTIBench | CTIBench 的 CTI-TAA 是 benchmark 任务；APT-MMF 是结构化图归因模型。 |
| Opinion Pools | APT-MMF 可作为 graph/IOC attributor，输出 actor 分布后进入 opinion pool。 |
| High Stakes, Low Certainty | APT-MMF 使用 IOC/TTP 证据；High Stakes 提醒这些证据可能跨组重叠，需评估证据充分性。 |
| TechniqueRAG / TTPXHunter | 它们主要抽取 ATT&CK/TTP；APT-MMF 把 ATT&CK/TTP 作为 IOC 类型纳入 actor attribution。 |
| Open-CyKG / CTIConnect | 都关注 CTI 结构化与图检索；APT-MMF 更明确面向 actor classification。 |
| PROGRAPHER / THREATRACE | 它们提供日志侧可疑节点/异常 evidence；APT-MMF 提供 CTI 报告侧 actor attribution。 |

## 13. 论文写作可引用句式

- CTI-based actor attribution methods such as APT-MMF demonstrate that threat reports can be represented as heterogeneous attributed graphs centered on reports and linked to IOC nodes.
- However, actor classification over known APT groups does not address evidence insufficiency, unknown actors, or false-flag operations.
- A practical LLM-assisted attribution system should therefore combine structured IOC evidence, provenance evidence, and calibrated uncertainty rather than forcing every incident into a closed set of actor labels.

## 14. 我的批注与疑问

- 这篇是 Project05 归因侧强基线，重要性高于很多泛安全 LLM benchmark。
- 它最值得借鉴的不是具体网络结构，而是“报告-IOC-属性-关系-metapath”的证据组织方式。
- 它和 Opinion Pools 之间很自然：APT-MMF 输出一个 actor 分布，LLM/RAG/provenance 模块也输出分布，最后融合。
- 真正的硕士创新空间在 APT-MMF 没覆盖的部分：未知 actor、证据不足拒答、false flag、多源证据冲突、日志证据对齐。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是，作为 CTI/IOC graph-based actor attribution 核心基线进入主线。
