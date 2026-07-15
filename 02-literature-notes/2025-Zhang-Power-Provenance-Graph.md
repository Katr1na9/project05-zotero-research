# Provenance Graph Modeling and Feature Enhancement for Power System APT Detection

## 1. 基本信息

- 中文译名：面向电力系统 APT 检测的溯源图建模与特征增强
- 作者：Xuan Zhang; Haohui Su; Lincheng Li; Lvjun Zheng
- 年份：2025
- Venue：Electronics, 14(21), 4241
- DOI：https://doi.org/10.3390/electronics14214241
- 开放全文：https://www.mdpi.com/2079-9292/14/21/4241
- 阅读日期：2026-07-14
- 阅读优先级：重点读（统一建图与边重构近邻）
- 所属主题：PROV-DM / APT Detection / Temporal GNN / Edge Reconstruction / CICAPT-IIoT

## 2. 一句话总结

本文把 CICAPT-IIoT 和 Unicorn Wget 的 provenance 事件映射到 PROV-DM，以标签辅助的时间切窗构造图样本，再用时间编码、节点掩码和边重构的 GAT 自编码器增强表示并执行异常检测；它证明统一图建模和 edge reconstruction 可单独成为论文贡献，但并未使用 CICAPT-IIoT 的原始 PCAP 建立独立流量子图，边重构也只是已有单图拓扑的自监督任务，不是 packet-log 跨源关系识别。

## 3. 研究问题

- 如何把电力系统相关的异构安全事件映射为统一且可解释的 provenance 语义？
- 如何同时编码 APT 的时间演化、节点类型与图结构？
- 节点掩码和边重构能否提高无监督/一类式 APT 异常检测性能？
- 在电力领域数据稀缺时，通用 provenance 数据能否通过领域语义映射复用？

## 4. 核心贡献

1. 基于 W3C PROV-DM 定义 Entity、Activity、Agent 及关系，并扩展电力业务 namespace。
2. 将 CICAPT-IIoT 的 Process/Artifact 和四类关系映射到 PROV-DM。
3. 用 KDE 识别 burst/calm 区间，并按等事件数量切分连续日志为 snapshot graph。
4. 拼接 one-hot 类型与 Functional Time Encoding，训练 GAT 自编码器重建掩码节点和采样边。
5. 在 CICAPT-IIoT 与 Unicorn Wget 上以 KNN 评价图级异常检测，并做三个模块消融。

## 5. 方法框架

### 输入

- CICAPT-IIoT 的 provenance event records；论文没有把该数据集随附 PCAP 作为独立输入。
- Unicorn Wget 的 CamFlow provenance graphs。
- 节点/边类型、时间戳和恶意/良性事件标签。

### 输出

- 映射到 PROV-DM/电力 namespace 的 snapshot provenance graphs。
- 图级 latent embeddings 与良性/异常判定。
- 节点和边重构训练信号。

### 关键模块

| 模块 | 作用 | 对本支线的边界意义 |
|---|---|---|
| PROV semantic mapping | 统一节点/边语义 | 可作为日志侧 schema baseline |
| Label-assisted snapshotting | 将连续事件切成图样本 | 可能破坏完整链并引入标签辅助预处理 |
| Functional Time Encoding | 表达相对时间与周期性 | 可用于源内边，但不能证明因果 |
| Edge reconstruction | 区分真实边与均匀负采样边 | 是单图自监督，不是跨源 pair linking |

### 方法流程

```text
provenance event records
  -> PROV-DM/电力语义映射
  -> KDE burst/calm + 等事件切窗
  -> node/edge type + time encoding
  -> GAT encoder + node masking + edge reconstruction
  -> graph pooling -> KNN anomaly detection
```

## 6. 数据集与实验

- Unicorn Wget：125 个良性、25 个恶意 batch graph，平均图规模约 3-4 万节点、12-15 万边。
- CICAPT-IIoT：作者从 event-level provenance records 人工切出 49 个良性、15 个恶意 snapshot；原始数据虽包含 PCAP，但本方法只处理 provenance records。
- CICAPT-IIoT 中 80% 良性 snapshot 用于训练，其余良性与全部恶意用于测试；测试样本极少。
- Full model 在 Wget 上 AUC/F1/Precision/Recall 为 0.99/0.97/0.95/0.98；在 CICAPT-IIoT 上为 0.88/0.91/0.87/0.97。
- 去除 edge reconstruction 后 Wget F1 从 0.97 降至 0.93，CICAPT-IIoT 从 0.91 降至 0.87；但只证明表示学习对图级分类有益。
- 作者承认 CICAPT-IIoT snapshot 来自同一连续攻击时间线，样本不独立且每个 snapshot 只覆盖部分攻击阶段。

