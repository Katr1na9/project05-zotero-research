# Project05 机器学习学习路线备忘录

> 用途：以后如果学习方向混乱，或者 ChatGPT 忘记上下文，就把这份文件发回来。  
> 核心目标：不是为了“泛泛学机器学习”，而是为了服务 Project05 —— **在证据不完整时，如何根据当前证据状态选择下一步取证动作，从而提升威胁归因、行为追溯和意图感知能力。**

---

## Codex 审阅修订说明

日期：2026-07-08

这份路线图总体方向正确，适合作为 Project05 的学习路线备忘录。需要注意三点：

1. 当前 MVP 的核心评价目标不应写成泛泛的“归因置信度提升”，而应更精确地写成“当前证据可支撑归因粒度提升、过度归因率下降、达到目标粒度的取证成本降低”。
2. Agent 和多模态应作为支线方向登记，不进入第一版实验流程；第一版实验只验证 `evidence state + acquisition action planning`。
3. 大模型不是主模型。Project05 主学习线应落在机器学习、主动特征获取、强化学习和实验设计上；LLM 只做受控证据编译、解释生成和 direct baseline。

---

## 0. Project05 的核心研究定位

当前 Project05 不应该简单写成：

> 我调用 LLM 读取 CTI 报告，然后让大模型判断攻击者是谁。

这个方向容易显得过于工程化，也容易出现不可控、不可评价、创新点不清晰的问题。

更合适的研究表述是：

> 将 APT / 威胁归因中的补证过程建模为一种结构化安全证据场景下的主动特征获取问题。系统根据当前 evidence state 判断证据缺口、冲突、不确定性与取证成本，选择下一步最有价值的取证动作，逐步补全证据链，提高威胁归因、行为追溯和攻击意图判断的可靠性。

也就是说，Project05 的重点不是“大模型本身”，而是：

```text
证据不完整
→ 建模当前证据状态
→ 判断缺什么证据
→ 选择下一步取证动作
→ 更新证据状态
→ 逐步提升归因和意图判断效果
```

---

## 1. 总体学习优先级

建议学习顺序：

```text
机器学习基础
→ 强化学习 / 主动特征获取 AFA
→ 深度学习 / 图神经网络
→ 大模型工程
```

原因：

1. **机器学习基础**是所有实验设计、模型评价、baseline、ablation 的基础。
2. **强化学习 / 主动特征获取**最贴近 Project05 的核心创新点。
3. **深度学习 / 图神经网络**后续可能用于 evidence graph、provenance graph、action value prediction，但不是第一优先。
4. **大模型工程**在本项目中更适合作为证据抽取、结构化输出、解释生成工具，而不是主菜。

---

## 2. 第一优先：机器学习基础

### 2.1 为什么最先学机器学习？

因为 Project05 里很多东西最终都会变成结构化特征、分类器、排序器、评价指标和实验对比。

例如 evidence state 可以表示成：

```text
coverage：当前证据覆盖了多少攻击阶段
gap_count：攻击链中还有几个缺口
conflict_count：证据之间有多少冲突
candidate_entropy：候选攻击者分布的不确定性
top2_margin：第一名和第二名攻击者置信度差距
cost：继续取证的成本
expected_gain：下一步证据可能带来的收益
```

这些本质上就是机器学习中的**结构化特征**。

你需要先学会：

```text
如何把现实问题变成特征
如何用特征训练模型
如何判断模型好不好
如何设计 baseline
如何做 ablation
如何避免过拟合
如何解释 precision / recall / F1
```

---

### 2.2 第一阶段具体学习内容

按顺序学：

```text
1. 监督学习 / 无监督学习
2. 回归 / 分类 / 聚类
3. 线性回归
4. 损失函数 / 代价函数
5. 梯度下降
6. Logistic Regression
7. 训练集 / 验证集 / 测试集
8. 过拟合 / 欠拟合
9. Precision / Recall / F1
10. 混淆矩阵
11. ROC / AUC
12. 交叉验证
13. 特征工程
14. 决策树
15. Random Forest
16. XGBoost
17. baseline 设计
18. ablation 消融实验
19. calibration 置信度校准
20. 排序 / learning to rank 的基本概念
```

---

### 2.3 这一阶段要达到的程度

不是要求推公式推得很深，而是要能做到：

```text
看到一个安全问题，知道如何抽成特征
看到一个模型，知道它是回归、分类还是排序
看到实验表格，知道 precision / recall / F1 在说什么
看到模型训练结果，能判断是否过拟合
能设计合理 baseline
能解释为什么要做 ablation
能用 Logistic Regression / Random Forest / XGBoost 跑一个基础实验
```

