# 撞题补读后的方向决策

## 1. 这几篇到底在研究什么

| 论文 | 它真正做的事 | 对 Project05 的含义 |
|---|---|---|
| AURA | 用 RAG + multi-agent + LLM 做 APT 归因，输入 TTP、IOC、malware、tools、timeline，输出 group/nation attribution 和自然语言 justification | 直接堵住“LLM/RAG/Agent 做可解释 APT 归因”的宽题 |
| Guru et al. 2025 | 从 CTI 文档抽 TTP，再用 actor-TTP profile 做 actor ranking | 堵住“CTI->TTP->actor”的朴素路线；TTP-only attribution 只能做 baseline |
| AttacKG+ | 用 LLM 从 CTI 文本构建 behavior graph、ATT&CK labels、state summary | 堵住“用 LLM 构建文本 attack graph”的创新 |
| MM-AttacKG | 用 MLLM 解析 CTI 图像，把图像信息补进 attack graph | 堵住“多模态 CTI 图文融合构图”的创新 |
| TAA-EPLMR | 题名显示其做 evidence path-enhanced LLM reasoning for threat actor attribution | 最高撞题风险；全文未获取前必须避开 evidence-path 宽题 |

## 2. 已经不能作为主创新的方向

1. 不能只写：`LLM + RAG 做 APT 归因解释`。
   - AURA 已经做了。

2. 不能只写：`多智能体做 APT 归因`。
   - AURA 已经做了。

3. 不能只写：`CTI 文本 -> TTP -> actor attribution`。
   - Guru et al. 已经做了。

4. 不能只写：`LLM 从 CTI 构建 attack graph`。
   - AttacKG+ 已经做了。

5. 不能只写：`多模态 CTI 图文构建 attack graph`。
   - MM-AttacKG 已经做了。

6. 暂时不要写：`evidence path-enhanced LLM attribution`。
   - TAA-EPLMR 题名已经高度接近。

## 3. 现在真正可做的窄口

最稳方向：

> 面向证据不完整场景的证据充分性感知与可拒答大语言模型辅助 APT 归因解释方法。

这个方向的重点不是“让 LLM 给出 actor”，而是：

> 判断当前证据能不能支持 actor-level attribution；如果不能，应降级到 technique / intent / campaign，或者拒答。

## 4. 你的方法应该怎么设计

### 核心输入

最小可行输入：

- CTI report；
- 从报告抽取的 TTP / atomic threat actions；
- IOC / malware / tool / infrastructure mentions；
- ATT&CK / actor profile / CTI KG 检索证据。

可选增强输入：

- sample linking features；
- provenance / log evidence；
- attack summary graph；
- CTI images / attack graph evidence。

### 核心输出

不要只输出 actor label。应输出：

- 可支持的最高归因层级：
  - technique；
  - intent；
  - campaign；
  - actor；
  - insufficient evidence。
- candidate actors；
- confidence / probability；
- supporting evidence；
- conflicting evidence；
- missing evidence；
- refusal / abstention reason。

### 核心模块

```text
Input evidence
  -> evidence availability profile
  -> evidence unit construction
  -> actor / intent / campaign candidate retrieval
  -> evidence sufficiency scoring
  -> confidence calibration
  -> adaptive attribution granularity
  -> grounded explanation or refusal
```

## 5. 和已有工作的差异

| 已有工作 | 它们问的问题 | 你应问的问题 |
|---|---|---|
| Guru | 用 TTP 能不能排 actor？ | TTP 什么时候不足以支撑 actor？ |
| AURA | 能不能生成可解释归因？ | 解释的证据是否足够，何时应拒答？ |
| AttacKG+ | 能不能把 CTI 文本构成 attack graph？ | attack graph 证据能支持哪一层归因？ |
| MM-AttacKG | 图像能不能补全 attack graph？ | 图文证据冲突/缺失时如何降级归因？ |
| APT-MMF | report-IOC graph 能否分类 actor？ | closed-set 分类不可信时如何表达 unknown / insufficient evidence？ |
| TAA-EPLMR | evidence path 能否增强 LLM 归因？ | evidence path 不足或冲突时如何校准置信度并拒答？ |

## 6. 专利写法建议

专利题目建议：

> 一种面向证据不完整场景的证据充分性感知与可拒答大语言模型辅助高级持续性威胁归因解释方法。

权利要求核心不要写成“LLM + RAG + attribution”，而应写成：

1. 证据可用性画像生成；
2. 多粒度证据单元构建；
3. 归因层级可支持性判断；
4. 候选 actor 证据充分性评分；
5. 置信度校准；
6. 证据不足时的降级输出或拒答；
7. 带证据引用、缺失证据说明和补充取证建议的报告生成。

## 7. 论文实验应该怎么做

### Baseline

- closed-book LLM attribution；
- vanilla RAG attribution；
- AURA-style RAG/agent attribution；
- TTP-only attribution；
- graph-only attribution；
- no-refusal version；
- no-sufficiency-score version。

### Ablation

- CTI only；
- CTI + TTP；
- CTI + IOC；
- CTI + IOC + actor profile；
- 删除关键证据；
- 加入冲突证据；
- 加入 actor overlap case。

### 指标

- actor top-1 / top-2 accuracy；
- intent / campaign accuracy；
- evidence citation precision；
- confidence calibration：ECE / Brier；
- refusal correctness；
- over-attribution rate；
- adaptive granularity accuracy；
- hallucinated evidence rate。

## 8. 最终判断

Project05 不应该继续推进原宽题：

> 多源安全证据自适应融合与大语言模型辅助 APT 归因解释。

因为它会被 AURA / TAA-EPLMR / APT-MMF / CTIConnect 分别撞掉。

更稳、更像专利、也更能转论文的方向是：

> 证据不完整条件下，LLM 辅助归因系统如何判断证据是否足以支撑某一级别的归因，并在证据不足时进行降级或拒答。

