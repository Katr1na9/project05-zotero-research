# Project05 论文 v0.8 写作记录

日期：2026-07-13

流程：nature-writing → Reviewer major revision → C11/C12 分层外部压力 → 外部 AFA 源码审计 → 双人盲标首轮导入与一致性分析 → v0.8 人工复现边界整合

## 1. 一句话论点

在证据只能部分对齐、动作收益事前不可见、通道可能失效且预算有限时，本文把 APT 归因的前置环节定义为可审计的调查控制问题；C07-C12 说明策略效用不能脱离任务粒度、证据组合、来源结构和动作空间外推，双人盲标首轮又表明当前 Claim/Intent codebook 尚不可复现，因此方法贡献必须同时包含信息边界和被人工负结果约束的适用范围。

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
| C12 operational-data stress | C12 生产 SOC 衍生 G1 压力 | 自然 APT actor benchmark |
| multi-provider corroboration | 同一主机归档内多 provider 证据 | 独立传感器证据 |
| multi-stream evidence | ASA 与 Windows AD 原始事件流 | 厂商产品标签多源 |
| internal freeze record | 内部冻结记录 | 外部可验证预注册 |
| frozen policy transfer | 冻结策略迁移 | 在 C11/C12 上重新训练或调参 |
| official source-code audit | 官方/作者代码与任务端点审计 | 官方同任务数值复现 |
| vendor projection context | 厂商 `INCIDENT_LINK` 相关投影 | 原始遥测因果边 |
| round-1 human agreement | A/B 首轮一致性 | 最终人工代理校准 |
| provenance anomaly | 粒度源文件哈希相同，待独立性确认 | 完美双盲一致性 |

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
| 闭环在分层压力案例可执行 | C07-C10、180 M2 episode；C11、45；C12、45；均 0 ceiling violation | 支持；C11 仅 G2，C12 仅 G1 |
| 节点级恢复映射会泄漏 | intended≠OR 校验、性质 1、回归测试 | 支持节点级，不等于完整 Oracle |
| 代理粒度随 claims 单调 | 性质 2、OR/AND 实现 | 支持固定阈值/上限条件下 |
| M2 是 C07-C10 当前非 Oracle 部署锚点 | C07-C10、紧预算、AFA、Depth-2 | 支持原四例；C11 中不是最低成本 |
| AFA 适配未超过 M2 | 720 episode、24/91/65 配对 | 支持本文适配，不外推方法族 |
| M2 局部稳定 | 16 个 OAT 权重扰动 | 支持 ±25% 局部范围 |
| 内部粒度代理需要人工校准 | C01-C06 OR/AND 开发压力、C11 AND/OR 成本差、空标注包 | 支持为风险，不构成人工效度 |
| Claim codebook 首轮未获可靠复现 | 27 项 raw agreement 0.7407、weighted kappa -0.1455 | 支持；7 项待裁决，仍需 round 2 |
| 公开意图 codebook 首轮未获可靠复现 | 27 项 exact 0.0741、Jaccard 0.3673、micro F1 0.4878 | 支持；25 项待裁决，仍需 round 2 |
| 粒度首轮完美一致 | 数值为 1.0000，但 A/B 源文件 SHA-256 完全相同 | 暂缓解释，不能作为独立双盲证据 |
| 第三数据封装可接入 | C11 OTRF JSONL、8 条 source-pointer 回查、冻结重跑 | 支持一个 APT29 emulation 链，不等于广泛泛化 |
| 策略排序依赖案例结构 | C11 冻结迁移：XGBoost/Logistic 比 M2 少 0.6000 成本；Depth-2 有 1 次退化 | 支持一个 AND 多 Claim/G2 案例，不构成跨域优势 |
| 生产 SOC 双流证据可接入 | C12：13,119→5→2 两级 Gate；119 leads；5 claims；4 actions | 支持一个厂商相关 incident 的 G1 接入，不是自然 APT benchmark |
| C12 策略排序再次改变 | Depth-2/Oracle 0.8889，M2 1.4222，AFA Myopic 1.5111；均 45/45 | 支持单 incident 配对结果，不构成非短视普遍优势 |
| 厂商投影不被误作原始证据 | 49/49 GraphML 边均为 `INCIDENT_LINK`；gold observations 来自 embedded leads | 支持当前 C12 编译合同 |
| 外部官方代码任务不等价 | AFABench、WinRegRL、AACO commit 审计；C07-C12 动作族 5/5 可映射 | 支持“不可直接同表”，尚无 external endpoint 数值 |
| 离线分类指标不等于序贯效用 | C11 中 Logistic AP 0.6322、XGBoost AP 0.3952，但序贯成本均为 3.0667 | 支持当前主标签与动作空间 |
| 真实归因准确率提高 | 无 actor/campaign 终点 | 不支持 |
| LLM 改善规划 | 主实验未调用 LLM | 不支持 |

## 6. 尚未闭合的审稿门槛

1. 完成 7 个 Claim、25 个 Intent 的第三人裁决，并确认或重做粒度独立标注；最终代理校准仍未完成。
2. 根据首轮失败模式冻结 codebook round 2；裁决不会改变首轮 IAA 未过门槛的事实。
3. 更多独立运营 engagement；C12 只关闭一个生产 SOC 衍生 incident 的最小接入缺口。
4. 真实归因正确性或分析师效用小样本。
5. 若目标 venue 要求严格外部数值基线，冻结 external endpoint adapter；官方源码与任务映射已经完成，但 direct same-task Gate 不通过。
6. 作者、单位、ORCID、贡献、资金、利益冲突、数据许可和目标模板。
