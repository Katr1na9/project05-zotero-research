# M3 缺口条件证据效用模型研究

日期：2026-07-09  
状态：M2 独立留出负结果后的方法重构

## 1. 研究结论

下一版不应继续修改 M2 固定权重，也不应直接跳到端到端 RL。

推荐主方法：

> **Gap-Conditioned Evidence Utility Network（GCEU-Net，缺口条件证据效用网络）**

它学习的不是动作平均价值，而是：

```text
P(动作 a 解决未匹配关键节点 v | 当前证据缺口图 H_t)
P(执行动作 a 后归因粒度达到 g* | H_t)
```

规划器再根据预测分布、动作成本和剩余预算选择动作。

## 2. M2 为什么失败

C06 有 45 个条件，其中 18 个初始已达到 G3；27 个挑战条件中：

| 方法 | 成功数 | 成功率 |
|---|---:|---:|
| M2 | 5/27 | 0.1852 |
| M1 | 5/27 | 0.1852 |
| coverage greedy | 14/27 | 0.5185 |
| Oracle | 27/27 | 1.0000 |

最关键的失败模式：

- 10 个 stage-mask 挑战条件和 10 个 discriminative-mask 挑战条件都缺 `N01_initial_access`；
- Oracle 20/20 首选 `C06-AA-001`；
- M2 20/20 首选 `C06-AA-002`；
- `AA-001` 与 `AA-002` 的 `expected_stages` 都是 execution，M2 无法区分它们指向哪个 CTI 缺口；
- `AA-002` 的手写 `expected_granularity_gain=2` 高于 `AA-001=1`，固定先验压过了当前案件状态；
- 随后 M2 又选择高成本 `AA-007`，预算耗尽时 `N01_initial_access` 仍未解决。

因此，问题不是“反馈权重太小”，而是**状态与动作之间缺少节点级对应关系**。

## 3. 文献与撞题边界

### 3.1 Active Feature Acquisition

