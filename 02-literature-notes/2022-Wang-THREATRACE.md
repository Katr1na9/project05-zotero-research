# THREATRACE: Detecting and Tracing Host-Based Threats in Node Level Through Provenance Graph Learning

## 1. 基本信息

- 英文题名：THREATRACE: Detecting and Tracing Host-Based Threats in Node Level Through Provenance Graph Learning
- 中文译名：THREATRACE：通过溯源图学习在节点级检测和追踪主机威胁
- 作者：Su Wang; Zhiliang Wang; Tao Zhou; Xia Yin; Dongqi Han; Han Zhang; Hongbin Sun; Xingang Shi; Jiahai Yang
- 年份：2022
- Venue：IEEE Transactions on Information Forensics and Security
- DOI / arXiv / URL：10.1109/TIFS.2022.3208815；https://arxiv.org/abs/2111.04333
- Zotero key：RST9FRJ6 / FLA5EZDB 附件
- 阅读日期：2026-07-05
- 阅读优先级：重点读
- 所属主题：Provenance-based Detection / Graph Learning / Node-level Tracing / Baseline

## 2. 一句话总结

THREATRACE 将主机威胁检测从 UNICORN 式 graph-level anomaly detection 推进到 node-level anomalous entity detection。它用 GraphSAGE 学习 benign provenance graph 中每类系统实体的局部角色，如果执行阶段某个节点无法被任何子模型高置信分类回自己的节点类型，就把它判为异常并在其 2-hop 邻域中追踪威胁。

## 3. 研究问题

- 论文要解决的核心问题是什么？
  - 现有 provenance-based anomaly detector 多从整图或路径层面检测异常。
  - APT 等 stealthy threats 中异常实体可能只占全图极小比例，整图特征会被大量正常行为淹没。
  - 整图检测只能报警，不能定位具体异常系统实体，难以辅助调查和修复。
- 这个问题为什么重要？
  - 安全分析师不只需要知道“系统异常”，还需要知道异常在哪些 process、file、socket 或 remote IP 上。
  - Project05 若要做证据链、ATT&CK/intent 映射或归因解释，需要 node/edge/path 级证据，而不是只有 graph-level label。
- 之前方法哪里不够？
  - StreamSpot / UNICORN / IPG 偏 graph-level detection，对少量异常节点不敏感。
  - ProvDetector 偏 path-level malware detection，但复杂 APT 可能被拆成多个分散片段，不一定形成完整异常路径。
  - Holmes / Poirot / RapSheet 等 misuse-based 方法依赖 TTP、规则或专家知识，难以检测未知攻击。
- 它和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG、Agent 的关系是什么？
  - 它属于日志/provenance 侧的 node-level local evidence generator。
  - 它不做 CTI 文本理解、ATT&CK 标注、攻击意图识别或 actor attribution。
  - 它输出的异常节点可作为后续 LLM/RAG 解释和证据链构建的候选证据。

## 4. 核心贡献

1. 任务贡献：首次将 host-based threat detection 明确形式化为 provenance graph 上的 anomalous node detection and tracing。
2. 方法贡献：提出 GraphSAGE-based multi-model framework，在没有攻击样本和攻击规则的情况下学习 benign node roles。
3. 工程贡献：使用磁盘存完整图、内存维护受限子图的 streaming 架构，支持长期主机监控。
4. 追踪贡献：检测异常节点后，在 2-hop ancestors / descendants 范围内进行 anomaly tracing。
5. 实验贡献：在 StreamSpot、UNICORN SC-2、DARPA TC 三类公开数据上与 StreamSpot、UNICORN、ProvDetector 对比。

## 5. 方法框架

### 输入

- 数据类型：
  - whole-system provenance graph；
  - streaming audit data；
  - benign provenance graphs for training。
- 输入格式：
  - 节点表示系统实体，如 process、file、socket、remote IP；
  - 边表示系统调用或信息流，如 read、write、execute、connect、fork；
  - 图带时间顺序。
