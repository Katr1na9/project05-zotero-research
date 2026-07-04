# KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance

## 1. 基本信息

- 英文题名：KAIROS: Practical Intrusion Detection and Investigation using Whole-system Provenance
- 中文译名：KAIROS：基于全系统溯源的实用入侵检测与调查
- 作者：Zijun Cheng; Qiujian Lv; Jinyuan Liang; Yan Wang; Degang Sun; Thomas Pasquier; Xueyuan Han
- 年份：2024
- Venue：IEEE Symposium on Security and Privacy, S&P 2024
- DOI / arXiv / URL：arXiv:2308.05034 / https://github.com/ProvenanceAnalytics/kairos
- 阅读日期：2026-07-01
- 阅读优先级：必读
- 所属主题：Provenance Graph / PIDS / Intrusion Detection / Attack Reconstruction / Threat Investigation

## 2. 一句话总结

KAIROS 从系统审计日志构建 whole-system provenance graph，并用 temporal graph neural network 的 encoder-decoder 模型学习正常系统行为，在运行时发现异常事件，再基于异常边和信息流自动生成紧凑的攻击摘要图，用于入侵检测和攻击调查。

## 3. 研究问题

- 现代 APT 攻击常跨应用、跨进程、跨主机，并以 low-and-slow 方式长期潜伏，单点 IOC 或单应用检测很难覆盖完整攻击链。
- 现有 provenance-based intrusion detection systems, PIDSes，通常在四个维度之间取舍：scope、attack agnosticity、timeliness、attack reconstruction。
- 基于签名或攻击规则的方法能够解释攻击，但依赖已知攻击知识，难以发现未知攻击。
- 基于异常检测的方法能发现未知攻击，但往往只输出异常分数、异常图或异常节点，不能直接帮助分析员理解完整攻击故事。
- 系统级 provenance graph 规模极大，真实数据中攻击边可能只占 0.01% 左右，人工从百万级边中回溯攻击链几乎不可行。

## 4. 核心贡献

1. 提出 KAIROS，一个同时兼顾全系统范围、攻击无关性、运行时检测和攻击重建的 PIDS。
2. 使用 temporal graph neural network 学习 provenance graph 的时空结构变化，为每条系统事件边计算 reconstruction error。
3. 提出基于 suspicious nodes 的 time window queue 机制，用于捕捉 low-and-slow APT 中跨时间窗口的异常活动。
4. 将异常边按信息流和 reconstruction error 组织成候选攻击摘要图，显著降低人工调查规模。
5. 在 Manzoor et al.、DARPA TC E3/E5 和 OpTC 等公开数据集上验证检测性能、攻击重建能力和运行时开销。

## 5. 方法框架

### 输入

- 系统审计日志；
- Windows ETW、Linux Audit、CamFlow、THEIA、CADETS、ClearScope 等 provenance capture 系统输出；
- 训练阶段的 benign provenance graphs；
- 运行阶段持续到来的 provenance edge stream。

### 输出

- 运行时异常告警；
- anomalous time window queues；
- compact attack summary graphs；
- 可供系统管理员调查的攻击脚印图。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Graph Construction and Representation | 将审计事件转换成有向、带时间戳的 provenance graph | 将日志统一建模为进程、文件、socket 等实体及其交互 |
| Hierarchical Feature Hashing | 对文件路径、IP 地址等层级属性编码 | 保留路径/IP 的层级相似性，降低特征维度 |
| Graph Learning | 用 TGN encoder 和 MLP decoder 重构边类型 | reconstruction error 可作为细粒度异常度 |
| Anomaly Detection | 将异常边聚合为 suspicious nodes 和 time window queues | 适合捕捉跨长时间的 low-and-slow 攻击 |
| Anomaly Investigation | 对异常队列做图约简和 Louvain 社区发现 | 从巨大日志图中生成可读攻击摘要图 |
| Model Retrain | 用确认的 benign false positives 增量更新模型 | 缓解 concept drift，但存在 poisoning 风险 |

### 方法流程

```text
系统审计日志
  ↓
Whole-system provenance graph：process / file / socket + system events
  ↓
Hierarchical feature hashing：节点属性编码
  ↓
Temporal graph learning：TGN encoder + MLP decoder
  ↓
Edge-level reconstruction error
  ↓
Suspicious nodes：异常性 + 稀有性
  ↓
Time window queues：跨窗口关联 suspicious nodes
  ↓
Anomalous queue detection
  ↓
Graph reduction + Louvain community discovery
  ↓
Attack summary graph
```

