# Project05 论文 v0.3 写作记录

> **历史记录。** 当前写作记录为 `paper-main-authoring-record-v0.4-20260711.md`。

日期：2026-07-11
流程：nature-writing → Zotero/citation audit → nature-figure → nature-polishing → reviewer/rigor audit

## 1. 路由结果

- paper type：algorithmic research。
- sections：title、abstract、introduction、related work、problem、method、experiments、results、discussion、conclusion。
- language：中文主稿；保留英文题目，后续按目标期刊决定是否整体英译。
- journal：generic high-impact security/AI venue；未强行套用 Nature 主刊篇幅或 CNS 引文范围。
- primary reader：安全分析、威胁归因、主动特征获取和可信 AI 研究者。

## 2. 一句话论点

在 CTI 与本地证据只能部分对齐、动作收益事前不可见且采集通道可能失效时，本文把对齐结果转化为证据缺口状态，并在预算和支持粒度约束下选择取证动作或 STOP；四个参数锁定真实案例和受控非短视诊断表明该闭环可执行，同时否定了 M3a 成本优势、学习器替代 M2 和当前必须使用 DQN 三个更强主张。

## 3. 术语账本

| 概念 | 正文规范用语 | 代码/字段 |
|---|---|---|
| evidence-gap state | 证据缺口状态 | alignment state |
| supportable attribution granularity | 可支撑归因粒度 | `supportable_granularity` |
| public action intent | 公开动作意图 | `intended_cti_node_ids` |
| hidden realized recovery | 隐藏实际恢复集合 | `recoverable_claim_ids` |
| support ceiling | 证据支持上限 | `support_ceiling` |
| justified degrade stop | 正当降级停止 | `justified_degrade_stop` |
| premature stop | 过早停止 | `premature_stop` |
| action-gap compatibility | 动作-缺口兼容性 | M3a |
| nonmyopic planning | 非短视规划 | Depth-2 / DP |

M2、M3a、Logistic、XGBoost、Oracle 和 STOP 在全文中保持上述写法。LLM 不称为“主模型”；DQN 不称为“已验证方法”。

## 4. 章节论证任务

- 引言：从证据不完整导致的决策缺口进入，而不是从 LLM 能力进入。
- 相关工作：区分抽取/对齐、归因推理和主动获取三条谱系。
- 问题定义：锁定状态、动作、粒度、目标和信息边界。
- 方法：分开说明系统是什么、为何这样设计、哪些策略只是实现变体。
- 实验：用 RQ1-RQ3 和可证伪判据组织，不把 mask/seed 当独立样本。
- 结果：先真实紧预算与序贯结果，再 STOP、部分可达负结果和非短视 Gate。
- 讨论：解释任务定义的价值、负结果的知识增量、LLM/图谱位置和外部有效性。
- 结论：只重述已由实验支持的范围，不引入新机制。

## 5. 主张-证据映射

| 主张 | 证据 | 状态 |
|---|---|---|
| 部分对齐可转换为可更新取证状态 | schema、`run_mvp.py`、C07-C10 完整 episode | supported as implementation |
| 信息边界可阻止规划器读取实际恢复结果 | `intended_equals_recoverable_or`、边界测试、通道门控 | supported |
| M2 是当前部署锚点 | C07-C09 紧预算、C07-C10 序贯结果 | supported within four cases |
| M3a 成本优势不成立 | 三案例配对结果、C10 过早停止 | supported negative result |
| XGBoost 优于 Logistic 但未超过 M2 | 990 test rows 与 180 episode/planner | supported descriptively |
| 非短视需求成立 | 192 独立受控环境，Gate A | supported for controlled family only |
| 当前需要 DQN | DP 复杂度未过阈值，Gate B failed | rejected |
| LLM 改善当前规划效果 | 在线主实验未调用 LLM | unsupported; excluded |

## 6. 缺失输入

- 作者、单位、通讯作者、ORCID、作者贡献与资金信息。
- 目标期刊及字数、章节、图数和引文格式。
- claim/意图人工标注一致性及 LLM 编译器独立评测。
- 更多跨 engagement 独立案例，以及真实 trace 上的轻量非短视规划结果。