- 先验知识：
  - 不需要攻击样本；
  - 不需要 TTP rule / attack pattern；
  - 假设 provenance collection 正确；
  - 假设 GraphSAGE 能学习节点在图中的结构角色。

### 输出

- 预测结果：
  - anomalous nodes；
  - graph-level alarm 可由节点异常聚合得到。
- 图结构：
  - 输入为 provenance DAG；
  - 内存维护 active nodes、related nodes 和局部子图。
- 标签：
  - 训练时用 node type 作为 benign 节点的监督标签。
- 报告：
  - 不生成攻击报告。
- 证据链：
  - 异常节点 + 2-hop ancestors / descendants，作为局部调查证据。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Data Provenance Generator | 用 CamFlow 等工具生成 streaming provenance graph | 本地日志证据入口 |
| Data Storage | 磁盘存完整图，内存维护受限子图 | 长期监控的工程折中 |
| Feature Extraction | 用入边/出边类型分布表示节点行为 | 简单但可解释的节点行为特征 |
| Label Assignment | 将 node type 作为监督标签 | 无攻击样本时训练 benign role model |
| GraphSAGE submodel | 聚合 K-hop 邻居信息学习节点角色 | 适合 evolving graph 的 inductive learning |
| Multi-model Framework | 为不平衡节点类型和隐藏角色训练多个子模型 | 缓解 false positives |
| Alert and Trace | 等待阈值 + 容忍阈值 + 2-hop tracing | 从检测转向证据定位 |

### 方法流程

```text
Streaming audit data
  ↓
Whole-system provenance graph
  ↓
Disk stores full graph; memory keeps bounded subgraph
  ↓
Node feature extraction: in/out edge-type distribution
  ↓
Label assignment: node type as supervised label
  ↓
GraphSAGE multi-model training on benign node roles
  ↓
Execution: classify active nodes through submodels
  ↓
If no submodel classifies node to its type with high confidence
  ↓
Mark as anomalous node
  ↓
Trace 2-hop ancestors / descendants and raise alert
```

## 6. 数据集与实验

- 数据集：
  - StreamSpot dataset；
  - UNICORN SC-2 supply-chain dataset；
  - DARPA TC third engagement：THEIA、Trace、CADETS、fivedirections。
- 数据规模：
  - StreamSpot：benign 500 graphs，attack 100 graphs。
  - UNICORN SC-2：benign 125 graphs，attack 25 graphs。
  - DARPA TC：
    - THEIA Ubuntu：3,505,326 benign nodes，25,362 abnormal nodes，102,929,710 edges。
    - Trace Ubuntu：2,416,007 benign nodes，67,383 abnormal nodes，6,978,024 edges。
    - CADETS FreeBSD：706,966 benign nodes，12,852 abnormal nodes，8,663,569 edges。
    - fivedirections Windows：569,848 benign nodes，425 abnormal nodes，9,852,465 edges。
- 标注方式：
  - StreamSpot / SC-2 使用 graph-level labels。
  - DARPA TC 使用公开 ground truth 标注 abnormal nodes。
  - 节点级评价中，若异常节点本身或其 2-hop ancestors / descendants 被检测为异常，计为 true positive。
- Baseline：
  - StreamSpot；
  - UNICORN；
  - ProvDetector。
- 指标：
  - Precision、Recall、Accuracy、F-score、FPR；
  - processing speed、CPU utilization、memory usage；
  - adaptive evasion FNR。
