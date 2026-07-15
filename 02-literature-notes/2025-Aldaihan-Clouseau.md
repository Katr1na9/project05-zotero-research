# Clouseau: A Hierarchical Multi-Agent Approach for Autonomous Attack Investigation

## 1. 基本信息

- 中文译名：Clouseau：面向自主攻击调查的分层多智能体方法
- 作者：Abdullah Aldaihan; Fahad Alotaibi; Sergio Maffeis
- 年份：2025
- Venue：2025 Annual Computer Security Applications Conference (ACSAC)
- DOI：https://doi.org/10.1109/ACSAC67867.2025.00051
- 论文：https://www.acsac.org/2025/files/web/acsac2025-234-aldaihan.pdf
- 代码：https://github.com/ICL-ml4csec/Clouseau
- 阅读日期：2026-07-14
- 阅读优先级：重点读（Agent 附录；意图/目标任务红线）
- 所属主题：LLM Agent / Attack Investigation / Evidence Retrieval / Attack Narrative

## 2. 一句话总结

Clouseau 从一个 Point of Interest 出发，以 Chief Inspector、Investigator 和按数据表划分的 QA agents 分层查询结构化日志，迭代恢复攻击来源、时间线、攻击目标和 Cyber Kill Chain；它证明“LLM 调查系统输出攻击 objectives”已被明确提出，但论文的定量指标实际衡量恶意日志事件检索，而非目标/意图结论本身的正确性或证据忠实度。

## 3. 研究问题

- 如何在不依赖任务微调、预定义调查规则和大规模标注数据的前提下，从单个 POI 自动展开端到端攻击调查？
- 分层、多角色 Agent 是否比单体 LLM 更能控制上下文、SQL 错误和幻觉？
- 系统能否跨 ATLAS 与 OpTC 两种不同环境恢复攻击相关事件和叙事？
- 论文要求输出 attack objectives，但没有把它定义为独立可评分的高层意图任务。

## 4. 核心贡献

1. 提出 Chief Inspector -> Investigator -> source-specific QA 的分层多智能体调查架构。
2. 将原始日志转换为带人工 schema 注释和示例的 SQL 表，以自然语言问题驱动多步证据检索。
3. 从单一 POI 迭代生成调查线索，汇总攻击来源、时间线、目标、制品和 Kill Chain 叙事。
4. 扩展 ATLAS 场景并引入语义间隙、公共云地址与制品重命名，测试关键词敏感性。
5. 将 OpTC 转换为调查 benchmark，跨 21 个场景、3 个 POI 和 3 次重复共执行 63 次调查。

## 5. 方法框架

### 输入

- 初始 POI：可疑域名、IP、进程、文件等。
- 环境上下文：内部地址范围、允许服务、认证策略等站点知识。
- ATLAS：Windows Security、浏览器、DNS 日志。
- OpTC：进程、文件、DNS、HTTP 和进程关联的网络 flow 日志。

### 输出

- 攻击相关进程、文件、地址、域名和日志事件。
- 攻击来源、攻击时间线、攻击 objectives、Cyber Kill Chain 映射与自然语言报告。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| QA Agent | 把自然语言问题分解为 SQL 查询并返回记录 | 可作为冻结证据库上的交互式查询接口 |
| Investigator | 围绕一条 attack lead 前后向、关联式探索 | 可借鉴为候选假设检索，而非核心创新 |
| Chief Inspector | 拆分线索、交叉核对报告并生成最终叙事 | 说明多报告复核可抑制部分幻觉 |
| Query budget | 限制查询数、返回行数与上下文增长 | 是可复用的 LLM 调查安全阀 |

### 方法流程

```text
原始日志 -> 环境相关预处理 -> 结构化 SQL 表
POI + 环境上下文 -> Chief Inspector 生成 attack leads
  -> 多个 Investigator 调用 source-specific QA agents
  -> SQL 证据记录与局部报告
  -> Chief Inspector 交叉检查、继续派生线索
  -> 来源/时间线/objectives/Kill Chain/攻击叙事
```

## 6. 数据集与实验

- ATLAS 原始 10 个场景：4 个单主机场景、6 个多主机场景；作者另构造 4 个 extended 与 4 个 keyword-sensitivity 场景。
- OpTC 选择 3 个攻击场景，每个场景在初始、中间和末期选择 3 个 POI；仅处理初始失陷主机的失陷日数据。
- 评价以最终报告中识别出的攻击制品匹配日志，再在日志事件级计算 Precision、Recall、F1；没有单独评价攻击来源、时间线顺序、objective 或 Kill Chain 正确性。
- ATLAS：单主机 F1 99.79%，多主机 97.37%，扩展单主机 99.79%；均显著高于 ATLAS/AIRTAG 复现基线。
- 重命名场景：Clouseau 在 GPT-4.1-mini、LLaMA-3.3、DeepSeek-V3 上 F1 分别为 99.8%、98.3%、98.3%；单 Agent 分别为 95.8%、89.6%、82.2%。
- OpTC：GPT-4.1-mini Precision 96.0%、Recall 93.6%、F1 94.2%；LLaMA-3.3 F1 69.4%，DeepSeek-V3 F1 83.9%，显示明显模型与隐私-性能权衡。
- 论文以检查 trace 的方式声称单 Agent 更常生成错误 SQL 或虚假链接，但未报告独立的 hallucination rate 或 claim entailment 指标。

