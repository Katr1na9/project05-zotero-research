# P05-L2 Research Dashboard

更新：2026-07-15

## 当前状态

| 项目 | 状态 |
|---|---|
| Working name | Traffic-Log Evidence Graph + LLM Threat Tracing |
| ARS mode | deep-research / synthesis complete |
| Current stage | Stage 3 complete; user topic selection pending |
| Literature freeze | 2026-07-13 |
| Corpus | C01-C61/F01-F06；全文/受限状态已分层 |
| G2 Search | passed |
| G3 White Space | conditional pass; R2 strongest |
| RQ Brief | 3 candidates prepared, not frozen |
| Data feasibility | ProvICS primary, AIT v2 external; pilot/license gates pending |
| Zotero sync | 20 new items in target collection; 12 stored PDFs verified; 8 metadata-only |
| Method/experiment | blueprint only; implementation prohibited before user approval |

## 当前最安全表述

> 面向独立构建且保留原始锚点的流量与日志观测子图，将 packet-log 关联建模为 campaign-disjoint、可校准的多候选关系任务，研究关系不确定性如何影响攻击链重构及证据约束 LLM 的解释与拒答。

## Project03 复用边界

- 复用：PCAP 解析、ThreatObservation 生成、图查询与溯源定位思想。
- 补建：统一 TrafficObservation、LogObservation、raw anchors、跨源关系状态和独立日志子图。
- 不复用：CENI controller/网元部署、为平台兼容做的隧道/代理妥协、attack-type 规则真值。
- IPv4/IPv6/MPLS/Geo/SCION：作为协议/环境分层；只有数据真实存在时才进入鲁棒性实验。

## Gate 状态

| Gate | 状态 | 证据/通过条件 |
|---|---|---|
| Workspace | 通过 | 独立 00-09 工作区及共享边界存在 |
| G1 RQ | 待用户 | 从 A/B/C 中选择并冻结一个 Primary RQ |
| G2 Search | 通过 | v0.3 语料、二次检索、引文 sweep、访问分层 |
| G3 White Space | 条件通过 | R2 直接等价未发现；禁止 universal first claim |
| G4 Method | 仅蓝图 | 用户确认后细化 schema/model/failure criteria |
| G5 Experiment | 未通过 | license、pilot annotation agreement、campaign split 尚未完成 |

## 三个候选

1. A：source-preserving 双源事件证据图 + evidence-constrained LLM chain reasoning。
2. B：calibrated traffic-log relation learning + uncertainty propagation。
3. C：可信 LLM 攻击链解释 + 高层意图感知。

推荐：A 作为叙事，B 作为必做核心，C 作为可选扩展。详见 [候选题矩阵](../03-ideas/candidate-thesis-topics-and-feasibility-v0.1-20260715.md)。

## 当前唯一下一步

由用户人工选择候选题或批准推荐层级。确认前不下载数据、不实现模型、不写论文正文。
