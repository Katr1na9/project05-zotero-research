# Project05 二次深度撞题扫描

日期：2026-07-06

## 1. 扫描结论

这轮重新扫描后，Project05 的可写空间进一步收窄。

新增发现说明：APT 归因方向不是空白，2024-2026 年已经出现大量从 CTI、IOC、TTP、KG、流量、行为、恶意样本和 LLM 框架推进的工作。尤其是以下方向已经不适合继续作为核心创新：

1. IOC/KG 关联图直接做 APT 归因。
2. 异构威胁情报表示 + 机器学习/集成学习做 actor 分类。
3. APT KG + LLM 协同增强问答或分析。
4. 基于流量周期性特征和攻击组织关联图做 APT 组织归因。
5. TTP/目标行业/目标国家加权后做攻击组织分类。
6. LLM 构建网络攻击归因框架。
7. CTI 文本到攻击技术建模再归因。
8. CTI 异构图 / GAT / GNN / RGCN 做威胁归因。
9. ATT&CK + Bayesian / probabilistic attack prediction。
10. 图预测结果再由 LLM 做语义验证或关系补全。

但截至本轮扫描，仍没有看到一个工作完整覆盖下面这个组合：

```text
证据可用性画像
  + 证据区分度/充分性/冲突/伪旗风险评分
  + 归因粒度门控
  + open-set / unknown actor / false flag 下拒答或降级
  + LLM 受控解释
  + 缺失证据采集建议
```

因此，Project05 仍可推进，但题名和权利要求必须继续收缩，不能写成“多源证据融合归因系统”。

## 2. 新增红色风险项

### 2.1 CN121887534A：一种 APT 攻击组织归因方法、装置、设备及存储介质

- 来源：https://finance.sina.com.cn/stock/aigc/zl/2026-04-23/doc-inhvmvzk8835127.shtml
- 公开号：CN121887534A
- 申请号：CN202610317984.9
- 申请日：2026-03-16
- 公开日：2026-04-17
- 申请人：绿盟科技集团股份有限公司、东南大学

公开摘要显示，该专利从通信流量中提取三类序列：

- 数据包之间时间差序列；
- 发包频率序列；
- 数据包长度序列。

然后筛选具有周期性和周期值的目标序列，通过目标序列配对相似度构建攻击组织关联关系图，并用该图对未知通信流量做 APT 攻击组织归因。

#### 撞题影响

这项专利直接堵住：

- 基于通信流量时序特征的 APT 组织归因；
- 基于流量相似度构建攻击组织关联图；
- 用未知流量在组织关联图中做归因。

Project05 如果引入日志/流量/provenance evidence，不能把“流量周期性关联图归因”写成核心创新。日志或流量只能作为证据通道之一，核心仍应是“证据是否足以归因”的门控机制。

风险等级：红色。

### 2.2 CN118802369A：一种面向 APT 知识图谱和大语言模型的协同增强方法

- 来源：https://patents.google.com/patent/CN118802369A/zh
- 公开号：CN118802369A
- 申请日：2024-09-11
- 公开日：2024-10-18

该专利覆盖：

- 构建专注网络安全领域的 APT 知识图谱；
- 根据用户问题设计链式提示语；
- 大语言模型利用 APT KG 查询与定位；
- 利用子图检索强相关节点丰富上下文提示；
- LLM 根据上下文提示生成答案。

#### 撞题影响

这比之前已记录的 CN118646607A 更明确地覆盖了“APT KG + LLM + chain prompt + subgraph retrieval + contextual answer”。

Project05 不能把以下内容作为独立发明点：

- APT KG 与 LLM 协同增强；
- KG 子图检索增强 LLM；
- chain prompt 引导 APT 分析；
- 用 KG 提高 LLM 对 APT 攻击者、攻击路径、攻击行为的理解。

风险等级：红色。

### 2.3 TRAIL：Knowledge Graph-Based APT Attribution

- 来源：https://isaiahjking.com/papers/trail.pdf
- IEEE ICDE 2025
- DOI：10.1109/ICDE65448.2025.00095

TRAIL 构建网络 IOC 共现知识图谱，并将 IOC 与攻击事件、APT actor 关联。论文报告：

- 约 4,500 个已归因安全事件；
- 22 个 APT；
- 2.1M+ nodes；
- 7.9M+ edges；
- 单个 IOC 归因准确率约 45%；
- 事件级 IOC 组合仅用间接资源复用可达到约 82%；
- 图拓扑与特征分析结合 GNN 可达到约 84%；
- 进行了 6 个月新事件验证，数据库更新滞后超过 1 个月会影响效果。

