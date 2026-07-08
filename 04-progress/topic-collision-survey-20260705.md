# 选题撞题调查：证据不完整场景下的 LLM 辅助 APT 归因

## 2026-07-05 增补结论：2026 H1 并非空白

本轮进一步补读 2026 年上半年关键工作后，判断需要更新：

| 工作 | 已经推进到哪里 | 对 Project05 的压力/启发 |
|---|---|---|
| TTPrint | evidence-grounded TTP extraction，含证据片段定位和验证 | TTP 抽取与 evidence grounding 不能再作为核心创新 |
| CTI-Thinker | LLM + LoRA + CTI KG + ATT&CK alignment + GraphRAG attack reasoning | GraphRAG/KG attack reasoning 已有强相关工作，Project05 必须区分为 evidence sufficiency/refusal |
| OpenSec | 测量安全 agent 在 adversarial evidence 下是否 evidence-gated action | 可迁移为 evidence-gated attribution、over-attribution rate、correct abstention |
| Minerva | CTI LLM 的 RLVR 和 verifiable rewards | 可借鉴 verifier，但不要把“训练 CTI LLM”当作主创新 |
| High-Precision APT Malware Attribution | open-set / out-of-scope malware attribution，显式 abstain | Project05 必须纳入 unknown actor/OOS，否则拒答创新不够强 |
| Synthetic APTs | AI agent 可模仿 APT TTP，TTP-based attribution 假设被削弱 | Project05 应把 TTP 当中弱证据，并做 mimicry/false-flag 压力测试 |
| ARCANE | 跨 campaign Bayesian telemetry 累积仍可能低置信 | 多证据累积不等于可归因，系统价值在于判断“不够” |

因此，Project05 不能继续表述为：

> 一种面向证据不完整场景的多源安全证据自适应融合与大语言模型辅助 APT 归因解释方法

更稳妥的专利/论文切口是：

> 一种面向证据不完整与开放集行为体场景的证据充分性感知、分层降级与可拒答大语言模型辅助 APT 归因解释方法

核心差异化不在“多源融合”本身，而在：

1. 证据可用性画像；
2. 证据区分度与可靠性评分；
3. actor/campaign/intent/technique 分层归因门控；
4. unknown actor / out-of-scope / false flag / TTP mimicry 下的拒答；
5. 带证据引用、缺失证据说明和补充取证建议的 LLM 解释。

## 候选题目

一种面向证据不完整场景的多源安全证据自适应融合与大语言模型辅助 APT 归因解释方法。

## 核心判断

该方向不是空白。2024-2026 年已经出现了多条强相关工作：

- APT-MMF 已经做了 CTI/IOC 多模态、多层级特征融合的 APT actor classification，并宣称对不完整和噪声信息有鲁棒性。
- ADAPT it! 已经做了异构恶意文件样本的 campaign/group 双层归因。
- CTIBench / CTIConnect 已经把 LLM-CTI 评测和异构 CTI RAG 推到比较成熟的位置。
- Guru 等 2025 已经做了 LLM/embedding 从 CTI 文档到 TTP，再到 threat actor attribution 的端到端 proof-of-concept。
- AURA 2025 已经提出 RAG + multi-agent + LLM 的可解释 APT 归因框架，覆盖 TTP、IOC、malware、tools、timeline 等威胁情报线索。
- TAA-EPLMR 2025 已经非常接近“evidence path + LLM reasoning + threat actor attribution”。

因此，不能把创新点写成泛泛的“多源证据融合 + LLM 归因解释”。这个表述撞题风险较高。

## 现有工作做到的程度

| 工作 | 已做到 | 没完全做到 |
|---|---|---|
| APT-MMF | 报告-IOC 异构属性图，多模态特征融合，多层注意力，actor 分类，对缺失/噪声有一定鲁棒性 | 不是 LLM 解释系统；主要是已知 actor 分类；unknown actor、false flag、拒答和证据充分性不足 |
| ADAPT it! | 异构文件样本的 campaign/group 聚类，支持 executables/documents/linking features | 不处理 CTI 文本推理，不输出自然语言归因解释，不处理证据不足拒答 |
| AttacKG+ / MM-AttacKG | LLM/MLLM 从 CTI 文本/图像构建攻击图、TTP label、状态摘要 | 重点是 attack graph construction，不是 actor attribution 的不确定性与证据充分性 |
| CTIBench | LLM-CTI benchmark，包含 attack technique extraction 与 threat actor attribution | closed-book 为主，不是多源证据融合方法 |
| CTIConnect | 异构 CTI RAG benchmark，覆盖 CVE/CWE/CAPEC/ATT&CK/report 等跨源检索 | 重点在检索评测，不是 APT 归因解释方法；不强调 evidence missing/refusal |
| Guru et al. 2025 | LLM/embedding 做 TTP identification，再用 TTP 做 actor attribution | 主要依赖 TTP；作者也指出 off-the-shelf LLM 不足以用于高风险自动化归因 |
| AURA 2025 | RAG + multi-agent + LLM 的可解释 APT attribution，输入包括 TTP/IOC/malware/tools/timeline | 评测集小；解释没有显式 evidence weighting/confidence scoring；证据缺失不是核心机制 |
| TAA-EPLMR 2025 | evidence path-enhanced LLM reasoning for threat actor attribution | 题目高度接近；需要进一步找全文确认其 evidence path、confidence 和不完整证据设置 |
| High Stakes, Low Certainty | 实证说明单类 IOC/TTP 对归因并不充分，误归因风险高 | 不是方法论文，但强力支撑 evidence sufficiency/refusal 的研究必要性 |
| LLMs Are Unreliable for CTI | 证明真实 CTI 报告上 LLM 存在性能、一致性、过度自信问题 | 不是归因方法，但支撑校准、拒答和证据约束 |

