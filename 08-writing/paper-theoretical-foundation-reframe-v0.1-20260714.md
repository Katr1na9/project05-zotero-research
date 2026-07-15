# [已废止] Project05 论文理论底座重构 v0.1

> **状态：SUPERSEDED（2026-07-14）**。本文件曾尝试为论文指定单一的通用理论底座，但该方向已经被作者否决。当前权威口径见 `paper-top4-positioning-and-gap-synthesis-v0.1-20260714.md`：不再强行寻找一篇“母文”，而以近五年安全 Top-4 溯源调查工作、精确的 CTI—日志对齐先驱和最新语义对齐红线共同界定研究空缺。

日期：2026-07-14  
状态：理论定位冻结候选；待全文精读、Zotero 入库和引文逐句审计后写入论文母本

## 1. 结论

Aronsson 等人的 AFA 综述不再承担理论底座，只保留为 2025 年 AFA 方法分类与术语入口。Project05 不应以单篇低引用预印本证明问题合法性，而应采用“一个主锚点、三个支撑层”的理论结构。

## 2. 主锚点

**Golovin, D. and Krause, A. (2011). Adaptive Submodularity: Theory and Applications in Active Learning and Stochastic Optimization. Journal of Artificial Intelligence Research, 42, 427-486. DOI: 10.1613/jair.3278.**

该文是 Project05 的首选理论主锚点，因为它形式化了部分可观测条件下、动作结果不确定时，根据历史观测自适应选择下一项行动的随机优化问题，并覆盖带成本的目标覆盖和动作失败情形。对应关系为：

| Adaptive stochastic optimization | Project05 |
|---|---|
| item/action | 候选取证动作 |
| unknown realization | 实际恢复证据或零收益 |
| partial realization | 当前 evidence claims 与动作反馈历史 |
| adaptive policy | 根据当前缺口选择下一动作或 STOP |
| item cost/budget | 动作成本与剩余预算 |
| coverage/quota | 目标支持粒度及关键节点覆盖 |

使用红线：本文只借用其“自适应随机优化/部分实现”问题结构。除非另行证明 Project05 的效用满足 adaptive monotonicity 和 adaptive submodularity，否则不得引用其贪心近似保证，也不得把 M2 称为有理论近似比的 adaptive greedy 算法。C11 的 AND 组合证据、动作互补和非短视 Gate 反而可能违反边际收益递减假设，应作为理论适用边界报告。

## 3. 三个支撑层

### 3.1 成本敏感主动获取的直接谱系

**Greiner, R., Grove, A. J. and Roth, D. (2002). Learning Cost-Sensitive Active Classifiers. Artificial Intelligence, 139(2), 137-174. DOI: 10.1016/S0004-3702(02)00209-6.**

该文承担“为什么可以在最终判断前以成本获取缺失信息”的直接理论责任，并给出一般环境中最优主动分类器难以学习的复杂性边界。Project05 对它的扩展不是新 AFA，而是把标量特征测试替换为可能失败的安全证据 bundle，并把分类损失替换为证据支持粒度、越级风险和 STOP。

**Ji, S. and Carin, L. (2007). Cost-Sensitive Feature Acquisition and Classification. Pattern Recognition, 40(5), 1474-1485. DOI: 10.1016/j.patcog.2006.11.008.**

该文把按成本顺序获取观测、根据已有结果决定下一测试以及自适应停止连接到 POMDP。它适合支撑成本与 STOP 的 AFA 近邻，不承担 Project05 的安全信息边界或归因粒度创新。

### 3.2 部分可观测序贯决策与停止

**Kaelbling, L. P., Littman, M. L. and Cassandra, A. R. (1998). Planning and Acting in Partially Observable Stochastic Domains. Artificial Intelligence, 101(1-2), 99-134. DOI: 10.1016/S0004-3702(98)00023-X.**

该文承担状态、动作、观测、隐藏环境和 Bellman continuation value 的一般决策论来源。Project05 当前没有学习完整 belief state 或真实转移模型，因此论文只能写“与有限时域部分可观测决策一致”，不能写成已求解 POMDP。

### 3.3 数字调查的领域必要性

**Ryser, E., Spichiger, H. and Casey, E. (2020). Structured Decision Making in Investigations Involving Digital and Multimedia Evidence. Forensic Science International: Digital Investigation, 34, 301015. DOI: 10.1016/j.fsidi.2020.301015.**

该文承担数字调查过程中必须对证据收集、分析方法和停止/推进作出透明决策的领域论证。NIST SP 800-86 用于支撑多类取证数据源和事件响应中的证据获取实践；NIST SP 800-61 Rev. 3 用于当前事件响应治理背景。二者是实践标准，不替代数学理论。

## 4. 与现有安全文献的职责分离

- POIROT、SLEUTH 等承担“攻击行为图、审计数据和攻击重建为何构成上游状态”的安全系统依据。
- WinRegRL 承担“数字取证动作可以被建模为序贯决策”的近期任务邻居，不承担基础理论权威。
- AFA/NOCTA/AFABench/AACO 承担方法族和外部基线位置，不承担 Project05 的新颖性证明。
- Aronsson AFA 综述仅用于概括方法分类、术语和文献导航，不用于推出任何性能、最优性或领域适用性结论。

## 5. 论文中的推荐表述

> 本文将不完整证据下的调查控制置于成本敏感主动信息获取与部分可观测自适应随机优化的交叉位置。经典主动分类研究允许决策者在输出判断前以成本获取缺失观测；自适应随机优化进一步刻画了动作结果只有在执行后才显现、后续选择依赖既有观测的策略结构。本文不把这些一般机制视为创新，也不假设当前效用满足自适应次模性。我们的增量位于安全调查的部署信息结构：动作请求侧的声明目标与执行侧实际恢复证据必须隔离，采集通道可能失败，状态更新必须保留来源回指，最终结论还受证据支持粒度上限约束。

## 6. 待完成工作

1. 对上述五篇论文完成全文精读和逐项 claim-evidence 表。
2. 将元数据、PDF/可访问链接和精读笔记纳入 Project05 Zotero 集合。
3. 在参考文献库中加入正式 BibTeX，并核对 DOI、卷期、页码和出版状态。
4. 重写相关工作 2.3 与问题定义 3.3-3.5，删除“以 Aronsson 综述为理论底座”的任何显式或隐式表述。
5. 审计性质 3 和非短视 Gate：只保留 Bellman 条件与反例，不借用未满足前提的近似保证。
