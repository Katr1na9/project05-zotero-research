# Project05 最终撞题矩阵与选题边界 - 2026-07-06

> **2026-07-09 覆盖性更新**：本文件以下“粒度门控 + 缺失证据清单”结论仅保留为历史决策记录，不再代表当前主线。M2 留出实验已经证明固定启发式取证规划不足；新主线为 **归因证据缺口图上的节点级条件收益学习与成本约束序贯取证**。新增红线 WinRegRL（Ghanem et al., Scientific Reports, 2026）已经覆盖 forensic MDP、动作本体、专家 transition、动态规划、有限 Q-learning 和 POMDP 扩展，因此不得再宽泛主张“首次用 MDP/RL 进行主动取证”。当前边界详见 `04-progress/m3-gap-conditioned-evidence-utility-research-20260709.md`。

## 结论先行

Project05 不应继续使用以下宽题：

> 一种基于多源证据融合与大语言模型的高级持续性威胁归因解释方法

原因：`多源证据融合`、`KG/RAG/GraphRAG 归因`、`LLM-based APT attribution`、`attack technique modeling`、`DS/Bayesian/weighted evidence fusion` 均已有强相关工作或高风险待证工作。

当前可推进的窄题是：

> 一种面向证据不完整与攻击者混淆场景的 APT 归因粒度门控与可拒答解释方法

核心定位：

```text
不是再做一个 APT 归因模型，
不是再做一个多源证据融合模型，
而是在已有归因/融合模型输出之上，
判断当前证据最多允许输出哪一级归因结论。
```

## 最终红线

下列方向不得作为 Project05 主创新：

1. 多源/多层 CTI 特征融合用于 APT group attribution。
2. Dempster-Shafer、Bayesian、weighted averaging、opinion pool 等证据融合提升归因准确率。
3. CTI-KG、HIN、GNN、RGCN、GraphRAG 或 temporal embedding 归因。
4. IOC、TTP、malware、command sequence、traffic pattern 的单一或组合闭集 actor classification。
5. LLM-based APT attribution framework。
6. LLM 构建 attack technique schema、technique profile 或 TTP implementation profile 后做归因。
7. evidence path-enhanced LLM reasoning for threat actor attribution。
8. confidence score、information gap、hunting recommendation 作为单点创新。
9. 单纯 open-set、abstention、selective classification 或 unknown actor detection。
10. provenance graph + LLM 攻击摘要或 APT detection explanation。

## 代表工作压缩面

| 压缩面 | 代表工作 | 对 Project05 的约束 |
|---|---|---|
| 多模态/多层特征融合归因 | APT-MMF, MLDSJ, Au et al. 2025, APT-ATT | 不再主张“多源证据融合提高 APT 归因” |
| KG/HIN/GNN 图归因 | TRAIL, APT-scope, HG-CTA, Au et al. 2025, GAPT, CN117560223B | 不再主张“知识图谱归因框架” |
| LLM 归因框架 | AURA, LLMAPT, TAA-EPLMR, Construction of Cyber-attack Attribution Framework Based on LLM | 不再主张“LLM 辅助 APT attribution framework” |
| attack technique 建模 | APTChaser, CN119766567B, Guru et al. | 不再主张“细化 TTP/technique 后归因” |
| 概率/证据融合 | Opinion Pools, BAN, ARCANE, US12368730B2 | 不再主张“置信度融合/证据权重本身” |
| 日志/provenance 解释 | KAIROS, DEPCOMM, THREATRACE, PROGRAPHER, SHIELD | 不再主张“日志图检测/摘要/解释” |
| 开放集与拒答 | High-Precision APT Malware Attribution, OpenSec, ARCANE | 不把 open-set 或 abstention 单独作为新意 |

## 仍可保护的组合机制

Project05 仍有空间的不是单点模块，而是以下组合链：

```text
候选归因结果及证据账本
  -> 证据充分性画像
  -> actor-specific 区分度评估
  -> long-tail / time drift / mimicry / false-flag / missing-feature 风险检测
  -> 归因粒度门控
  -> actor / campaign / intent / technique / unknown / refusal
  -> LLM 受控解释与缺失证据清单
```

## 技术问题重写

不再写：

> 如何融合多源证据并用 LLM 解释 APT 归因结果。

改写为：

> 在证据不完整、证据冲突、候选行为体不可区分或存在攻击者模仿时，如何自动判断当前证据是否足以支持威胁行为体层级归因，并在证据不足时输出较低粒度结论、未知行为体判断或拒答解释。

## 可写创新点

1. **证据充分性画像**  
   对每一类证据记录可用性、粒度、来源可靠性、时间有效性、可验证性、缺失状态和可回溯标识。

2. **actor-specific 区分度评估**  
   区分通用 TTP、共享工具、共享基础设施、二手 CTI、专属样本特征、campaign linkage 等证据对不同归因粒度的支持强度。

3. **混淆风险检测**  
   对 long-tail 数据不足、time drift、mimicry、false flag、feature blurring、候选 actor 相似度过高等风险生成门控惩罚。

4. **归因粒度门控**  
   不输出单一 actor label，而是输出当前证据允许的最高归因粒度：technique、intent、campaign、actor candidate、unknown 或 refusal。

5. **LLM 受控解释**  
   LLM 只把门控结果、证据账本和缺失证据转成可读解释，不允许自由补事实或强行给 actor。

6. **缺失证据清单生成**  
   当无法支持更高粒度归因时，输出能提升归因粒度的证据类型、采集对象和风险说明。

## 四篇缺全文的处理

以下文献被设置为待办，不阻塞当前主线：

- An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN
- APTChaser: Cyber Threat Attribution via Attack Technique Modeling
- GAPT: A Graph-based APT Attribution Framework Using Temporal Relation Embeddings

当前写作策略是主动避开它们最可能覆盖的空间：

- 不写异构情报表示/CTGAN；
- 不写 attack technique schema/profile；
- 不写 temporal relation embedding；

已获取并确认的新增红线：

- A Multi-Source Feature Fusion-Based Knowledge Graph Construction from Cyber Threat Intelligence to Facilitate APT Attribution in IDS

该文已确认直接覆盖 multi-source feature fusion + HKG + APT attribution，因此 `multi-source feature fusion KG` 不再是待证风险，而是已确认红线。

## 最终建议题名

专利题名：

> 一种面向证据不完整与攻击者混淆场景的 APT 归因粒度门控与可拒答解释方法

论文题名：

> Evidence-Sufficiency-Gated Attribution Granularity Control for LLM-Assisted APT Analysis under Incomplete and Ambiguous Evidence

中文论文题名：

> 面向不完整与混淆证据的大语言模型辅助 APT 归因粒度门控方法
