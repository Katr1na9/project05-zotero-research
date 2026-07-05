# ProGraPher: An Anomaly Detection System based on Provenance Graph Embedding

## 1. 基本信息

- 英文题名：ProGraPher: An Anomaly Detection System based on Provenance Graph Embedding
- 中文译名：ProGraPher：基于溯源图嵌入的异常检测系统
- 作者：Fan Yang; Jiacen Xu; Chunlin Xiong; Zhou Li; Kehuan Zhang
- 年份：2023
- Venue：32nd USENIX Security Symposium
- DOI / URL：https://www.usenix.org/conference/usenixsecurity23/presentation/yang-fan
- Zotero key：待补
- 阅读日期：2026-07-05
- 阅读优先级：重点读
- 所属主题：Provenance-based Detection / Graph Embedding / Snapshot-level Anomaly Detection / Indicator Generation

## 2. 一句话总结

PROGRAPHER 把长时间运行的 provenance graph 切成时间有序的重叠 snapshot，用 graph2vec 学每个 snapshot 的 whole-graph embedding，再用 TextRCNN 根据历史 snapshot embedding 预测下一个 snapshot；如果真实 embedding 与预测偏离过大则报警，并通过 Rooted Subgraph 排名把 graph-level 异常落回到可供分析师查看的可疑节点。

## 3. 研究问题

- 论文要解决的问题是什么？
  - 现有 provenance anomaly detection 要么依赖攻击知识，要么只给整图报警，要么受 dependency explosion 影响难以在大规模日志上连续运行。
  - graph-level detector 能降低标注需求，但报警后分析师仍要在大量节点中定位攻击相关实体。
  - 系统行为具有时间动态性，单独看一个静态全图会丢失正常行为随时间演化的模式。
- 为什么重要？
  - Project05 如果要把日志侧证据接入 LLM/ATT&CK/intent/attribution，需要的不只是“这段日志异常”，还要有可追溯的局部证据。
  - PROGRAPHER 提供了从 snapshot-level anomaly 到 suspicious node indicator 的桥梁。
- 和威胁归因、攻击链、意图识别、CTI、ATT&CK、RAG 的关系是什么？
  - 它不是 actor attribution 或 CTI 文本理解方法。
  - 它属于日志/provenance 侧的 evidence generator：输出异常 snapshot 和候选可疑节点。
  - 后续可以把这些节点、Rooted Subgraph 和时间序列异常作为 LLM 解释、ATT&CK 映射、意图推断或证据充分性判断的输入。

## 4. 核心贡献

1. 任务贡献：在无需攻击样本和攻击知识的前提下做 provenance graph anomaly detection。
2. 表征贡献：把长 provenance graph 切成时间有序 snapshot，并用 graph2vec 做 whole graph embedding。
3. 时序贡献：用 sequence model 学习 benign snapshot sequence 的动态演化，预测下一时刻 snapshot embedding。
4. 调查贡献：提出 key indicator generator，通过 Rooted Subgraph 排名把异常 snapshot 转换为可疑节点集合。
5. 工程贡献：在公开 DARPA/StreamSpot/ATLAS 数据和真实商业 EDR 数据上评估，展示比 UNICORN 更好的生产环境 AUC。

## 5. 方法框架

### 输入

- 数据类型：
  - 系统审计日志；
  - provenance graph；
  - benign graphs for training。
- 图元素：
  - 节点类型包括 PROCESS、NETFLOW、PACKETSOCKET、FILE、PIPELINE、MEMORY、PRINCIPAL；
  - 边类型包括 CONNECT、SEND、ACCEPT、LISTEN、OPEN、READ、WRITE、COPY、LOAD、UNLINK、MODIFY_ATTRIBUTES、CLONE、EXECUTE、TERMINATE、MEMORY_PROTECT、MEMORY_MAP。
- 使用字段：
  - 主要使用 node type 和 edge type；
  - 未使用更丰富的事件字段，作者将其留作 future work。
- 威胁模型：
  - 假设攻击者不能篡改 audit logs 或 end-host monitor；
  - log integrity attack 不在本文范围内。

### 输出