- [A Survey on Active Feature Acquisition Strategies](https://arxiv.org/abs/2502.11067) 已说明 CMI 贪心通常很强，但短视策略无法处理联合信息价值；AFA 的常见状态仍是固定维度特征子集。
- [Acquisition Conditioned Oracle](https://proceedings.mlr.press/v235/valancius24a.html) 用 acquisition-conditioned oracle 处理非短视获取，说明端到端 RL 不是唯一选择。
- [Stochastic Encodings for Active Feature Acquisition](https://proceedings.mlr.press/v267/norcliffe25a.html) 在 stochastic latent space 中推演未观测实现，避免单步 CMI 的短视性。
- [Towards Cost Sensitive Decision Making](https://proceedings.mlr.press/v258/li25h.html) 提出 Active-Acquisition POMDP，用生成模型形成 belief，再用 hierarchical RL 平衡信息与成本。
- [Active feature acquisition via explainability-driven ranking](https://proceedings.mlr.press/v267/guney25a.html) 用 instance-specific explanation ranking 监督 Decision Transformer policy。

这些方法证明“条件收益学习”本身不是新意。Project05 的差异只能来自：

- graph-structured attribution gaps；
- grouped heterogeneous evidence actions；
- attribution-granularity target；
- systematic/natural missingness；
- calibrated abstention and stopping。

### 3.2 安全调查与取证

- [WinRegRL](https://doi.org/10.1038/s41598-026-57787-6) 已覆盖 Windows forensic MDP、39 个 atomic actions、专家 transition、value iteration 和有限 Q-learning；附录覆盖 POMDP belief update。
- [ExCyTIn-Bench](https://arxiv.org/abs/2507.14201) 把 SQL 查询作为动作、执行结果作为 observation，并提供 investigation-graph intermediate reward。
- [Cyber Defense Benchmark](https://arxiv.org/abs/2604.19533) 已把开放式日志查询封装为 Gymnasium 环境，并显示 frontier LLM agent 在无提示 threat hunting 中仍严重失败。

所以 Project05 不能把“LLM agent 查询日志”或“RL 做安全调查”当作主创新。

## 4. 研究问题

### Primary RQ

> 在不访问隐藏证据真值的情况下，节点级缺口条件收益模型能否比固定启发式、coverage greedy 和通用 AFA baseline 更准确地选择取证动作，并以更低预算达到目标 APT 归因粒度？

### Sub-RQ

1. 节点级 action-gap compatibility 是否比 stage/type coverage 更能预测动作实际收益？
2. 直接预测 node resolution 与直接预测 granularity transition，哪一种更可校准、可迁移？
3. 两步 model-predictive planning 是否仅在存在互补证据动作时优于一步 greedy？

### FINER 快评

| 维度 | 评分 | 判断 |
|---|---:|---|
| Feasible | 4/5 | 模拟器能为全部 state-action pair 生成反事实标签，但真实独立案例仍少 |
| Interesting | 5/5 | 直接解释 M2 负结果，并对应真实调查中的 next-best evidence |
| Novel | 3.5/5 | 宽口被 AFA 与 WinRegRL 覆盖，需靠 attribution-gap graph 和目标粒度守住边界 |
| Ethical | 4/5 | 防御用途明确；公开结果应避免暴露可操作攻击细节 |
| Relevant | 5/5 | 可直接形成专利方法步骤和论文可证伪实验 |

## 5. GCEU-Net 技术设计

### 5.1 输入：Evidence-Gap Graph

每个 CTI 节点包含：

- stage / tactic / technique；
- criticality；
- 当前 required-claim support ratio；
- 已观察 evidence types；
- missing requirement types；
- 与前后攻击步骤的拓扑关系；
- 当前 alignment confidence / conflict；
- 距目标 attribution granularity 的依赖关系。

每条 action 包含：

- action type；
- target type 和 target embedding；
- expected evidence types；
- intended CTI node candidates；
- cost、latency、availability；
- 历史同类动作的 yield feedback。

其中 `intended_cti_node_candidates` 是查询语义对应的公开候选节点，不是隐藏的 `recoverable_claim_ids`。

### 5.2 编码器

最小版本：

```text
node encoder: MLP
graph aggregation: 2-layer GraphSAGE 或 GAT
action encoder: categorical embedding + numeric features
action-gap interaction: bilinear score 或 cross-attention
```

不建议第一版使用大语言模型直接预测效用。自然语言 target 可由冻结的安全领域 encoder 转成 embedding，但核心 transition head 应由可监督、可校准的小模型承担。

### 5.3 三个预测头

1. **Node Resolution Head**

```text
p_av = P(action a resolves gap node v | H_t)
```

2. **Granularity Transition Head**

```text
q_ak = P(G_{t+1}=k | H_t, a)
```

3. **Yield / No-yield Head**

```text
r_a = P(recovered_count > 0 | H_t, a)
```

主头应是 node resolution；granularity transition 用作辅助监督和校验，不能只学一个黑盒 scalar Q value。

### 5.4 训练目标

```text
L =
  L_node_BCE
  + beta1 * L_granularity_CE
  + beta2 * L_yield_BCE
  + beta3 * L_pairwise_oracle_ranking
  + beta4 * L_calibration
```

- `L_node_BCE`：动作对每个 unresolved node 的解决标签；
- `L_granularity_CE`：执行动作后的粒度；
- `L_pairwise_oracle_ranking`：同一状态下有效动作应排在无效动作前；
- `L_calibration`：Brier loss 或 differentiable ECE surrogate。

### 5.5 效用与规划

一步效用：

```text
U(a | H_t, g*) =
  P(G_{t+1} >= g* | H_t, a)
  - lambda_c * cost(a) / budget_remaining
  - lambda_o * over_attribution_risk
```

非短视版本不直接训练 end-to-end RL，而使用 learned transition model 做 depth-2 beam search：

```text
a* = argmax_a E[U(a) + gamma * max_a' U(a' | H_{t+1})]
```

只有当合成互补动作场景显示一步 greedy 存在稳定缺陷时，才启用两步 planning。

### 5.6 在线反馈

动作执行后更新：

- 实际 resolved node；
- recovered claim count；
- action latency / cost；
- predicted vs observed calibration residual。

第一版使用 provider/action-type 分层 Bayesian calibration 或 online logistic update；暂不做 unrestricted online RL。

## 6. 为什么暂不做端到端 RL

1. 当前只有少量独立 campaign，深度 RL 极易记忆 case/action ID；
2. 模拟器能计算所有 action 的 counterfactual outcome，监督学习比稀疏 reward 更充分；
3. AFA 文献已经表明 RL 训练困难，简单 CMI/greedy 经常表现很强；
4. WinRegRL 已占据“专家 MDP + RL refinement”的近邻空间；
5. 论文首先需要证明 node-level transition learning 有效，再讨论 policy learning。

## 7. 数据构造与泄漏控制

### 7.1 训练样本

对完整 attack trace 生成多种 mask state。对每个 state 枚举全部可用 action，计算：

- resolved claim ids；
- resolved CTI node ids；
- before/after granularity；
- cost；
- 是否达到 target。

这样每个状态能产生 dense counterfactual state-action labels，而不只使用策略实际走过的 trajectory。

### 7.2 必须按 case 先切分

正确顺序：

```text
campaign/provider/dataset split
-> 在各 split 内生成 masks
-> 训练和评估
```

禁止先生成 mask 再随机切分，否则同一完整 trace 会同时进入训练和测试。

### 7.3 当前数据边界

- C04/C05：开发案例；
- C06：已经用于 M2 留出验证，后续可用于诊断，但不能重新包装成 M3 独立测试；
- M3 最终测试必须使用未参与设计的 E5、OpTC 或其他 campaign-level holdout；
- 现有 3 个真实 case 不足以支撑深模型有效性结论。

## 8. 分阶段最小实验

### M3a：Action-Gap Compatibility Oracle-free Baseline

先给 action 增加公开 `intended_cti_node_ids`，按“未匹配关键节点命中概率 / cost”排序。

目的不是发表，而是验证：

> M2 失败是否主要来自 action-gap 表示缺失。

若 M3a 仍不优于 coverage greedy，说明问题不只在表示，还在动作空间或粒度规则。

### M3b：可校准条件收益模型

先使用 logistic regression / small MLP，不使用 GNN：

- 输入：state summary + per-node gap features + action features；
- 输出：node-resolution probability；
- 评估：AUROC、AUPRC、Brier、ECE、NDCG、top-1 hit、budget success。

### M3c：图条件模型

数据量足够后加入 GraphSAGE/GAT 和 depth-2 planning，并与 M3b 做消融。

## 9. 实验基线

必须包含：

1. random；
2. fixed order；
3. cheapest first；
4. coverage greedy；
5. M1；
6. frozen M2；
7. CMI greedy；
8. ACO / supervised oracle-ranking 类 baseline；
9. WinRegRL-style expert transition MDP；
10. Oracle optimal。

## 10. 主要指标

### 10.1 Transition model

- node-resolution AUROC / AUPRC；
- Brier score / ECE；
- granularity-transition macro-F1；
- pairwise ranking accuracy；
- top-1 action hit / NDCG。

### 10.2 Policy

- challenge-subset budget success rate；
- cost to target；
- regret vs Oracle；
- zero-yield actions；
- unresolved critical nodes at stop；
- over-attribution / correct abstention。

总体成功率必须同时报告 challenge subset，避免初始已达目标的状态稀释失败。

## 11. LLM 的具体作用

LLM 只承担三个受控角色：

1. 把 CTI、日志、IOC、样本报告编译为带 source pointer 的 evidence claims；
2. 把自然语言取证请求映射到 action schema 和候选 CTI gap nodes；
3. 根据模型输出生成带证据引用的行动理由、停止原因和剩余不确定性说明。

LLM 不直接：

- 读取隐藏结果；
- 产生 action utility 真值；
- 替代 transition model；
- 自由决定 actor label；
- 在没有证据时补全事实。

## 12. 专利边界建议

建议题名：

> 一种基于归因目标约束的缺失证据节点条件收益预测与序贯取证方法

可主张的技术链：

```text
构建归因证据缺口图
-> 建立取证动作与候选缺口节点的语义对应
-> 预测节点解决概率和归因粒度迁移概率
-> 在成本/预算约束下规划动作序列
-> 根据执行反馈校准条件收益
-> 达到目标粒度或触发停止/降级
```

不能宽泛主张：

- MDP/RL 取证；
- 证据不足后追加查询；
- LLM agent 自动调查；
- 固定 reward 下的动作排序。

## 13. Devil's Advocate

### Major 1：动作标签可能由 ground truth 反向泄漏

`intended_cti_node_ids` 必须来自 query semantics 和当前 CTI schema，而不是从实际 `recoverable_claim_ids` 自动复制。需要单独记录其生成来源并做边界测试。

### Major 2：小样本下 GNN 只是复杂化

如果 M3b 小模型已经达到相同效果，GNN 不能成为装饰性创新。必须用跨图拓扑泛化或节点级消融证明图编码必要。

### Major 3：粒度规则决定 reward，可能形成自证循环

需要至少两套粒度判定：

- 规则化可审计 gate；
- 独立专家或学习式 gate。

否则模型只是学习复现手写规则。

### Major 4：masked evidence 不等于可获取 evidence

必须给 action 增加 availability / natural absence 标签。对天然不存在的证据，模型应预测不可恢复，而不是把它当普通 hidden feature。

### Strongest counter-argument

> 该方法只是把 AFA 的 feature 改名为 CTI node，再套一个 GNN。

回应这一质疑所需的实证，不是措辞：

1. grouped action 同时揭示文本、网络和 provenance claim；
2. 图拓扑决定粒度升级，扁平特征 baseline 无法等价恢复；
3. natural missingness 和 action failure 被显式建模；
4. 目标是 calibrated attribution granularity transition，而非分类 accuracy。

## 14. 下一步决策

立即推进顺序：

1. 将 WinRegRL 纳入撞题矩阵和 Zotero 待精读集合；
2. 实现 M3a，仅验证 action-gap 表示假设；
3. 新增训练样本导出 schema：`state_action_outcome`；
4. 扩展至少一个未使用的 E5/OpTC campaign 作为最终 holdout；
5. 数据量达到可训练条件后实现 M3b，再决定是否进入 GCEU-Net。

当前不应：

- 在 C06 上调权；
- 直接实现 PPO/DQN；
- 用 LLM 替代 utility model；
- 立即写“性能优于现有方法”的专利实施例。
