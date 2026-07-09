# Leveraging Reinforcement Learning for an Efficient Windows Registry Analysis during Cyber Incident Response

- 作者：Mohamed Chahine Ghanem, Dominik Wojtczak, Elhadj Benkhelifa, Hamza Kheddar, Erivelton G. Nepomuceno, Wanpeng Li
- 期刊：Scientific Reports
- 发表时间：2026-06-12
- DOI：10.1038/s41598-026-57787-6
- 正文：[Nature / Scientific Reports](https://www.nature.com/articles/s41598-026-57787-6)
- 状态：已完成 36 页 Article in Press 正文的 Project05 定向结构化精读（方法、实验、局限与 POMDP 附录）
- Project05 定位：主动取证规划方向的新增高风险近邻工作

## 一、它解决什么问题

WinRegRL 面向 Windows Registry、内存、事件日志和时间线取证。在证据规模大、来源分散且调查时间受限的场景下，系统决定下一步执行哪项取证动作，以提高相关 artefact 的发现效率。

它不是 APT actor attribution 方法，也不输出 technique/campaign/actor 粒度；目标是提高 DFIR 调查效率和 artefact-level evidence coverage。

## 二、状态、动作与奖励

### 2.1 状态

系统把取证状态编码为 8 维离散元组：

1. evidence source；
2. Registry hive scope；
3. SANS-aligned artefact family；
4. processing stage；
5. temporal support；
6. corroboration level；
7. evidential priority；
8. investigative objective。

主实验是完全可观测 MDP。Registry 子 MDP 有 90 个离散状态，memory/event/timeline 子 MDP 有 99 个状态，不使用连续 embedding 或神经网络状态编码。

### 2.2 动作

全局动作本体含 39 个 atomic forensic actions，覆盖：

- acquisition and ingest；
- hive traversal；
- user-activity parsing；
- persistence parsing；
- device/network parsing；
- cross-source correlation；
- validation/reporting。

动作是否可用由当前离散状态决定。

### 2.3 转移与奖励

- 当前转移概率不是从数据学习，而是由 GCFE/GCFA 专家调查图设定并归一化。
- reward 从 `-10` 到 `+100`，强 corroboration、case-critical artefact 获得高奖励，无效或越界动作受罚。
- 作者明确把“从累积调查轨迹学习 transition model”列为未来工作。

## 三、规划算法

核心不是端到端 deep RL，而是两阶段方法：

1. 用 value iteration 求解专家指定 MDP 的 nominal optimal policy；
2. 仅对 support 低于阈值的 state-action pair 做有限、局部 tabular Q-learning refinement。

因此论文自己把方法限定为：

> MDP / dynamic programming with bounded RL refinement

而不是 fully learned RL agent。

## 四、部分可观测扩展

附录给出 POMDP：

```text
<S, A, P_expert, R, Omega, O, gamma, b0>
```

其中：

- observation 表示 parser/validation 返回的 absent、weak、partial、strong、conflicting 等结果；
- observation model 编码 parser reliability 和 acquisition quality；
- belief state 使用标准 Bayesian filter 更新；
- 可采用 PBVI 或 SARSOP 等 point-based solver。

重要边界：该 POMDP 只是形式化扩展，没有进入主实验。论文未来工作才计划评估 noisy、partial 和 anti-forensic evidence。

## 五、实验与结果

论文使用 4 个 Windows forensic datasets，包括 Magnet-CTF 2022、IGU-CTF 2024、MemLabs-CTF 2019 和作者参与构建的 MalVol-25，并与 FTK、KAPE 和 examiner-led workflow 对比。

论文报告：

- investigation time 最多降低 68%；
- adjudicated relevant artefacts 最多增加 35%；
- 在测试场景中保持较高 artefact-level precision。

这些数字只适用于其受控 Windows forensic protocol，不能直接外推到 APT 归因。

## 六、局限

1. transition 和 reward 仍以专家设定为主；
2. 主实验假定状态完全可观测；
3. 尚未覆盖完整 disk image、browser、cloud 和 network telemetry；
4. noisy/partial/anti-forensic 条件只在 POMDP 附录中形式化，未实证；
5. 目标是 artefact recovery 和 investigation efficiency，不是 attribution granularity；
6. 不建模 CTI attack graph 与本地 evidence graph 的节点级缺口；
7. 不预测动作解决某个 attribution-critical evidence gap 的条件概率。

## 七、对 Project05 的红线

以下表述已经不能再作为 Project05 创新：

- 首次把数字取证建模为 MDP；
- 首次使用 RL 优化调查动作顺序；
- 首次在部分证据条件下使用 POMDP 做取证规划；
- 首次把动作成本、证据收益和调查效率放入统一 reward。

## 八、Project05 可保留边界

Project05 必须进一步限定为：

1. 状态是 CTI-local alignment 形成的 evidence-gap graph，而不是 Registry artefact 分类元组；
2. 目标是达到可支持的 attribution granularity，而不是发现更多 artefact；
3. 学习 `action -> unresolved critical CTI node` 的条件转移，而不是使用专家固定 transition；
4. 输出经过校准的 node-resolution probability 和 granularity-transition probability；
5. 训练/测试基于 campaign-level split，并显式区分 masked evidence 与 naturally unavailable evidence；
6. LLM 只负责异构证据语义编译、动作语义映射和受控解释，不能冒充 transition model。

## 九、Project05 一句话结论

WinRegRL 抢占了“MDP/RL 安全取证规划”的宽口，但没有覆盖“面向归因粒度的图缺口条件收益学习”。Project05 下一版不能只是换 reward，而必须把核心推进到 **learned, graph-conditioned, attribution-goal-specific transition model**。
