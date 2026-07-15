# ProHunter: A Comprehensive APT Hunting System Based on Whole-System Provenance

## 1. 基本信息

- 中文译名：ProHunter：基于全系统溯源的综合 APT 狩猎系统
- 作者：Xuebo Qiu; Mingqi Lv; Tiantian Zhu; Yimei Zhang; Tieming Chen
- 年份：2026
- 来源：arXiv 预印本；稿件注明投稿至 Computers & Security，尚不能按正式期刊论文引用
- arXiv：https://arxiv.org/abs/2603.19658
- 阅读状态：`full-read`
- 阅读日期：2026-07-14
- 所属主题：Whole-system Provenance / CTI Query Graph / Graph Matching / APT Hunting

## 2. 一句话总结

ProHunter 将审计日志压缩为进程、文件和网络流实体构成的精简 provenance graph，再从 CTI 报告生成并人工修正查询图，通过威胁子图采样和定制 GIN 图匹配识别攻击；它直接占据“CTI 攻击模式图与审计溯源图匹配”的宽泛创新，但没有独立原始流量子图、traffic-log 跨源边校准、冲突状态或高层意图评测。

## 3. 研究问题

- 如何在全系统审计日志规模持续增长的条件下，保留攻击调查所需语义并降低图规模？
- 如何从 CTI 报告获得可迁移的攻击查询图，并在运行时 provenance graph 中匹配其变体？
- 如何围绕通用关注点采样小型威胁图，避免在完整图上直接进行高成本匹配？
- 如何应对查询图与实际攻击图之间的结构和语义差异？

## 4. 核心贡献

1. 构建由 process、file、netflow 节点及其交互边组成的精简 provenance graph，并结合通用压缩与语义抽象控制规模。
2. 将 CTI 报告经 AttacKG 转换为查询图，再由人工修正和补全作为攻击模式输入。
3. 设计面向通用 POI 的启发式 BFS 威胁子图采样器，减少进入图匹配模块的噪声和规模。
4. 设计包含特征增强、图内与图间消息传递的 GIN 匹配网络，比较查询图和候选威胁图。
5. 在 DARPA TC E3、E5 和 OpTC 上评估召回、误报、压缩、采样和运行开销。

## 5. 方法框架

### 输入

- Linux/Windows 全系统审计日志及由此形成的 provenance event。
- CTI 报告及其经 AttacKG 提取、人工校正后的攻击查询图。
- 调查窗口内由通用关注点触发的候选子图。

### 输出

- 与查询图相似的候选威胁图及匹配分数。
- 用于分析员复核的攻击相关实体和交互结构。

### 关键模块

| 模块 | 作用 | 对本支线的边界意义 |
|---|---|---|
| PPG construction | 压缩审计事件并做语义层级编码 | 强日志侧图 baseline，但不是独立 traffic graph |
| CTI query graph | 把报告转为攻击模式图 | 已占据 CTI-to-provenance alignment |
| Threat graph sampler | 以 POI 为种子做启发式 BFS | 可作为联合图上的候选链裁剪 baseline |
| Customized GIN | 查询图与候选图的跨图匹配 | 解决模式匹配，不输出跨源记录后验 |

### 方法流程

```text
审计日志 -> 精简 provenance graph
                    -> POI 触发 -> 威胁子图采样 --+
CTI 报告 -> AttacKG -> 人工修正查询图 -----------+-> 定制 GIN 匹配 -> APT 告警
```

## 6. 数据集与实验

- 数据集包括 DARPA TC E3、E5 和 OpTC，共覆盖 28 个攻击案例；候选集合约 3,846 个图，其中威胁图占比约 0.7%。
- 训练使用攻击发生前抽样的 15,000 个良性子图；正样本通过图增强生成，负样本结合良性图与图编辑距离构造。
- 论文报告 E3/E5 召回率 100%、FPR 0，OpTC 召回率 100%、FPR 0.07；这些是系统级威胁图识别指标，不是链边或因果边准确率。
- PPG 日增规模约 3-25 MB；威胁图采样压缩率约 70%-90%，样本中约 20% 被作者归为少量噪声节点。
- 约每 5 分钟窗口总处理 0.67 秒，其中采样约 0.03 秒、匹配约 0.15 秒；模型内存约 556 MB。
- 与 SLEUTH 的压缩比较来自估算，因为作者无法获得该系统实现，不能视为同条件复现实验。

## 7. 关键知识点