- 主要结果：
  - StreamSpot dataset：
    - StreamSpot：Precision 0.72，Recall 1.0，Accuracy 0.69，F-score 0.75。
    - UNICORN：Precision 0.95，Recall 0.97，Accuracy 0.99，F-score 0.96。
    - THREATRACE：Precision/Recall/Accuracy/F-score 均为 1.0。
  - UNICORN SC-2：
    - UNICORN：Precision 0.75，Recall 0.80，Accuracy 0.77，F-score 0.78。
    - ProvDetector：Precision 0.67，Recall 0.60，Accuracy 0.65，F-score 0.63。
    - THREATRACE K=1：Precision 0.81，Recall 0.79，Accuracy 0.80，F-score 0.80。
    - THREATRACE K=2：Precision 0.91，Recall 0.96，Accuracy 0.93，F-score 0.93。
  - DARPA TC node-level：
    - THEIA：Precision 0.87，Recall 0.99，F-score 0.93，FPR 0.001。
    - Trace：Precision 0.72，Recall 0.99，F-score 0.83，FPR 0.011。
    - CADETS：Precision 0.90，Recall 0.99，F-score 0.94，FPR 0.002。
    - fivedirections：Precision 0.67，Recall 0.92，F-score 0.80，FPR 0.0003。
  - DARPA TC graph-level：
    - THREATRACE 与 UNICORN 在 THEIA、CADETS、fivedirections、Trace 上均达到 Precision/Recall/F-score 1.0。
- 消融/参数：
  - K=2 优于 K=1，说明适度邻居信息有助于检测。
  - R 是概率比阈值，提高 R 会训练更多子模型并降低误报/漏报风险，但过高可能导致模型难收敛。
  - T 是等待时间阈值，避免 streaming early detection 中尚未完成行为的 benign node 被误判。
  - T_hat 是容忍阈值，用于控制多少异常节点触发系统级告警。
- 鲁棒性：
  - 论文设计 optimization-based evasion attack。
  - 在 attacker knows model 场景下，FNR 随扰动预算增大而升高，但从约 0.04 增至约 0.07，作者认为仍可接受。
- 运行开销：
  - THREATRACE 速度和资源开销可接受，但 CPU 和内存高于 UNICORN / ProvDetector，因为它是 deep-learning-based method。

## 7. 关键知识点

### 概念

- Node-level detection：把异常定位到具体系统实体，而不是只给整图打标签。
- Benign node role：同一 node type 下，不同进程/文件可能承担不同隐藏角色。
- Dominant label：显式节点类型，如 process、file、socket。
- Hidden label：同一显式类型下的具体功能角色，论文中不直接观测，只用多模型隐式学习。
- Closed-world assumption：训练集覆盖所有 benign behavior，未覆盖行为视为异常；这是 anomaly detection 的核心风险。

### 技术路线

- THREATRACE 的核心判断逻辑：

```text
如果一个 benign process 的局部结构应当像 process，
但执行时它的 in/out edge-type distribution + K-hop context
无法被任何子模型高置信分类为 process，
则该 process 的角色偏离正常，可能是异常节点。
```

- 它比 UNICORN 更细：

```text
UNICORN: whole provenance graph -> graph sketch -> graph-level alarm
THREATRACE: provenance graph -> node role learning -> anomalous nodes + local tracing
Kairos: provenance graph -> edge anomalousness -> attack summary graph
```

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| anomalous node detection | 异常节点检测 | THREATRACE 核心任务 |
| node-level tracing | 节点级追踪 | 定位异常实体 |
| active node | 活跃节点 | 当前用于训练/检测的节点 |
| related node | 相关节点 | 可在 K-hop 内到达 active node 的节点 |
| dominant label | 显式标签 / 主标签 | node type |
| hidden label | 隐式标签 | 同一 node type 下的具体角色 |
| multi-model framework | 多模型框架 | 多个 GraphSAGE 子模型 |
| closed-world assumption | 封闭世界假设 | 未见正常行为会被当异常 |

## 8. 优点

- 把 detection granularity 从 graph-level 推到 node-level，更接近调查证据。
- 不需要攻击样本或 attack pattern，适合未知攻击检测。
- 使用 GraphSAGE inductive learning，适合 evolving provenance graph。
- 多模型框架专门处理节点类别不平衡和同类节点隐藏角色差异。
- DARPA TC 上给出了 node-level ground truth 评价，比只测 graph-level 更有价值。

## 9. 局限

