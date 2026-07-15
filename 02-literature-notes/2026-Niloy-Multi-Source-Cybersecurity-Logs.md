# Multi-Source Cybersecurity Logs: An ATT&CK-Labeled Dataset and SLM Evaluation

## 1. 基本信息

- 中文译名：多源网络安全日志：ATT&CK 标注数据集与小语言模型评测
- 作者：Niloy et al.
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2606.18190
- Zotero key：Z83KC3QY（PDF：26AC5SH8）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Multisource Dataset / ATT&CK Labeling / SLM

## 2. 一句话总结

该文同步采集 PCAP、Windows 系统日志和浏览器活动，形成 870 个会话、约 230 万事件并逐事件映射 ATT&CK，再用三个 SLM 做窗口级检测和技术警报生成。它是本课题很强的数据与标注基础，但没有统一事件图、跨源因果边、攻击链重构或主张级原始证据谱系。

## 3. 研究问题

- 能否构建同步、多源、逐事件 ATT&CK 标注的数据集？
- LoRA 微调的小模型能否从短事件块识别可疑活动和技术？
- 任务仍是 chunk 分类/生成，不是跨会话攻击链、意图或行为体归因。

## 4. 核心贡献

1. 三源同步：完整 PCAP、Sysmon/Windows Event、ActivityWatch 浏览器活动。
2. 870 个固定 20 分钟会话，70 个攻击、800 个正常，约 290 小时。
3. 覆盖 12 tactics、53 techniques 的逐事件 ATT&CK 标注。
4. Qwen2.5-1.5B、Llama-3.2-3B、Phi-4-Mini 的 LoRA 基线。

## 5. 方法框架

```text
PCAP + Windows logs + browser activity
  -> JSON conversion and time normalization
  -> PII anonymization and unified fields
  -> event-level ATT&CK annotation
  -> chronological chunks of 7 events
  -> SLM normal/suspicious classification + structured alert
```

- chunk 是有序列表，不是事件图。
- ATT&CK 是标签体系，不是参与推理的背景知识图谱。
- 输出能提及字段，但没有稳定连接回原始 packet/event record ID。

## 6. 数据集与实验

- 数据采集期：2025-01 至 2026-02；系统/网络/浏览器事件约占 78%/17%/4%。
- 约 112,726 chunks；原 train/validation/test 为 89,693/12,427/10,606，过滤/抽样后训练/验证 22,896/3,065。
- 微调后准确率：Llama 0.928、Phi 0.970、Qwen 0.899；基座模型约 0.07--0.08。
- Phi exact match 0.416、partial match 0.931、word-F1 0.930。
- Llama 对少数 suspicious 类检出率仅 39.5%，Phi 97.0%，Qwen 85.8%。

## 7. 关键知识点

- 多源“同时存在”不等于已完成实体关联和因果融合。
- 切分必须按 session/host/time 隔离；随机 chunk 切分可能让同一会话泄漏到训练和测试。
- ATT&CK exact match 不能独立证明警报语义或攻击链正确。

## 8. 优点

- 与本课题最匹配的同步流量+日志公开数据方向。
- 攻击工具、正常会话、浏览器上下文和 ATT&CK 标注较丰富。
- 给出了数据完整性和小模型可学习性基线。

## 9. 局限

- 固定 20 分钟和预定攻击时间表可被模型记忆。
- 攻击设计者兼任标注者，且模型只各运行一次。
- 未明确按 session 隔离数据划分，存在潜在泄漏风险。
- 无事件图、跨 chunk 链、意图候选、组织级归因和原始证据回指指标。

## 10. 对我选题的启发

- 可作为双源采集、统一字段和 ATT&CK 标注的首选候选数据集。
- 需要在其事件之上补充实体解析、时间边、支持/冲突边和原始记录坐标。
- 实验必须加入 session-level split 和单源/双源消融。

## 11. 可转化的研究问题

1. 三源事件如何从窗口列表提升为有 provenance 的统一事件图？
2. 双源融合的收益来自补阶段还是提供稳定 join key？
3. 模型能否在未知会话和缺失一源时仍输出校准的链/意图候选？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| SynthChain | 同为多源链可观测性数据；后者侧重供应链与源预算 |
| StageFinder | 可把网络告警与主机日志构成事件图并做阶段分类 |
| Llama-PcapLog | 直接用 PCAP+syslog 微调 Llama，方法重合但缺图 |

## 13. 论文写作可引用句式

- 同步多源采集为攻击链研究提供必要数据基础，但仍需显式实体关系和原始证据谱系才能支持可审计推理。

## 14. 我的批注与疑问

- 优先核验数据许可、下载内容和 session-level split。
- 数据 artifact presence 100% 与 PCAP capture success 95% 不应混为一谈。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：4.5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
