# Preliminary Investigation into Uncertainty-Aware Attack Stage Classification

## 1. 基本信息

- 中文译名：面向不确定性感知的攻击阶段分类初步研究
- 作者：Alessandro Gaudenzi; Lorenzo Nodari; Lance Kaplan; Alessandra Russo; Murat Sensoy; Federico Cerutti
- 年份：2025
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2508.00368
- Zotero key：IGPCP4WY（PDF：GPPYR4IZ）
- 阅读日期：2026-07-13
- 阅读优先级：重点读
- 所属主题：Attack Stage / Evidential Deep Learning / OOD

## 2. 一句话总结

该文在 CyberBattleSim 中用 ATT&CK Flow/reward machine 定义阶段，再让 Evidential Deep Learning 输出 Dirichlet 类别证据和不确定性，以识别噪声/OOD。它不含真实 PCAP/日志、事件图或 LLM，适合作为本课题的阶段/意图置信门控组件，而非数据融合或攻击链主体。

## 3. 研究问题

- 如何在攻击战术变化、未知行为或输入损坏时降低阶段分类置信度？
- 场景是 switched-LAN CTF：攻击者寻找凭据节点再访问目标节点。

## 4. 核心贡献

1. ATT&CK Flow 到 reward machine 的阶段标注表示。
2. CNN-MLP Evidential Deep Learning 输出 Dirichlet 参数。
3. 用位翻转噪声模拟 OOD，观察正确/错误预测不确定性。

## 5. 方法框架

- 输入：CyberBattleSim 高层状态的滚动窗口，约 30 个观测特征和标签位。
- 输出：阶段类别和 `u=K/S` 不确定性。
- 攻击动作被省略，假设状态转移隐含唯一动作。
- 环境网络图、ATT&CK Flow 与 reward machine 是模拟/背景模型，不是现场事件证据图。
- 无 LLM、PCAP、网络流、系统/应用/蜜罐日志。

## 6. 数据集与实验

- 全文未报告样本数、划分规模和比例。
- 10 个传统基线中 Gradient Boosting/SVC Accuracy 0.8264、F1 0.8128；LSTM Accuracy 0.5795、F1 0.4252。
- EDL 训练使用 40% 位翻转构造 OOD，测试噪声 0/20/40%。
- 主实验只定性展示不确定性分布，没有 ECE、Brier、NLL 或 OOD AUROC。

## 7. 关键知识点

- 不确定性应区分数据噪声、证据缺失、阶段歧义和未知战术。
- 模拟位翻转不等于真实传感器缺失或新 TTP。
- softmax/LLM 自报信心不应直接当作校准概率。

## 8. 优点

- 明确把阶段识别从点分类扩展到 OOD/不确定性。
- Dirichlet 证据输出可与拒答和人工升级联动。

## 9. 局限

- 输入是模拟器状态，省略真实解析、对齐与良性噪声。
- 高噪声时正确/错误不确定性重叠，甚至低于随机基线。
- 缺多随机种子、真实场景和标准校准指标。
- 无链、证据、LLM、意图或行为体归因。

## 10. 对我选题的启发

- 可用 evidential output 为阶段/意图候选提供不确定性门控。
- 应将双源缺失、跨源冲突和未知 TTP 分别构造实验，而非统一位翻转。
- 拒答正确率、ECE/Brier 和 selective risk 应进入评价。

## 11. 可转化的研究问题

1. 事件图证据支持度能否形成比 LLM 自报信心更可校准的意图概率？
2. 缺失流量源与缺失日志源是否产生不同的不确定性模式？
3. 如何让候选链/意图在证据不足时安全停止？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| StageFinder | 提供双源阶段分类，可加入不确定性层 |
| HunterAgent | 提供预算耗尽弃权和证据/线索分层 |
| LLMs Unreliable for CTI | 提醒同时评价一致性和校准 |

## 13. 论文写作可引用句式

- 面向高风险攻击阶段判断，模型不仅应输出类别，还应在未知行为和证据损坏时显式表达不确定性并支持拒答。

## 14. 我的批注与疑问

- 目标节点是模拟器预设任务，不是被推断的攻击意图。
- 该文只能作为组件引用，不能作为双源系统效果证据。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：4/5
- 实验可复现性：2.5/5
- 作为硕士论文基础价值：3.5/5
- 是否进入核心文献：条件性保留
