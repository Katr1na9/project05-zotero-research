# Comprehensive Analysis of Provenance-Based APT Detection: An Evaluation-First Modeling Perspective

## 1. 基本信息

- 中文译名：基于溯源的 APT 检测综合分析：评测优先的建模视角
- 作者：Mustafa Ipekbayrak; Zeynep Gurkas-Aydin
- 年份：2026
- Venue：Journal of Mathematical Sciences and Modelling, 9(1), 13-26
- DOI：https://doi.org/10.33187/jmsm.1825484
- 阅读日期：2026-07-13
- 阅读优先级：重点读
- 所属主题：Evaluation / Provenance APT Survey / Campaign Recall

## 2. 一句话总结

该综述编码了截至 2025-10-20 的 76 篇 provenance APT 论文，指出 alert unit、evaluation unit、阶段覆盖和运行指标普遍报告不足，并提出以可观测阶段为分母的 Campaign Recall；它不是高等级新颖性证据，但为本项目设计多粒度、显式分母和缺失证据 stress test 提供了直接评测框架。

## 3. 研究问题

- provenance APT 系统在何种单位上分析、评价和向 SOC 发出告警？
- 现有指标能否表达一个多阶段 campaign 被覆盖了多少？
- 哪些数据集、方法和报告缺口阻碍横向比较与 operational interpretation？

## 4. 核心贡献

1. 对 76 篇 2017-2025 provenance APT 工作编码 55 个字段。
2. 区分 Node、Subgraph、Graph 三种 evaluation/alert units。
3. 统一为八阶段 ATT&CK-aligned taxonomy。
4. 提出 Campaign Recall `CR=k/N`，分母来自场景中可观测阶段集合。
5. 给出数据集-指标兼容性、泄漏检查和最小报告建议。

## 5. 方法框架

- Google Scholar 查询 `APT AND provenance` 得到 160 条，全文筛至 76 篇 peer-reviewed work。
- 纳入 host/whole-system provenance 且有自动化 detection/hunting/triage/reconstruction 输出的研究；排除纯网络检测。
- 对缺失字段显式记 NA；alert unit 相关统计只在可映射的 36 篇上进行。
- CR 对每个 observable stage 只计一次是否至少命中，不衡量同阶段内事件/边完整度。

## 6. 数据与结果

- 55/76（72.4%）使用 anomaly-based ML；48/76（63.2%）只做 offline evaluation。
- 66/76（86.8%）是 single-host，cross-host 仅 10 篇。
- 40/76（52.6%）没有可映射的 alert unit。
- 同时报告 evaluation 与 alert unit 的映射中，仅 29/70（41.4%）处于同一粒度。
- 只有 8 篇输出 attributed edges；TTFD 仅 2 篇，campaign precision 3 篇，case recall 2 篇。
- 常见局限为 dataset bias、false positives、logging gaps；端到端 tamper testing 仅 1 篇。

## 7. 关键知识点

- 节点级 AUC/F1 不应直接支持“攻击链已恢复”或“campaign 已理解”。
- 评价单位、告警单位和最终调查结论单位必须分开报告，并给出单位转换规则。
- CR 适合衡量阶段广度，但还需链边 precision/recall、evidence coverage 和时序正确性。
- 不完整证据场景应做 controlled dropout、tamper/integrity perturbation 与明确分母。

## 8. 优点

- 明确指出 granularity mismatch，是本项目评测设计的直接依据。
- 用 `k/N` 强制阶段覆盖声明给出可观测分母。
- 强调 alert volume、latency、throughput、peak memory 等 SOC 指标。

## 9. 局限

- 检索源主要是单一 Google Scholar 查询，系统综述完整性有限。
- 期刊影响力和综述方法透明度不足，不能单独用来证明 novelty。
- 仅覆盖到 2025-10-20，不含 2026 的 Auto-Prov、StageFinder、FuseChain、Sentient、Minos 等。
- CR 对每阶段只需一个正确项，可能高估链恢复质量。
- 网络侧纯检测被排除，因此不能覆盖本项目 PCAP+日志双线全景。

## 10. 对我选题的启发

- 最终实验矩阵必须同时报告 record/edge/subgraph/campaign 四级结果。
- 引入 `observable-stage CR`，并补充 `chain-edge F1`、`evidence-anchor precision` 和 `intent calibration/abstention`。
- 将 source dropout、time drift、tampering、NAT/shared-IP 设为核心 stress tests。

## 11. 可转化的研究问题

1. 双源证据图能否在不增加 analyst alert volume 的条件下提高 Campaign Recall？
2. evaluation-alert unit 转换中损失了多少证据和错误？
3. logging/traffic dropout 下，证据覆盖与结论置信度是否保持校准？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| KAIROS/StageFinder/Sentient | 都可能用节点/图指标支持更高层结论；需按 unit 重审 |
| FuseChain/SynthChain | 提供阶段覆盖和源预算实验，可结合 CR |
| TracLLM | 可补充模型依赖追踪，但不替代真实 evidence-edge 评价 |

## 13. 论文写作可引用句式

- provenance APT 研究常在节点级评价模型、在图或攻击活动级输出结论，而单位转换缺乏明确规则；因此，多源调查系统必须同时报告证据边、子图与 campaign 粒度的结果。

## 14. 我的批注与疑问

- CR 需要与 stage precision 配套，否则每阶段命中一个点即可获得高分。
- 本项目不应复制其八阶段映射后默认所有数据可观测；分母必须由每个 scenario 的 sensor visibility 决定。
- 该文适合支撑实验规范，不适合作为“无人做过”的证据。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是（评价方法补充，不承担 novelty 结论）