## 对原题的风险判断

原题如果写成：

> 一种面向证据不完整场景的多源安全证据自适应融合与大语言模型辅助 APT 归因解释方法

风险在于：

1. “多源安全证据融合”已经被 APT-MMF、ADAPT、AURA、CTIConnect 分别覆盖了一大块。
2. “LLM 辅助 APT 归因解释”已经被 AURA 和 TAA-EPLMR 明显靠近。
3. “证据不完整”在 APT-MMF 和 AURA 的问题动机中已经出现，但还未被做成核心机制。

所以更稳的切口不是“多源融合本身”，而是：

> 缺失感知的证据充分性评估、动态降级归因和拒答机制。

## 更稳的收窄方向

建议把题目收窄为：

一种面向证据不完整场景的证据充分性感知与可拒答大语言模型辅助 APT 归因解释方法。

或者：

一种基于可用证据自适应融合和证据充分性校准的大语言模型辅助 APT 归因解释方法。

核心创新点应变为：

1. Evidence availability profile：先识别当前案件可用证据类型、缺失证据类型、证据粒度和可靠性。
2. Evidence sufficiency scoring：判断证据足以支持 TTP、intent、campaign、actor 哪一层结论。
3. Adaptive attribution granularity：证据不足时不强行输出 actor，而是降级到 technique / intent / campaign hypothesis。
4. Refusal / abstention：当候选 actor 相似度高、证据冲突、关键证据缺失时拒绝高置信归因。
5. Evidence-grounded explanation：每个结论绑定 CTI sentence、IOC edge、sample feature、provenance path 或 retrieved source。

## 专利可写的差异化表述

专利不应重点保护“LLM + RAG + APT 归因”这个大框，因为已有 AURA / TAA-EPLMR。

更可保护的技术方案是：

1. 对输入案件生成证据可用性画像；
2. 根据证据画像选择不同证据通道和不同归因粒度；
3. 对候选归因结论生成证据充分性分数；
4. 根据分数触发高置信归因、低置信候选、降级解释或拒答；
5. 输出带证据引用、缺失证据说明和补充取证建议的归因解释。

## 下一步需要补查

- 获取并精读 TAA-EPLMR 全文，确认它是否已经覆盖：
  - evidence sufficiency；
  - incomplete evidence ablation；
  - confidence calibration；
  - refusal / abstention；
  - unknown actor / false flag；
  - 多证据源是否包含日志/provenance 或仅限 CTI KG。
- 若 TAA-EPLMR 已覆盖 evidence path + confidence，则 Project05 必须进一步转向：
  - provenance/log evidence 与 CTI evidence 的对齐；
  - evidence missing 下的 abstention calibration；
  - actor attribution 的 open-set/unknown actor 机制。

## 2026-07-05 补读更新

- 已新增全文精读：AURA、Guru et al. 2025、AttacKG+、MM-AttacKG。
- 已建立高风险笔记：TAA-EPLMR；2026-07-08 已完成新主线复核，确认其覆盖 evidence path + LLM CoT + confidence + incomplete/noisy IOC 鲁棒归因。
- 更新判断：
  - AURA 已经覆盖 RAG + multi-agent + LLM 的可解释 APT attribution。
  - Guru et al. 已经覆盖 CTI -> TTP -> actor ranking。
  - AttacKG+ / MM-AttacKG 已经覆盖 LLM/MLLM 文本与多模态 attack graph construction。
  - Project05 的安全切口应从“多源证据融合”改成“证据不完整下的 evidence sufficiency / confidence / refusal / adaptive granularity”。

## 参考来源

- APT-MMF: https://arxiv.org/abs/2402.12743
- ADAPT it!: https://discovery.ucl.ac.uk/id/eprint/10212286/
- AttacKG+: https://arxiv.org/abs/2405.04753
- MM-AttacKG: https://arxiv.org/abs/2506.16968
- CTIBench: https://arxiv.org/abs/2406.07599
- CTIConnect: https://cticonnect.github.io/
- Guru et al. 2025: https://arxiv.org/html/2505.11547
- AURA: https://arxiv.org/pdf/2506.10175
- TAA-EPLMR: https://ieeexplore.ieee.org/document/11402113/
- High Stakes, Low Certainty: https://www.usenix.org/conference/usenixsecurity25/presentation/van-der-horst
- LLMs Are Unreliable for CTI: https://www.researchgate.net/publication/390354860_Large_Language_Models_are_Unreliable_for_Cyber_Threat_Intelligence
