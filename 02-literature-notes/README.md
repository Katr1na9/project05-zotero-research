# Literature Notes

这里存放 Project05 的逐篇精读笔记、专利红线笔记和高风险相关工作记录。

阅读要求：

- 不只写摘要，要写清楚“这篇对我的选题有什么影响”。
- 每篇至少提炼：研究问题、方法框架、数据集与指标、可借鉴点、局限、对 Project05 的撞题风险。
- 专利类材料重点记录权利要求红线。

## 当前精读清单

- [x] `2019-Milajerdi-POIROT.md`
- [x] `2020-Han-UNICORN.md`
- [x] `2021-Wei-DeepHunter.md`
- [x] `2021-Sarhan-Open-CyKG.md`
- [x] `2021-Satvat-EXTRACTOR.md`
- [x] `2021-US20210281585A1-Confidence-Level-Cyber-Campaign-Attribution.md`
- [x] `2022-Li-AttacKG.md`
- [x] `2022-Wang-THREATRACE.md`
- [x] `2022-Xu-DEPCOMM.md`
- [x] `2023-Teuwen-Modular-Threat-Attribution-Opinion-Pools.md`
- [x] `2023-Yang-PROGRAPHER.md`
- [x] `2024-Alam-CTIBench.md`
- [x] `2024-Chen-GAPT-Temporal-Relation-Embeddings.md`
- [x] `2024-Cheng-KAIROS.md`
- [x] `2024-Aly-MEGR-APT.md`
- [x] `2024-CN118646607A-APT-KG-LLM-Enhancement-Patent.md`
- [x] `2024-HG-CTA-Heterogeneous-Graph-Cyber-Threat-Attribution.md`
- [x] `2024-Huang-Cascade-APT-Campaign-Attribution-Logs.md`
- [x] `2024-Huang-SAGA-Synthetic-Audit-Log-Generation-APT.md`
- [x] `2024-Ji-SEvenLLM.md`
- [x] `2024-Rani-TTPXHunter.md`
- [x] `2024-Saha-ADAPT-it.md`
- [x] `2024-Xiao-APT-MMF.md`
- [x] `2024-Zhang-AttacKG-plus.md`
- [x] `2025-Aronsson-AFA-Survey.md`
- [x] `2025-Au-Multi-Source-Feature-Fusion-HKG-APT-Attribution-IDS.md`
- [x] `2025-Basnet-APT-Attribution-DRL.md`
- [x] `2025-Boge-Unveiling-Cyber-Threat-Actors.md`
- [x] `2025-Cai-APT-ATT-High-Risk-Related.md`
- [x] `2025-CN120110776B-Attack-Pattern-Clustering-Attribution-Patent.md`
- [x] `2025-Gandhi-SHIELD-APT-Detection-LLM-Explanation.md`
- [x] `2025-Guru-Technique-Identification-Threat-Actor-Attribution.md`
- [x] `2025-Horst-High-Stakes-Low-Certainty.md`
- [x] `2025-Kim-Multi-Step-LLM-Pipeline-TTP-Extraction.md`
- [x] `2025-Lekssays-TechniqueRAG.md`
- [x] `2025-Li-CLIProv.md`
- [x] `2025-Mezzi-LLMs-Unreliable-CTI.md`
- [x] `2025-Mitra-LocalIntel.md`
- [x] `2025-NOCTA-Non-Greedy-Objective-Cost-Tradeoff-Acquisition.md`
- [x] `2025-Prasad-Cyber-Threat-Attribution-Survey.md`
- [x] `2025-Qiu-APT-CGLP.md`
- [x] `2025-Rani-AURA.md`
- [x] `2025-US12368730B2-Multiple-Evidence-Threat-Actor-Attribution-Patent.md`
- [x] `2025-Xiao-TAA-EPLMR.md`
- [x] `2025-Zhang-APTChaser-Attack-Technique-Modeling.md`
- [x] `2025-Zhang-MM-AttacKG.md`
- [x] `2025-ExCyTIn-Bench-Cyber-Threat-Investigation.md`
- [x] `2026-AARGS-APT-Attack-Inference-Organization-Patent.md`
- [x] `2026-Adaptive-Malware-Detection-Sequential-Feature-Selection-DDQN.md`
- [x] `2026-Alam-Minerva.md`
- [x] `2026-Alshamrani-LLMAPT.md`
- [x] `2026-APTA2D-Attention-Pruning-2D-Convolutional-Reasoning.md`
- [x] `2026-Balassone-Synthetic-APTs.md`
- [x] `2026-Barnes-OpenSec.md`
- [x] `2026-Cheng-CTIConnect.md`
- [x] `2026-Cheng-TTPrint.md`
- [x] `2026-Duan-MLDSJ-Multi-Level-Feature-Joint-Attribution.md`
- [x] `2026-Hamzic-Beyond-RAG-CTI.md`
- [x] `2026-Meng-Uncovering-Vulnerabilities-LLM-Assisted-CTI.md`
- [x] `2026-Saha-Kitten-or-Panda-Group-Profile-Specificity.md`
- [x] `2026-Varonis-US12530469-LLM-Alert-Investigation.md`
- [x] `2026-Weinberg-ARCANE-Bayesian-Cyber-Attribution.md`
- [x] `2026-Williams-High-Precision-APT-Malware-Attribution.md`
- [x] `2026-Yang-CTI-Thinker.md`

