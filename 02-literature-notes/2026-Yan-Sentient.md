# Sentient: Detecting APTs via Capturing Indirect Dependencies and Behavioral Logic

## 1. 基本信息

- 系统名：Sentient
- 中文译名：Sentient：通过捕获间接依赖与行为逻辑检测 APT
- 作者：Wenhao Yan; Ning An; Wei Qiao; Weiheng Wu; Zhigang Lu; Bo Jiang; Baoxu Liu; Junrong Liu
- 年份：2026
- Venue：Proceedings of the AAAI Conference on Artificial Intelligence, 40(2), 1409-1417
- DOI：https://doi.org/10.1609/aaai.v40i2.37115
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Provenance Graph / Behavioral Intent Embedding / Graph Transformer / Bi-Mamba2

## 2. 一句话总结

Sentient 从单源 audit logs 构建 provenance graph，用 Graph Transformer 捕获间接依赖、随机游走形成行为序列，再以 Bi-Mamba2 学习所谓 behavioral intent embedding 并重构动作检测异常；它已占据“图上行为逻辑/意图表示”，但该 intent 是无语义标签的潜在向量，不是可验证的攻击目标、动机或 actor intent 结论。

## 3. 研究问题

- 如何避免 GNN 局部邻居聚合遗漏多跳间接依赖？
- 如何减少恶意节点周围大量 benign behavior 的噪声干扰？
- 如何学习行为之间的逻辑关联并用于异常检测与攻击故事聚类？
- 威胁模型假定审计日志准确、完整并受完整性保护。

## 4. 核心贡献

1. Graph Transformer 联合 Word2Vec 语义和 Laplacian 位置编码学习全局节点表示。
2. 随机游走构建行为序列，Bi-Mamba2 捕获双向逻辑关联并形成 intent embedding。
3. 仅用 benign data 训练 masked action reconstruction 进行异常检测。
4. 拼接 intent/source/destination embedding 并聚类相似行为，生成压缩攻击活动视图。

## 5. 方法框架

- 图节点为 process/file 等，边为 write/open 等系统交互。
- Pre-training 通过节点类型重构学习结构与语义表示。
- 行为序列长度上限 W；每条边由 source/destination node embedding 拼接表示。
- Bi-Mamba2 输出 `h_e`，论文称为 behavioral intent embedding。
- MLP 重构被 mask 的 read/write/execute 等动作；重构误差高于 benign mean + 1.5 std 判为异常。
- Attack investigation 对 `h_e + source + destination` 聚类，输出简化行为图。

## 6. 数据集与实验

- StreamSpot、UNICORN Wget、DARPA E3 CADETS/THEIA/TRACE。
- Sentient 在各数据集的 F1 为 0.97-0.99，FPR 为 0.2%-4.1%。
- 在 CADETS/THEIA/TRACE 上 precision 0.95-0.97、recall 0.99。
- 去除 pre-training precision 下降 20.75%；去除 IAM 下降 31.59%。
- CADETS 处理两天日志时，作者估算日均 preprocessing+detection 约 63.6 秒，峰值内存 2.01 GB。
- Mimicry 增加 1,000-3,000 benign events 后，F1 下降不超过约 0.93 个百分点。

## 7. 关键知识点

- 论文中的 intent 是行为关联的隐向量，不带“窃密/破坏/持久化”等目标语义，也没有 intent ground truth。
- 行为逻辑建模可作为攻击链表示基础，但不能直接宣称完成意图识别。
- 仅报告节点/图检测指标，无法证明聚类后的攻击故事覆盖正确阶段和边。

## 8. 优点

- AAAI 2026 最新代表工作，直接覆盖 provenance 图上的行为逻辑关联。
- 仅 benign training，适合未知攻击与样本稀缺场景。
- 有 IAM 消融、性能开销和 mimicry stress test。
- 将全局依赖与局部行为序列结合，适合作为图编码 baseline。

## 9. 局限

- 单一 audit provenance，未融合独立 traffic/PCAP 与日志证据。
- `intent embedding` 没有可解释语义、目标标签、证据链或人工验证。
- 随机游走不保证遵循真实因果/时间顺序，可能采到拓扑相关但语义无关的路径。
- 攻击故事只以简化案例展示，没有 chain edge F1、stage coverage 或 intent accuracy。
- 使用既有非官方 DARPA 标签，且未分析跨数据集泛化。
- 假设日志完整可信，没有测试日志缺失、时间漂移或篡改。

## 10. 对我选题的启发

- “intent representation”已被占位，论文创新不能只是在事件图后加序列模型。
- 可以把 Sentient 作为行为表征 baseline，再要求 LLM 输出带证据的显式目标候选，并允许 unknown/abstain。
- 双源图可用网络侧证据约束随机游走/行为序列，使路径符合时间、会话与方向。

## 11. 可转化的研究问题

1. 双源证据约束能否提高 latent intent cluster 到显式 ATT&CK objective/goal 的可解释映射？
2. 无 semantic intent label 时，如何评价“意图感知”而不是只评价异常检测？
3. 证据图上的路径采样如何同时满足因果、时间和跨源一致性？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| AISL | AISL 使用专家给定 intent 规则扩正样本；Sentient 学习无标签 latent intent embedding |
| SHIELD | SHIELD 用 LLM 输出 kill-chain 摘要；Sentient 用神经序列模型学习行为逻辑 |
| StageFinder | 同为图+序列模型；StageFinder 输出显式 stage probabilities，Sentient 输出异常与聚类 |

## 13. 论文写作可引用句式

- 近期工作已将行为意图建模为 provenance 图上的潜在序列表示，但这种表示主要服务于异常检测，尚未被验证为可解释、可证伪的攻击目标或动机判断。

## 14. 我的批注与疑问

- “intent”命名有明显外延扩张，实际数学目标是 masked action reconstruction。
- 论文称关注 logical association，但随机游走与双向序列可能引入未来信息和非因果关联。
- 需要在我们术语表中区分 latent behavioral intent、attack objective、actor motivation。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（意图表示直接碰撞）
