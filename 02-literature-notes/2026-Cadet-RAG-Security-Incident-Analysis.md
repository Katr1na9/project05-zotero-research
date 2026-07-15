# Retrieval-Augmented LLMs for Security Incident Analysis

## 1. 基本信息

- 中文译名：用于安全事件分析的检索增强大语言模型
- 作者：Cadet et al.
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2603.18196
- Zotero key：BY7IXNF9（PDF：CTPBNPN9）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Multisource Logs / RAG / Incident Reconstruction

## 2. 一句话总结

该文先用 ATT&CK 关联的规则查询压缩 Security Onion、网络和认证日志，再以向量 RAG 让 LLM 回答取证问题并重构攻击步骤。它已经覆盖多源日志加 LLM 链式叙事，但关联停留在聚合 chunk 和文件级引用，尚无显式事件证据图、原始记录级主张绑定、意图候选与组织归因。

## 3. 研究问题

- 海量多源日志超出上下文窗口时，如何让 LLM 找到感染主机、C2、入口并恢复攻击步骤？
- 如何评估跨多个检索块的集合型取证问题和攻击步骤完整性？

## 4. 核心贡献

1. ATT&CK 查询库驱动的日志过滤和聚合。
2. 语义 chunk + FAISS top-k RAG 的跨源证据合成。
3. 17 个恶意流量场景和一个 AD 红蓝对抗事件的系统评测。
4. 引入结构 recall、多 chunk 引用率、步骤 P/R 和成本比较。

## 5. 方法框架

```text
SIEM logs
  -> predefined ATT&CK queries
  -> Elasticsearch filtering/aggregation
  -> semantic chunks
  -> embedding + FAISS top-k (default k=7)
  -> LLM forensic QA / attack-step reconstruction
  -> report + cited chunk files
```

- 共享 IP、账号、主机名、时间和证书用于关联，但没有物化成节点/边。
- `CITED CHUNKS` 只能回到聚合 JSON，不能稳定回到包号或 Windows Event Record ID。

## 6. 数据集与实验

- 17 个恶意流量场景：321 MB PCAP、94,948 条 Security Onion 事件、129 个问题、218 个参考指标。
- AD 场景包含网络监测与 Windows/认证事件，是更明确的双源融合；其他场景多为同一流量的 Suricata/Zeek 派生视图。
- 17 场景平均 recall：Claude Sonnet 4 为 94%，DeepSeek V3 89%，Llama 3.1:70B 81%，其余约 64%--71%。
- 42 个跨 chunk 集合问题：Claude 结构 recall 89%、多 chunk 引用率 95%；DeepSeek 78%/88%。
- `k=1` 到 `k=7` 时 Claude recall 从 39% 升至 94%，`k=14` 无新增且多数模型下降。
- AD 攻击步骤：Claude/DeepSeek recall 均 96%，报告步骤 precision 100%。
- DeepSeek 每次约 0.008 美元、89% recall；Claude 0.12 美元、94%。

## 7. 关键知识点

- RAG 召回、跨块合成和因果叙事必须分开评价。
- 规则查询库提高精度但限制未知攻击泛化。
- 文件级 chunk 引用不是主张级 provenance。

## 8. 优点

- 问题、答案和多源上下文均接近真实调查流程。
- 对 no-RAG、单源、top-k 和多模型做了系统消融。
- 同时报告性能、结构完整性和成本。

## 9. 局限

- 查询库针对已知攻击迭代开发；覆盖率决定检测上限。
- 聚合 top-N、字符限制和时间窗会丢证据。
- AD 只有一个受控场景，因果叙事缺少独立边级验证。
- 无事件图、原始记录坐标、意图候选、行为体归因和校准。

## 10. 对我选题的启发

- 它应成为“文本 chunk RAG”强基线。
- 本课题差异必须是显式图关系、逐步骤最小证据集、反证/冲突边和原始记录回指。
- 可复用其结构 recall、引用率、单源/no-RAG 消融和费用评估。

## 11. 可转化的研究问题

1. Graph retrieval 是否比 chunk RAG 更准确恢复跨源链边？
2. 强制每一步绑定包/日志 ID 能否降低无依据因果叙事？
3. 在未知查询模式下，事件图检索能否减少对人工 ATT&CK 查询库的依赖？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| PROVSEEK | 后者以 node/edge ID 做 verification-first 调查 |
| OCR-APT | 后者在审计 provenance 子图上生成攻击故事 |
| HunterAgent | 后者处理日志缺失和反取证，用验证器区分证据/线索 |

## 13. 论文写作可引用句式

- 多源 RAG 能显著提升跨日志事件的取证召回，但聚合块引用仍不足以证明每条攻击步骤的原始证据支持关系。

## 14. 我的批注与疑问

- 需要复查其查询库能否移植到 Project03 HFish/PCAP 字段。
- “报告步骤 precision 100%”不等于因果边和主张级证据均正确。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
