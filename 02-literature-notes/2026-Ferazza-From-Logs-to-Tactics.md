# From Logs to Tactics: Unsupervised Reconstruction of APT Campaigns with MITRE-Enriched Meta-Alerts

## 1. 基本信息

- 中文译名：从日志到战术：使用 MITRE 增强元告警进行 APT 活动无监督重构
- 作者：Francesco Ferazza; Cosimo Melella; Konstantinos Mersinas; Ricardo Lugo; Rain Ottis
- 年份：2026
- 来源：International Journal of Information Security, Vol. 25, Article 79
- DOI：https://doi.org/10.1007/s10207-026-01254-w
- 阅读状态：`full-read`
- 阅读日期：2026-07-13
- 所属主题：Heterogeneous Logs / GNN / LLM Summarization / ATT&CK / Campaign Reconstruction

## 2. 一句话总结

该文把 Linux syslog 与 SentinelOne EDR 等异构告警规范化为日志节点图，用图自编码器提取事件序列、GPT-3.5 生成行为摘要、S-BERT/HDBSCAN 聚合元告警，再以 ontology+ATT&CK-BERT 混合映射和时间/主机/战术规则重构跨主机 campaign；它占据了“异构日志图 + LLM + ATT&CK + 攻击链”的组合，但没有独立原始 PCAP 线、来源保持的跨源证据边和边级校准。

## 3. 研究问题

- 无标签、格式异构且噪声很高的 SOC 告警如何形成连贯事件序列？
- 如何把数百条低层告警压缩成少量可解释、带 ATT&CK 语义的元告警？
- 如何在时间、主机和 tactic 三个维度上把元告警连接成多阶段 APT campaign？

## 4. 核心贡献

1. 设计从规范化、图序列提取、LLM 摘要、语义聚类到 ATT&CK 映射和 campaign 关联的模块化流水线。
2. 用 GAE/GCN 替代 PID 窗口和 session chunking，提升事件序列内部凝聚度并减少碎片化。
3. 用 S-BERT+HDBSCAN 形成高层元告警，显著降低分析员面向的告警量。
4. 融合符号 ontology 与 ATT&CK-BERT 语义分类，处理两者冲突并输出置信度。
5. 在 NATO CCDCOE Crossed Swords 2024 数据和红队事后报告上评价链重构。

## 5. 方法框架

- 规范化：syslog 用正则抽取核心语义，SentinelOne JSON 做 schema 映射，时间统一为 UTC。
- 图构建：节点为日志/告警记录；边由 PID、host ID 和时间邻近建立。
- 图编码：两层 GCN 图自编码器重构邻接矩阵，训练后以 connected components 形成候选事件序列。
- 摘要：GPT-3.5-turbo、固定零样本模板、temperature=0，把序列转为 MITRE 兼容行为叙述。
- 聚类：S-BERT 嵌入 + HDBSCAN，把相近序列聚为 meta-alert；TF-IDF+DBSCAN 为基线。
- ATT&CK：符号本体匹配与 45-technique ATT&CK-BERT 的置信度仲裁；共同命中最高，单模型高置信命中可接受，冲突取规范化置信度更高者。
- 链关联：meta-alert 需满足 tactic 合法转移、时间邻近和 host/subnet/user 关联。
- 阈值：跨主机 24 小时、同主机快速序列 5 分钟、同 IP/hostname/user 或同 `/24`。

## 6. 数据集与实验

- XS24 Linux syslog：来自 auditd、snoopy 等生成器，基本无标签且缺少稳定 IOC。
- SentinelOne EDR：925 条经过可复现筛选的高质量告警。
- 图规模：约 925 nodes、3200 edges；同主机时间边阈值 300 秒。
- GAE：hidden 64、latent 32、Adam、lr 0.01、200 epochs；1:1 负采样。
- 图序列内部 cosine cohesion：0.72，对比启发式 0.49；平均序列长度增加 43%。
- 聚类：925 alerts -> 20 meta-alerts，25 条作为噪声，分析项减少约 97.8%；Silhouette 0.81，对比 TF-IDF+DBSCAN 的 0.48。
- ATT&CK 映射：symbolic-only F1 0.68、semantic-only 0.73、hybrid 0.87；Precision@3 0.91；标注者 Fleiss' kappa 0.79。
- campaign：与 12 个红队事后报告比较，要求 technique Jaccard、tactic 顺序及 host 重合；Precision 0.71、Recall 0.66、F1 0.68；两名专家认为 10/12 捕获了高层意图与顺序。