---

## 3. 第二优先：强化学习 / 主动特征获取 AFA

### 3.1 为什么这一部分最贴近论文核心？

Project05 的核心不是“已经有完整证据后做分类”，而是：

```text
证据不完整时，下一步该查什么？
```

这正好对应主动特征获取 AFA：

```text
当前特征不完整
→ 每个特征都有获取成本
→ 系统要判断哪个特征最值得获取
→ 获取后希望提升最终判断效果
```

也接近强化学习：

```text
state：当前证据状态
action：下一步取证动作
reward：取证收益
policy：决策策略
```

---

### 3.2 Project05 中的 RL / AFA 映射关系

可以这样对应：

| 强化学习 / AFA 概念 | Project05 对应含义 |
|---|---|
| state | 当前 evidence state，例如证据覆盖率、缺口数、冲突数、不确定性 |
| action | 下一步取证动作，例如查 IOC、查 TTP、查日志、查 provenance path |
| reward | 取证收益，例如归因置信度提升、证据缺口减少、攻击链更完整 |
| cost | 动作成本，例如查询时间、系统开销、人工审核成本 |
| policy | 当前状态下选择哪个取证动作的策略 |
| Q-value | 某个动作在当前证据状态下的长期价值 |
| stop action | 停止补证并输出归因 / 意图判断结果 |

---

### 3.3 第二阶段具体学习内容

按顺序学：

```text
1. Markov Decision Process, MDP
2. state / action / reward
3. policy
4. value function
5. Q-value
6. greedy policy
7. epsilon-greedy
8. contextual bandit
9. cost-sensitive decision making
10. active feature acquisition, AFA
11. stopping policy
12. information gain
13. entropy / uncertainty
14. Q-learning
15. DQN
16. Dueling DQN
17. reward design
18. offline evaluation
```

---

### 3.4 这一阶段要达到的程度

最低目标：

```text
能把 Project05 的补证问题讲成 AFA 问题
能解释 state / action / reward 分别是什么
能设计一个简单的 reward 函数
能设计一个 greedy baseline
能设计一个 cost-aware baseline
能解释为什么不是每次都查最多证据
能解释什么时候应该 stop
```

更进一步：

```text
能用 XGBoost / MLP 预测 action value
能比较 rule-based、greedy、bandit、DQN 几种策略
能用实验说明主动补证比固定流程更有效
```

---

## 4. 第三优先：深度学习 / 图神经网络

### 4.1 为什么不是第一优先？

深度学习和 GNN 很重要，但 Project05 一开始不应该直接上复杂模型。

原因：

```text
如果机器学习基础和 AFA 问题定义不清楚，
直接上 GNN / DQN / LLM 会导致模型很炫但问题不稳。
```

MVP 阶段更建议先用：

```text
规则策略
Logistic Regression
Random Forest
XGBoost
简单 MLP
```

先把任务定义、数据结构、实验指标、baseline 跑通。

---

### 4.2 后续可能用到的深度学习内容

后面可能需要：

```text
MLP：用于 action value prediction
Graph2Vec：把 evidence graph / provenance graph 编码成向量
GNN：表示攻击链、溯源图、证据图
RoBERTa / SecureBERT：编码 CTI 文本
DQN：做序列化取证动作决策
```

---

### 4.3 第三阶段具体学习内容

按顺序学：

```text
1. 神经网络基本结构
2. MLP
3. activation function
4. backpropagation 基本直觉
5. embedding
6. graph embedding
7. Graph2Vec
8. GCN
9. GraphSAGE
10. GAT
11. provenance graph 表示
12. evidence graph 表示
13. DQN 网络结构
14. 图表示 + 动作决策结合
```

---

## 5. 第四优先：大模型工程

### 5.1 LLM 在 Project05 中的位置

LLM 不是主菜，更像工具层。

建议定位：

```text
LLM = 证据抽取与解释工具
AFA / RL = 主动补证决策核心
机器学习模型 = 证据状态评估与动作选择模型
知识图谱 / provenance graph = 证据组织载体
```

LLM 可以用于：

```text
CTI 文本实体抽取
IOC / TTP / Actor / Malware 抽取
文本证据标准化
证据摘要
JSON 结构化输出
攻击链解释
自然语言报告生成
```

但不要把论文写成：

```text
我让大模型自己判断攻击者是谁。
```

更好的写法是：

```text
LLM 负责把非结构化 CTI 文本转为结构化证据；
主动补证模块根据当前证据状态选择下一步取证动作；
图谱和机器学习模型共同支撑归因、溯源和意图判断。
```

---

### 5.2 第四阶段具体学习内容

按顺序学：

