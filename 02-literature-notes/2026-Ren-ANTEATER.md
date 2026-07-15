# ANTEATER: A Filter-then-Scrutinize Architecture for End-to-End Attack Investigation

## 1. 基本信息

- 中文译名：ANTEATER：面向端到端攻击调查的“先过滤、后审查”架构
- 作者：Yiming Ren; Haoqiang Wang; Linghao Li; Haoyang Chen; Chengxiang Si; Zhou Zhou; Qingyun Liu
- 年份：2026
- 来源：Proceedings of the ACM on Management of Data, 4(3), Article 135, 1-27
- DOI：https://doi.org/10.1145/3802012
- 阅读状态：`metadata-abstract-only`；正式全文未取得
- 核验日期：2026-07-15
- 所属主题：Audit Logs / Provenance Graph / Multi-Agent Investigation / Attack Report

## 2. 一句话总结

ANTEATER 采用“先过滤、后审查”：先由轻量流式异常模型筛选原始审计日志，再从异常日志构建 provenance graph，由三个 LLM agents 探索攻击子图并生成结构化报告；它直接占据“raw audit logs + provenance graph + 多智能体端到端调查”，但摘要未显示独立流量证据、跨源校准或链/意图的严格评价。

## 3. 研究问题

- 海量长期审计日志如何先压缩到 LLM 可处理范围？
- 如何把传统异常检测输出转化为分析员需要的攻击子图和报告？
- 多智能体协作能否在 provenance graph 上完成端到端攻击调查？

## 4. 核心贡献

1. 提出 filter-then-scrutinize 级联架构。
2. 以轻量 flow-based anomaly model 过滤海量审计日志。
3. 从过滤后的异常日志构建 provenance graph。
4. 以三个 LLM agents 协同探索、重构攻击子图并生成结构化报告。

> 证据边界：以上全部来自 ACM/Crossref 出版元数据和摘要；没有全文时不记录模型结构、数据集、数值或消融结论。

## 5. 方法框架

```text
raw audit logs
  -> lightweight flow-based anomaly filter
  -> anomalous-log provenance graph
  -> three-agent scrutiny
  -> attack subgraph + structured report
```

- `flow-based` 在摘要语境中指流式/流结构异常过滤，不能据此推断其使用独立网络 PCAP。
- provenance graph 由过滤后的审计日志构建，公开摘要未说明 raw packet anchors。

## 6. 数据集与实验

- 摘要确认该工作声称能够处理长期隐蔽攻击并缓解 LLM 成本和上下文限制。
- 未取得全文，因此数据集、基线、定量结果、agent 角色和评价协议全部标记为待核验。
- 本项目不得用该文支持任何具体性能数值。

## 7. 关键知识点

- “异常过滤 -> provenance graph -> 多智能体调查 -> 报告”的完整链路已正式发表。
- 使用 LLM agents 的创新顺位应后移；图质量与证据约束才是可防守的主线。
- 过滤器可能在 LLM 之前不可逆地丢失攻击证据，需要评价 chain recall 与 missing-event robustness。
- 结构化报告是否可信，必须有 claim-to-edge/record 指标，而非只评价可读性。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Filter-then-scrutinize | 先过滤、后审查 | 级联式候选压缩与深度调查 |
| Attack subgraph | 攻击子图 | 需区分观测边和模型假设边 |
| Flow-based anomaly model | 基于事件流的异常模型 | 摘要不足以认定为网络流量模型 |
| Structured report | 结构化调查报告 | 需评价事实支撑度 |

## 8. 优点

- 正式发表于 PACMMOD，研究问题直接面向大规模数据管理与安全调查。
- 架构清楚地解决“全量日志不能直接送入 LLM”的工程瓶颈。
- 输出攻击子图和结构化报告，贴近 SOC 工作流。

## 9. 局限

- 当前只有元数据/摘要，无法独立核验方法细节和性能。
- 从摘要看是 audit-log-only，不是独立 traffic/log 双源证据图。
- 过滤造成的漏检、三智能体的 hallucination、链边正确性和 intent 真值均待核验。
- 未见跨源关系校准、来源冲突、raw replay 和 evidence abstention。

## 10. 对我选题的启发

- agent 只能作为后置增强，不可作为本支线主 novelty。
- 双源图应在过滤前保留 raw anchors，并测量过滤对每条攻击链的证据召回。
- LLM 报告必须绑定联合图节点/边和原始记录，未绑定结论应拒绝或标成假设。

## 11. 可转化的研究问题

1. 先构建 source-preserving 双子图再做筛选，能否比“先过滤再构图”保留更多链证据？
2. cross-source relation uncertainty 能否指导 LLM 上下文选择和停止条件？
3. claim-to-record replay 能否成为比报告可读性更严格的 agent 调查指标？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| ProvAgent | 都是 provenance 检测后接多智能体调查；ANTEATER 更强调级联过滤 |
| Clouseau | 都输出 SOC 调查结果；ANTEATER 显式在 anomaly provenance graph 上探索 |
| KAIROS / DEPCOMM | 可作为其图过滤/压缩阶段的传统非 LLM 对照 |
| Project03 支线 | 是 agent appendix 的强红线，但没有覆盖双源跨源边校准主问题 |

## 13. 论文写作可引用句式

- 2026 年已有正式工作采用“轻量过滤—provenance graph—多智能体审查”架构，从原始审计日志生成攻击子图与结构化报告；这进一步说明仅增加 LLM agents 已不足以构成主要创新。

## 14. 我的批注与疑问

- `flow-based` 的准确含义必须待全文确认，不能翻译成“网络流量检测器”。
- 取得全文后首要复核：过滤召回、攻击子图真值、agent 角色、报告事实性和成本。
- Article 135 与页码 1-27 已由 ACM/Crossref 元数据确认。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：待全文
- 证据可用性：2/5
- 作为硕士论文边界价值：4.5/5
- 是否进入核心文献：agent 附录边界；取得全文前不承担方法细节或定量结论
