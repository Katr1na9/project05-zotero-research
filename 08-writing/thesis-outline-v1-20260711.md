# 硕士论文大纲 v1

日期：2026-07-11
状态：当前主线写作依据；取代 `thesis-outline-v0.md`

## 暂定题目

面向不完整证据 APT 归因的对齐感知证据缺口建模与成本约束主动取证规划

英文题目：Alignment-Aware Evidence-Gap Modeling and Cost-Constrained Active Acquisition for APT Attribution under Incomplete Evidence

## 核心论点

APT 归因系统不应在证据不足时直接输出更细粒度标签，而应把 CTI 行为图与本地证据的部分对齐结果表示为可更新的证据缺口状态，在信息边界和成本约束下选择下一取证动作，并在不可达时显式停止或降级。

## 第 1 章 绪论

- 背景：APT 调查中的证据异构、不完整、通道失效和过度归因风险。
- 问题：已有工作大量覆盖 CTI 抽取、图对齐、actor 分类和 LLM 解释，但较少回答“当前证据还不足时，下一步应取什么、何时停止”。
- 研究问题：证据缺口如何表示；动作如何在隐藏恢复结果不可见时排序；如何在目标不可达时停止；冻结方法能否跨异构真实 trace 复现。
- 贡献边界：主张状态表示、信息边界、规划和停止；不主张新的对齐器、在线 LLM 效用预测或成本优于全部基线。

## 第 2 章 相关工作与撞题边界

- APT 归因与闭集 actor classification。
- CTI 文本结构化、ATT&CK/TTP 映射和攻击知识图谱。
- provenance graph、attack summary graph 与 CTI–日志对齐。
- Active Feature Acquisition、POMDP 与成本敏感调查。
- LLM/RAG/Agent 在 CTI 和安全调查中的作用与可靠性限制。
- 专利与论文红线：不把宽泛“LLM 多轮拉数据”或“多源融合”作为主创新。

## 第 3 章 问题定义与证据缺口状态

- 输入：CTI 行为图、本地 evidence claims、候选动作、通道先验、动作成本和粒度序列。
- 状态：已覆盖节点、关键缺口、边覆盖、当前可支撑粒度、剩余预算和执行后反馈。
- 信息边界：公开 `intended_cti_node_ids` 与隐藏 `recoverable_claim_ids` 分离；规划器不得读取隐藏恢复结果。
- 输出：下一取证动作，或当前证据可支撑的粒度与 STOP/降级结论。
- 目标：在预算内达到目标粒度；不可达时避免越过 `support_ceiling` 并合理停止。

## 第 4 章 对齐感知主动取证规划方法

- 异构证据到 evidence claim 的语义编译接口；LLM 仅作为可选离线编译/解释组件。
- 当前规则部署基线 M2：联合成本、动作重叠、执行反馈、阶段/证据缺口与预期效果。
- 主学习模型路线：已实现 Logistic M3b，下一步以 XGBoost 预测 state-action value；数据量和环境多样性通过 Gate 后，再以 DQN/Dueling DQN 学习非短视序贯策略。
- action–gap 兼容性 M3a：作为机制变体检验关键缺口命中、意图精确率/召回率和成本惩罚是否足以改善规划。
- 通道可靠性门控：声明目标与实际恢复解耦，执行后才暴露零收益反馈。
- 状态更新与粒度门控：证据加入后重算节点/边覆盖和最高可支撑粒度。
- 显式 STOP：达到目标、预算耗尽、无正收益动作或目标不可达时停止/降级。
- 复杂度、实现边界与可审计输出。

## 第 5 章 实验设计

- 开发案例 C01–C06：toy 与 DARPA E3，用于方法诊断和消融，不作为最终独立泛化证据。
- 真留出 C07–C09：E5 THEIA、E5 ClearScope、OpTC SysClient0201。
- 对照：Random、Fixed、Coverage、M1、M2、CMI proxy、Oracle、M3b 及消融。
- 指标：success、cost-to-target、regret vs Oracle、premature/justified stop、ceiling violation、zero-yield 和动作选择。
- 压力测试：通道离线、真正应停、部分可达紧预算和同质 decoy。
- 冻结协议：C07/C08/C09 不调 M3a；自然缺失不合成 claim。
- Oracle 相对预算协议：按条件求 `C*`，在 `C* / C*+1 / C*+2 / 原预算` 上作配对评估。

## 第 6 章 结果与分析

- 开发矩阵：M3a 的成功率优于 M2，但信息边界收紧后成本上升。
- 三条真留出：M3a 与 M2 均为 45/45 达标且无 ceiling violation；M3a 成本均高于 M2。
- 三源平均 `M3a_regret - M2_regret = 0.5481`，支持工程可复现，不支持成本优越。
- 紧预算曲线：M2 为 `66.67% / 66.67% / 100%`，M3a 为 `50.37% / 50.37% / 90.37%`；M3a 对 M2 无配对净胜，M2 确立为当前部署基线。
- XGBoost：相对 Logistic M3b 将 success 从 `0.9778` 提升到 `1.0000`、成本从 `4.8561` 降至 `4.7556`，但仍差于 M2 的 `4.5259`；主标签 AUROC 未优于 Logistic，不能写成全面胜出。
- 统计边界：135 个遮蔽条件来自 3 个独立案例，只作配对描述与机制诊断。
- M4：强方法能在真正不可达时停止，但在部分可达紧预算下仍会错误选路。
- C09 case study：Empire C2、windir UAC bypass、Get-Screenshot、WMI pivot 与良性 GoogleUpdate。
- 错误分析：过宽意图、廉价不可靠通道、动作空间表达和自然缺失。

## 第 7 章 LLM 边界、系统实现与讨论

- 已实现主循环是确定性证据状态和规则规划，不依赖在线 LLM。
- LLM 可用于异构证据语义规范化、动作意图草拟、缺口解释和报告表达。
- 当前实验未调用 LLM；Qwen/SEvenLLM 仅为暂停的语义编译支线，不是核心决策模型。
- LLM 实验只评估 evidence-claim 编译及其对冻结 M2 的下游影响，不让 LLM 直接裁决 actor 或规划动作。
- 讨论专利保护对象、可部署接口、数据质量与外部有效性。

## 第 8 章 总结与展望

- 总结证据缺口表示、信息边界、成本规划、STOP 和三源验证。
- 明确负结果：M3a 没有建立成本优势。
- 后续工作：独立标注评估 LLM 语义编译、改进部分可达选路、扩展更多 engagement，而不是回调冻结 holdout。