#### 撞题影响

TRAIL 强烈压缩：

- IOC 共现图；
- 资源复用证据；
- OSINT IOC KG；
- GNN/图分析做 APT actor attribution。

Project05 不能把“IOC 图 + GNN/图推理 + APT 归因”作为主创新。

风险等级：红色。

### 2.4 APT-ATT：heterogeneous threat intelligence representation + CTGAN

- 来源：https://www.sciencedirect.com/science/article/pii/S1389128625004785
- Computer Networks, Volume 270, 2025, Article 111511
- DOI：10.1016/j.comnet.2025.111511

公开摘要已经足够确认 APT-ATT 不是空白。它提出：

- 面向长异构威胁情报的表示学习；
- N-Gram 捕获局部语义；
- TF-IDF 快速向量化；
- 卡方统计做特征重要性排序和降维；
- CTGAN 生成小类别特征向量，缓解类别不平衡；
- KNN/RF/XGBoost + logistic regression stacking；
- 平均 accuracy 约 94.91%。

#### 撞题影响

APT-ATT 堵住：

- 异构威胁情报表示；
- 类别不平衡增强；
- 集成学习稳定性提升；
- 闭集 APT actor 分类。

它目前未明显覆盖：

- LLM 受控解释；
- 证据不足拒答；
- open-set unknown actor；
- 分层归因粒度门控；
- 缺失证据采集建议。

风险等级：红色，但不完全堵死 Project05 当前收窄方向。

### 2.5 HG-CTA：heterogeneous graph-based cyber threat attribution

- 来源：https://dl.acm.org/doi/fullHtml/10.1145/3651671.3651707
- 时间：2024

HG-CTA 直接把 cyber threat intelligence 构建为 heterogeneous graph，并在异构图上做 cyber threat attribution。

#### 撞题影响

它堵住：

- CTI 异构图归因；
- 多类型实体/关系图归因；
- heterogeneous graph-based threat attribution；
- “把多源威胁情报组织成图再归因”的宽泛表述。

风险等级：红色。

### 2.6 AARGS：APT organization prediction + LLM semantic validation

- 来源：https://www.researchsquare.com/article/rs-8631020/latest.pdf
- 时间：2026

AARGS 相关工作把 CVE、CWE、CAPEC、IOC 等实体组织为 attack graph，通过 RGCN / adaptive relation aggregation 预测 APT organization，并使用 LLM 做 semantic reasoning and relationship completion，同时结合多维可视分析。

#### 撞题影响

它直接压缩：

- 多源攻击链图；
- RGCN / 图神经网络做 APT 组织预测；
- LLM 对 APT 候选组织做语义验证；
- LLM 补全攻击链关系；
- 可视化 APT 归因解释。

尤其危险的是，它已经触及“预测置信度低、不确定性建模、动态多源证据扩展”等未来方向。Project05 不能再把“图预测 + LLM 验证 + 解释”作为创新。

风险等级：红色。

## 3. 新增橙色风险项

### 3.1 APT-scope：HIN + active enrichment + unknown perpetrator prediction

- 来源：https://www.sciencedirect.com/science/article/pii/S2215098624001770
- Engineering Science and Technology, 2024
- DOI：10.1016/j.jestch.2024.101791

APT-scope 构建异构信息网络，流程包括：

- 数据收集；
- DNS / WHOIS / port scan / SSL footprinting 等主动富化；
- NER；
- FastRP + Logistic Regression 关系预测；
- APT group alias discovery；
- 对 unknown perpetrators 做 threat actor prediction；
- 报告 AUCPR train 96.57%、test 92.36%。

#### 撞题影响

它明显压缩“异构 CTI 富化 + HIN + unknown perpetrator 预测”的空间。Project05 不能简单声称“多源 CTI 富化后预测未知攻击者”。

风险等级：橙色。

### 3.2 APT Attribution Using Heterogeneous GNN with Contextual CTI

- 来源：https://www.mdpi.com/2079-9292/14/23/4597
- Electronics 2025, 14(23), 4597
- DOI：10.3390/electronics14234597

公开信息显示，该工作构建三部图：

- APT groups；
- contextualized TTPs；
- Cyber Kill Chain stages。

TTP 节点使用 SBERT embedding，CKC 阶段提供过程上下文，并使用异构 GNN 做 APT attribution。

