# ExCyTIn-Bench: Evaluating LLM agents on Cyber Threat Investigation

## 1. 基本信息

- 英文题名：ExCyTIn-Bench: Evaluating LLM agents on Cyber Threat Investigation
- 中文译名：ExCyTIn-Bench：面向网络威胁调查的 LLM Agent 评测基准
- 作者：Yiran Wu 等
- 年份：2025；2026 v3
- Venue：ICML 2026 accepted；arXiv
- DOI / arXiv / URL：https://arxiv.org/abs/2507.14201
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：重点读
- 所属主题：LLM agent / Cyber threat investigation / Benchmark / Evidence chain
- 阅读状态：arXiv + 本地 PDF 抽取文本精读

## 2. 一句话总结

ExCyTIn-Bench 构建了一个用于评测 LLM agent 做网络威胁调查的 benchmark：agent 需要在包含 57 张安全日志表的 SQL 环境中多跳查询证据，回答由 investigation graph 派生的问题。

## 3. 研究问题

- 安全分析员需要在异构日志中跨多跳证据链调查威胁。
- LLM agent 看似适合自动调查，但缺乏面向 cyber threat investigation 的标准评测环境。
- 需要可复用、可解释、可自动评分的安全调查 benchmark。

## 4. 核心贡献

1. 提出 ExCyTIn-Bench，用 investigation graph 派生安全调查问题。
2. 构建 controlled Azure tenant 和 SQL 查询环境，覆盖 Microsoft Sentinel 等相关服务的 57 张日志表。
3. 利用专家规则提取的安全日志构造 threat investigation graphs，再用图上节点对生成 QA。
4. 将问题锚定到显式节点和边，提供可解释 ground truth。
5. 实验显示当前模型仍有明显提升空间，最佳 reward 约 0.606。

## 5. 方法框架

### 输入

- 问题背景。
- SQL database environment。
- 多张安全日志表。
- agent 可执行查询动作。

### 输出

- 问题答案。
- 调查轨迹 / SQL 查询过程。
- reward / correctness score。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| Investigation graph | 把安全事件组织成可追踪证据链 | 可借鉴为实验 ground truth 结构 |
| SQL environment | agent 通过查询获取证据 | 可模拟 Project05 的取证 action space |
| Graph-derived QA | 从图节点路径生成问题和答案 | 可借鉴为 evidence ablation 的问题生成 |
| Agent evaluation | 评估 LLM 多跳调查能力 | 说明“LLM agent 调查”方向很拥挤 |

### 方法流程

```text
controlled security environment
  -> logs + expert detection logic
  -> threat investigation graph
  -> graph-node-pair questions
  -> SQL interaction environment
  -> LLM agent answers / reward
```

## 6. 数据集与实验

- 环境：controlled Azure tenant。
- 日志：57 log tables，来自 Microsoft Sentinel 及相关服务。
- 问题规模：7542 generated questions；测试集 589 questions。
- 任务：agent 通过数据库查询进行多跳调查。
- 结果：最佳模型 reward 约 0.606，说明任务仍难。

## 7. 关键知识点

### 概念

- Investigation graph：安全调查图，节点和边能支撑问题、答案与解释。
- Agent action as database query：将调查动作具体化为 SQL 查询。
- Explainable ground truth：每个答案对应图上的证据路径。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| cyber threat investigation | 网络威胁调查 | 与 threat hunting 有重叠但更偏调查问答 |
| investigation graph | 调查图 | Project05 可用作实验标注结构 |
| SQL environment | SQL 交互环境 | 对应可执行取证环境 |

## 8. 优点

- 评测设计非常接近“证据链调查”。
- 将 agent action 约束为数据库查询，便于记录成本、步数和证据轨迹。
- 生成式问题锚定图节点，ground truth 可解释。

## 9. 局限

- 目标是回答安全调查问题，不是 APT 归因粒度判定。
- action space 偏 SQL 查询，未覆盖样本分析、外部 CTI 检索、人工取证、沙箱分析等异构动作。
- 关注 agent 能否找到答案，不关注当前证据是否足够支持某一归因粒度。

## 10. 对我选题的启发

- 红线：不要把 Project05 写成“LLM agent 自动调查安全事件”，这个方向已经有 benchmark 化工作。
- 可复用：Project05 的 MVP 可以仿照 ExCyTIn，把证据动作落成查询或检索动作，并记录每步 cost。
- 差异点：我们不是让 LLM 自由探索回答问题，而是让 planner 根据 attribution granularity reward 选择 next evidence action。

## 11. 可转化的研究问题

1. 能否从 investigation graph 中构造 evidence ablation 任务：隐藏部分边/节点，让 planner 决定查询顺序？
2. 能否把 SQL 查询步数、表成本、时间成本作为取证成本？
3. 能否把 reward 从 QA correctness 改成“达到目标归因粒度的最小成本”？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CTIConnect / CTIBench | 都是安全 LLM benchmark，但 ExCyTIn 更偏交互式调查 |
| NOCTA | ExCyTIn 提供环境化调查动作，NOCTA 提供采集规划理论 |
| Project05 | 可借鉴其 graph-grounded evaluation，不把 LLM agent 作为主创新 |

## 13. 论文写作可引用句式

- Recent cyber investigation benchmarks evaluate whether LLM agents can retrieve multi-hop evidence from heterogeneous logs, but they do not optimize evidence acquisition toward controlled attribution granularity.

## 14. 我的批注与疑问

- ExCyTIn 是我们实验设计的重要参考，不是主线撞题。
- 如果之后做 MVP，可以优先做一个“小型 ExCyTIn 化”的本地实验：固定事件图，隐藏证据，比较 planner 与 LLM agent 查询策略。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是