```text
1. prompt engineering
2. JSON constrained output
3. structured extraction
4. hallucination
5. evidence grounding
6. RAG
7. chunking
8. embedding retrieval
9. citation / provenance tracking
10. LLM evaluation
11. extraction accuracy
12. groundedness
13. consistency
14. agent workflow
```

---

## 6. Project05 可落地技术路线草案

一个较稳的 MVP 路线：

```text
CTI 报告 / 日志 / 流量 / provenance 数据
→ LLM / 规则 / parser 抽取结构化证据
→ 构建 evidence graph / provenance graph
→ 计算 evidence state 特征
→ 主动补证策略选择下一步 action
→ 获取新证据
→ 更新 evidence state
→ 输出归因结果、证据链、攻击意图判断
```

---

## 7. 可能的 action 设计

Project05 中的取证动作可以包括：

### 7.1 MVP 第一版动作

```text
扩展日志时间窗口
查询主机 / 进程 provenance 子图
恢复 network flow / DNS 摘要
查询 process tree
查询 file access record
查询 registry record
查询指定 ATT&CK technique 的局部证据
停止取证并输出结果
```

### 7.2 扩展动作

```text
查询 IOC 富集证据
查询 malware / sample 分析证据
查询 infrastructure history
查询 actor 历史行为
查询 geolocation / ASN / IP reputation
人工复核冲突证据
```

第一版实验必须保证每个 action 都能映射到可恢复的 `evidence_claim`，不能只是自然语言建议。

---

## 8. 可能的 evidence state 特征

可以设计为：

```text
coverage
gap_count
conflict_count
candidate_entropy
top1_confidence
top2_margin
evidence_count
ioc_count
ttp_count
provenance_path_count
missing_stage_count
average_evidence_quality
average_evidence_freshness
cost_spent
remaining_budget
expected_gain
```

解释：

```text
coverage：证据覆盖程度
gap_count：攻击链缺口数量
conflict_count：证据冲突数量
candidate_entropy：候选攻击者不确定性
top2_margin：第一候选和第二候选之间的置信度差距
cost_spent：已经消耗的取证成本
remaining_budget：剩余取证预算
expected_gain：继续取证可能带来的收益
```

---

## 9. 可能的 reward 设计

reward 可以考虑：

```text
当前可支撑归因粒度提升
候选攻击者熵下降
攻击链缺口减少
证据冲突减少
攻击阶段覆盖率提升
高质量证据数量增加
取证成本惩罚
无效查询惩罚
过度取证惩罚
正确 stop 奖励
错误 stop 惩罚
```

一个简单形式：

```text
reward =
归因粒度可支撑性提升
+ 攻击链完整度提升
+ 证据不确定性下降
- 取证成本
```

---

## 10. 实验设计关键词

需要重点掌握：

```text
baseline
ablation
train / validation / test split
cross validation
precision
recall
F1
AUC
accuracy
macro-F1
micro-F1
calibration
confusion matrix
cost-sensitive evaluation
average acquisition cost
evidence acquisition efficiency
```

---

## 11. 可能的 baseline

可以设置：

```text
固定顺序补证策略
随机补证策略
只按最低成本补证
只按最高置信度提升补证
greedy information gain
Logistic Regression policy
Random Forest policy
XGBoost policy
DQN policy
不主动补证，直接归因
```

---

## 12. 可能的 ablation

可以做：

```text
去掉 cost 项
去掉 entropy 特征
去掉 provenance path 特征
去掉 LLM 抽取证据
去掉 graph 特征
去掉 stop action
去掉 conflict_count
去掉 top2_margin
只用 IOC
只用 TTP
只用 provenance graph
```

目的是证明每个模块确实有贡献。

---

## 13. 最重要的学习提醒

不要被算法名吓住。

这条路线的核心不是背算法，而是建立一条清晰逻辑：

```text
现实安全问题
→ 抽象成机器学习问题
→ 定义输入特征
→ 定义输出目标
→ 设计模型
→ 设计评价指标
→ 设计 baseline
→ 做 ablation
→ 解释实验结果
```

Project05 的核心表达应该始终围绕：

```text
证据不完整
证据有缺口
证据有冲突
取证有成本
如何决定下一步查什么
如何提高归因和意图感知可靠性
```

---

## 14. 一句话总纲

> Project05 的学习路线不是为了训练一个大模型，而是为了把威胁归因中的补证过程建模为一个机器学习 / 主动特征获取 / 强化学习问题：在证据不完整且取证有成本的情况下，根据当前 evidence state 选择最有价值的下一步证据获取动作，逐步补全证据链，提高行为追溯、攻击意图感知与威胁归因的可靠性。
