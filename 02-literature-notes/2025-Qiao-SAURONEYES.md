# SAURONEYES: Disentangling Voluminous Logs to Unveil Camouflaged Attack Intentions

## 1. 基本信息

- 中文译名：SAURONEYES：解耦海量日志以揭示伪装的攻击意图
- 作者：Wei Qiao; Weiheng Wu; Song Liu; Yebo Feng; Zehui Wang; Junrong Liu; Teng Li; Bo Jiang; Zhigang Lu; Baoxu Liu
- 年份：2025
- 来源：IEEE Transactions on Information Forensics and Security, Vol. 20, pp. 11744-11757
- DOI：https://doi.org/10.1109/TIFS.2025.3618381
- 阅读状态：`full-read`
- 阅读日期：2026-07-13
- 所属主题：Audit Logs / Graph Disentanglement / APT Detection / Attack Reconstruction

## 2. 一句话总结

SAURONEYES 把审计日志同时构造成实体属性知识图和因果交互图，通过多视图图解耦、对比学习和恶意边检测，从单一审计源中提取攻击子图，再用重叠社区发现分离共享入口的多条攻击链；论文所谓“攻击意图”是潜在交互倾向或恶意边语义，并不是具有标注真值的高层攻击目标、动机或行为体意图。

## 3. 研究问题

- 如何从恶意活动占比极低的海量审计日志中识别伪装为正常操作的 APT 行为？
- 如何避免普通 GNN 聚合被高频正常邻居主导？
- 当多条攻击活动共享入口节点时，如何避免传统非重叠社区发现把攻击链错误合并？

## 4. 核心贡献

1. 从同一批审计日志构建知识视图 KG 与交互视图 IG。
2. 在 KG 上采用路径感知 GNN 和注意力邻居分配，在 IG 上采用 LightGCN，学习实体的多方面表示。
3. 用视图内与视图间对比学习缓解恶意样本稀疏和伪装问题。
4. 在边级别预测主体与客体交互是否恶意，而不是只做图级或节点级检测。
5. 从恶意边子图出发，以 BIGCLAM/NMF 重叠社区检测区分共享入口的不同攻击活动。
6. 在 StreamSpot、Unicorn Wget 与 DARPA TC E3 上验证检测、链重构、效率、对抗扰动与概念漂移。

## 5. 方法框架

- 图构建：从审计日志抽取进程、文件、socket、network flow、IP、命令行、路径和父子关系。
- KG：`(entity, relation, attribute_value)`，表达实体属性和属性关系。
- IG：`(subject, object, timestamp)`，表达具有因果方向的系统交互。
- 多方面初始化：门控单元把实体表示投影到多个潜在方面。
- 视图解耦：KG 使用路径感知聚合与邻居分配；IG 使用 LightGCN。
- 对比学习：分别优化 KG/IG 内部结构一致性，并对齐两个视图中的同一实体。
- 检测：融合各方面的交互分数，以 BPR、视图内对比、视图间对比及正则项联合训练。
- 链重构：抽取恶意边子图，以 BIGCLAM 最大化节点对社区隶属强度，得到可重叠的攻击社区。

## 6. 数据集与实验

- StreamSpot：6 类场景，其中 5 个正常、1 个 drive-by download 攻击。
- Unicorn Wget：150 个 CamFlow 日志，125 个正常、25 个隐蔽供应链攻击。
- DARPA TC E3：CADETS、TRACE、THEIA 等真实红队/企业背景数据。
- 检测指标：Accuracy、Precision、Recall、F1 和 ROC。
- 社区指标：NMI、Jaccard、F1。
- 实现：Python 3.11、PyTorch、64 维嵌入、学习率 0.001、batch size 1024。
- 摘要报告平均检测准确率约 99%；CADETS E3 约 4 GB、两天日志的预测耗时为 27 秒。
- 消融：KG 解耦替换为普通 GCN 后 precision 降至 75%；IG 解耦替换为 MLP 后为 67%；全部替换后约为 55%。

## 7. 关键知识点

