# Project05 论文 v0.5 写作记录

日期：2026-07-13

流程：nature-writing → Reviewer major revision → C11 第三封装内部冻结评估 → 原始回指复核 → v0.5 边界整合

## 1. 一句话论点

在证据只能部分对齐、动作收益事前不可见、通道可能失效且预算有限时，本文把 APT 归因的前置环节定义为可审计的调查控制问题；C07-C10 支持闭环可执行性和 M2 的局部部署价值，C11 则证明第三封装可接入并否定 M2 跨场景最低成本与 OR/AND 可互换的更强外推。

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
| C11 external-validity stress | C11 第三封装外部效度压力 | 第五个同质真实攻击 |
| multi-provider corroboration | 同一主机归档内多 provider 证据 | 独立传感器证据 |
| internal freeze record | 内部冻结记录 | 外部可验证预注册 |

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
| 闭环在参数锁定案例可执行 | C07-C10、180 M2 episode；C11、45 M2 episode；均 0 ceiling violation | 支持，C11 目标仅 G2 |
| 节点级恢复映射会泄漏 | intended≠OR 校验、性质 1、回归测试 | 支持节点级，不等于完整 Oracle |
| 代理粒度随 claims 单调 | 性质 2、OR/AND 实现 | 支持固定阈值/上限条件下 |
| M2 是 C07-C10 当前非 Oracle 部署锚点 | C07-C10、紧预算、AFA、Depth-2 | 支持原四例；C11 中不是最低成本 |
| AFA 适配未超过 M2 | 720 episode、24/91/65 配对 | 支持本文适配，不外推方法族 |
| M2 局部稳定 | 16 个 OAT 权重扰动 | 支持 ±25% 局部范围 |
| 内部粒度代理需要人工校准 | C01-C06 OR/AND 开发压力、C11 AND/OR 成本差、空标注包 | 支持为风险，不构成人工效度 |
| 第三数据封装可接入 | C11 OTRF JSONL、8 条 source-pointer 回查、冻结重跑 | 支持一个 APT29 emulation 链，不等于广泛泛化 |
| 真实归因准确率提高 | 无 actor/campaign 终点 | 不支持 |
| LLM 改善规划 | 主实验未调用 LLM | 不支持 |

## 6. 尚未闭合的审稿门槛

1. 双人盲标和 IAA/校准；这是当前最优先未完成项。
2. 自然发生或更接近运营现场的独立 engagement；C11 只关闭第三封装工程缺口。
3. 真实归因正确性或分析师效用小样本。
4. 若目标 venue 要求严格外部基线，补官方 AFA/公开代码映射；当前只有诚实标注的领域适配。
5. 作者、单位、ORCID、贡献、资金、利益冲突、数据许可和目标模板。