## 2026-07-06 新增主线增量

- `2025-Aronsson-AFA-Survey.md`: 将 Project05 的“补证/取证”问题连接到 Active Feature Acquisition 与 POMDP 形式化，是当前新主线的理论基座。
- `2025-Li-CLIProv.md`: 命中日志 / provenance 到威胁情报语义对齐方向，提示“语义统一/对齐”不能作为主创新。
- `2025-Qiu-APT-CGLP.md`: 命中 CTI report 与 provenance graph 的 graph-language pre-training，进一步压缩单独做 CTI-local alignment 的空间。
- `2026-Varonis-US12530469-LLM-Alert-Investigation.md`: 专利红线，覆盖 LLM 多阶段告警调查、置信收敛和追加上下文请求的宽泛循环。

## 2026-07-07 精读补齐增量

- `2019-Milajerdi-POIROT.md`: CTI query graph 与 provenance graph 对齐的起点文献，确认“CTI-local evidence alignment”不能作为 Project05 主创新。
- `2021-Wei-DeepHunter.md`: GNN 增强 POIROT 式威胁狩猎，压缩“攻击图表示学习匹配”创新空间。
- `2024-Aly-MEGR-APT.md`: 大规模、内存高效 provenance graph hunting 系统，提示 Project05 不应写成可扩展图匹配。
- `2025-Li-CLIProv.md`: 已由摘要级占位升级为全文精读；确认 log-to-intelligence semantic alignment 与 TTP/attack scenario 输出已被覆盖。
- `2025-Qiu-APT-CGLP.md`: 已由摘要级占位升级为全文精读；确认 graph-language pre-training + LLM synthetic CTI 已被覆盖。
- `2025-NOCTA-Non-Greedy-Objective-Cost-Tradeoff-Acquisition.md`: 为 Project05 的 cost-aware next evidence action planning 提供非贪心 AFA 参照。
- `2025-ExCyTIn-Bench-Cyber-Threat-Investigation.md`: 作为安全调查 agent benchmark 参照，可借鉴其 graph-grounded evaluation，但不把 LLM agent 调查作为主创新。
- `2026-Adaptive-Malware-Detection-Sequential-Feature-Selection-DDQN.md`: 安全侧顺序特征获取最近邻，适合作为 Project05 planner baseline/对比对象。

## 仍需补全文

- [ ] `APT-ATT`: `An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN`
- [ ] `APTChaser`: 当前只有 Springer 摘要和元数据，正文仍需获取。
- [ ] `GAPT`: 当前只确认二级引用线索，需验证 DOI、全文和独立记录。
- [x] `US12530469`: 当前保留为说明书/摘要级风险笔记；权利要求原文补读已从当前 workflow 剔除。
- [ ] `TAA-EPLMR`: 已有正文线索，但需复核是否覆盖 confidence / reasoning chain / evidence path / incomplete evidence。

## 当前红线判断

宽泛的 `多源证据融合 + LLM 辅助 APT 归因解释` 已经不安全。

尤其需要避开的表述：

- `multiple evidence + threat actor attribution`
- `evidence path + LLM reasoning + threat actor attribution`
- `LLM-based APT attribution framework`
- `APT KG + LLM`
- `LLM/RAG/KG/TTP + attack tree + attribution`
- `confidence level + information gap + hunting recommendation`
- `multi-level feature + Dempster-Shafer evidence fusion + APT group attribution`
- `LLM-based attack technique schema / technique profile for APT attribution`
- `CTI graph + provenance/local evidence alignment`
- `log-to-intelligence multimodal alignment`

当前相对更安全的收窄方向：

> 将 CTI-本地证据对齐结果作为部分可观测证据状态，在归因粒度收益和取证成本约束下，规划下一步证据获取动作，并在达到目标粒度或预算终止时输出粒度受控的归因结论。
