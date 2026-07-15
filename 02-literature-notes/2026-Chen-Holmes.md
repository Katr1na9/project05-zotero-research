# Holmes: An Evidence-Grounded LLM Agent for Auditable DDoS Investigation in Cloud Networks

## 1. 基本信息

- 中文译名：Holmes：面向云网络可审计 DDoS 调查的证据约束 LLM 智能体
- 作者：Haodong Chen; Ziheng Zhang; Jinghui Jiang; Xuanhao Liu; Qiang Su; Qiao Xiang
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2601.14601
- Zotero key：BZW8FDXH（PDF：KTIULXZL）
- 阅读日期：2026-07-13
- 阅读优先级：重点读
- 所属主题：PCAP Forensics / Evidence Grounding / LLM-Agent

## 2. 一句话总结

Holmes 用计数器和 sFlow 触发 DDoS 异常窗口，再把窗口 PCAP 压缩成 Evidence Pack，由 LLM 在封闭证据上完成攻击族/类型判断、引用证据和生成建议。它提供了有价值的流量侧证据契约，但仍是单源、单窗口对象，既非跨源事件图，也未解决高置信误判。

## 3. 研究问题

- 如何兼顾线速监测、按需深度取证和可审计的 DDoS 类型归因？
- “attribution”仅指 DDoS 类型识别，不是攻击源或威胁行为体归因。
- 任务不涉及多阶段 APT 链、攻击意图或组织级归因。

## 4. 核心贡献

1. 三层调查管线：接口计数器、sFlow 分流、预算化 PCAP 深度分析。
2. Evidence Pack：集中保存包/流结构特征、payload 摘录和 hexdump。
3. Prompt Contract：只允许使用给定证据、强制引用和 JSON schema，并对格式错误自修复。

## 5. 方法框架

### 输入与输出

- 输入：接口计数器、sFlow、时间切片 PCAP；均为网络侧遥测。
- 输出：verdict、attack family/type、analysis trace、2--6 条证据、置信度和响应建议。
- 文中的 audit log 是 Holmes 自身运行日志，不是独立系统/应用日志模态。

### 方法流程

```text
counter anomaly
  -> sFlow triage and victim/protocol localization
  -> budgeted tshark on PCAP slice
  -> Evidence Pack
  -> OpenPangu-7B Detective
  -> evidence-cited JSON report
```

Evidence Pack 包含主流量簇、代表包、`udp.length` 模式、TCP flag、ASCII 比例、Shannon entropy、ASCII/hexdump。LangGraph 仅是控制状态机，不是事件证据图。

## 6. 数据集与实验

- 数据：CICDDoS2019 的 DNS、NetBIOS、SNMP、LDAP、MSSQL、SSDP、NTP，加脚本生成 UDP/SYN/ACK Flood。
- 一次完整运行 15 分钟；正文没有报告标准基线、精确率/召回率/F1、误报率、时延或消融。
- Table 2 的 10 个代表窗口按表计数为 6 个匹配、4 个误判，这是精读复算而非作者报告的总体准确率。
- 4 个误判置信度均较高，均值约 0.92，高于正确项约 0.87；说明“引用证据”不等于结论正确或置信度校准。

## 7. 关键知识点

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Evidence Pack | 证据包 | 结构化事件窗口对象，不是图 |
| Quote Rule | 引用规则 | 保证引用子串，不保证语义蕴含 |
| protocol-gated reasoning | 协议门控推理 | 先攻击族、后协议类型 |

- 可引用性、正确性和校准是三个独立评价维度。
- 网络侧证据应保留 `pcap/frame/timestamp/field/byte offset`，而不是只保留摘要字符串。

## 8. 优点

- 确定性监测与昂贵 LLM 分析解耦。
- 证据包、结构输出和封闭世界提示词便于审计。
- 明确保存分析轨迹和证据摘录。

## 9. 局限

- 重放/脚本环境，缺少真实良性噪声、混合攻击和未知变体。
- 代表采样可漏掉低频关键包；没有稳定 packet/frame ID 的主张级回指。
- 高置信误判突出，论文没有 ECE/Brier/拒答评测。
- 无日志侧、跨窗口关系、事件图、攻击链或意图候选。

## 10. 对我选题的启发

- 可把 Evidence Pack 升级为网络侧证据适配器，每项特征同时保存原始包坐标。
- 日志侧建立对称证据适配器，再通过实体、时间、会话和进程关系合并到统一事件图。
- 让 LLM 输出每个阶段/意图候选的支持路径与反证，而不只引用摘要子串。

## 11. 可转化的研究问题

1. 主张级原始证据锚点能否降低“有引用但高置信错误”的比例？
2. 双源事件图能否补足单个 DDoS/流量窗口看不到的主机执行和持久化证据？
3. 如何把数据缺失、证据冲突和未知类型传播为可校准拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| CyberSleuth | 都从 PCAP 生成调查结论；Holmes 的证据契约更强、任务更窄 |
| HunterAgent | 后者把证据与推断分层并使用物理标识验证 |
| PROVSEEK | 后者强制报告主张绑定 provenance node/edge ID |

## 13. 论文写作可引用句式

- 证据引用约束能够提升输出可审查性，但不能替代结论正确性和置信度校准。
- 单窗口证据包是可复用接口，却不足以表达跨源、跨阶段的事件关系。

## 14. 我的批注与疑问

- 需避免把系统自己的 audit trail 误写成第二现场观测源。
- 论文最值得借的是证据契约，不是其 DDoS 分类结果。

## 15. 结论评级

- 相关性评分：4/5
- 方法可借鉴性：4.5/5
- 实验可复现性：2.5/5
- 作为硕士论文基础价值：4/5
- 是否进入核心文献：是
