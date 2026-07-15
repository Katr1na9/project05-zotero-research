# Fine-tuning Llama3 for Integrated Analysis of Network Packet and System Log Data

## 1. 基本信息

- 系统名：Llama-PcapLog
- 中文译名：面向网络数据包与系统日志联合分析的 Llama3 微调框架
- 作者：Hyun-Min Choi; Youngseok Lee
- 年份：2025
- Venue：The 30th Asia-Pacific Conference on Communications (APCC 2025)
- DOI：https://doi.org/10.34385/proc.97.T3.3.4
- 全文：https://www.ieice.org/publications/proceedings/bin/pdf_link.php?fname=T3-3-4.pdf&iconf=APCC&lang=E&number=T3.3.4&vol=97&year=2025
- 代码：https://github.com/choihyuunmin/Llama-PcapLog
- 阅读状态：`full-read`（6 页会议全文）
- 阅读日期：2026-07-13
- 所属主题：PCAP + Syslog / Instruction Tuning / Joint Analysis

## 2. 一句话总结

Llama-PcapLog 将时间对齐的 PCAP 与 syslog 结构化为 Alpaca 指令样本，再以 GPT-4o 自指令扩增和 LoRA 微调 Llama-3-8B，证明双源数据可提升问答与漏洞分类；但其“融合”发生在文本上下文与答案层，没有显式事件图、跨源证据边、攻击链/意图标签或原始记录级可审计锚点。

## 3. 研究问题

- 单一流量或单一日志分析会遗漏哪些跨层攻击线索？
- 如何在本地部署条件下，让开源 LLM 同时理解 PCAP 与 syslog？
- 少量人工双源样本能否借助 self-instruct 扩展为可微调语料？

## 4. 核心贡献

1. 构建 PCAP 与 syslog 联合输入的指令微调流程。
2. 按时间、会话和共享标识符分组，并用滑动窗口保留上下文。
3. 由 80 个专家复核种子扩增到 20,714 条指令样本。
4. 在 Llama-3-8B 上采用 4-bit 量化和 LoRA，实现本地化分析。
5. 同时评估基础分析、高级分析、漏洞分类与代码生成。

## 5. 方法框架

- 数据预处理：Scapy 提取数据包字段，正则解析 syslog；按时间、会话和共享标识符对齐。
- 数据重构：转为 `{instruction, input, output}` 的 Alpaca JSON 格式。
- 数据扩增：以 GPT-4o 对人工种子做 self-instruct，生成网络包和日志任务。
- 模型训练：Llama-3-8B，LoRA + 4-bit，3 epochs，batch size 1，梯度累积 32，学习率 0.0002。
- 输出任务：问答、威胁解释、漏洞分类、可视化/分析代码生成。

## 6. 数据集与实验

- 数据来源：AIT Log Data Set、公开网络/日志数据、私有服务器日志。
- 种子数据：基础分析 30、高级分析 30、可视化代码 10、漏洞分类 10，共 80 条。
- 扩增数据：network packet 10,391 条，system log 10,243 条，总计 20,714 条。
- 测试集：80 个配对 PCAP/syslog 样本，四类任务各 20 个。
- 训练资源：NVIDIA L40、94 GB RAM、8 核 CPU，约 60 小时。
- 基础分析 F1：0.7506；高级分析 F1：0.7318；漏洞分类 F1：0.9600。
- 代码生成：20/20，Pass@k 1.00，平均延迟约 3.85 秒。

## 7. 关键知识点

- “PCAP + 日志”并不自动等于多模态图融合；本文只是将两个来源并置进同一指令上下文。
- 时间/会话对齐是双源任务成立的前提，但本文没有评估配对错误率。
- self-instruct 可以快速扩充任务表面形式，却可能放大 80 个种子的偏差。
- ROUGE、BLEU、token F1 和 Pass@k 不能替代攻击链、证据忠实度与意图正确率评价。

## 8. 优点

- 直接处理成对 PCAP 与 syslog，是本支线最贴近输入形式的工作之一。
- 给出完整训练配置、任务划分和公开代码入口。
- 本地模型路线符合安全数据隐私和离线部署需求。

## 9. 局限

- 未构建事件级图谱，也没有跨源边的真假标注。
- 20,714 条扩增样本按来源分成 packet-based 与 log-based，未证明每条都包含真正的双源因果关系。
- 测试集仅 80 条，且与人工种子规模相同，训练/测试独立性与场景泄漏风险需核验。
- 没有 traffic-only、log-only、joint 三组严格消融。
- 未评估 ATT&CK 技术、攻击阶段、攻击链、意图、归因或原始证据回指。
- 作者承认扩展训练出现过拟合，持续重训成本较高。

## 10. 对我选题的启示

- “直接把双源文本喂给 LLM”已经有人做过，不能作为主创新。
- Project03 应将 TrafficObservation 与 LogObservation 先形成可审计事件图，再让 LLM 在受约束图上做链与意图推理。
- 实验必须加入 source ablation、pairing noise、time drift、missing source 和 evidence replay。

## 11. 可转化的研究问题

1. 事件图融合是否比双源文本拼接更能提升跨场景攻击链恢复？
2. 跨源边置信度和原始 packet/log 锚点能否降低 LLM 的无证据推断？
3. 当两侧证据冲突或缺失时，模型能否校准置信度并拒答？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| Two-stage multi-datasource ML | 同为同步双源/多源；后者做决策级投票，本文做 LLM 上下文级联合输入 |
| MuSAR | 同为流量/日志关联；MuSAR进一步构造事件与攻击链，但关联主要靠规则和启发式 |
| Traffic2Chain | 后者在流量侧完成 ATT&CK 标注与链重构，但没有日志侧独立证据 |
| Project03 | 可提供更细粒度 TrafficObservation 与可回放 PCAP 锚点 |

## 13. 论文写作可引用句式

- 现有研究已通过指令微调证明时间对齐的 PCAP 与系统日志能够改善本地大模型的安全问答和分类性能，但双源记录之间的事件关系仍被隐式压缩在文本上下文中，尚未形成可验证的跨源证据边和链级推理对象。

## 14. 我的批注与疑问

- 表 I 将扩增样本拆成 packet-based 与 log-based，两者是否真正成对需要检查代码和数据。
- “preserve causality”主要依靠时间/标识符窗口，不等价于因果边真值。
- 专家“人工验证”20k 样本的流程、人数和一致性没有充分报告。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4/5
- 实验可复现性：3.5/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（双源 LLM 直接基线）
