# P05-L2 Reading Queue

更新：2026-07-12  
目的：验证 W1 是否有真实白空间。Agent 论文继续后置。

## P0：直接决定去留

1. [SecTracer: A framework for uncovering the root causes of network intrusions via security provenance](https://doi.org/10.1016/j.cose.2025.104760)
2. [Auditing Inferential Blind Spots: A Framework for Evaluating Forensic Coverage in Network Telemetry Architectures](https://doi.org/10.3390/network6010009)
3. [ID-INT: Secure Inter-Domain In-Band Telemetry](https://dl.ifip.org/db/conf/cnsm/cnsm2024/1571050975.pdf)
4. [P4Prime: Deterministic runtime consistency and loop verification with faulty switch localization in programmable SDNs](https://doi.org/10.1016/j.comnet.2026.112446)
5. [EPIC: Every Packet Is Checked in the Data Plane of a Path-Aware Internet](https://www.usenix.org/conference/usenixsecurity20/presentation/legner)

精读问题：它们是否已经把 protocol transformation、path evidence 与 attack semantics 连接起来？若答案为是，W1 终止。

## P1：阶段/意图红线

6. [Preliminary Investigation into Uncertainty-Aware Attack Stage Classification](https://arxiv.org/abs/2508.00368)
7. [XAPT: Explainable Anomaly-Driven Prediction of Threat Stages in APT Campaigns](https://doi.org/10.1109/ACCESS.2025.3636501)
8. [Learning the APT Kill Chain: Temporal Reasoning over Provenance Data for Attack Stage Estimation](https://arxiv.org/abs/2603.07560)
9. [Attack plan recognition using hidden Markov and probabilistic inference](https://doi.org/10.1016/j.cose.2020.101974)

精读问题：P05-L2 能否只把 stage/TTP/intent 作为受上游证据边界约束的验证终点，而不重复这些模型贡献？

## P2：跨协议与多模态基线

10. [Protocol-Agnostic and Packet-Based Intrusion Detection Using a Multi-Layer Deep-Learning Architecture at the Network Edge](https://ieeexplore.ieee.org/document/10942348/)
11. [Training with Only 1.0 per mille Samples: Malicious Traffic Detection via Cross-Modality Feature Fusion](https://doi.org/10.1145/3719027.3765143)
12. [M-IDAS preprint](https://openreview.net/pdf?id=rTdbRWWdR5)

精读问题：跨协议行为表示是否已经有足够强的 baseline；Project03 的五协议是否真的提供独立证据，而不只是重新封装同一 PCAP？

## Zotero 状态

本队列仅完成来源发现与稳定链接核验，尚未批量导入 Zotero。待 W1 初读通过后，再建立 P05-L2 子集合并导入保留项，避免把高噪声撞题材料全部并入核心库。

