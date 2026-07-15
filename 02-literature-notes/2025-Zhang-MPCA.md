# MPCA: Constructing the APTs Provenance Graphs through Multi-Perspective Confidence and Association

## 1. 基本信息

- 中文译名：MPCA：通过多视角置信度与关联构建 APT 溯源图
- 作者：Zhao Zhang; Senlin Luo; Yingdan Guan; Limin Pan
- 年份：2025
- Venue：Information and Software Technology, 180, 107670
- DOI：https://doi.org/10.1016/j.infsof.2025.107670
- 阅读状态：`extended-publisher-read`（出版商预览含摘要、完整引言、贡献、方法/实验片段；全文受限，结论不超出可见内容）
- 阅读日期：2026-07-14
- 阅读优先级：重点读（置信图边界）
- 所属主题：Audit Logs / Provenance Graph / Event Confidence / Attack Reconstruction

## 2. 一句话总结

MPCA 从系统审计日志构建进程依赖图，以行为模式语义合并并行冗余分支，再估计 `subject-relation-object` 事件三元组置信度、挖掘事件内/事件间关联并结合告警定位攻击事件；它占据“置信度辅助 provenance graph 构建和攻击场景重构”，但置信对象仍是单域日志事件及其告警关联，不是原始 PCAP 与日志之间的候选跨源边，也未证明概率校准。

## 3. 研究问题

- 长期 APT 日志如何避免实体与依赖爆炸，同时保留关键高层行为？
- 如何表达事件内部和事件之间的隐式关联，减少告警向邻近良性事件错误传播？
- 如何从大规模审计日志中形成紧凑、较低误报的攻击场景图？

## 4. 核心贡献

1. 基于行为模式语义合并 process-connected subgraph 中的平行冗余分支。
2. 从多个视角估计事件三元组可靠性，排除良性事件并增强攻击/良性事件在特征空间的差异。
3. 建模事件与告警之间的关联，突出攻击事件并重构场景图。
4. 在 DARPA CADETS 与 TRACE 上评价图缩减、定位准确性和误报/漏报。

## 5. 方法框架

### 输入

- 大规模系统审计日志、系统实体、事件三元组和已有告警。

### 输出

- 缩减后的 provenance/dependency graph。
- 事件置信度、攻击事件位置和攻击场景图。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Semantic branch merging | 合并行为语义一致的平行依赖 | 可作为日志子图压缩 baseline |
| Multi-perspective confidence | 评估事件三元组可靠性 | 提醒必须明确“置信度属于节点、边还是跨源关系” |
| Event-alert association | 用告警关联突出攻击事件 | 可作为已有告警增强基线，但需防标签传播偏差 |

### 方法流程

```text
审计日志 -> 系统实体/事件三元组 -> 依赖图
  -> 行为语义分支合并
  -> 多视角事件置信度 + 事件/告警关联
  -> 攻击事件定位与紧凑攻击场景图
```

## 6. 数据集与实验

- 数据集：DARPA Transparent Computing CADETS 与 TRACE。
- 出版商可见结果称：相对既有方法，reduction rate 提高 44.16%，accuracy 提高 82%，false positive rate 降低 21%。
- 预览未暴露这些百分比的绝对基值、完整 baseline 表、置信区间、重复次数和全部参数，不能据此作更细比较。
- 可见实验问题覆盖数据缩减、总体攻击归因/场景重构效率与准确性；未见跨数据源边级真值或 probability calibration 指标。

## 7. 关键知识点

- 名称中的 `confidence` 不自动等于 calibrated probability；必须检查置信变量、监督信号和 ECE/Brier/reliability diagram。
- MPCA 的 event 是由 audit log 形成的主谓宾依赖，不是 packet-log 两类 observation 的配对关系。
- 告警关联可提升攻击事件定位，也可能把告警标签或错误偏差传播到图中，必须用无告警/噪声告警消融审计。
- 图压缩准确率与跨源关联正确性是不同任务，不能用前者替代后者。

## 8. 优点

- 同时处理 dependency explosion 和告警污染，问题定义比只做图剪枝更完整。
- 将事件可靠性显式引入图构建，说明“图不是确定真值”已成为近年研究问题。
- 使用 CADETS/TRACE 两个真实攻防演练数据集并有组件级评价设计。

## 9. 局限

- 仅基于系统审计日志/网络连接实体，不包含独立 raw PCAP 观察线。
- 无原始 packet frame/log record 双锚点、跨源候选边和 source conflict 状态。
- 可见材料没有 calibration 指标，不能确认 confidence 是否概率可解释。
- 依赖已有告警，可能受告警覆盖、误报和标签泄漏影响。
- 全文受限，方法公式、绝对结果和复现材料仍需在获得合法全文后补核。

## 10. 对我选题的启发

- 题目不能只写“置信 provenance graph”；MPCA 已直接覆盖。
- 我们需明确新变量是 `P(packet observation <-> log observation | evidence)`，并通过 edge-level ECE/Brier/risk-coverage 验证，而不是给日志事件打启发式分数。
- MPCA 可作为日志侧缩减/事件置信 baseline；双线方法还必须与 traffic-only、log-only 和 deterministic join 比较。

## 11. 可转化的研究问题

1. 跨源关系校准是否在保持 MPCA 式日志图缩减率的同时降低错误链合并？
2. 告警噪声、PCAP 缺失和日志缺失分别如何影响事件置信与链置信？
3. 节点/事件置信和跨源边置信应如何分层传播而不被混为一个总分？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| DEPCOMM | 都压缩审计日志图；MPCA 进一步加入事件置信与告警关联 |
| M-DUCAG | 两者均显式表示不确定性；MPCA 面向审计事件，M-DUCAG 面向预建攻击图 |
| BotFence | BotFence 用 PID/5-tuple 确定接边；MPCA 有 confidence，但仍不是 packet-log relation calibration |
| Project03 支线 | 限制“置信图”表述，保留跨源关系校准和双线贡献评价空间 |

## 13. 论文写作可引用句式

- 近年工作已通过事件三元组置信度和告警关联改善审计溯源图的压缩与攻击事件定位，但这类事件级可靠性尚未回答原始网络包与日志记录之间多义关联的概率校准问题。

## 14. 我的批注与疑问

- 出版商称 accuracy “improved by 82%”需要核对是相对增幅还是百分点，获得全文前不得改写成绝对提升。
- `attack attribution` 在本文更接近事件定位和场景重构，不是 actor attribution。
- 后续合法获得全文后，优先补：置信公式、监督标签、阈值选择、绝对表格和代码/参数。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：2.5/5（全文受限）
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是（置信图边界；引用时限制在已核验内容）