- anomaly score / abnormal snapshot；
- top-K suspicious Rooted Subgraphs；
- 从 suspicious RSG 映射回原始 snapshot 中的可疑节点；
- 不输出完整 attack story、actor 归因或 ATT&CK 技术标签。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Snapshot Builder | 从 streaming logs 构建固定规模、重叠的 temporal snapshots | 缓解 dependency explosion，并形成可建模的时间序列 |
| Encoder | 用 graph2vec 学习 snapshot embedding | 将复杂图压缩成可预测向量 |
| Anomaly Detector | 用 TextRCNN 预测下一个 snapshot embedding | 把异常定义为偏离正常时间动态 |
| Key Indicator Generator | 排名异常贡献最高的 Rooted Subgraphs 并映射回节点 | 从 graph-level alarm 回到 analyst-facing evidence |

### 方法流程

```text
Audit logs
  -> Provenance graph stream
  -> Snapshot builder: fixed-size overlapping snapshots
  -> Graph2vec encoder: snapshot -> graph embedding
  -> TextRCNN anomaly detector: previous k embeddings -> predicted next embedding
  -> Compare predicted embedding with actual embedding
  -> Abnormal snapshot if distance > threshold
  -> Rank Rooted Subgraphs by anomaly contribution
  -> Map suspicious RSGs back to nodes for analyst inspection
```

### Snapshot Builder

- 维护一个 cache graph。
- 当节点数达到 snapshot size n 时输出第一个 snapshot。
- 后续当 graph size 达到 `n * (1 + fr)` 时，删除最早的 `n * fr` 个节点并输出新 snapshot。
- 相邻 snapshots 的重叠比例约为 `1 - fr`。
- 论文默认 forgetting rate `fr = 1/3`。

### Encoder

- 使用 graph2vec，思想类似 doc2vec。
- 对每个 snapshot 中每个节点抽取 degree 0 到 D 的 Rooted Subgraph。
- 使用 Weisfeiler-Lehman graph kernel 生成子图标签。
- 原始 WL 主要考虑节点标签，本文扩展到同时考虑 node type 和 edge type。
- 通过负采样学习 graph embedding 和 RSG 的共现关系。

### Anomaly Detector

- 输入为一段 snapshot embedding sequence。
- 使用 TextRCNN 结合双向 recurrent layer 和 convolution layer。
- 根据前 k 个 snapshot embedding 预测下一个 snapshot embedding。
- 测试时计算预测 embedding 与真实 embedding 的距离，超过阈值则判定异常。

### Key Indicator Generator

- 对异常 snapshot 中的 RSG 计算异常贡献并排序。
- 选取 top-K suspicious RSGs。
- 由于一个 RSG 模式可能匹配多个真实节点，需要在 snapshot 中搜索匹配节点。
- 最终把匹配节点作为 key indicators 提供给分析师。

## 6. 数据集与实验

### 数据集

| 数据集 | Benign | Attack | 规模 |
|---|---:|---:|---:|
| StreamSpot-DS | 500 | 100 | 8.3 GB |
| DARPA3 CADETS | 127 | 4 | 9.2 GB |
| DARPA3 CLEARSCOPE | 116 | 4 | 2 GB |
| DARPA3 THEIA | 66 | 3 | 27 GB |
| ATLAS-DS | 10 | 10 | 1.1 GB |
| DARPA ENGAGEMENT | 24 | 2 | 38 GB |
| Production EDR | 58,692 | 486 | 43 GB |

生产 EDR 数据来自商业 EDR，在 18K endpoints、100 多家公司中采集。原始日志约 332,433,377 events / 180 GB，预处理后用于 7 天训练/验证和 2 天测试。

### Baseline

- UNICORN；
- ATLAS；
- 论文也在相关工作表中对比 ShadeWatcher、SIGL、ATLAS、ProvDetector、Prov-Gem、UNICORN。

### 主要检测结果

- StreamSpot-DS：
  - UNICORN：P/R/Acc/F1 = 0.85/1.00/0.91/0.92；
  - PROGRAPHER：P/R/Acc/F1 = 0.90/1.00/0.94/0.94。
- DARPA3 CADETS：
  - UNICORN：0.31/1.00/0.44/0.47；
  - PROGRAPHER：1.00/1.00/1.00/1.00。
- DARPA3 CLEARSCOPE：
  - UNICORN：1.00/0.75/0.93/0.86；
  - PROGRAPHER：0.80/1.00/0.93/0.89。