## 7. 关键知识点

- 该文的图是 `log-entry graph`，不是进程/文件/socket 组成的 provenance graph。
- GNN 负责序列凝聚，LLM 只负责把序列转成语义摘要；最终 campaign 仍由显式规则关联。
- 混合 ATT&CK 映射已有置信度冲突仲裁，但这是模型输出冲突，不是 packet-log 证据边冲突。
- “高层意图”来自专家对 campaign 摘要的定性判断，没有独立目标意图标签集。
- 结构指标、映射指标和 campaign 指标被分开评价，是本支线实验设计应借鉴的优点。

## 8. 优点

- 2026 年开放获取正式期刊，方法、阈值、消融和标注协议较完整。
- 使用真实演习中的噪声、异构和跨主机数据，不是清洗后的理想数据。
- campaign 给出独立 Precision/Recall/F1，而非只展示一个 LLM 案例。
- 符号+语义映射的混合设计具有清楚、可复现的功能贡献。
- 把告警压缩量、语义映射和链重构三层评价分开，结论边界较严谨。

## 9. 局限

- 输入仍是 syslog/EDR 告警，没有独立原始 PCAP 或 packet-level evidence。
- 图边由 PID、host 和时间阈值确定，未学习或校准关系概率，也不保留多候选边状态。
- GPT 摘要的事实一致性和 prompt 变体稳定性没有正式评价，错误会传播到聚类与映射。
- campaign 规则依赖预定义 tactic 转移和固定时间窗，面对并发/非标准 tactic 顺序可能失效。
- 关键 NATO 数据不公开，只提供匿名样例与伪代码，外部复现受限。
- “关键告警未丢失”的定义使用系统自身 ATT&CK 置信度大于 0.5，存在循环评价风险。
- 人因评价样本规模较小，且高层意图判断是定性结果。

## 10. 对我选题的启示

- 图构建与双线贡献都可以纳入，但必须明确区别于日志节点图和规则时间边。
- 该文适合作为 log-only graph+LLM+chain 强基线；Project03 支线的差异是独立 PCAP observation、原始证据锚点和校准跨源边。
- 可复用其分层评价：图关联/序列、ATT&CK 映射、campaign、最终意图分别评价。
- 可把 ontology+semantic 的冲突仲裁迁移到 relation verifier，但需要用 ECE/Brier/可靠性图做真正校准。

## 11. 可转化的研究问题

1. packet-log 事件关系图能否比 PID/host/time 图提高 campaign F1，尤其在时钟漂移和多 campaign 下？
2. LLM 摘要若附带 packet/log 证据 ID，能否降低摘要错误向 ATT&CK 与 campaign 层的传播？
3. 结构关系置信度与 ATT&CK 映射置信度如何联合传播到意图候选和拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| MuSAR | 都从多源日志重构跨主机链；MuSAR 形成实体事件图，本文形成日志节点序列与 meta-alert |
| APTGuard | 都将阶段/序列交给 LLM；APTGuard 有 PCAP+auditd，但无图和链级评价 |
| Traffic2Chain | 后者流量侧直接映射技术并生成链；本文是日志/EDR 侧完整流水线 |
| TechniqueRAG | 都做 ATT&CK 映射；本文的 ontology+BERT 混合映射可作强分类基线 |
| Project03 支线 | 直接堵住“日志图+LLM+ATT&CK+链”宽泛创新，保留 raw dual-source evidence graph 空位 |

## 13. 论文写作可引用句式

2026 年研究已将异构 syslog/EDR 规范化、图自编码序列提取、LLM 摘要、语义聚类与 ATT&CK 混合映射集成为跨主机 campaign 重构流水线，并报告链级 F1；但图边仍由 PID、主机和时间阈值确定，尚未覆盖原始 PCAP 与主机日志之间可校准、可回放的证据关系。

## 14. 我的批注与疑问

- `fully unsupervised` 只适用于前端聚类/序列；ATT&CK-BERT 使用 9000 条人工标注语料，系统整体不能简单称完全无监督。
- `no critical events lost` 使用自身 mapping score 定义 critical，应在引用时加限定。
- campaign F1 0.68 表明从高质量 mapping 到完整链仍有明显误差，正好支撑链级不确定性研究。
- 数据保密会阻碍严格复现，建议本支线用公开数据做主结果、Project03/CENI 真实数据只做外部案例。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3/5
- 硕士论文基础价值：5/5
- 是否进入核心文献：是，最高优先级 log-only 直接撞题与实验基线
