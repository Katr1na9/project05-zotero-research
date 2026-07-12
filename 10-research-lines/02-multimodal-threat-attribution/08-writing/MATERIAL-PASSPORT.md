# P05-L2 Material Passport

## Identity

- Line ID：P05-L2
- Working name：Multimodal Threat Attribution
- Created：2026-07-12
- Active workflow：academic-research-suite / deep-research / socratic
- Current stage：Stage 0 Inbox

## Verified Inputs

- 用户原始 idea：希望在 Project05 中建立多模态论文支线。
- 共享背景：Project05 已有威胁归因、CTI、ATT&CK、KG/RAG、provenance 和可信评估精读。
- 用户限定的五种模态：IPv4、IPv6、MPLS、GeoNetworking、SCION。
- 用户在 Project03 的已有职责与积累：行为追溯、攻击意图候选感知。
- Project03 本地快照已审计，见 [handoff audit](../04-progress/project03-handoff-audit-20260712.md)。
- 已核验 Geo 外层 `0x8947`；IPv6 有逐跳实测记录；SCION 当前只有 intended label，wire 表现为 IPv4/UDP。

## Not Yet Verified

- 具体研究问题；
- 具体模态组合；
- 多模态相对单模态的真实增益；
- 可用数据集与标签；
- 最新工作是否已覆盖候选 idea；
- 120 条多模态批次的原始 PCAP/CSV 与完整运行代码；
- MPLS 的完整证据包与真实 SCION 封装；
- stage/intent 的独立人工或权威 ground truth；
- W1 是否在 SecTracer、Forensic Coverage、ID-INT 和 P4Prime 的全文中仍有功能级差异；
- 方法、指标、venue 和论文题目。

## Human-Read State

本线尚未建立独立文献语料。不得把共享笔记的存在自动记为“本线已完成阅读与综合”。

## Current Boundary

工作区结构、五模态范围和 Project03 交接事实已冻结。I1/I2/I3 宽版本已被初步撞题检索淘汰或降级；W1 仅为 `amber` 问题母体，不是创新主张。任何后续 RQ、文献结论和方法主张都必须带来源、日期、验证状态和对应 Gate。