## 7. 关键知识点

- `PROV-DM mapping + temporal graph + edge reconstruction` 已有完整实现，不能作为宽泛创新。
- 数据集中“存在 PCAP”不等于论文“使用 raw PCAP”；必须按实际消费字段判断模态。
- 其 edge reconstruction 的正例来自原图、负例为均匀随机节点对，通常远易于 NAT/时钟漂移/共享 IP 下的跨源 hard-negative 配对。
- snapshot graph 的切分与标签都使用恶意事件分布；若在全数据上先计算 burst threshold/全局恶意率再划分，会形成 label-informed preprocessing 风险。
- 图级分类指标不能评价建图边是否正确，也不能评价攻击链完整性与意图忠实度。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Provenance graph modeling | 溯源图建模 | 本文主要为日志事件语义映射 |
| Functional Time Encoding | 函数式时间编码 | 连续时间到周期特征空间的映射 |
| Edge reconstruction | 边重构 | 自监督 topology reconstruction |
| Snapshot partitioning | 快照切分 | 可能截断跨窗口攻击链 |

## 8. 优点

- 清楚区分语义标准化、时间特征、结构学习和下游检测。
- 公开数据可获得，PROV 映射表与切窗算法描述较完整。
- 同时报告节点掩码、时间编码和边重构消融。
- 主动讨论 CICAPT-IIoT 的样本依赖、图规模和链碎片问题。

## 9. 局限

- 实验没有真正消费原始网络包；所谓多源异构主要是统一 provenance event schema。
- 图构造时合并同一节点对的重复同类边，会损失事件次数与独立 raw-record 锚点。
- KDE burst/calm 和 snapshot label 使用标签信息，且处理顺序与数据划分边界不够清楚。
- CICAPT-IIoT 只有 64 个 snapshot，来自同一时间线，统计独立性和外部效度弱。
- 均匀负采样让边重构任务过于容易，未测试难负例、跨源配对或校准。
- 只评价图级异常检测，没有 node/edge/chain/intent/replay 指标。
- 电力语义映射主要由示例和专家概念定义支撑，未评价映射正确率。

## 10. 对我选题的启发

- 图构建可以成为论文贡献，但必须评价**构建对象本身**，不能只用下游异常分类证明。
- 双线方案需要 traffic subgraph 与 log subgraph 各自保留重复事件、时间、frame/record ID 和来源哈希，避免简单去重破坏审计性。
- 跨源边训练必须用真实/可控关联真值和 hard negatives，不能沿用均匀随机负采样。
- 切窗不能使用测试标签；应按 campaign/session 先隔离，再在训练集拟合窗口或改用无标签事件边界。

## 11. 可转化的研究问题

1. source-preserving 双线建图相较 PROV-DM 单图映射，是否提高 edge fidelity 和 chain coverage？
2. 跨源 hard-negative 关系学习与校准，是否比单图 edge reconstruction 更能抵抗共享 IP、时钟漂移和并发连接？
3. 不使用标签的事件边界与跨窗口链连接，能否降低 snapshot fragmentation？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CICAPT-IIoT | 本文使用其 provenance event records；本支线可进一步使用同步 PCAP 做真实双线实验 |
| APMP | 两者均预测/重构图边；APMP 监督语义关系，本文自监督恢复已有拓扑 |
| BotFence | BotFence 真正采集 host event + packet；本文没有独立 packet graph |
| UTLParser | UTLParser 统一异构日志三元组；本文在统一图上做时间/结构表示学习 |
| Project03 支线 | 提供 PROV 基线，同时暴露 raw-source preservation 与 edge-level evaluation 空缺 |

## 13. 论文写作可引用句式

- 现有工作已利用 PROV-DM 统一安全事件语义，并通过节点掩码和边重构增强 APT 图表示；然而，这类自监督拓扑恢复并不等价于原始流量与主机日志之间的跨源事件关联，其下游图级分类也无法直接验证建图忠实度。

## 14. 我的批注与疑问

- 论文引言多次称数据包含 network traffic，但实际算法输入为已解析 provenance records；引用时必须保持这一差别。
- 用全局恶意率定义 snapshot label、用两类时间密度确定 burst threshold，可能让攻击标签参与样本构造。
- `K=参考集 50%` 的 KNN 设置非常大，且缺少独立验证集调参细节。
- 将重复边合并后再做 edge reconstruction，会把事件级证据问题转化为静态拓扑问题。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是（统一建图与边重构近邻）
