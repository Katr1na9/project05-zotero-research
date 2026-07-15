# Minos: A Multi-Agent Collaborative Framework for Provenance-Based Backward Tracking

## 1. 基本信息

- 系统名：Minos
- 中文译名：面向溯源图反向追踪的多智能体协作框架
- 作者：Jiahui Wang; Zhenyuan Li; Zhengkai Wang; Xiangmin Shen; Fan Zhang
- 年份：2026
- 来源：arXiv preprint
- arXiv：https://arxiv.org/abs/2607.00440
- 阅读状态：`full-read`（20 页全文）
- 阅读日期：2026-07-13
- 阅读顺位：Agent-last appendix
- 所属主题：Provenance / Backward Tracking / Multi-Agent / RAG / Intent Assessment

## 2. 一句话总结

Minos 在既有 provenance graph 上用 Planner、Query、对抗评估组和 Memory 四类 Agent 进行假设驱动的反向追踪，并以分层上下文、CTI/ATT&CK RAG、引用核验和 count-first 查询控制语义歧义与依赖爆炸；它已经覆盖“多 Agent + provenance 调查”，但不负责从原始 PCAP 与日志构建双源证据图，也没有跨源边校准和攻击者高层目标/动机真值。

## 3. 研究问题

- 传统低层统计与刚性遍历为何难以处理 living-off-the-land 事件的语义歧义？
- 如何让 LLM 在百万级 provenance graph 上避免上下文溢出和 dependency explosion？
- 多 Agent 分工是否优于把全部调查能力放进一个 ReAct Agent？

## 4. 核心贡献

1. 将 provenance backward tracking 重构为 LLM 驱动的按需推理过程。
2. 以细粒度叙事和粗粒度 ATT&CK tactic 序列维护分层上下文。
3. 用 CTI、ATT&CK、log schema 的混合 RAG 和确定性引用核验增强 grounding。
4. 以 prosecutor、defense attorney、judge 对抗辩论缓解 sycophancy false positives。
5. 用 Planner、Query、Adversarial Group、Memory 四角色和 FSM 编排端到端调查。
6. 在 5 个数据集 14 个场景上做边级重构、模型选择和组件消融。

## 5. 方法框架

- 输入：provenance graph `G` 与告警产生的 point-of-interest event。
- 分层记忆：细粒度 context 保存近期命令/路径/IoC 和因果叙事；粗粒度 context 保存 ATT&CK tactic sequence。
- RAG：CTI、ATT&CK、log schema 建混合索引，dense 与 BM25 等权，top-3。
- 引用协议：输出标注 `[CTI]`、`[MITRE]`、`[KNOWN]`；算法核验来源列表与 TTP ID，未匹配标为 `[SUSPECT]`。
- 事件判定：prosecutor 假设恶意、defense 假设良性、judge 按因果、引用与 tactic consistency 裁决。
- Planner：先 POI 局部扩展，再优先低度 frontier，最后以 ATT&CK 生命周期约束假设。
- Query：自然语言计划转 Cypher；先 count，候选超过阈值 50 时要求 Planner 收窄；执行错误自动修复。
- 终止：到达初始访问等逻辑根、连续 20 轮子图不增长，或达到 75 轮上限。
- 审计：每轮序列化假设、检索片段、辩论与状态。

## 6. 数据集与实验

- 数据集：DARPA TC 的 Cadets、Trace、Theia；Aurora；OpTC，共 5 个数据集、14 个场景。
- 图规模：约 23K-2.96M nodes、74K-18.5M edges；ground-truth attack edges 8-50。
- POI：每个场景 ground truth 中时间最后的恶意事件。
- Baseline：NoDoze、DepImpact、同工具同知识库的 GPT-5.2 Single-Agent ReAct。
- Minos 平均 edge recall 0.92、precision 0.64、输出 35 edges，GT 平均 24 edges。
- NoDoze：0.72/0.14/129；DepImpact：0.66/0.24/68；Single-Agent：0.40/0.15/120。
- 平均反向追踪时间 1,290 秒，约 164K tokens；传统非 LLM 方法在秒级。
- Cadets Case 2 recall 0.75，原因是一个 technique 对应多个 tactic，导致过早终止。

