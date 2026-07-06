# BAN: Predicting APT Attack Based on Bayesian Network With MITRE ATT&CK Framework

## 基本信息

- 年份：2023
- 题名：BAN: Predicting APT Attack Based on Bayesian Network With MITRE ATT&CK Framework
- 来源线索：ResearchGate / 相关引用页
- 当前状态：纳入 Project05 二次深扫补充材料。

## 它在研究什么

BAN 使用 MITRE ATT&CK framework 建模 APT attacker，基于 Bayesian Network 做攻击预测。相关公开信息显示，该方法使用结构学习和参数学习，把已检测攻击作为证据，预测后续 attack techniques 或 attacker goals。

## 对 Project05 的撞题影响

BAN 会压缩：

1. 基于 ATT&CK 的概率图模型；
2. 用已观测技术作为 evidence 预测后续攻击；
3. Bayesian network 表达攻击者行为和目标；
4. 基于概率证据做 APT attack prediction。

虽然 BAN 更偏 attack prediction，不是完整 actor attribution，但它说明“MITRE ATT&CK + Bayesian/probabilistic reasoning + evidence”已经是已有路线。

## Project05 可避让空间

Project05 不能把“基于 ATT&CK 证据的概率推理”写得过宽。可保留的是：

- 证据充分性判断；
- 归因粒度门控；
- 证据不足拒答；
- 缺失证据建议。

## 风险等级

黄色到橙色。

它不是直接堵死 Project05，但会限制“概率证据推理”相关权利要求的宽度。

