# Project05 最终选题候选与创新边界

日期：2026-07-06

## 1. 推荐主选题

二次深度撞题扫描后，推荐将 Project05 当前主线进一步收束为：

> 面向证据不完整场景的 APT 归因粒度门控、可判定性评估与可拒答解释方法。

专利题名不宜再使用“多源证据融合”作为主语。更推荐：

> 一种基于证据充分性画像的 APT 归因粒度门控与缺失证据生成方法。

如果必须保留大语言模型，可以写成：

> 一种基于证据充分性门控的大语言模型受控 APT 归因解释方法。

论文题名可以更学术化：

> Evidence-Sufficiency-Gated Attribution Granularity Control for LLM-Assisted APT Analysis under Incomplete Evidence

中文论文题名可写为：

> 面向不完整安全证据的大语言模型辅助 APT 归因粒度门控方法。

## 2. 问题定义

现有 APT 归因方法通常默认输入证据足够，最终目标是输出某个 actor label、候选排序或归因解释。但真实场景中常见的问题是：

- 只有公开 CTI 报告，没有本地日志；
- 只有 IOC，没有样本；
- 只有 TTP，没有基础设施；
- 证据之间互相冲突；
- 攻击者使用共享工具、外包基础设施或伪旗 TTP；
- 待归因对象可能不属于已知 actor 集合。

因此，Project05 不把“能不能猜出某个 actor”作为唯一目标，而把任务改写为：

> 在证据不完整、冲突或可疑的情况下，系统应判断当前证据最多支持哪一层归因结论，并在证据不足时拒绝或暂缓 actor-level 归因。

## 3. 与已有工作的边界

| 已有方向 | 代表工作 | 已经做到什么 | Project05 不再重复什么 |
|---|---|---|---|
| CTI -> TTP 抽取 | TTPXHunter, TechniqueRAG, Multi-Step LLM Pipeline | 从威胁报告中抽取 ATT&CK 技术 | 不把 TTP 抽取作为主创新 |
| CTI KG / GraphRAG | Open-CyKG, CTIConnect, Beyond RAG, CTI-Thinker | 构建和检索 CTI 图知识 | 不把 GraphRAG 本身作为主创新 |
| LLM 辅助 APT 归因 | AURA, TAA-EPLMR, LLMAPT | LLM/RAG/KG 支持归因解释或推理 | 不写宽泛的 LLM 归因框架 |
| 图/样本归因 | APT-MMF, ADAPT it! | 基于 report-IOC 图或样本特征做 actor/group attribution | 不做单纯闭集 actor 分类 |
| 日志 provenance 检测 | Kairos, DEPCOMM, THREATRACE, PROGRAPHER | 从审计日志中得到攻击摘要或异常证据 | 不做单纯异常检测 |
| 置信融合 | Opinion Pools, ARCANE | 多 attributor 或 Bayesian 方式融合证据 | 不只做普通概率融合 |

Project05 的独立边界是：

> 把 evidence sufficiency profile、attribution granularity gate、refusal/abstention trigger、missing evidence request 和 LLM grounded explanation 组合成一个面向证据不完整场景的归因控制机制。

注意：open-set / abstention / confidence score / information gap / evidence weighting 单独都已经不够新，必须与“归因粒度门控”和“缺失证据生成”组合出现。

## 4. 创新点拆解

### 4.1 证据可用性画像

系统不直接融合证据，而是先生成 evidence availability profile：

- 证据类型：CTI 文本、IOC、TTP、样本、基础设施、时间线、日志 provenance、组织本地上下文；
- 证据粒度：句子、实体、边、路径、样本特征、日志节点、InfoPath；
- 证据质量：来源可信度、时间新鲜度、可验证性、是否来自二手报告；
- 证据缺口：缺少哪类关键证据。

### 4.2 证据区分度与充分性评分

不是所有证据都能支持 actor-level attribution。系统应区分：

- 泛化 TTP：许多 actor 共享，区分度低；
- 专属工具或基础设施：区分度较高；
- 时间线和 campaign linkage：可能支持 campaign-level attribution；
- 本地日志 provenance：可增强事件真实性，但未必直接指向 actor。

输出不只是 confidence，而是：

- sufficiency score；
- distinctiveness score；
- conflict score；
- mimicry/false-flag risk；
- calibration-aware confidence。

### 4.3 自适应归因粒度

系统根据证据充分性决定输出层级：

| 证据状态 | 允许输出 |
|---|---|
| 证据极少或冲突严重 | 拒答 / 暂缓归因 |
| 只有低区分度 TTP | technique / intent 层解释 |
| 有 campaign linkage 但 actor 证据不足 | campaign-level / cluster-level attribution |
| 有高区分度证据且冲突低 | actor-level candidate ranking |
| 证据指向未知或不在候选集 | unknown actor / open-set |

### 4.4 LLM 受控解释

LLM 的作用不是自由生成“像专家一样”的归因故事，而是：

- 把证据账本转成可读解释；
- 对每条结论标注证据来源；
- 解释为什么不能归因到更细粒度；
- 生成下一步证据采集需求；
- 对冲突证据给出提示，而不是替系统强行裁决。

### 4.5 缺失证据需求生成

当证据不足时，系统输出：

- 当前缺少哪些关键证据；
- 哪些证据最可能提高归因粒度；
- 建议采集的日志、样本、IOC、基础设施或时间线信息；
- 若继续强行归因会产生什么风险。

## 5. 最小可行实验

实验不需要一开始就做完整产品，可以构造 evidence ablation benchmark：

1. 从已有 CTI 报告或公开数据中整理完整案例。
2. 构造不同缺失场景：
   - 删除工具证据；
   - 删除基础设施证据；
   - 删除 TTP 证据；
   - 只保留弱 IOC；
   - 加入噪声 IOC；
   - 加入伪旗 TTP；
   - 加入未知 actor 样本。
3. 比较 baseline：
   - 直接 LLM；
   - RAG + LLM；
   - KG/GraphRAG + LLM；
   - TAA-EPLMR 类 evidence path reasoning；
   - Project05 evidence-sufficiency-gated method。

## 6. 评价指标

建议评价不只看 actor accuracy：

- actor top-1 / top-k accuracy；
- selective accuracy；
- coverage；
- over-attribution rate；
- correct abstention rate；
- open-set rejection rate；
- false-flag robustness；
- calibration：ECE、Brier score；
- evidence grounding：结论是否能回指证据；
- missing evidence usefulness：缺失证据建议是否合理。

## 7. 最终判断

最稳的创新不是“给别人做的归因系统加保护层”，而是把真实安全分析中的一个核心问题明确建模：

> 证据不完整时，系统不应该装作知道答案。

如果专利和论文都围绕“归因可判定性”展开，这个方向就不是外挂保护，而是 APT 归因系统进入真实应用前必须具备的决策控制层。
