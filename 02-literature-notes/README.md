# Literature Notes

这里存放 Project05 的逐篇精读笔记、专利红线笔记和高风险相关工作记录。

阅读要求：

- 不只写摘要，要写清楚“这篇对我的选题有什么影响”。
- 每篇至少提炼：研究问题、方法框架、数据集与指标、可借鉴点、局限、对 Project05 的撞题风险。
- 专利类材料要重点记录权利要求红线。

## 当前精读清单

- [x] `2020-Han-UNICORN.md`
- [x] `2021-Sarhan-Open-CyKG.md`
- [x] `2021-Satvat-EXTRACTOR.md`
- [x] `2021-US20210281585A1-Confidence-Level-Cyber-Campaign-Attribution.md`
- [x] `2022-Li-AttacKG.md`
- [x] `2022-Wang-THREATRACE.md`
- [x] `2022-Xu-DEPCOMM.md`
- [x] `2023-Teuwen-Modular-Threat-Attribution-Opinion-Pools.md`
- [x] `2023-Yang-PROGRAPHER.md`
- [x] `2024-Alam-CTIBench.md`
- [x] `2024-Cheng-KAIROS.md`
- [x] `2024-CN118646607A-APT-KG-LLM-Enhancement-Patent.md`
- [x] `2024-Huang-Cascade-APT-Campaign-Attribution-Logs.md`
- [x] `2024-Huang-SAGA-Synthetic-Audit-Log-Generation-APT.md`
- [x] `2024-Ji-SEvenLLM.md`
- [x] `2024-Rani-TTPXHunter.md`
- [x] `2024-Saha-ADAPT-it.md`
- [x] `2024-Xiao-APT-MMF.md`
- [x] `2024-Zhang-AttacKG-plus.md`
- [x] `2025-Basnet-APT-Attribution-DRL.md`
- [x] `2025-Boge-Unveiling-Cyber-Threat-Actors.md`
- [x] `2025-Cai-APT-ATT-High-Risk-Related.md`
- [x] `2025-CN120110776B-Attack-Pattern-Clustering-Attribution-Patent.md`
- [x] `2025-Guru-Technique-Identification-Threat-Actor-Attribution.md`
- [x] `2025-Horst-High-Stakes-Low-Certainty.md`
- [x] `2025-Kim-Multi-Step-LLM-Pipeline-TTP-Extraction.md`
- [x] `2025-Lekssays-TechniqueRAG.md`
- [x] `2025-Mezzi-LLMs-Unreliable-CTI.md`
- [x] `2025-Mitra-LocalIntel.md`
- [x] `2025-Prasad-Cyber-Threat-Attribution-Survey.md`
- [x] `2025-Rani-AURA.md`
- [x] `2025-US12368730B2-Multiple-Evidence-Threat-Actor-Attribution-Patent.md`
- [x] `2025-Xiao-TAA-EPLMR.md`
- [x] `2025-Zhang-MM-AttacKG.md`
- [x] `2026-Alam-Minerva.md`
- [x] `2026-Alshamrani-LLMAPT.md`
- [x] `2026-APTA2D-Attention-Pruning-2D-Convolutional-Reasoning.md`
- [x] `2026-Balassone-Synthetic-APTs.md`
- [x] `2026-Barnes-OpenSec.md`
- [x] `2026-Cheng-CTIConnect.md`
- [x] `2026-Cheng-TTPrint.md`
- [x] `2026-Hamzic-Beyond-RAG-CTI.md`
- [x] `2026-Meng-Uncovering-Vulnerabilities-LLM-Assisted-CTI.md`
- [x] `2026-Saha-Kitten-or-Panda-Group-Profile-Specificity.md`
- [x] `2026-Weinberg-ARCANE-Bayesian-Cyber-Attribution.md`
- [x] `2026-Williams-High-Precision-APT-Malware-Attribution.md`
- [x] `2026-Yang-CTI-Thinker.md`

## 仍需补全文

- [ ] `APT-ATT`: `An efficient APT attribution model based on heterogeneous threat intelligence representation and CTGAN`

## 当前红线判断

宽泛的 `多源证据融合 + LLM 辅助 APT 归因解释` 已经不安全。

尤其需要避开的表述：

- `multiple evidence + threat actor attribution`
- `evidence path + LLM reasoning + threat actor attribution`
- `LLM-based APT attribution framework`
- `APT KG + LLM`
- `LLM/RAG/KG/TTP + attack tree + attribution`
- `confidence level + information gap + hunting recommendation`

相对更安全的收窄方向：

> 证据可用性诊断、证据充分性门控、自适应归因粒度、open-set / mimicry / false-flag 场景下的拒答或暂缓归因。