- CTI 报告生成攻击查询图、再到 provenance graph 中检索相似攻击结构，已经是明确发表路径。
- 论文的 netflow 是审计 provenance 中的对象节点，不代表从原始 PCAP 独立构建流量证据子图。
- 查询图仍依赖人工修正和补全，自动 CTI 抽取误差没有端到端传递评估。
- 图匹配分数代表模式相似性，不是某条 packet-log 记录关联的校准概率。
- 以同一攻击报告构造查询图并辅助定义攻击真值，可能形成评价循环，需要严格的 campaign-disjoint 设计。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Whole-system provenance | 全系统溯源 | 由操作系统审计事件构建的数据依赖图 |
| Query graph | 查询图 | 从 CTI 报告抽象出的攻击模式图 |
| Point of interest | 关注点/调查种子 | 触发局部图采样的实体或事件 |
| Cross-graph message passing | 跨图消息传递 | 查询图与候选图之间的信息交换 |

## 8. 优点

- 图构建、压缩、采样和匹配形成完整可运行的 APT hunting pipeline。
- 数据覆盖多个 DARPA 语料和多个攻击案例，并报告运行开销。
- 将查询图与候选图差异纳入学习，而非要求精确子图同构。
- 面向低攻击占比设计候选采样，符合实际调查的检索型工作流。

## 9. 局限

- 只使用审计 provenance；没有独立 PCAP observation graph，也没有跨源边真值和校准。
- CTI 查询图需人工修正，端到端自动性与复现成本被低估。
- 训练正样本主要来自图增强，真实跨 campaign 泛化仍需更严格检验。
- 部分噪声判断依赖文档是否提及，未记录的可疑节点可能被误当噪声。
- 与 SLEUTH 的压缩率比较不是复现实测。
- 假设审计日志和 CTI 完整可信，未处理日志缺失、来源冲突与伪造。
- 输出是模式匹配告警，没有攻击链顺序、意图真值或 claim-to-record replay 评价。

## 10. 对我选题的启发

- 不能把“CTI/ATT&CK 查询图与 provenance graph 匹配”作为核心 novelty；它应成为日志侧或下游 baseline。
- Project03 的 PCAP ThreatObservation 应保持为独立流量子图，通过带原始 frame 锚点的候选关系接入日志子图，而不是降格为一个 netflow 节点属性。
- 可将 ProHunter 的查询图采样用于缩小联合事件图的 LLM 上下文，但跨源关系必须先经过校准与证据状态控制。
- CTI 查询图属于知识/假设层，原始 packet/log 观测属于证据层；两层不能合并为同一种“事实边”。

## 11. 可转化的研究问题

1. source-preserving 双子图能否在不牺牲原始证据回放的情况下，达到 ProHunter 式局部图检索效率？
2. 校准的 traffic-log 候选关系能否改善查询图匹配对缺失日志或模糊 netflow 节点的鲁棒性？
3. 将 CTI 查询图限制为 hypothesis layer，是否能降低错误抽取对攻击链结论的污染？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AttacKG | ProHunter 使用其从 CTI 报告构造查询图，并增加人工修正 |
| KAIROS / DEPCOMM | 都以 audit provenance 图为调查基础；ProHunter 更强调 CTI 查询图匹配 |
| Citar | 都把 CTI 模式用于定位 audit log 中的攻击实例 |
| BotFence | BotFence 将 DPI 网络结果接到 TTP provenance；ProHunter 只在审计图中匹配 CTI 模式 |
| Project03 支线 | 其日志图、局部采样和图匹配可作 baseline，但不覆盖独立 PCAP 子图和跨源关系校准 |

## 13. 论文写作可引用句式

- 近期工作已将 CTI 报告转化为攻击查询图，并通过局部威胁图采样与跨图神经匹配在全系统审计溯源图中检索 APT 活动；然而，该路线仍以单一审计图为证据空间，未显式建模原始流量观测与日志记录之间的可校准关联。

## 14. 我的批注与疑问

- 论文首页注明向 Computers & Security 投稿，不应把它写成已经正式录用或发表的期刊论文。
- 生成查询图与构造 ground truth 是否共享同一 CTI 报告，需要在复现实验中隔离，避免 information leakage。
- 100% recall 出现在攻击比例极低、候选采样后的集合中，必须同时报告 precision、告警数和 analyst burden。
- “20% noise”中包含未被报告解释的可疑节点，这种口径可能把新发现当作噪声。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（CTI 查询图与 audit provenance 匹配的直接红线）
