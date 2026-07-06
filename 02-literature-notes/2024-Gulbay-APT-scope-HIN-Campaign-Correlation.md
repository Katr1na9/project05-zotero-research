# APT-scope: A graph-based approach for campaign correlation and attribution

## 基本信息

- 年份：2024
- 期刊：Engineering Science and Technology, an International Journal
- DOI：10.1016/j.jestch.2024.101791
- 来源：https://www.sciencedirect.com/science/article/pii/S2215098624001770
- 当前状态：纳入 Project05 二次深扫高风险材料。

## 它在研究什么

APT-scope 关注 APT campaign correlation and attribution。它使用异构信息网络，把威胁情报中的不同实体、关系和富化信息组织起来，用于发现 APT group alias 和预测 unknown perpetrators。

## 方法核心

公开信息显示其流程包括：

```text
威胁情报收集
  -> 主动富化：DNS / WHOIS / port scan / SSL footprinting
  -> NER
  -> 异构信息网络 HIN
  -> FastRP embedding
  -> Logistic Regression 关系预测
  -> APT group alias discovery / unknown perpetrator prediction
```

## 对 Project05 的撞题影响

APT-scope 压缩：

1. 异构 CTI 富化；
2. HIN 表示；
3. APT campaign correlation；
4. unknown perpetrator prediction；
5. APT group alias discovery。

Project05 如果写“多源威胁情报富化后预测未知攻击者”，会与该工作接近。

## Project05 可避让空间

APT-scope 仍然偏向“更好地关联/预测”，而不是“证据不足时拒绝归因”。Project05 的区别应放在：

- 当前证据是否足以支持 actor-level；
- 当 HIN 关系不足或证据冲突时如何降级；
- 如何解释缺少哪些证据；
- LLM 是否被约束在证据账本之内。

## 精读结论

APT-scope 说明“异构威胁情报 + 图表示 + unknown prediction”已经有人推进。Project05 不能把 unknown actor 作为单独创新点，必须把它放入更完整的归因粒度门控机制中。