- DARPA3 THEIA：
  - UNICORN：0.67/0.67/0.80/0.67；
  - PROGRAPHER：1.00/1.00/1.00/1.00。
- ATLAS-DS 与 DARPA ENGAGEMENT：
  - PROGRAPHER 均达到 P/R/Acc/F1 = 1.00。
- Production EDR：
  - PROGRAPHER AUC = 0.943；
  - UNICORN AUC = 0.542；
  - 论文给出的例子是 PROGRAPHER 在 14% FPR 时达到 94% TPR。

### Indicator Generation

- 有效性定义：
  - 给定 ground-truth attack node，如果 indicator 命中该节点或其 3-hop 邻域，则视为 effective。
- Effective rate：
  - CADETS：K=1 为 0.88，K=4/5 达到 1.00；
  - THEIA：K=1 为 0.89，K>=2 达到 1.00；
  - CLEARSCOPE：K=1 到 K=5 均为 1.00。
- Coverage rate：
  - CADETS：K=1 为 0.61，K=4/5 为 0.96；
  - THEIA 与 CLEARSCOPE：K=1 到 K=5 均为 1.00。
- 工作量降低：
  - K=4 时，平均覆盖节点 5,748 / 总节点 13,600；
  - 相比检查完整 snapshot，分析师工作量平均降低 57.7%；
  - 相比 UNICORN 的 snapshot 输出，PROGRAPHER 需要检查的节点约少 7.1 倍。

### 工程设置

- Python 3.7，约 2000 行代码。
- Encoder：TensorFlow 1.4。
- Detector：PyTorch 1.10。
- Snapshot size：小图 300，大图 900。
- Sequence length：按数据集设置为 32、128 或 176。
- Graph embedding dimension：256。
- WL depth：小图 d=3，大图 d=4。
- Negative samples：15。
- Detector hidden dimension：128；hidden layers：5；dropout：0.2。

## 7. 关键知识点

### 概念

- Snapshot：从长时间 provenance graph 中按节点规模和时间顺序切出的重叠子图。
- Whole graph embedding：把整个 snapshot 压缩为一个向量，而不是只嵌入单个节点或边。
- Rooted Subgraph：以某个节点为根，在一定 WL depth 内展开的局部子图模式。
- Key indicator：异常 snapshot 中最能解释异常的局部图模式或匹配节点。
- Transductive learning：测试阶段依赖训练阶段见过的 RSG vocabulary。

### 技术路线

```text
UNICORN: provenance stream -> graph sketch/histogram -> graph-level alarm
THREATRACE: provenance graph -> node role learning -> anomalous nodes + 2-hop tracing
PROGRAPHER: provenance graph -> snapshot sequence -> graph embedding prediction -> suspicious RSG/node indicators
Kairos: provenance graph -> edge anomaly -> attack summary graph
DEPCOMM: audit dependency graph -> POI-driven summarization -> InfoPaths
```

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| snapshot | 快照 / 图快照 | provenance graph 的时间片段 |
| snapshot builder | 快照构建器 | PROGRAPHER 核心模块 |
| whole graph embedding | 整图嵌入 | snapshot-level representation |
| Rooted Subgraph | 根子图 | RSG |
| RSG | 根子图 | Rooted Subgraph 缩写 |
| key indicator | 关键指示物 / 关键指标 | PROGRAPHER 中指向可疑节点的证据 |
| indicator generation | 指示物生成 | 把异常 snapshot 落到节点 |
| forgetting rate | 遗忘率 | 控制 snapshot 滑动删除比例 |
| transductive learning | 传导式学习 | 测试依赖训练词表/结构 |
| inductive learning | 归纳式学习 | 可泛化到未见结构 |

## 8. 优点

- 不需要攻击样本或攻击知识，适合未知攻击检测。
- 用 snapshot sequence 处理长时间 provenance graph，缓解 dependency explosion。
- 比纯 graph-level alarm 更进一步，能输出可疑节点 indicators。
- 在真实 EDR 数据上明显优于 UNICORN，说明方法不只是在小型公开数据上有效。
- Key indicator generation 对 Project05 很有价值：它提供了“异常图 -> 局部证据”的接口。

## 9. 局限

