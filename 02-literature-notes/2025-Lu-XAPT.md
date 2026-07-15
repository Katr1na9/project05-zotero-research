# XAPT: Explainable Anomaly-Driven Prediction of Threat Stages in APT Campaigns

## 1. 基本信息

- 系统名：XAPT
- 中文译名：XAPT：面向 APT 攻击活动阶段预测的可解释异常驱动方法
- 作者：Wei Lu; Issa Traore; Isaac Woungang; Eric Brown; Marcelo Luiz Brocardo; Qiaoyan Yu; Ornella Lucresse Soh
- 年份：2025
- Venue：IEEE Access, 13, 199737-199756
- DOI：https://doi.org/10.1109/ACCESS.2025.3636501
- PMCID：https://pmc.ncbi.nlm.nih.gov/articles/PMC12768332/
- 阅读日期：2026-07-13
- 阅读优先级：重点读
- 所属主题：APT Stage Prediction / Calibration / Explainable ML

## 2. 一句话总结

XAPT 把 PCA 重构误差校准为异常概率，再用贝叶斯分类器预测单条流量或 meta-alert 的攻击阶段，并以 SHAP 解释特征贡献；它验证了“校准异常分数 + 阶段分类”的价值，但没有联合使用流量与日志、没有构建事件证据图，也没有恢复攻击链或推断攻击意图。

## 3. 研究问题

- 如何把异常分数作为概率证据用于 APT 阶段预测，而不是只做阈值告警？
- 如何为阶段分类结果提供可解释的特征贡献？
- 论文中的 `stage-level attribution` 指攻击阶段归类，不是威胁行为体归因。

## 4. 核心贡献

1. 以 PCA 逆变换重构误差产生事件级异常分数。
2. 用 Logistic/Platt scaling 将异常分数校准为概率。
3. 将校准分数输入 Bayesian Network/Gaussian Naive Bayes 多分类器预测 kill-chain 阶段。
4. 用 SHAP 提供局部与全局特征贡献解释，并讨论 SIEM/SOC 中按需异步解释。

## 5. 方法框架

- 输入是已经结构化的单条观测特征，而不是原始 PCAP、原始日志或跨事件图。
- 训练：PCA -> reconstruction error -> calibration -> Bayesian classifier -> SHAP explainer。
- 在线推理：单事件异常分数 -> 校准概率 -> 阶段标签 -> SHAP 特征解释。
- 贝叶斯分类图描述特征概率依赖，不是攻击事件之间的因果图。
- 两个数据集分别训练和评估，未执行 traffic-log joint fusion。

## 6. 数据集与实验

- DAPT2020：17,339 条网络流量样本，85 个特征；benign、reconnaissance、foothold、lateral movement、exfiltration 五类，后两类极度稀缺。
- DAPT2020 阶段预测的 weighted F1 为 81.79%，macro F1 仅 53.05%；exfiltration 仅 3 个样本，召回率 0.13%。
- DAPT2020 的 lateral movement 召回率也只有 11.58%，说明整体 weighted F1 主要由 benign 与前期高频阶段支撑。
- Meta-alert 数据集：118,465 条 SIEM meta-alert，仅包含四类攻击阶段，类别近似均衡；macro F1 为 99.99%。
- 数据集分别验证跨输入抽象层适配性，不构成多源联合贡献。
- 后续敏感性实验中，Platt+KNN 在不同 PCA 维度的 accuracy 为 0.797-0.855，macro recall 为 0.788-0.838。
- Kernel SHAP 代价很高：特征数与 background size 增加时，单样本解释可从数秒增长到数百乃至上万秒。
- 评价完整性审计：正文声明采用 80/20 划分，但表中混淆矩阵/类别 support 的合计与完整数据规模相符，而不是约 20% 的测试规模；在代码或作者说明澄清前，应标记为潜在数据划分或报告口径不一致，不能据此把近满分结果当作可信上界。

## 7. 关键知识点

- `weighted F1` 会掩盖后期阶段极低召回，阶段任务必须同时报告 macro/per-stage 指标。
- 在均衡、已聚合的 meta-alert 上接近满分，不能外推到原始流量或真实双源调查。
- 特征级 SHAP 解释说明模型为何分类，不等于给出支撑攻击链或意图结论的事件证据路径。
- 校准需要报告 Brier score、ECE/reliability diagram；“用了 Platt scaling”本身不能证明概率可信。

## 8. 优点

- 明确把异常分数提升为可参与推断的概率证据。
- 对类别不平衡导致的阶段差异有直接实验呈现。
- 给出解释模块的运行时成本，适合设计在线分类、离线解释的两阶段系统。

## 9. 局限

- 网络流量与 meta-alert 分开实验，不是流量侧+日志侧联合建模。
- 无事件图、跨源关联、原始证据 ID、攻击路径、意图或 actor attribution。
- 论文称 Bayesian Network，但实现又描述 Gaussian Naive Bayes，实际依赖结构需要复现核验。
- DAPT2020 严重不平衡，meta-alert 又过于均衡且仅含攻击，两个结果可比性弱。
- 声明的 80/20 划分与混淆矩阵 support 合计存在明显不一致，可能涉及全量评估、划分描述错误或数据泄漏；当前材料无法唯一判定原因。
- SHAP 只解释模型特征依赖，不能验证结论与真实因果链一致。

## 10. 对我选题的启发

- 可把校准后的阶段概率作为双源证据图节点/子图的一个属性，而不是最终归因结论。
- 我们应把“模型解释”和“证据链解释”拆成两个评价层：前者看特征贡献，后者看原始 packet/log 锚点与跨源路径。
- 双线实验必须使用同一事件/场景中的同步流量与日志，而不是在两个数据集上分别取得结果。

## 11. 可转化的研究问题

1. 事件子图级置信度校准能否优于单事件异常分数校准？
2. 流量侧与日志侧证据冲突时，阶段/意图候选如何更新并触发拒答？
3. 证据路径完整度、概率校准与攻击链恢复准确率之间是什么关系？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| StageFinder | 后者真正融合主机与网络事件图；XAPT 仅分别测试两类数据 |
| FuseChain | 后者构建多源事件图并恢复阶段；XAPT 可提供概率校准与解释基线 |
| Uncertainty-aware Attack Stage | 同属阶段不确定性方向；XAPT 使用 Platt/贝叶斯，后者使用 Dirichlet |

## 13. 论文写作可引用句式

- 在不同数据抽象层上分别取得高阶段分类性能，并不能证明跨源证据已经被联合关联；尤其在平衡且预聚合的 meta-alert 上，接近满分的结果可能掩盖原始事件层的关联难度。

## 14. 我的批注与疑问

- 需要复核校准实验是否完整报告 Brier/ECE；正文强调校准，但主要表格更集中于分类结果。
- Platt scaling 只说明执行了概率映射；在缺少 Brier score、ECE、reliability diagram 和独立测试集核验时，不能写成“已经得到可信概率”。
- 应把 `stage attribution` 统一译为“阶段归类/阶段预测”，避免与 actor attribution 混淆。
- DAPT2020 中 exfiltration 仅 3 个样本，任何整体高准确率都不能支撑后期阶段可用性。
- 复现实验首先要核对 train/test index、PCA 与 scaler 的 fit 范围、校准集是否独立，以及混淆矩阵到底来自测试集还是全量数据。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：4/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是（校准与阶段基线，不是双源图方法）
