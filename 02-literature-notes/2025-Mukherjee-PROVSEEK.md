# LLM-driven Provenance Forensics for Threat Intelligence and Detection

## 1. 基本信息

- 系统名：PROVSEEK
- 中文译名：面向威胁情报与检测的 LLM 驱动溯源取证
- 作者：Kunal Mukherjee; Murat Kantarcioglu
- 年份：2025
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2508.21323
- Zotero key：S92XCGP6（PDF：URNJHP2M）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Provenance Forensics / Verification-first LLM / CTI

## 2. 一句话总结

PROVSEEK 把自然语言或 CTI IOC 转为类型化 provenance 数据库查询，通过 Investigation、Follow-Up 和 Safety Agent 反复检索、验证并生成报告，要求安全主张绑定 node/edge ID。它与“可审计 LLM 调查”高度重合，但事件观测仍是单一审计源，CTI 只是背景文本，不存在 PCAP+日志双源、意图或行为体归因。

## 3. 研究问题

- 如何让分析员以自然语言查询数亿条 provenance 事件，并得到有证据的攻击调查结果？
- 如何用外部工具阻止 LLM 把未验证的进程、文件或 IP 写进结论？

## 4. 核心贡献

1. 类型化 process/file/IP SQL 工具与 CTI IOC 检索。
2. Investigation、Follow-Up、Safety Agent 的 verification-first 闭环。
3. Type-Aware Correlator 将 node/edge ID 连接为局部因果链。
4. 多 DARPA/OpTC 数据集上的检测、RAG 与可扩展性评测。

## 5. 方法框架

- 事件形式：`l=(u,v,r,t)`；目标输出相关日志子集和自然语言总结。
- 背景层：公共 CTI 报告向量库；不是现场第二源，也不是 KG。
- 证据层：PostgreSQL 中 syscall/ETW/Linux Audit provenance；IP/port 是审计字段，不是独立流量源。
- Safety Agent 检查每个 claim 是否有可解析 node/edge ID；Follow-Up Agent 补查证据缺口。

## 6. 数据集与实验

- CADETS、THEIA、CLEARSCOPE 的 E3/E5 加 OpTC，共 7 个数据集。
- contextual precision 0.90--0.93、recall 0.87--0.94、faithfulness 0.88--0.94。
- 检测 F1 为 0.85--0.93；OpTC P/R/F1 为 0.95/0.91/0.93。
- 运行开销约 326K--570K tokens、18--50 分钟。
- 数据库从 4.98GB 到 295.45GB 时，token/时间增至约 1.42/1.63 倍。
- 每库 50 个问题的错误为 3--14 个；仅 CADETS E5 记录 2 个 hallucinated artifacts。

## 7. 关键知识点

- “user intent extraction”是用户查询意图，不是攻击者意图识别。
- 负证据和查询失败也应作为调查结果保存。
- claim-level ID binding 比自然语言引用更接近可审计证据链。

## 8. 优点

- 把 LLM 查询规划与数据库真实性验证分开。
- 明确要求主张绑定稳定节点/边标识。
- 对上下文爆炸、错误类型和扩展性有量化分析。

## 9. 局限

- 依赖完整可信日志，排除日志擦除和针对代理的 prompt injection。
- CTI 实体抽取可能误认命令、文件或进程。
- 无 chain-edge precision、顺序正确率和人工主张审计。
- 无独立 PCAP/flow、跨源冲突、意图或威胁组织归因。

## 10. 对我选题的启发

- Safety Agent 的核心应转化为确定性证据验证器，而不是再让另一个 LLM 自审。
- 统一事件图中的每个 claim 必须携带 packet/log/node/edge anchors。
- 加入 evidence missing/contradicted/verified 三态和拒答。

## 11. 可转化的研究问题

1. PCAP 与日志双源是否能把单源数据库验证扩展为跨源独立验证？
2. 如何评价 claim-level evidence precision、coverage 与 conflict resolution？
3. 对意图候选能否沿证据路径聚合支持与反证，而不是只生成解释？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| HunterAgent | 后者面向反取证缺失证据，验证器更偏物理标识 |
| OCR-APT | 后者从异常子图生成故事，但主张 ID 契约较弱 |
| TracLLM | 后者衡量上下文文本对 LLM 输出的贡献，不验证安全事件因果性 |

## 13. 论文写作可引用句式

- 将每项调查主张绑定到 provenance node/edge ID，是从“可读报告”迈向“可核查报告”的关键步骤。

## 14. 我的批注与疑问

- 表格存在个别 P/R/F1 不自洽，不能直接引用 headline 增益。
- CTI 不应计为第二现场观测模态。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