- KG 与 IG 是同一审计源的两个视图，不是网络流量线与日志线两个独立来源。
- 边级检测比节点级检测更接近“谁对谁做了什么”，适合作为攻击链构图入口。
- BIGCLAM 允许一个共享入口属于多条链，适合并发 campaign 或共同初始入侵点。
- 论文中的 `intention` 是通过潜在表示解耦出来的交互倾向，没有独立语义标签或高层目标标注。
- 攻击链重构主要依赖恶意边筛选与社区划分，不等于 ATT&CK 阶段推理或行为体动机推断。

## 8. 优点

- 在 TIFS 正式发表，实验覆盖三个典型 provenance 数据源和多类评价。
- 直接优化恶意边，输出比图级异常分数更细。
- 明确处理攻击社区重叠，补足 Louvain 一类硬划分的结构缺陷。
- 包含消融、开销、对抗扰动和概念漂移实验，工程评价较完整。
- 证明“图构建本身 + 攻击链结构分离”可以成为独立研究贡献。

## 9. 局限

- 输入仅为审计日志；network flow 只是审计记录中的对象类型，不是独立 PCAP/流量证据源。
- KG/IG 的边来自同一解析流程，没有跨源候选边、边置信度或冲突状态。
- “意图”没有高层目标、动机或语义真值，不能作为 intent recognition 的直接基线。
- 链重构通过社区发现获得，缺少 ATT&CK tactic/technique 顺序约束和链级因果置信度。
- 社区指标评价结构分区，但没有 claim-to-record 回放或证据蕴含评价。
- 概念漂移只用随机添加常见边模拟，没有在线学习机制。

## 10. 对我选题的启示

- 双线研究应明确写成“独立流量证据 + 独立日志证据”，不能把同源多视图包装成多模态。
- 可借鉴“属性图 + 交互图”的双视图设计，但增加 `TrafficObservation`、`LogObservation` 的原始证据血缘。
- 可把重叠攻击社区作为图剪枝/候选链生成模块，再让 LLM 只对候选链做 ATT&CK 与目标意图推理。
- 需要在术语层面把 `latent interaction intent`、`malicious purpose`、`ATT&CK tactic` 与 `goal intent` 分开。

## 11. 可转化的研究问题

1. 独立 PCAP 与日志视图之间的候选边校准，能否提升共享入口、多 campaign 场景下的链分离质量？
2. 把跨源边不确定性输入重叠社区发现，能否避免错误关联造成的链错误合并？
3. 在攻击链结构确定后，高层目标意图推断是否比仅用异常边嵌入更准确、更可解释？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| KAIROS | 都从 provenance 图发现攻击社区；SAURONEYES 增加图解耦和重叠社区 |
| THREATRACE | 都做节点/边级 provenance 检测；SAURONEYES 更强调多方面交互表示 |
| MuSAR | MuSAR 融合网络告警和应用日志；SAURONEYES 只处理审计日志但图学习更强 |
| APTGuard | APTGuard 是 PCAP+auditd 固定窗口融合；SAURONEYES 是审计图边检测与社区链重构 |
| Project03 支线 | 可借鉴双视图和重叠社区，但必须补独立流量证据、跨源边与高层意图 |

## 13. 论文写作可引用句式

近期 provenance 研究已经通过知识视图与交互视图解耦、边级恶意性预测和重叠社区发现，从单源审计日志中分离共享入口的多条攻击活动；然而，该类方法尚未建模原始网络流量与主机日志之间的独立证据关系，也未把潜在交互倾向提升为具有可核验证据链的高层攻击目标。

## 14. 我的批注与疑问

- 标题中的 `attack intentions` 容易与攻击目标识别混淆，后续引用必须限定为 latent interaction tendencies。
- BIGCLAM 的社区数与阈值如何确定会直接影响链数量，复现时需检查超参数和 ground truth 构造。
- 论文声称“完整攻击链”，但完整性的测量更接近社区覆盖，不是逐阶段 ATT&CK 链准确率。
- 表格图像中的逐数据集数值需要在复现实验阶段从正式 PDF 表格再次结构化录入。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：4/5
- 硕士论文基础价值：4.5/5
- 是否进入核心文献：是，作为“审计图构建、边检测与重叠链重构”的最新强基线
