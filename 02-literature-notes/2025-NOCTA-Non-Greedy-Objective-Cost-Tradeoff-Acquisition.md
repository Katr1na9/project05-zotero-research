# NOCTA: Non-Greedy Objective Cost-Tradeoff Acquisition for Longitudinal Data

## 1. 基本信息

- 英文题名：NOCTA: Non-Greedy Objective Cost-Tradeoff Acquisition for Longitudinal Data
- 中文译名：NOCTA：面向纵向数据的非贪心目标-成本权衡采集方法
- 作者：Dzung Dinh, Boqi Chen, Yunni Qu, Marc Niethammer, Junier Oliva
- 年份：2025/2026 revision
- Venue：arXiv preprint
- DOI / arXiv / URL：https://arxiv.org/abs/2507.12412
- Zotero key：待补
- 阅读日期：2026-07-07
- 阅读优先级：重点读
- 所属主题：Active Feature Acquisition / Cost-aware planning / Longitudinal decision
- 阅读状态：arXiv 正文级精读；作为 Project05 主动取证规划理论支撑

## 2. 一句话总结

NOCTA 研究的是推理时特征并非免费可得的场景：系统要在部分观测、时间约束和采集成本下选择未来要采集的特征。它提出非贪心 NOCT 目标和两个估计器，为 Project05 的“下一步取什么证据”提供直接理论参照。

## 3. 研究问题

- 许多关键领域中，特征获取有时间、金钱、风险成本。
- 纵向数据中，早期测量一旦错过可能永远不可补。
- 贪心 acquisition 容易只看当前边际收益，忽略特征组合、未来影响和采集时机。

## 4. 核心贡献

1. 聚焦 Longitudinal Active Feature Acquisition：在推理时决定采集哪些 feature、何时采集、何时停止。
2. 提出 NOCT objective，用预期预测损失和 acquisition cost 共同评价未来采集计划。
3. 提出 NOCT-Contrastive：用对比学习表示部分观测与未来采集效用。
4. 提出 NOCT-Amortized：用神经网络直接预测 candidate plan 的 NOCT 值，提升推理效率。

## 5. 方法框架

### 输入

- 当前部分观测特征。
- 可采集的 feature-time candidates。
- acquisition cost。
- 预测任务目标。

### 输出

- 下一步或未来一组采集计划。
- 终止或继续采集的决策。
- 最终预测。

### 关键模块

| 模块 | 作用 | 对 Project05 的意义 |
|---|---|---|
| NOCT objective | 统一评价预测收益与采集成本 | 可改写为“归因粒度收益 - 取证成本” |
| NOCT-Contrastive | 学习部分观测下未来采集效用表示 | 可借鉴为 evidence-state embedding |
| NOCT-Amortized | 快速预测候选计划价值 | 可作为 Project05 planner MVP 的实现形态 |
| Adaptive stopping | 当额外采集不值成本时停止 | 对应归因粒度门控 / 拒答 / 降级输出 |

### 方法流程

```text
partial observations
  -> enumerate/sample candidate acquisition plans
  -> estimate NOCT value
  -> choose plan/action with best objective-cost tradeoff
  -> acquire feature or stop
  -> prediction
```

## 6. 数据集与实验

- 数据：synthetic benchmark，ADNI，WOMAC，KLG 等医疗纵向数据。
- Baseline：AFA / active sensing / RL / greedy acquisition 相关方法，如 ASAC、RAS、DIME、DiFA 等。
- 指标：accuracy、AP、ROC、average acquisition cost。
- 结论：NOCTA 在多个任务中以更低采集成本达到更好或可比预测性能；非贪心策略更能处理早期测量价值和未来组合收益。

## 7. 关键知识点

### 概念

- Active Feature Acquisition：推理阶段特征有成本，需要主动选择。
- Longitudinal AFA：采集决策带时间维度，错过早期时间点可能不可逆。
- Non-greedy planning：不是只选当前最有信息量的特征，而是评估未来计划。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| active feature acquisition | 主动特征获取 | Project05 对应主动取证 |
| acquisition cost | 获取成本 / 取证成本 | 可含时间、权限、风险 |
| candidate acquisition plan | 候选采集计划 | 对应 evidence action sequence |

## 8. 优点

- 给 Project05 的主动取证规划提供现成形式化思路。
- 强调非贪心计划，适合 APT 调查中“先取哪类证据会影响后续判断”的问题。
- 有 adaptive stopping，可映射到“证据不够时不强行归因”。

## 9. 局限

- 领域是医疗/纵向预测，不是网络安全。
- 特征空间通常比 APT 取证动作规整；Project05 的 action 包含日志查询、样本分析、CTI 检索、网络侧证据等异构动作。
- 预测目标是固定标签，不是归因粒度提升和证据链完整性。

## 10. 对我选题的启发

- Project05 可以把“补证”明确写成 AFA 在安全归因场景中的实例化。
- 创新点不是凭空发明 planner，而是把 AFA 迁移到“对齐状态证据 + 归因粒度收益 + 异构取证成本”。
- NOCTA 支持我们反驳“只是生成缺失证据 list”：真正目标应是 cost-aware next evidence action planning，而不是列清单。

## 11. 可转化的研究问题

1. 如何定义 APT 归因任务中的 acquisition cost？
2. 如何把“从 G1 到 G2/G3 粒度的提升”写成 acquisition reward？
3. 在证据会随时间丢失或日志保留窗口有限时，如何引入 longitudinal constraint？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AFA Survey | NOCTA 是 AFA 最新非贪心代表之一 |
| D3QN Malware | 安全侧顺序特征选择先例，但更偏扁平特征分类 |
| Project05 | NOCTA 是主动取证规划的理论借鉴，不是撞题 |

## 13. 论文写作可引用句式

- Active evidence acquisition can be viewed as a cost-sensitive inference-time acquisition problem, where the value of an action depends on how much it improves the supportable attribution granularity under partial observations.

## 14. 我的批注与疑问

- 这篇非常重要，因为它把“下一步取什么证据”从业务直觉变成优化问题。
- Project05 不能直接照搬医疗纵向设定，而要把 action space 和 reward 改成安全可解释版本。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
