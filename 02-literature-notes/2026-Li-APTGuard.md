# APTGuard: An APT Detection Method Based on LLM and Time-Series Augmentation

## 1. 基本信息

- 中文译名：APTGuard：基于大语言模型与时间序列增强的 APT 检测方法
- 作者：Xinran Li; Zijun Dou
- 年份：2026
- 来源：1st ICLR Workshop on Time Series in the Age of Large Models (TSALM 2026), Poster
- 稳定链接：https://openreview.net/forum?id=U8LfIvhkI1
- DOI：无，OpenReview workshop paper
- 阅读状态：`full-read-via-primary-fulltext-index`（OpenReview PDF 受挑战页限制；由 OpenReview PDF 全文索引与 ICLR 官方元数据核对）
- 阅读日期：2026-07-13
- 所属主题：PCAP + auditd / Time-Series Augmentation / LLM Attack Chain

## 2. 一句话总结

APTGuard 在近真实网络设备测试床上用 tcpdump 与 auditd 同步采集原始流量和主机/设备日志，以 0.01 秒固定窗口拼接流量、日志和配置特征，经自适应时间序列增强和 ROCKET/TCN/RNN 识别攻击阶段，再让 LLM 按时间排序阶段标签、判断是否构成完整 APT 并生成 ATT&CK 攻击链解释；它直接占据“双源 + LLM + 攻击链”的宽泛表述，但没有事件级证据图、跨源边校准和链重构定量评价。

## 3. 研究问题

- APT 样本稀缺、类别不平衡时，如何提高细粒度时间片阶段分类？
- 如何把孤立时间片标签组合为具有连续性和因果关系的完整 APT 判断？
- 如何在面向路由器/BGP 控制面的攻击场景中融合数据平面与控制平面观测？

## 4. 核心贡献

1. 建立面向网络设备 APT 的虚拟化近真实测试环境。
2. 同步采集 tcpdump PCAP、auditd 系统调用/安全审计日志和配置特征。
3. 提出由特征提取器、策略决策器和变换池组成的自适应时间序列增强模块。
4. 在 ROCKET、TCN、RNN 三种下游模型上验证增强策略的跨模型收益。
5. 用 LLM 对时间片阶段标签进行顺序建模、因果判断、ATT&CK 映射和自然语言解释。

## 5. 方法框架

- 采集：tcpdump 观测网络流量；auditd 记录 `execve`、netlink、权限修改、配置写入、密钥管理等事件。
- 对齐：以固定 0.01 秒窗口进行时间对齐。
- 融合：把流量指标、日志指标和配置指标拼接成窗口级标准化样本。
- 增强：根据时间序列特征动态选择变换及强度，生成训练样本。
- 分类：ROCKET、TCN 或 RNN 以交叉熵学习时间片攻击阶段。
- LLM：将侦察、初始访问、C2、横向移动等标签按时间排序，检查阶段连续性、行为因果、长期持续性和网络设备攻击特征。
- 输出：APT/非 APT 判断、缺失阶段、ATT&CK 技术映射、完整攻击链和解释。

## 6. 数据集与实验

- 数据来自作者构建的虚拟化网络设备测试床，包含攻击演练与网络波动、管理员配置变更等正常行为。
- 论文未提供公开数据集入口，样本规模、类别分布和逐阶段标签数需进一步核验。
- 硬件：AMD EPYC 7742、NVIDIA A100 40GB；Ubuntu 22.04.4、Python 3.10.12、PyTorch。
- 训练：RAdam，初始学习率 0.005，batch size 16，100 epochs。
- 指标仅为时间序列分类 Accuracy。
- ROCKET：NoAug 0.7608，本文增强 0.8243。
- TCN：0.7403 -> 0.7838；RNN：0.6757 -> 0.7022。
- 三模型平均：0.7256 -> 0.7701，优于对比增强方法的最佳平均值 0.7500。
- LLM 攻击链只给出案例展示，没有链级 Precision/Recall/F1、事实一致性或人工评价。

## 7. 关键知识点

