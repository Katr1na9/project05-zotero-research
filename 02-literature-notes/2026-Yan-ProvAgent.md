# ProvAgent: An LLM-based Agentic System for Provenance-based APT Detection and Investigation

## 1. 基本信息

- 中文译名：ProvAgent：基于大模型智能体的溯源式 APT 检测与调查系统
- 作者：Wenhao Yan; Ning An; Linxu Li; Bingsheng Bi; Bo Jiang; Zhigang Lu; Baoxu Liu; Junrong Liu; Cong Dong
- 年份：2026
- 来源：arXiv 预印本
- arXiv：https://arxiv.org/abs/2603.09358
- 阅读状态：`full-read`
- 阅读日期：2026-07-14
- 所属主题：Provenance Detection / Identity-Behavior Profiling / Multi-Agent Investigation / APT

## 2. 一句话总结

ProvAgent 先从审计日志构建 provenance graph，以身份-行为对比学习和超球边界检测异常，再由分析、调查、领导和报告四类 LLM 智能体扩展 IOC、映射 kill chain 并生成调查报告；它占据“provenance 检测 + 多智能体调查”的宽泛组合，但检测精度在多个数据集上不足 1%-1.5%，调查评价也没有链边、意图或证据蕴含真值。

## 3. 研究问题

- 如何以实体身份与正常行为的偏离检测未知 APT，而非只匹配已知攻击签名？
- 如何把 provenance detector 产生的大量候选异常组织成可读的攻击调查？
- 多智能体能否通过 IOC 检索、良性参照和 kill-chain 映射扩展攻击上下文？
- 如何在成本可控的条件下把检测和调查放进同一系统？

## 4. 核心贡献

1. 由审计日志构建边聚合后的 provenance graph，并编码语义、动作频率和时间特征。
2. 使用 GraphSAGE/GNN 与 InfoNCE 学习 identity-behavior profile，为每类实体身份建立超球正常区域。
3. 当实体表示超出所属身份边界或更接近其他身份时触发异常。
4. 设计 Analyst、Investigator、Leader、Reporter 四智能体流程，完成 IOC 验证扩展、kill-chain 映射、缺失阶段假设和报告生成。
5. 在 DARPA E3、E5、OpTC 上评价检测，并在 E3 部分场景上评价智能体调查与成本。

## 5. 方法框架

### 输入

- 全系统审计事件及其 provenance graph。
- 良性初始化数据、实体身份标签与检测超参数。
- 检测器输出的异常实体和相关 IOC。

### 输出

- 异常实体/事件告警。
- 扩展 IOC、kill-chain 阶段覆盖和自然语言调查报告。

### 关键模块

| 模块 | 作用 | 对本支线的边界意义 |
|---|---|---|
| Edge aggregation | 滑动窗口内合并重复交互 | 可压缩日志子图，但会损失原始事件粒度 |
| Identity-behavior profile | 学习同身份实体的正常行为边界 | 是日志侧异常检测 baseline |
| Hypersphere detector | 以距离/身份错配判断异常 | 低 precision 暴露 analyst burden 问题 |
| Multi-agent investigator | 扩展 IOC、阶段和报告 | agent appendix 直接边界，不是图构建创新 |

### 方法流程

```text
审计日志 -> provenance graph -> 边聚合与节点特征
       -> identity-behavior 对比学习 -> 超球异常检测
       -> 异常实体/IOC -> Analyst/Investigator/Leader/Reporter
       -> IOC 扩展 + kill-chain 映射 + 调查报告
```

## 6. 数据集与实验

- 使用 DARPA TC E3、E5 和 OpTC；标签主要沿用 Orthrus，因标签不一致排除 Clearscope。
- 威胁模型假设内核/审计机制可信、已收集日志不可变、初始化良性数据干净。
- 根据论文 TP/FP/FN 表重算，多个场景 precision 极低：E3 CADETS 约 0.97%，E3 THEIA 约 1.07%，E5 CADETS 约 0.38%，E5 THEIA 约 0.63%。
- OpTC H051/H201/H501 precision 约 0.55%/1.44%/0.89%，对应 recall 约 43.0%/3.51%/11.9%。
- 论文强调相对部分 baseline 的 FP 降低，但没有突出这些绝对 precision 和分析员负担。
- 多智能体调查只在 E3 CADETS/THEIA 和两种 LLM 上评测，主要以 IOC 数量和阶段覆盖评价；调查后 IOC 数量增加约 160.7%，OCR-APT 相对减少约 61.5%。
- 报告最低日成本约 0.06 美元，平均处理时间约 0.252 小时；未提供完整 chain-edge/intent ground truth。

