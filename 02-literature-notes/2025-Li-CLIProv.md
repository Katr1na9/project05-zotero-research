# CLIProv: A Contrastive Log-to-Intelligence Multimodal Approach for Threat Detection and Provenance Analysis

- 作者：Jingwen Li, Ru Zhang, Jianyi Liu, Wanguo Zhao
- 来源：arXiv:2507.09133，提交于 2025-07-12
- 状态：**摘要级高风险占位，全文待获取**
- 风险等级：红（对新主线候选 A 的"语义提升"单点）

## 十问速览（基于摘要）

1. 输入是什么：系统溯源日志（provenance log）序列 + TTP 威胁情报。
2. 输出是什么：威胁行为检测结果 + TTP 识别 + 完整攻击场景（attack scenario）。
3. 核心模块：对比学习（contrastive learning）多模态框架，把溯源日志语义与威胁情报语义对齐；把威胁检测转化为语义搜索（找与日志序列最相似的情报）。
4. 是否做证据权重：摘要未见。
5. 是否做不完整证据：摘要未见。
6. 是否做 open-set / abstention：摘要未见。
7. 是否做 false flag / mimicry：摘要未见。
8. 是否生成缺失证据建议：**否**。
9. LLM 是决策层还是解释层：摘要未提 LLM（对比学习为主）。
10. 对 Project05 的红线：**"日志→情报语义对齐"和"日志→TTP 语义提升 + 攻击场景生成"这两个单点被覆盖**。Project05 不能把"用对比学习/语义对齐弥合日志与情报语义鸿沟"作为主创新。

## 任务边界

检测 + 溯源分析 + TTP 标注 + 场景生成为止。未延伸到：归因粒度（campaign/actor）、对齐质量的证据学解释、取证规划、闭环。

## 对新主线的含义

CLIProv 是新主线"对齐基座"的天然 baseline 或复用模块。Project05 的空间在对齐之后：对齐状态→归因粒度评估→取证规划闭环。

## 待办

- 获取全文，确认其是否有任何"对齐置信度/对齐失败处理"的机制（若有，需进一步避让）。
