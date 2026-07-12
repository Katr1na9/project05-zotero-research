# P05-L2 Research Dashboard

更新：2026-07-12

## 当前状态

| 项目 | 状态 |
|---|---|
| Working name | Multimodal Threat Attribution |
| ARS mode | deep-research / socratic |
| Current stage | Stage 1 preliminary collision complete; W1 amber |
| RQ Brief | 未生成 |
| FINER | 未评分 |
| Novelty search | 初筛完成；I1/I2/I3 宽版本撞题，G2 未通过 |
| Data feasibility | 已发现可控五模态实验链；本地数据与运行代码快照不完整 |
| Method/experiment | 禁止提前启动 |
| Material Passport | 已建立，内容为空 |

## 当前唯一安全表述

> 面向 IPv4、IPv6、MPLS、GeoNetworking 与 SCION 异构路径，探索配置、声明和实际数据面观测之间的一致性证据如何约束攻击行为追溯与意图候选感知；具体 RQ 仍需撞题检索和用户确认。

## Project03 交接状态

- 已核验工程主链、理论边界、五模态验收流程、stage/intent 代码和 2026-06 开发记录。
- 已建立 [交接审计](../04-progress/project03-handoff-audit-20260712.md)、[候选 idea 池](../03-ideas/project03-derived-idea-pool-v0.1.md) 与 [复用验证计划](../09-experiments/project03-reuse-and-validation-plan-v0.1.md)。
- [初步撞题扫描](../02-literature-notes/collision-scan-project03-ideas-20260712.md) 已完成：I1/I2/I3 宽版本均淘汰或降级。
- 当前唯一保留的是 `amber` W1：协议 transformation 下行为证据的保真/丢失/冲突及其对 stage/TTP/intent supportability 的约束。
- 当前没有把 W1 标记为论文创新。

## Gate 状态

| Gate | 状态 | 通过条件 |
|---|---|---|
| Workspace Gate | 通过 | 独立 00-09 工作区、共享边界和日志已建立 |
| G1 RQ | 未开始 | 单一可回答问题；明确输入、输出、数据、指标和排除范围 |
| G2 Search | 未开始 | 完成当前成果与撞题检索，来源可验证 |
| G3 White Space | 未开始 | 多模态贡献未被既有工作完整覆盖 |
| G4 Method | 未开始 | 方法模块与失败条件可证伪 |
| G5 Experiment | 未开始 | 数据、baseline、指标和计算资源可执行 |

## 尚未决定的问题

1. I1、I3 或 I2 中，哪个在最新成果中仍存在功能级白空间？
2. Project03 能否恢复五模态严格配对数据，尤其是 MPLS 和真实 SCION wire evidence？
3. 主要输出应收敛到逐跳行为追溯、阶段/TTP 候选，还是二者中的一个？
4. intent ground truth 从哪里获得，避免继续用 attack type 规则自证？
5. 多模态增益能否超越更可靠的单模态观测与协议归一化 baseline？

## 下一步

按 [reading queue](../02-literature-notes/reading-queue.md) 精读 P0 五篇直接近邻。只有 W1 在 P0 精读后仍能与 SecTracer、Forensic Coverage、ID-INT 和 P4Prime 形成可操作差异，才生成 RQ Summary 交由用户选择。