## 7. 关键知识点

- 本文的 `intent assessment` 是判断单个系统事件是否具有恶意目的及其 ATT&CK 角色，不等于行为体动机、最终攻击目标或 actor attribution。
- 粗粒度 tactic sequence 是强搜索先验：能显著提升 precision，也可能在映射歧义时提前截断真链。
- Agent 分工的收益部分来自上下文隔离与工具专业化，而非“多 Agent”标签本身。
- 引用核验只确认引用 ID 存在，不验证自然语言 claim 是否被来源语义蕴含。

## 8. 优点

- 以边级 recall/precision 和子图规模评价，而非只用 LLM 文本相似度。
- Single-Agent 控制组使用相同工具和知识库，较好隔离编排结构贡献。
- 消融覆盖分层 context、对抗推理、count-first、CTI、ATT&CK 与 log schema。
- 明确报告失败案例与两个数量级的延迟代价。
- 推理轨迹、检索来源和辩论过程均持久化，利于审计。

## 9. 局限

- 输入是假定已正确构建的单一 provenance graph；不研究异构 PCAP/log 抽取和跨源建图误差。
- 依赖高成本闭源 GPT-5.2/GPT-5.2-Codex 与云 embedding，不满足敏感日志本地部署。
- POI 由 ground truth 最后恶意事件模拟，现实告警质量与多 POI 场景未验证。
- precision 0.64 仍意味着约三分之一输出边为误报。
- tactic lifecycle 被用作停止与搜索约束，面对非标准顺序、多 tactic technique 和并发 campaign 会有偏差。
- 只做 edge reconstruction；没有跨源边准确率、原始证据回放、意图标签精度、概率校准或 ECE/Brier。
- 论文在 2026-07-01 发布，尚为预印本，同行评审状态待核验。

## 10. 对我选题的启示

- Agent 只能作为既有证据图上的调查策略层，不能替代双源图构建贡献。
- Project03 支线若后续加入 Agent，应把 Minos 作为直接 baseline，并保持 Agent 可拔插。
- 更基础的研究价值仍在 raw-evidence graph、cross-source candidate edges、冲突/缺失和校准。
- 可借鉴其 edge-level evaluation、POI tracking 和 audit-state persistence，但要增加 source-aware 指标。

## 11. 可转化的研究问题

1. 在跨源边含概率和冲突状态的证据图上，Minos 类 Planner 是否能比确定图上更好地控制误报？
2. 当 packet/log 原始证据不足时，Agent 能否根据校准置信度主动拒绝扩展某条链？
3. 图构建错误、POI 错误和 tactic mapping ambiguity 分别如何影响 agentic backward tracking？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| HunterAgent | 都用生成/验证式调查应对缺失或污染证据；Minos强调 provenance graph 查询与多角色分工 |
| PROVSEEK | 都在 provenance 上做 RAG/Agent 调查；Minos给出边级重构与更强编排实验 |
| SHIELD | 后者从 provenance 检测子图生成 LLM 链摘要；Minos主动查询并扩展子图 |
| MuSAR | MuSAR负责网络告警+日志事件关联和链构造；Minos从已建图/POI开始追踪 |
| Project03 | 双源 evidence graph 可作为 Minos 类 Agent 的上游，而非与其竞争同一贡献 |

## 13. 论文写作可引用句式

- 最新研究已将多智能体用于既有溯源图上的假设驱动反向追踪，并通过分层上下文、对抗式事件判定和按需数据库查询提高边级重构精度；然而，该类方法通常假设输入图已经正确构建，尚未处理原始流量与日志之间的跨源证据关系及其不确定性。

## 14. 我的批注与疑问

- `[CTI]`/`[MITRE]` 校验是 reference-validity，而非 claim-entailment；不应写成完整事实核验。
- “49% more compact”应与具体 baseline 和 ground truth 偏差共同解释，不能把小图直接等同于高质量。
- `fine-grained context` 删除后 precision 升高到 0.68，但 recall 降到 0.72，说明局部严格判定会丢失跨阶段弱边。
- 实验公开代码/数据复现入口在当前全文中不清楚，需后续核验。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：Agent 附录必读；不改变上游双源图构建主线