#### 撞题影响

它堵住“APT-TTP-CKC 三部图 + SBERT/GNN 归因”方向。Project05 不能把“把 TTP 放到 kill chain 上再图神经网络归因”作为创新。

风险等级：橙色。

### 3.3 Correlation Analysis of APT Attack Organizations Based on Knowledge Graphs

- 来源：https://www.mdpi.com/2079-9292/15/1/87
- Electronics 2026, 15(1), 87
- DOI：10.3390/electronics15010087

该文构建 APT ontology，从威胁报告中抽取实体和关系，归一化并集成到 Neo4j KG 中。然后使用：

- 显式结构推理；
- TransE / RotatE 语义嵌入；
- T-GCN 时间演化模块；
- 多级 APT correlation；
- sector-oriented threat analysis。

#### 撞题影响

它压缩“APT KG + 多级关联 + 时间演化 + 归因决策支持”。Project05 若使用 KG，必须避免写成 APT 组织关联分析或攻击链推理系统。

风险等级：橙色。

### 3.4 APTChaser：Cyber Threat Attribution via Attack Technique Modeling

- 来源：https://link.springer.com/chapter/10.1007/978-3-031-89363-6_10
- First online：2025-05-25

APTChaser 题名和摘要显示其核心是 attack technique modeling，用于 cyber threat attribution。二级资料显示其使用 LLM 构建攻击技术图式化表示，并以更细粒度建模攻击实施细节。

#### 撞题影响

APTChaser 会压缩：

- attack technique modeling；
- 技术层建模后做归因；
- 用 LLM 生成攻击技术结构表示再归因。

风险等级：橙色。需要后续获取全文。

### 3.5 Construction of Cyber-attack Attribution Framework Based on LLM

- 来源：https://ieeexplore.ieee.org/document/10945110/
- IEEE TrustCom 2024
- DOI：10.1109/TrustCom63139.2024.00310

公开摘要显示该文提出层次化 cyber-attack attribution framework，并结合人工与 LLM 填充框架内容。

#### 撞题影响

它堵住“基于 LLM 构建网络攻击归因框架”的宽题。Project05 不能再写成 LLM attribution framework。

风险等级：橙色。

### 3.6 CN116467438A：基于图注意力机制的威胁情报报告归因分析

- 来源：https://patents.google.com/patent/CN116467438A/zh

该中文专利覆盖“威胁情报报告 + 图注意力机制 + 归因分析”。

#### 撞题影响

它压缩：

- 威胁情报报告图建模；
- 图注意力权重归因；
- 对威胁情报中的实体/关系加权后归因。

风险等级：红色。

### 3.7 CN117560223B：基于 IP 及威胁情报知识图谱的威胁归因预测

- 来源：https://patents.google.com/patent/CN117560223B/zh

该专利覆盖“IP + 威胁情报知识图谱 + 威胁归因预测”。

#### 撞题影响

它压缩：

- IP/IOC 证据归因；
- 威胁情报知识图谱辅助归因预测；
- 基础设施证据映射到威胁行为体。

风险等级：红色。

### 3.8 GAPT：Graph-based APT Attribution Framework Using Temporal Relation Embeddings

- 来源线索：IEEE Access 2024, 12, 76532-76545
- 当前状态：全文待获取。

GAPT 题名已经覆盖 `graph-based APT attribution framework + temporal relation embeddings`。

#### 撞题影响

它压缩：

- 图结构 APT attribution framework；
- 时间关系嵌入；
- 动态/时序关系用于归因。

风险等级：橙色，全文待获取。

## 4. 新增黄色风险项

### 4.1 Threat Actor Attribution Applying a TTP Approach

- 来源：https://www.preprints.org/manuscript/202511.0711

该预印本使用 TTP、目标国家/地区、行业等特征做 threat actor attribution，并引入 rarity-based feature weights。它明确要求 TTP 必须有报告证据支持，不能凭已知 actor 行为推断。

#### 撞题影响

它不直接堵死 Project05，但说明：

- TTP rarity / feature weighting 已经有人做；
- evidence quote grounding 已经有人用于 TTP 抽取；
- TTP + target context 做 actor classification 已经很拥挤。

风险等级：黄色到橙色。

### 4.2 Clustering APT Groups Through CTI by Weighted Similarity Measurement

- 来源：https://ieeexplore.ieee.org/document/10697172
- IEEE Access 2024
- DOI：10.1109/ACCESS.2024.3469552