- 仍依赖干净且足够覆盖的 benign training data，存在 closed-world assumption。
- 在 DARPA TC 中仍有较多 false positives，作者建议用 whitelist 和更多子模型缓解。
- 不能自动构造 attack story；论文明确说它能 trace anomaly，但不能 reconstruct attack story。
- provenance graph 粒度不足时无法检测，如文件内部恶意代码、线程级威胁等。
- 深度学习方法开销高于 UNICORN / ProvDetector。
- 只研究了一类 optimization-based evasion attack，未覆盖 poisoning attack、graph backdoor 等更强威胁。

## 10. 对我选题的启发

- 可以直接借鉴：
  - node-level evidence 比 graph-level alarm 更适合后续 LLM 解释。
  - `异常节点 + 2-hop context` 可作为最小 provenance evidence unit。
  - “节点角色偏离”可作为攻击意图/ATT&CK 映射的触发信号。
- 可以改进：
  - 将 anomalous nodes 自动组织为 attack story / InfoPath / attack summary graph。
  - 用 LLM 将异常节点局部子图解释为 ATT&CK technique、tactic 或 intent。
  - 加入 evidence sufficiency：异常节点是否足以支持某个归因/意图结论？
- 可以作为 baseline：
  - node-level provenance graph learning baseline。
  - 与 UNICORN 的 graph-level、Kairos 的 edge-level、DEPCOMM 的 InfoPath-level 对比。
- 可以用于研究动机：
  - 现有方法能定位异常实体，但还不能把这些实体转换成分析师可直接理解的攻击故事、意图和归因证据。
- 可以用于实验设计：
  - 评价维度应拆成 detection、tracing、story reconstruction、ATT&CK/intent mapping、evidence grounding。

## 11. 可转化的研究问题

1. 如何将 THREATRACE 输出的 anomalous nodes 聚合为可读的 attack story 或 attack summary graph？
2. 如何把 `anomalous node + 2-hop context` 映射到 ATT&CK technique / tactic / attack intent？
3. LLM 能否作为 node-level anomaly explanation layer，生成带证据引用的调查叙事？
4. 如何降低 THREATRACE 这类 anomaly detector 的 false positives，并让模型在证据不足时拒绝上升到归因结论？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| UNICORN | UNICORN 做 graph-level anomaly detection；THREATRACE 做 node-level anomaly detection/tracing。 |
| Kairos | Kairos 做 edge-level anomalousness 和 attack summary graph；THREATRACE 定位异常实体但不重建故事。 |
| DEPCOMM | DEPCOMM 从 POI 出发压缩 dependency graph 为 InfoPaths；THREATRACE 从异常节点出发做 local tracing。 |
| ProvDetector | ProvDetector 做 anomalous path / malware detection；THREATRACE 面向更一般 host threats。 |
| TechniqueRAG / Multi-Step LLM Pipeline | 它们做 CTI text -> ATT&CK；THREATRACE 的输出可作为日志侧 evidence，后续可接 ATT&CK/intent 映射。 |

## 13. 论文写作可引用句式

- Node-level provenance detectors such as THREATRACE move beyond graph-level alarms by localizing suspicious system entities, making them more suitable as evidence sources for investigation.
- However, anomalous node localization alone does not reconstruct attack stories or infer adversarial intent, leaving a semantic gap between detection and analyst-facing reasoning.
- A practical LLM-assisted provenance analysis system should preserve node-level evidence while elevating it into ATT&CK, intent, and evidence-sufficiency layers.

## 14. 我的批注与疑问

- THREATRACE 很适合放在 Project05 的“日志证据粒度演进表”中：graph-level -> node-level -> edge-level -> path/summary-level。
- 它的 2-hop tracing 是可解释性的起点，但还不是人类真正想看的 attack narrative。
- 对当前选题最有价值的不是复现 GraphSAGE，而是把异常节点/边/路径转成可引用证据，再让 LLM 做受约束语义解释。
- 后续读 PROGRAPHER 时要重点比较：PROGRAPHER 是 graph embedding/anomaly detection，是否比 THREATRACE 更适合解释或只是更换表征。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是，作为 node-level provenance graph learning 基线进入主线。