## 6. 关键知识点

### PIDS 的四个评价维度

| 维度 | 含义 | KAIROS 的做法 |
|---|---|---|
| Scope | 是否能覆盖跨应用、跨主机、全系统活动 | 分析 whole-system provenance graph |
| Attack Agnosticity | 是否不依赖已知攻击签名或规则 | 只用 benign 数据训练异常检测模型 |
| Timeliness | 是否能运行时检测 | 按时间窗口流式处理 provenance edge stream |
| Attack Reconstruction | 是否能解释和重建攻击过程 | 输出 compact attack summary graph |

### Provenance graph 的表示

KAIROS 将系统事件表示为有向时间戳边：

```text
source node --event type/time--> destination node
```

节点主要包括：

- Process；
- File；
- Socket。

边主要包括：

- process-process：Start、Close、Clone；
- process-file：Read、Write、Open、Exec；
- process-socket：Send、Receive。

这和 EXTRACTOR 的 provenance graph 有明显对应关系，但 KAIROS 的图来自真实系统审计日志，而不是 CTI 文本。

### Graph learning 的核心思想

KAIROS 的模型只在 benign provenance graphs 上训练。

训练时：

```text
给定一条边出现前的邻域结构和节点历史状态
→ encoder 生成 edge embedding
→ decoder 预测这条边的类型
→ 用真实边类型计算 reconstruction error
```

测试时：

```text
如果某条边很像正常历史行为
→ reconstruction error 低

如果某条边的结构/时间上下文偏离正常行为
→ reconstruction error 高
→ 可能是攻击相关事件
```

### Temporal + Structural context

KAIROS 不只看一个事件本身，而是看：

- 这个进程过去和谁交互；
- 这个文件/进程/socket 的邻域结构如何变化；
- 事件出现的时间顺序；
- 当前交互是否符合该实体历史上的正常模式。

这对 process injection、C&C 通信、异常文件落地、横向移动等场景很重要，因为单独看某个系统调用可能很普通，但放在上下文里会异常。

### Time window queue

APT 常常是 low-and-slow 的：

```text
攻击事件 A
  隔很久
攻击事件 B
  隔很久
攻击事件 C
```

如果只看单个时间窗口，攻击痕迹容易被大量 benign 行为淹没。

KAIROS 的做法是：

```text
每个时间窗口中找 suspicious nodes
如果两个窗口共享 suspicious nodes
就把它们放进同一个 queue
```

这样可以把长时间跨度中的相关异常活动串起来。

### Suspicious node 的两个条件

KAIROS 判断一个节点可疑，需要同时考虑：

| 条件 | 含义 |
|---|---|
| Anomalousness | 节点关联的边 reconstruction error 高 |
| Rareness | 节点在 benign 时间窗口中很少出现 |

稀有性使用 IDF 思想：

```text
IDF(v) = ln(N / (Nv + 1))
```

其中 `N` 是总时间窗口数，`Nv` 是包含节点 `v` 的时间窗口数。

### Attack summary graph

检测到 anomalous time window queue 后，KAIROS 不直接把整个异常窗口交给分析员，而是：

```text
异常队列
  ↓
保留高 reconstruction error 边
  ↓
图约简
  ↓
Louvain 社区发现
  ↓
候选攻击摘要图
```

这个摘要图是 KAIROS 最接近“威胁溯源结果”的部分，因为它把攻击相关的进程、文件、socket 和因果边压缩成可读结构。

## 7. 数据集与实验

- Manzoor et al. dataset：SystemTap 采集的实验室 provenance graphs，包含 YouTube、Gmail、Video Game、Download、CNN 等 benign 场景，以及一个 drive-by download 攻击场景。
- DARPA TC E3/E5：模拟真实 APT 的公开数据集，包括 THEIA、CADETS、ClearScope 等不同 provenance capture 系统。
- DARPA OpTC：Windows 主机网络的大规模数据，包含 500 台主机 7 天 benign 活动和 3 天混合 benign/APT 活动。
- 实验平台：CentOS 7.9，20-core Intel Xeon Silver 4210 CPU，64 GB memory。
- 默认超参数：节点属性维度 16，节点状态维度 100，邻域采样 20，边 embedding 维度 200，时间窗口 15 分钟。

### 数据规模