该文使用 MITRE ATT&CK techniques、software、target nations、industries 等作为特征，通过 weighted similarity measurement 聚类 APT groups。

#### 撞题影响

它压缩“加权相似度 + APT group clustering”的空间。Project05 不能把 evidence weighting 写成简单频率或稀有度权重。

风险等级：黄色到橙色。

### 4.3 TIBlender：insufficient evidence and follow-up investigation

- 来源：https://arxiv.org/html/2606.04580v1

TIBlender 是跨平台社媒早期威胁情报系统，不是 APT actor attribution 专项。但其多视角调查轨迹会让评估 agent 识别 insufficient evidence 并请求 targeted follow-up investigation。

#### 撞题影响

它提醒 Project05 的“缺失证据采集建议”不能写得太泛。需要限定在 APT 归因粒度升级所需证据，而不是泛泛的 follow-up investigation。

风险等级：黄色。

### 4.4 OpenSec：Evidence-Gated Action Rate

- 来源：https://arxiv.org/html/2601.21083v3
- 数据集说明：https://huggingface.co/datasets/Jarrodbarnes/opensec-seeds/blob/main/README.md

OpenSec 关注 incident response agent calibration，引入 Evidence-Gated Action Rate，衡量 containment action 是否由 trusted evidence 支撑。

#### 撞题影响

OpenSec 不做 APT 归因专利，但会压缩“evidence-gated”这一宽泛术语。Project05 应避免只说 evidence-gated，必须具体到 attribution granularity gate。

风险等级：黄色。

### 4.5 BAN：MITRE ATT&CK + Bayesian Network APT Attack Prediction

BAN 不是直接做 actor attribution，而是使用 MITRE ATT&CK 和 Bayesian Network 做 APT attack prediction。

#### 撞题影响

它限制 Project05 不能把“ATT&CK + 概率证据推理”写得过宽。概率图、attack prediction、技术链推断都已有基础。

风险等级：黄色到橙色。

### 4.6 CN117786088B：威胁情报分析方法、装置、设备、介质及程序产品

- 来源：https://patents.google.com/patent/CN117786088B/zh

该专利与 LLM/语言模型威胁情报分析、结构化抽取方向接近。它不一定直接做 APT actor attribution，但会压缩“LLM 抽取威胁情报证据”作为创新点的空间。

风险等级：橙色。

### 4.7 CN119766567B：TTP 描述相似度匹配归因

- 来源：https://patents.google.com/patent/CN119766567B/zh

该专利围绕 TTP 描述相似度匹配做威胁归因。

风险等级：橙色。

### 4.8 SHIELD：APT Detection and Intelligent Explanation Using LLM

- 来源：https://arxiv.org/abs/2502.02342
- HTML：https://arxiv.org/html/2502.02342v1
- 时间：2025

SHIELD 不是 actor attribution，但它已经把 provenance graph、统计异常检测、图分析、LLM 多阶段推理、confidence threshold、dynamic confidence decay/reinforcement 和可解释 attack summary 结合起来。

#### 撞题影响

它压缩：

- provenance graph + LLM attack investigation；
- LLM 解释日志证据；
- LLM 生成 APT attack summary；
- kill-chain mapping；
- confidence threshold / dynamic confidence scoring。

Project05 如果使用日志/provenance 证据，必须把它限定为 evidence channel，不能把“LLM 解释日志图”写成核心。

风险等级：橙色。

## 5. 功能级覆盖更新

