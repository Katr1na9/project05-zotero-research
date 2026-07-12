# P05-L2 Research Dashboard

更新：2026-07-12

## 当前状态

| 项目 | 状态 |
|---|---|
| Working name | Multimodal Threat Attribution |
| ARS mode | deep-research / socratic |
| Current stage | Stage 0 Inbox |
| RQ Brief | 未生成 |
| FINER | 未评分 |
| Novelty search | 未启动 |
| Data feasibility | 未确认 |
| Method/experiment | 禁止提前启动 |
| Material Passport | 已建立，内容为空 |

## 当前唯一安全表述

> 探索多模态证据在威胁归因或安全调查中的任务价值；具体模态、任务、数据、方法和评价终点均待 RQ Scoping 决定。

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

1. 目标任务是 threat actor attribution、campaign reconstruction、TTP/attack-chain extraction，还是调查控制？
2. 要融合的模态是报告文本、报告图像、主机日志、网络流、provenance graph、IOC、恶意样本，还是其中的严格子集？
3. 多模态增益要解决缺失证据、冲突证据、跨模态对应，还是单模态不可观察性？
4. 有哪些公开数据能提供真实配对模态和可靠标签？
5. 最终评价是归因正确性、证据 grounding、攻击链完整性、调查成本，还是拒答/校准？

## 下一步

进入 [RQ Scoping](../03-ideas/rq-scoping.md)，由用户回答 Socratic 第一轮问题。用户确认至少一个 RQ 方向前，不进行系统检索、题名生成、论文大纲或模型设计。