## 7. 关键知识点

- “识别攻击目标/objectives”已经是正式会议系统的显式输出，不能作为我们的首次任务贡献。
- 其 objective 只存在于 prompt 和最终报告中，没有独立标签体系、正确率、证据充分性或置信度。
- 事件级 F1 衡量找回了多少恶意日志，不代表攻击链顺序、因果关系或高层目标正确。
- Clouseau 查询结构化日志/flow 表，不从 raw PCAP 构建流量侧观察子图，也不学习跨源关系。
- Chief Inspector 的交叉检查是启发式文本复核，没有显式概率、矛盾图或可校准拒答。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Point of Interest | 调查起点 / 关注点 | 触发调查的可疑实体或事件 |
| Attack lead | 调查线索 | 被派发给 Investigator 的聚焦任务 |
| Attack objective | 攻击目标 | 不等同于已被独立标注和验证的攻击意图 |
| Attack narrative | 攻击叙事 | 对来源、时间线、制品和阶段的自然语言汇总 |

## 8. 优点

- 端到端流程和 Agent 角色职责清楚，代码、prompt 与评价脚本公开。
- 通过 SQL 工具把 LLM 与有限证据记录连接，优于把全量日志直接塞入上下文。
- 有多 POI、跨环境、制品重命名与单 Agent 消融，评价规模在 Agent 调查论文中较扎实。
- 明确讨论幻觉、prompt injection、隐私、延迟和开放权重模型性能差距。

## 9. 局限

- 假设日志采集不可篡改且输入净化已经消除 prompt injection，回避了两个关键安全威胁。
- 依赖环境特定的预处理、人工 schema 注释、few-shot SQL 示例与存储过程，不能称为无专家规则的完整端到端系统。
- 只从既定 POI 开始，POI 的产生、漏报与误报不在系统评价内。
- ATLAS 场景中的核心恶意制品较集中，作者扩展虽增加难度，仍存在合成场景偏差。
- OpTC 只标注初始失陷主机的一天，无法评价完整多主机攻击链。
- 没有原始 packet/log 不可变锚点、跨源边置信度、冲突传播与 claim-to-record entailment。
- 攻击 objective 和 Kill Chain 只有叙事案例，没有独立 benchmark 指标。
- Agent 依赖较昂贵的 LLM 推理，开放模型在 OpTC 上性能显著下降。

## 10. 对我选题的启发

- Agent 应后置为附录或交互层，核心论文贡献仍放在双线证据图、跨源边校准和可信链/意图推理。
- 高层意图任务必须先定义有限、可区分的 goal ontology，并建立 chain-grounded 标注，不能仅在 prompt 中要求“identify objectives”。
- 评价需分四层：事件找回、跨源边、链结构、意图/目标；Clouseau 可作为事件检索和自然语言叙事 baseline。
- 最终每条 LLM claim 都应绑定 evidence graph edge/node 和 raw packet/log anchor，并允许 `INSUFFICIENT_EVIDENCE`，从而补上 Clouseau 未量化的可信性。

## 11. 可转化的研究问题

1. 在相同事件检索 F1 下，带双源证据图约束的 LLM 是否能显著提高攻击链顺序和 objective 的正确性？
2. 当流量与日志证据冲突或缺失时，显式矛盾传播与拒答是否优于 Chief Inspector 的文本交叉检查？
3. claim-to-raw-record 的可回放率与证据蕴含率能否成为攻击调查系统的独立评价指标？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| HunterAgent | 两者均从调查起点迭代检索；HunterAgent 有多候选验证与 `INSUFFICIENT_EVIDENCE`，可信边界更强 |
| PROVSEEK | 后者把生成结论绑定 provenance edge ID；Clouseau 主要绑定查询结果和文本报告 |
| ExCyTIn-Bench | 可用于补充 Clouseau 未独立衡量的调查推理和证据忠实度 |
| APTGuard | 后者为 PCAP+auditd 阶段标签后处理；Clouseau 更强于日志调查，但没有双源建图 |
| Project03 支线 | 划定“LLM 推断 attack objectives”红线，并提供后置 Agent 对照而非核心方法路线 |

## 13. 论文写作可引用句式

- 最新自主调查系统已经能够从单一关注点迭代查询多源遥测，并在报告中给出攻击来源、时间线、目标与 Kill Chain；然而，其主要定量评价仍集中于恶意日志事件检索，高层目标结论的证据充分性、校准和可回放性尚未被单独验证。

## 14. 我的批注与疑问

- `objectives` 在 prompt 中出现，但全文没有 objective taxonomy；这更像报告要求，而非经过形式化定义的新任务。
- “无需 predefined heuristics”需要谨慎引用：系统仍使用环境预处理、schema 注释、查询示例、存储过程、预算与标签传播规则。
- ATLAS 的近满分结果不能直接外推到 raw PCAP + heterogeneous logs；OpTC 上开放模型下降更能反映现实难度。
- 后续候选 idea 不应把多 Agent 数量作为创新；可把 Clouseau 放入 Agent appendix，比较受证据图约束前后的报告忠实度。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是（Agent 附录；攻击目标任务与评价红线）