| 功能点 | 新增覆盖情况 | 对 Project05 的影响 |
|---|---|---|
| 多源/异构 CTI 表示 | APT-ATT, APT-scope, APT-MMF | 已拥挤，不能作为核心 |
| IOC/KG 资源复用归因 | TRAIL | 红线 |
| CTI 异构图归因 | HG-CTA | 红线 |
| 图注意力威胁情报报告归因 | CN116467438A | 红线 |
| IP/威胁情报 KG 归因预测 | CN117560223B | 红线 |
| APT KG + LLM 协同 | CN118802369A, CN118646607A | 红线 |
| 流量特征归因 | CN121887534A | 红线 |
| TTP/CKC/GNN 归因 | Heterogeneous GNN 2025 | 橙色风险 |
| RGCN/attack graph + LLM 语义验证 | AARGS | 红线 |
| APT 组织 KG 多级关联 | Electronics 2026 KG correlation | 橙色风险 |
| LLM attribution framework | TrustCom 2024, LLMAPT, AURA | 红/橙风险 |
| evidence weighting | Weighted Similarity, TTP rarity weighting, US patents | 不能写泛泛权重 |
| TTP 描述相似度归因 | CN119766567B, APTChaser | 橙色风险 |
| LLM 威胁情报抽取/结构化 | CN117786088B, AttacKG+, MM-AttacKG | 不能作为核心 |
| temporal relation graph attribution | GAPT, APT KG correlation | 橙色风险 |
| ATT&CK Bayesian/probabilistic prediction | BAN, ARCANE | 不能写泛泛概率推理 |
| provenance graph + LLM attack explanation | SHIELD | 不能把日志图解释作为核心 |
| incomplete/noisy evidence | TAA-EPLMR, LLMAPT | 不能只做缺失消融 |
| insufficient evidence / follow-up | TIBlender, OpenSec, LLM-CTI vulnerability paper | 需要具体化到归因门控 |
| open-set / abstention / selective classification | High-Precision APT Malware Attribution | 不能只做 open-set 分类或拒答 |
| false flag/mimicry | survey, Synthetic APTs, false flag literature | 可作为风险评分之一 |
| missing evidence for attribution upgrade | 只见相邻表达，未见完整机制 | 仍是可保留空间 |
| attribution granularity gate | 未见完整覆盖 | 当前最值得保留 |

## 6. 更新后的不可写红线

以下方向应从专利题名、独立权利要求和论文主创新中删除或降级：

1. 基于多源证据融合的 APT 归因。
2. 基于 LLM 的 APT 归因框架。
3. APT KG + LLM 协同增强分析。
4. CTI-KG / IOC KG / HIN 做 actor attribution。
5. evidence path-enhanced LLM threat actor attribution。
6. TTP 加权相似度或 rarity weighting 做 actor/group attribution。
7. 流量周期性序列相似度做 APT 组织归因。
8. 异构威胁情报表示 + CTGAN/集成学习做 APT 分类。
9. APT-TTP-CKC 图神经网络归因。
10. 单纯 confidence score、information gap 或 hunting recommendation。
11. CTI 异构图/GAT/GNN/RGCN 归因。
12. IP/IOC/基础设施知识图谱归因预测。
13. LLM 对图预测结果做语义验证或关系补全。
14. ATT&CK + Bayesian/probabilistic attack prediction。
15. 单纯 open-set、out-of-scope resilience、selective classification 或 abstention。
16. provenance graph + LLM 多阶段推理生成攻击摘要。

## 7. 更新后的可写白名单

更可写的保护点必须体现“归因控制”，而不是“归因模型”：

1. 证据可用性画像：记录可用、缺失、冲突、时效、可信度和粒度。
2. 证据区分度评分：识别 generic TTP、共享工具、共享基础设施、可模仿证据。
3. 证据充分性评分：判断当前证据最多支持 technique、intent、campaign、actor 哪一层。
4. 归因粒度门控：禁止证据不足时输出 actor-level attribution。
5. 开放集/未知行为体判断：作为归因门控的一个触发条件，而不是单独创新点。
6. 冲突/伪旗风险控制：冲突高或 mimicry 风险高时降级或拒答。
7. LLM 受控解释：LLM 只解释证据账本和门控结果，不自由裁决 actor。
8. 缺失证据采集建议：说明缺什么证据才能从当前层级升级到更高归因粒度。

## 8. 题名调整建议

不推荐：

> 一种面向证据不完整场景的多源安全证据自适应融合与大语言模型辅助 APT 归因解释方法

原因：“多源安全证据自适应融合”仍然太像 US12368730B2、APT-MMF、APT-ATT、APT-scope、TRAIL、CN120110776B。

更推荐：

> 一种面向证据不完整场景的 APT 归因粒度门控与可拒答解释方法

或者：

> 一种基于证据充分性画像的 APT 归因可判定性评估与缺失证据生成方法

如果必须保留 LLM：

> 一种基于证据充分性门控的大语言模型受控 APT 归因解释方法

## 9. 当前判断

这轮深扫之后，方向不是不能写，而是必须再往“归因前控制层”收。

真正的新颖性不应放在：

```text
如何更准地归因到 actor
```

而应放在：

```text
什么时候不应该归因到 actor，
当前证据最多只能支持哪一层结论，
还缺什么证据才能升级归因粒度。
```

这是当前仍能防守的主线。