| 数据集 | 节点数 | 边数 | 攻击边比例 |
|---|---:|---:|---:|
| Manzoor et al. | 999,999 | 89.8M | 3.165% |
| DARPA-E3-THEIA | 690,105 | 32.4M | 0.010% |
| DARPA-E3-CADETS | 178,965 | 10.1M | 0.012% |
| DARPA-E3-ClearScope | 68,549 | 9.7M | 0.006% |
| DARPA-E5-THEIA | 739,329 | 55.4M | 0.156% |
| DARPA-E5-CADETS | 90,397 | 26.5M | 0.003% |
| DARPA-E5-ClearScope | 91,475 | 40.0M | 0.010% |
| DARPA-OpTC | 9,485,265 | 75.0M | 0.045% |

### 主要结果

- 在所有数据集上，KAIROS 的 recall 均为 1.000，未漏报攻击时间窗口。
- 原始结果中 precision 受 false positives 影响，最低为 OpTC 的 0.579、E5-CADETS 的 0.438。
- 经过人工确认“fake FPs”和模型增量更新后，部分数据集 precision 明显提升，例如 E5-CADETS 从 0.438 提升到 1.000，OpTC 从 0.579 提升到 0.842。
- E5-ClearScope 中，用 5 月 15 日的 false positives 重新训练后，5 月 17 日结果从 precision 0.750 提升到 1.000。
- 与 Unicorn 比较，KAIROS 在 Manzoor、E3-CADETS、E3-THEIA、E3-ClearScope 上达到相同或更优表现。
- 与 ThreaTrace 比较，KAIROS 整体可比或更优，并且能够输出完整攻击摘要图，而不是只给异常节点。

### 攻击重建效果

KAIROS 的攻击摘要图大幅减少人工检查规模：

| 数据集 | 摘要图节点 | 摘要图边 | 异常窗口边数 | Reduction |
|---|---:|---:|---:|---:|
| E3-THEIA | 20 | 31 | 3,393,536 | 109,469X |
| E3-CADETS | 18 | 26 | 115,712 | 4,450X |
| E3-ClearScope | 10 | 16 | 210,944 | 13,184X |
| E5-THEIA | 11 | 17 | 826,368 | 48,610X |
| E5-CADETS | 11 | 17 | 351,232 | 20,661X |
| E5-ClearScope | 10 | 10 | 344,064 | 34,406X |
| OpTC | 77 | 101 | 1,065,984 | 10,554X |

E3-THEIA 中，原始异常时间窗口包含 3,393,536 条边，KAIROS 压缩为 31 条边，说明其主要价值不仅是检测，而是把检测结果转化成可调查的攻击故事。

### 运行时性能

- E3-THEIA 中，15 分钟时间窗口最多处理 228.8 秒，约为窗口长度的 25.4%，不会落后于实时流。
- 中位时间窗口约 57K 边，计算耗时 11.6 秒。
- KAIROS 约处理 11K edges/s，略低于 StreamSpot 的约 14K edges/s，但检测效果显著更强。
- CPU 利用率整体较低，作者认为可用于运行时监控。

## 8. 优点

- 同时覆盖检测和调查，不只是输出异常分数。
- 不依赖已知攻击签名，适合未知攻击和 zero-day 场景。
- 使用 whole-system provenance，可处理跨应用、跨进程、跨主机的信息流。
- edge-level reconstruction error 比 graph-level anomaly score 更适合攻击定位。
- time window queue 设计贴合 APT 的 low-and-slow 特征。
- 摘要图大幅降低人工调查成本，和威胁溯源中的证据链构建高度相关。
- 公开代码和公开数据集更利于复现与后续研究。

## 9. 局限

- 依赖干净的 benign 训练数据；如果训练期已被攻击者污染，模型可能学习到恶意行为。
- 对 concept drift 敏感，新出现但正常的应用行为可能被误报。
- 攻击重建依赖 reconstruction error；如果攻击边在上下文中不够异常，可能不会进入摘要图。
- 模型没有直接做 ATT&CK technique 映射、攻击意图识别或组织归因。
- 对抗者如果了解模型和目标环境，理论上可能通过 mimicry 或噪声行为降低异常性。
- 实验仍受 PIDS 领域共同问题限制：公开数据集少、标注粒度不统一、不同系统指标难以公平比较。

## 10. 对我选题的启发

