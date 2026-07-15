# P05-L2: Multimodal Threat Attribution

中文工作名：流量/日志双源事件证据图与 LLM 攻击链/意图推理。

> 目录名仍沿用 `multimodal-threat-attribution`。它不是已冻结论文题目；最终题目和 RQ 等待用户从 3 个候选中人工选择。

## 当前阶段

- ARS workflow：`deep-research / literature investigation and synthesis`
- Stage：Stage 3 synthesis/collision complete
- 文献冻结日期：2026-07-13
- 文献状态：C01-C61/F01-F06 已综合；合法全文均已精读，访问受限条目已显式降级
- G2 Search：通过
- G3 White Space：条件通过；最强残余为 calibrated multi-candidate traffic-log relation
- RQ/G1：3 个候选待用户选择，尚未冻结
- 方法/实验：仅形成蓝图，未启动；G1 与 pilot annotation gate 前禁止实施

## 当前研究边界

流量侧复用 Project03 的 `PCAP -> ThreatObservation`、图查询和溯源定位；日志侧独立构建 `LogObservation/provenance` 子图。两侧通过带不确定性和证据状态的跨源关系进入联合事件证据图，LLM 只消费可回放证据并输出链/ATT&CK/可选高层意图候选。

IPv4、IPv6、MPLS、GeoNetworking 和 SCION 是协议/环境条件，不是五个独立模态。CENI controller、网元部署和兼容性妥协不进入论文主线。

已被占据的宽泛主张包括：traffic+logs+graph、网络增强 provenance、概率证据图、图补边、CTI-to-provenance 匹配、missing-hop recovery 和多智能体调查。禁止再用“首次融合/首次构图/首次 Agent 调查”措辞。

## 权威入口

- [Research Dashboard](00-dashboard/research-dashboard.md)
- [本线科研流程](01-sop/multimodal-research-workflow-v0.1.md)
- [Project03 可复用科研核心](04-progress/project03-reusable-core-audit-20260713.md)
- [检索协议](02-literature-notes/search-protocol-pcap-llm-kg-20260713.md)
- [撞题语料 v0.3](02-literature-notes/collision-corpus-v0.3-20260713.md)
- [功能碰撞矩阵 v0.2](02-literature-notes/functional-collision-matrix-v0.2-20260713.md)
- [二次检索与反方空白审计](02-literature-notes/second-collision-search-20260713.md)
- [数据集可行性审计](09-experiments/dataset-feasibility-audit-v0.1-20260715.md)
- [专利碰撞红线](03-ideas/patent-collision-redline-20260713.md)
- [3 个候选题与可行性矩阵](03-ideas/candidate-thesis-topics-and-feasibility-v0.1-20260715.md)
- [Devil's Advocate Checkpoint 2](03-ideas/devils-advocate-checkpoint-2-20260715.md)
- [Reading Queue](02-literature-notes/reading-queue.md)
- [Material Passport](08-writing/MATERIAL-PASSPORT.md)

## 推荐但未批准的方向

推荐 Candidate A 作为论文叙事，Candidate B 作为必须完成的可测核心，Candidate C 作为可选扩展：

```text
校准 traffic-log 跨源关系
  -> source-preserving 联合事件证据图
  -> 攻击链重构
  -> 证据约束 LLM 的 ATT&CK/意图候选与拒答
```

用户确认前不下载数据、不选择模型、不创建实验结果或论文正文。

## 与 P05-L1 的边界

可共享：单篇精读、CTI/ATT&CK/KG/provenance 概念、证据血缘与可信评价原则。

不可继承：P05-L1 的调查控制 RQ、M2 性能、G0-G3 阈值、C07-C11 结论、规划器和专利叙事。P05-L2 的核心对象是 traffic-log observation relation 与 joint evidence graph，不是证据获取策略。

## 共享入口

- [Project05 共享工作区](../00-shared-workspace/README.md)
- [共享论文精读](../../02-literature-notes/)
- [共享 Zotero 导出](../../07-zotero-exports/)
- [多研究线 SOP](../../01-sop/project05-multi-line-workspace-sop-v0.1.md)