## 7. 关键知识点

- “provenance detector 后接 LLM 多智能体做攻击调查”已经有直接成果，不能作为新颖性主张。
- FP 数低于某些 baseline 不等于系统具有可运营的 precision；必须从 TP/FP/FN 重算指标。
- IOC 增长和 kill-chain 阶段覆盖只说明报告更丰富，不能证明新增事实正确或链条因果成立。
- Leader 智能体生成缺失步骤时，若不分离 hypothesis 与 evidence，会把合理叙事误写为事实。
- 以 process name、file name、service port 定义 identity 可能对重命名、共享服务和环境漂移敏感。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Identity-behavior profile | 身份-行为画像 | 表示同类实体的正常行为范围 |
| Hypersphere boundary | 超球边界 | 正常嵌入的距离阈值区域 |
| Kill-chain coverage | 攻击链阶段覆盖 | 不等于阶段顺序或边级正确性 |
| Missing-step hypothesis | 缺失步骤假设 | 必须和观测证据分层 |

## 8. 优点

- 将检测和调查放到一个端到端系统框架中，并报告计算成本。
- 利用良性参照和身份错配增强异常解释，比纯黑盒异常分数更易分析。
- 对多个大规模 DARPA provenance 数据集给出 TP/FP/FN，可重新审计指标。
- 智能体角色分工清晰，适合作为 agentic investigation baseline。

## 9. 局限

- 检测 precision 在多个场景不足 1%-1.5%，远未达到“高保真告警”的通常含义。
- 依赖干净良性初始化、可信审计和不可变日志，现实中可能被污染或绕过。
- 每天默认单一 campaign，难以处理并发或跨日攻击活动。
- 固定 kill chain 对非线性、循环和环境特定攻击路径较僵硬。
- 调查实验只覆盖部分数据和两个模型，缺少 retrieval/agent loop 充分消融。
- 缺失步骤由 LLM 假设，未对 hallucination、证据蕴含和错误传播做独立评测。
- 无独立流量子图、跨源关系、冲突状态和 packet/log raw replay。

## 10. 对我选题的启发

- 本支线不能以“GNN 检测 + LLM agent 报告”作为核心，要把贡献前移到双源事件图与跨源关系质量。
- 实验必须报告 precision、alerts/day、analyst burden，而不是只报告相对 FP 降幅或 IOC 增长。
- LLM 只能对已验证联合图生成结论；缺失步骤必须进入 `hypothesis` 层，并允许拒答。
- 原始 packet frame 与 log record 锚点可以为每条生成结论提供可回放证据，补足 ProvAgent 的评价空白。

## 11. 可转化的研究问题

1. traffic-log 联合证据能否在固定 recall 下显著提高 provenance detector 的 precision 并降低 alerts/day？
2. 将 LLM 缺失步骤与观测边分层，能否提高 claim entailment 并降低 unsupported claim rate？
3. 在并发/跨日 campaign 中，带跨源边不确定性的联合图能否优于单日单 campaign 假设？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| SAURONEYES | 都从审计图检测攻击；SAURONEYES 做边级检测和社区分链，ProvAgent 后接多智能体调查 |
| Clouseau | 都用多智能体生成 SOC 调查结果；ProvAgent 以 provenance detector 输出为起点 |
| ANTEATER | 都是 audit provenance + LLM agents；ProvAgent 更强调身份行为检测 |
| HunterAgent | HunterAgent 有确定性验证和证据不足终止；ProvAgent 更容易将缺失阶段转为叙事假设 |
| Project03 支线 | 可作为日志检测和 agent 报告 baseline，但不覆盖独立 PCAP 图、跨源校准和证据回放 |

## 13. 论文写作可引用句式

- 已有系统把基于身份-行为画像的 provenance 异常检测与多智能体 IOC 扩展和 kill-chain 报告结合起来，但其绝对告警精度仍较低，且调查质量主要以 IOC 数量和阶段覆盖衡量，缺少链边与证据蕴含真值。

## 14. 我的批注与疑问

- 论文使用“high-fidelity alerts”措辞，但由公开 TP/FP 计算出的 precision 多数不足 1%，引用时必须呈现绝对值。
- IOC 数增长可能同时增加正确线索与幻觉，未见人工逐条验证比例。
- “每个检测日一个 campaign”的假设与真实并发攻击差距较大。
- 若边聚合后不保留原始 record anchors，会削弱审计与取证可用性。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：3.5/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是（作为 provenance + multi-agent investigation 的最新红线和反例）