- 仍依赖 benign training data 覆盖正常行为；正常行为变化会导致 concept drift 和 false positives。
- 当前设计偏 transductive：测试中出现训练未见 RSG 时需要重新训练；作者把 GraphSAGE 式 inductive learning 作为未来方向。
- 使用字段较少，主要依赖 node type 和 edge type，未充分利用命令行、路径、参数、用户、进程名等高语义字段。
- Key indicator 只是可疑节点/局部结构，不是完整 attack story。
- 威胁模型排除了攻击者篡改 audit logs 或监控组件的情况。
- 鲁棒性主要考虑随机事件注入，更高级的 mimicry attack 仍可能绕过。

## 10. 对我选题的启发

- 可以直接借鉴：
  - snapshot sequence 可作为“日志证据时间片”的组织方式；
  - suspicious RSG / node indicators 可以作为 LLM 解释层的输入；
  - prediction error 可作为 evidence salience 的来源之一。
- 可以改进：
  - 把 key indicators 自动组织成 attack story、ATT&CK tactic/technique、intent hypothesis；
  - 为每个 indicator 生成证据引用和置信度，而不是只给节点列表；
  - 引入高语义字段，增强 LLM 可解释性。
- 可以作为 baseline：
  - provenance graph embedding baseline；
  - graph-level anomaly + indicator generation baseline；
  - 与 UNICORN、THREATRACE、Kairos、DEPCOMM 形成日志侧证据粒度对比。
- 对研究动机的贡献：
  - PROGRAPHER 说明现有方法已经能从整图报警推进到局部节点提示；
  - 但“节点提示”距离“攻击意图/归因解释”仍有语义鸿沟，这正是 LLM 增强层可以介入的位置。

## 11. 可转化的研究问题

1. 如何把 PROGRAPHER 的 suspicious RSGs 转换为带证据引用的 ATT&CK technique / tactic 解释？
2. 如何把 snapshot-level temporal anomaly 与 CTI 文本中的 attack campaign 描述对齐？
3. LLM 能否根据 key indicators、节点上下文和历史 CTI 生成可审计的 intent hypothesis？
4. 如何判断一个异常 snapshot 的证据是否足以支持 actor attribution，何时应该拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| UNICORN | 都做 graph-level anomaly detection；PROGRAPHER 用 graph embedding + sequence prediction，并进一步输出节点 indicators。 |
| THREATRACE | THREATRACE 直接做 node-level anomaly detection；PROGRAPHER 从 snapshot-level anomaly 通过 RSG 映射回节点。 |
| Kairos | Kairos 做 edge anomaly 和 attack summary graph；PROGRAPHER 做 snapshot embedding anomaly 和可疑节点提示。 |
| DEPCOMM | DEPCOMM 从 POI 出发压缩 dependency graph；PROGRAPHER 从异常 snapshot 出发定位 suspicious RSGs/nodes。 |
| TechniqueRAG / CTIBench / CTIConnect | 这些属于 CTI/LLM/RAG 语义层；PROGRAPHER 可提供日志侧结构证据。 |
| Opinion Pools | PROGRAPHER 的 anomaly score / indicator 可作为一个 attributor 或 evidence module 输入概率融合框架。 |

## 13. 论文写作可引用句式

- Snapshot-based provenance embedding methods such as PROGRAPHER reduce dependency explosion by modeling temporal subgraphs rather than monolithic audit graphs.
- Although PROGRAPHER can identify suspicious indicators within abnormal snapshots, it does not translate these indicators into ATT&CK-level semantics, adversarial intent, or actor attribution.
- This leaves a semantic gap between provenance anomaly evidence and analyst-facing threat reasoning, motivating an LLM-assisted explanation and evidence-grounding layer.

## 14. 我的批注与疑问

- PROGRAPHER 比 UNICORN 更适合 Project05，因为它至少尝试把报警落回节点证据。
- 它和 THREATRACE 的差异很关键：THREATRACE 是 node role deviation，PROGRAPHER 是 snapshot temporal prediction deviation。
- 对硕士论文而言，不必复现 graph2vec/TextRCNN 本身，价值更可能在“如何把 indicators 解释为可审计的攻击语义”。
- 如果后续做实验，可以把 PROGRAPHER/THREATRACE 的输出抽象成统一 evidence unit，再比较不同 LLM/RAG/KG 解释策略。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是，作为 provenance graph embedding 与 snapshot-level anomaly baseline 进入主线。
