# Project05 论文 v0.4 写作记录

日期：2026-07-11

流程：nature-writing → peer review triage → preregistered AFA/sensitivity experiments → nature-figure → rigor audit

## 1. 一句话论点

在证据只能部分对齐、动作收益事前不可见、通道可能失效且预算有限时，本文把 APT 归因的前置环节定义为可审计的调查控制问题；四个参数锁定案例支持闭环可执行性，同时否定了复杂策略已优于透明 M2 的更强主张。

## 2. 稿件类型与读者

- 类型：security investigation framework / empirical systems-method paper，而不是 actor-classification model paper。
- 主读者：安全调查、APT/provenance、主动特征获取、可信自动化研究者。
- 标题边界：必须包含 investigation control 或等价限定；不得只写 APT attribution method。
- 语言：中文主稿，待目标 venue 确定后整体英译。

## 3. 术语账本

| 概念 | 正文规范用语 | 禁止替换成 |
|---|---|---|
| evidence-gap state | 证据缺口状态 | 缺失证据列表 |
| supportable conclusion granularity | 可支撑调查结论粒度 | 归因准确率 |
| public action intent | 公开动作意图 | 真实可恢复内容 |
| hidden realized recovery | 隐藏实际恢复集合 | 规划器可见收益 |
| interpretable deployment policy | 透明部署策略 M2 | 全局最优模型 |
| AFA-VOI adapter | AFA-VOI 同接口领域适配 | NOCTA/WinRegRL 复现 |
| justified degrade stop | 正当降级停止 | 失败 |
| premature stop | 过早停止 | 正常降级 |

LLM 不称“主模型”；DP 不称“部署策略”；DQN 不称“待实现主线”；M3a 不称“核心创新算法”。

## 4. 章节论证任务

- 引言：从调查决策缺口进入，明确不直接回答 who attacked。
- 相关工作：承认 AFA/MDP 已覆盖宽泛采集问题，差异落在安全信息边界和输出粒度。
- 问题定义：状态、动作、隐藏实现、预算、STOP、粒度和统计单位必须可复核。
- 方法：框架先于策略；M2、M3a、学习、AFA 和前瞻均为可替换策略。
- 实验：RQ1-RQ4，所有方法优越性均有否证条件。
- 结果：先报告 M2 的当前折中，再报告复杂策略和代理敏感性的负结果。
- 讨论：解释部署锚点，不把局部经验写成“简单模型普遍更好”。
- 结论：贡献是接口、边界和实证范围，不是 actor attribution SOTA。

## 5. 主张—证据映射

| 主张 | 证据 | 状态 |
|---|---|---|
| 闭环在参数锁定案例可执行 | C07-C10、180 M2 episode、0 ceiling violation | 支持，限四案例 |
| 节点级恢复映射会泄漏 | intended≠OR 校验、性质 1、回归测试 | 支持节点级，不等于完整 Oracle |
| 代理粒度随 claims 单调 | 性质 2、OR/AND 实现 | 支持固定阈值/上限条件下 |
| M2 是当前非 Oracle 部署锚点 | C07-C10、紧预算、AFA、Depth-2 | 支持当前案例与所评估策略内 |
| AFA 适配未超过 M2 | 720 episode、24/91/65 配对 | 支持本文适配，不外推方法族 |
| M2 局部稳定 | 16 个 OAT 权重扰动 | 支持 ±25% 局部范围 |
| 内部粒度代理需要人工校准 | OR/AND 开发压力、空标注包 | 支持为风险，不构成人工效度 |
| 真实归因准确率提高 | 无 actor/campaign 终点 | 不支持 |
| LLM 改善规划 | 主实验未调用 LLM | 不支持 |

## 6. 尚未闭合的审稿门槛

1. 双人盲标和 IAA/校准；这是当前最优先未完成项。
2. 第三数据家族或更多独立 engagement。
3. 真实归因正确性或分析师效用小样本。
4. 若目标 venue 要求严格外部基线，补官方 AFA/公开代码映射；当前只有诚实标注的领域适配。
5. 作者、单位、ORCID、贡献、资金、利益冲突、数据许可和目标模板。
