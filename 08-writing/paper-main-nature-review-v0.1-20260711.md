# Project05 模拟审稿报告 v0.1

## Review setup

- Input scope：论文 v0.3 全文、两幅主图、Zotero 引文导出和仓库实验摘要。
- Assessment boundary：评价当前稿件的原创性、重要性、技术可靠性与可读性；不代表编辑决定。
- Shared manuscript claim：把 CTI-本地证据部分对齐转化为受预算、通道反馈和支持粒度约束的主动取证闭环。
- Visible evidence：C01-C06 开发案例、C07-C10 参数锁定案例、紧预算/STOP/部分可达压力、XGBoost 与非短视 Gate。
- Missing materials：作者信息、目标期刊、独立人工粒度标注、更多真实攻击链和轻量非短视真实 trace 结果。

## Reviewer 1

- Overall assessment：问题设定清楚，信息边界和负结果记录具有方法学价值，但当前真实独立样本规模不足以支撑强泛化主张。
- Who would be interested：威胁归因、provenance/CTI 对齐和安全调查自动化研究者，因为稿件研究的是对齐之后的调查控制，而不是再次输出 actor 标签。
- Major strengths：公开意图与隐藏恢复集合隔离；重复条件与独立案例数明确区分；M3a/XGBoost/DQN 的负结果没有被掩盖。
- Major concerns：G0-G3 粒度是内部代理；四个案例来自两个主要家族；缺少真实分析师标注。
- Technical failings：需要粒度阈值敏感性和人工校准；需要至少一个新数据家族；需说明动作空间如何由真实 SOC 能力生成。
- Recommendation posture：major revision 后可形成可信的方法/系统论文。

## Reviewer 2

- Overall assessment：统一状态-动作接口具有复现价值，但当前最强结果来自 M2，而非论文命名的新规划器，贡献必须继续定位为任务、状态和评价协议。
- Who would be interested：主动特征获取、成本敏感决策和可信机器学习研究者，因为论文提供了通道失效、STOP 和支持粒度等通用 AFA 中较少出现的约束。
- Major strengths：RQ2 可证伪且被诚实否定；紧预算评价比宽松预算更有区分力；Gate A/B 避免了无依据启动 DQN。
- Major concerns：现有学习器训练环境少；CMI proxy 与 M1 的实现细节需在最终稿/附录充分展开；DP 依赖完整转移概率。
- Technical failings：应把轻量 Depth-2 或 beam search 接入真实案例；增加至少一个通用 AFA 非贪心基线；报告计算成本与状态展开数在真实案例中的变化。
- Recommendation posture：作为负结果边界清晰的算法系统稿有潜力，但尚不是“新模型性能论文”。

## Reviewer 3

- Overall assessment：稿件叙事已明显优于以 LLM 为中心的宽泛归因框架，但 LLM、多模态和 agent 的位置仍应保持在讨论或未来工作，除非增加独立编译实验。
- Who would be interested：安全 LLM、可解释归因和多模态 CTI 研究者，因为该框架提供了可插拔但受来源约束的语义层。
- Major strengths：不让语言模型直接承担在线动作效用；引用覆盖了 TAA-EPLMR、AURA、APT-ATT、LLMAPT、MM-AttacKG 和 ExCyTIn；图1清楚表达信息边界。
- Major concerns：当前 claims 和动作仍由人工/脚本编译；未测量来源指针和 unsupported claim；LLM 相关意义目前是架构兼容性而非实验贡献。
- Technical failings：需要双盲 claim 编译小样例、规则/通用 LLM/安全 LLM 对照，以及冻结 M2 的下游传播实验。
- Recommendation posture：维持当前标题不含 LLM 是正确的；完成编译评测后再决定是否扩展标题与摘要。

## Cross-review synthesis

- Consensus strengths：任务边界明确；信息泄漏控制可审计；负结果和统计单位诚实；代码与结果可复现。
- Consensus technical risks：独立真实案例不足；粒度代理缺少人工校准；非短视规划尚未进入真实 trace；claim/意图标注可靠性未测量。
- Where emphasis differs：Reviewer 1 更重外部效度，Reviewer 2 更重规划基线与真实非短视实验，Reviewer 3 更重 LLM 编译与来源可靠性。
- Broad-interest readout：对安全调查决策和可信自动化有明确意义，但现阶段更适合安全/AI 方法或系统期刊，而非依赖广泛跨学科影响的综合刊物。
- Most important next actions：先完成轻量非短视真实案例接入和 claim/粒度人工标注评测，再扩展新数据家族；这三项比继续训练 DQN 或把 LLM 放入主循环更能提高可发表性。

## Risk / unsupported claims

- “跨数据集统计泛化”“达到真实 actor 归因正确性”“LLM 改善规划”“DQN 必要”均不受当前证据支持。
- “M2 是最优方法”只能写成当前案例和基线集合内的部署锚点。
- “非短视规划有效”必须限定为受控先决依赖环境，真实 trace 仍待验证。