- 这是当前检索中最直接的“原始 PCAP + auditd + LLM 攻击链”撞题。
- 其多模态融合是固定窗口特征拼接，不是由 observation 节点和跨源关系组成的事件证据图。
- LLM 接收的是分类后的阶段标签与聚合特征，不直接检索 packet/log 原始记录。
- 论文实验证明的是增强策略提升阶段分类 accuracy，并未证明 LLM 提升攻击链重构质量。
- 0.01 秒统一窗口在时钟漂移、异步日志、长连接和 NAT 场景下未必合理。

## 8. 优点

- 双线数据源真实且清楚，覆盖 tcpdump、auditd 与配置状态。
- 面向网络设备控制面/数据平面的场景与 Project03 背景接近。
- 有完整攻击演练和正常运维干扰，而非只用静态公开数据。
- 下游模型和增强基线明确，表格结果可直接作为分类模块参照。
- Prompt 明确区分完整 APT、缺失阶段和正常运维干扰。

## 9. 局限

- 固定窗口拼接压平了流量与日志各自的来源、对象、因果与证据层级。
- 没有 packet index、log record ID、哈希和解析版本等原始证据回指。
- 没有候选跨源关系、关系置信度、冲突/拒绝状态或不确定性传播。
- 数据集未公开，规模与标注协议不透明，外部可复现性弱。
- 只报告 Accuracy，未报告类别不平衡下更关键的 macro-F1、PR-AUC、每阶段召回和校准。
- LLM 模型、重复次数、随机性和链级评价不完整。
- Prompt 要求 LLM 自行结合 MITRE 知识，但没有 RAG、引用核验或幻觉测量。
- workshop 论文篇幅和同行评审强度低于正式主会/期刊。

## 10. 对我选题的启示

- 不能把“PCAP+日志+LLM 攻击链”作为论文级创新描述，APTGuard 已经直接覆盖。
- 真正差异应放在：事件级双线建图、原始证据锚点、跨源边概率与冲突、链级不确定性、证据约束的意图输出。
- APTGuard 可作为无图的 early-fusion baseline：固定窗口拼接 + 时间序列分类 + LLM。
- Project03 的 `ThreatObservation` 可升级为 source-preserving observation schema，比较固定窗口与事件关系图两种融合范式。

## 11. 可转化的研究问题

1. 事件级图融合是否优于固定 0.01 秒窗口拼接，尤其在时钟漂移、异步观测和缺失源下？
2. 让 LLM 检索带 packet/log 锚点的候选链，能否降低 ATT&CK 映射和高层意图幻觉？
3. 跨源关系概率与拒答机制能否改善链级 calibration，而不仅是阶段分类 accuracy？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Llama-PcapLog | 都联合 PCAP 与日志；APTGuard 增加阶段分类和 LLM 链推理 |
| Two-stage multi-datasource | 都采用同步窗口融合；APTGuard 窗口更细并增加增强与 LLM |
| MuSAR | MuSAR 显式形成事件图和多主机链；APTGuard 保留原始双源但只做窗口特征融合 |
| Traffic2Chain | 都从时间序列阶段进入 LLM 攻击链；Traffic2Chain 仅流量侧 |
| Project03 支线 | 是最直接的场景对手和 early-fusion baseline，迫使创新收紧到证据图与校准 |

## 13. 论文写作可引用句式

最新工作已通过固定时间窗对齐 tcpdump 流量、auditd 日志和设备配置，并利用时间序列分类器与 LLM 重构网络设备 APT 攻击链；然而，窗口级特征融合未保留可回放的原始证据关系，且攻击链生成仅作案例展示，缺乏跨源关联和链级可靠性的定量评价。

## 14. 我的批注与疑问

- 0.01 秒窗口远小于很多 auditd 写入延迟和跨主机时钟偏差，需检查是否存在同机理想同步假设。
- 论文将 APT 检测称为“典型时间序列分类”，这一简化可能忽略稀疏事件、并发 campaign 和实体关系。
- Accuracy 改善主要来自数据增强；LLM 是独立后处理，不能把表 1 的收益归因给 LLM。
- 后续撞题矩阵要把它标记为“宽泛主线已占据、图构建与可信推理未占据”。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：2.5/5
- 硕士论文基础价值：5/5
- 是否进入核心文献：是，最高优先级直接撞题与 baseline
