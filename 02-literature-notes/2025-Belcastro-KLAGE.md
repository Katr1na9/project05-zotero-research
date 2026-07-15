# Enhancing Network Security Using Knowledge Graphs and Large Language Models for Explainable Threat Detection

## 1. 基本信息

- 系统名：KLAGE
- 中文译名：利用知识图谱与大语言模型增强可解释网络威胁检测
- 作者：Loris Belcastro; Carmine Carlucci; Cristian Cosentino; Pietro Liò; Fabrizio Marozzo
- 年份：2025 online / 2026 volume
- Venue：Future Generation Computer Systems, 176, 108160
- DOI：https://doi.org/10.1016/j.future.2025.108160
- 阅读状态：`extended-publisher-read`（开放出版商 HTML 含方法与结果；PDF 下载受限）
- 阅读日期：2026-07-13
- 所属主题：Traffic Graph / Graph-BERT / XAI / LLM Report

## 2. 一句话总结

KLAGE 把 PCAP 聚合流转成通信知识图谱，以 Graph-BERT 分类、LIME 解释、图剪枝和 LLM 生成报告，已覆盖“流量建图 + LLM 解释”这一宽泛组合；但它的图是流量通信/分类图，不是流量与日志双侧事件证据图，也没有攻击链、意图或原始记录级证据忠实度评价。

## 3. 研究问题

- 如何用图结构表达网络通信及威胁上下文？
- 如何解释 Graph-BERT 的节点级威胁分类？
- 如何把图分类与 XAI 结果转成分析员可读报告？

## 4. 核心贡献

1. PCAP/流量日志到单流 KG，再合并为统一 KG。
2. 用 Graph-BERT 对统一图做威胁分类。
3. 用 LIME 生成局部特征解释并剪除无关节点。
4. 比较基础、中间和高级结构化提示的 LLM 报告质量。

## 5. 方法框架

- PCAP 由 Wireshark/tcpdump 获取，再按五元组聚合为 flow。
- 每个 flow 构成一个 KG；节点由端口标识，并携带包数、数据量与攻击属性。
- `E_connected(source,destination)` 表示通信，`E_caused(attack,source)` 表示检测到的攻击与来源。
- 单图合并为统一图，Graph-BERT 输出节点威胁类别。
- LIME 对实例特征做扰动并输出 JSON 解释；图剪枝后交给 LLM 生成报告。

## 6. 数据集与实验

- 任务包含 DDoS、ARP poisoning、Nmap reconnaissance 等网络攻击。
- Graph-BERT 分类准确率 84.11%，比报告的基线高 5% 以上。
- 报告评价包含 LLM-as-a-judge 与 10 名专家、5 类攻击的人工审阅。
- 高级提示版本在准确性、技术深度和清晰度上总体最好；专家偏好约为 GPT-adv 60%、GPT-int 33%、GPT-base 7%。

## 7. 关键知识点

- KG 在本文中更接近富属性通信图，而非严格的事件因果/溯源图。
- 将 XAI 特征交给 LLM 能改善报告，但 LIME 的局部代理不保证全局因果解释。
- 节点剪枝有利于可读性，同时可能丢失链级弱信号，需单独评估。

## 8. 优点

- 流量建图、分类、解释和报告形成完整流水线。
- 同时采用自动评价和领域专家评价。
- 出版商标记开放获取，代码组件已公开声明。

## 9. 局限

- 只有流量侧，没有独立日志侧及跨源证据边。
- 节点以端口为核心，难以稳定代表进程、用户、文件和会话实体。
- `E_caused` 建立在既有攻击检测结果上，不是从证据中发现的因果关系。
- 主要目标仍是分类与报告，不是链重构、意图推断或威胁归因。
- 没有 packet index、log record ID、hash、parser version 等审计锚点。
- 报告质量部分依赖 LLM-as-a-judge，缺少证据引用精确率和幻觉率。

## 10. 对我选题的启示

- “流量图 + LLM 报告”已被占据；新工作必须加入真正的双源事件图和链/意图任务。
- Project03 的图谱贡献应把节点从端口提升为 event/entity/evidence 三层，并保留来源与版本。
- KLAGE 可作为 traffic-only graph+LLM baseline。

## 11. 可转化的研究问题

1. 双源事件证据图是否比端口通信 KG 更适合攻击链重构？
2. 图剪枝如何在可读性与 campaign recall 之间取得可量化平衡？
3. LLM 报告能否为每个结论返回 packet/log evidence ID？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Traffic2Chain | 同为 traffic-only；后者进一步输出 ATT&CK 子技术和攻击链 |
| Auto-Prov | 后者从异构日志构建 provenance graph，图语义更接近系统行为 |
| MuSAR | 后者把网络告警和应用日志统一成事件并重构多主机链 |
| Project03 | 可复用 TrafficObservation，并补日志侧与原始证据锚点 |

## 13. 论文写作可引用句式

- 流量知识图谱与大模型报告的组合已用于可解释威胁分类，但现有图结构多围绕通信与分类结果构建，尚不能直接表示来自流量和主机日志的独立证据、跨源冲突及链级因果关系。

## 14. 我的批注与疑问

- 需要从代码核验节点“由端口标识”的实现是否会在多主机/多时间窗口下发生实体碰撞。
- 专家评价样本量较小，且“偏好”不等价于证据真实性。

## 15. 结论评级

- 相关性评分：4.5/5
- 方法可借鉴性：4/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：4.5/5
- 是否进入核心文献：是（traffic-only graph+LLM 直接基线）