- KAIROS 可以作为“真实系统日志 -> provenance graph -> 攻击重建”的核心文献。
- 如果 EXTRACTOR 是从 CTI 文本侧生成 provenance graph，KAIROS 就是从系统审计日志侧生成和分析 provenance graph。
- 对组织归因而言，KAIROS 的输出不是最终归因结论，而是底层证据链：

```text
真实审计日志
  ↓
系统实体与系统调用
  ↓
异常信息流
  ↓
攻击摘要图
  ↓
与 CTI / ATT&CK / TTP / actor profile 对齐
  ↓
候选组织归因
```

- KAIROS 的 attack summary graph 可以作为 LLM/RAG 的输入，让模型基于真实日志证据解释攻击过程，而不是只基于 CTI 文本推理。
- 可以考虑把 KAIROS 的异常边、摘要图与 AttacKG 的 technique templates 对齐，从日志行为层映射到 ATT&CK 技术层。
- 如果做攻击意图识别，可以把 KAIROS 摘要图中的行为阶段作为意图推断证据，例如 foothold、C&C、payload download、privilege escalation、port scan、lateral movement。

## 11. 可转化的研究问题

1. 如何将 KAIROS 的 attack summary graph 自动映射到 MITRE ATT&CK techniques？
2. LLM 能否在 KAIROS 摘要图基础上生成可解释的攻击调查报告？
3. 如何融合 CTI 文本图和系统日志 provenance graph，形成双源证据增强的攻击链？
4. 能否基于 KAIROS 输出的异常信息流推断攻击意图和下一步行为？
5. 如何将 EXTRACTOR/AttacKG 的文本侧技术图谱与 KAIROS 的日志侧 provenance graph 对齐？
6. 对组织归因而言，哪些 provenance graph 子结构可以作为更稳定的 TTP-level evidence？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| EXTRACTOR | EXTRACTOR 从 CTI 文本中抽取 provenance graph；KAIROS 从真实审计日志中构建和分析 provenance graph |
| AttacKG | AttacKG 面向 ATT&CK technique knowledge graph；KAIROS 面向日志侧异常检测和攻击摘要图 |
| Unicorn | 同为 anomaly-based PIDS，但 Unicorn 更偏 graph sketch 和 graph-level detection，缺少攻击重建 |
| ThreaTrace | 同为 anomaly-based PIDS，但 ThreaTrace 输出异常节点，难以形成完整攻击故事 |
| POIROT | POIROT 使用手工或 CTI 生成的 query graph 做图匹配；KAIROS 不依赖已知攻击签名 |
| Holmes / RapSheet | 基于已知威胁知识或规则重建攻击，解释性强但 attack agnosticity 不足 |
| DEPCOMM | 关注审计日志图摘要；可与 KAIROS 的 post-detection graph reduction 思路比较 |

## 13. 论文写作可引用观点

- Whole-system provenance 能提供跨进程、跨文件、跨网络连接的因果上下文，是检测 APT 和重建攻击链的重要数据基础。
- 仅输出异常分数或异常节点不足以支撑安全调查，入侵检测系统需要提供可解释、可调查的攻击摘要图。
- 对未知攻击而言，基于 benign 行为学习的异常检测比签名检测更具 attack agnosticity，但必须处理 false positives 和 concept drift。
- APT 的 low-and-slow 特征要求检测系统跨时间窗口关联异常活动，而不是孤立分析单个事件或单个窗口。
- 攻击重建可以显著降低人工分析负担，将百万级边压缩为几十条边的摘要图。

## 14. 我的批注与疑问

- KAIROS 的检测和重建很强，但它本身不输出 ATT&CK 技术标签。后续研究可以把摘要图作为中间证据，再做 technique annotation。
- KAIROS 的异常性来自 benign baseline 偏离；组织归因需要进一步判断“这种偏离像谁”，因此还需要 CTI/TTP 知识库参与。
- 如果将 KAIROS 与 AttacKG 结合，可以形成：

```text
日志侧 provenance evidence
  +
CTI 侧 technique knowledge
  =
证据增强的威胁溯源/组织归因
```

- 需要注意训练数据可信问题。现实环境中很难保证 benign period 完全无攻击，模型污染会影响检测。
- KAIROS 输出摘要图后，仍需要人或 LLM 判断哪些节点/边对应攻击阶段、攻击意图和组织特征。
- 后续读 DEPCOMM 时应重点比较：KAIROS 的异常驱动摘要图和 DEPCOMM 的图摘要方法在攻击调查中的区别。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
