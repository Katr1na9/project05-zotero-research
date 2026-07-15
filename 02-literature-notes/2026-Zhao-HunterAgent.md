# HunterAgent: Neuro-Symbolic Attack Trace Reconstruction under Anti-Forensics

## 1. 基本信息

- 中文译名：HunterAgent：反取证条件下的神经符号攻击轨迹重构
- 作者：Guangze Zhao et al.
- 年份：2026
- Venue：arXiv preprint
- arXiv：https://arxiv.org/abs/2605.29269
- Zotero key：8KXR3HPW（PDF：I8F4422S）
- 阅读日期：2026-07-13
- 阅读优先级：必读
- 所属主题：Provenance / Anti-Forensics / Neuro-Symbolic LLM

## 2. 一句话总结

HunterAgent 从高置信告警出发，在日志擦除、PPID 欺骗和无文件执行等反取证条件下，让 LLM 只提出类型化缺失语义，再由物理标识碰撞和预算化搜索验证攻击路径。它已覆盖事件图、背景 ATT&CK graphlet、证据/推断分层和安全停止，是本课题最强撞题之一，但仍缺 PCAP 细粒度双源、攻击意图与行为体归因。

## 3. 研究问题

- 遥测被删除或伪造时，如何在两个锚点间恢复可信因果路径？
- 攻击者可删除日志、伪造用户态标识并注入单一通道伪事件；系统要求至少一个正交 OS 层源幸存。
- Ring-0 同时抹除所有源、SOC 供应链失陷与阻止告警产生不在范围内。

## 4. 核心贡献

1. 类型化时间 DAG 事件本体和 ATT&CK/Atomic Red Team/APT graphlet 背景库。
2. LLM 语义生成与确定性物理验证严格分工。
3. `G_verified` 与 `G_inferred` 分层，推断跳只作为 investigative lead。
4. 反取证擦除/注入评测、安全停止、PHR 和 LOFO 设计。

## 5. 方法框架

```text
alert anchor + fragmented provenance telemetry
  -> serialize neighborhood
  -> retrieve top-8 threat graphlets
  -> LLM proposes typed semantic nodes/edges
  -> schema validation
  -> physical identity collision (5-tuple/inode/PPID/ETW)
  -> cost-constrained beam search (width 6)
  -> verified evidence graph + inferred leads
```

- 节点：Process/File/Network/Registry；边：ProcessCreate、FileWrite、NetConnect 等。
- LLM 禁止生成 PID、inode、5-tuple 等物理标识，也不能裁决真实性。
- 网络侧主要是 NetFlow/5-tuple，非 PCAP payload；真正较完整的正交多源主要在自建 D4。

## 6. 数据集与实验

- D1 DARPA TC E3：38.5M 事件；D2 OpTC：24.7M；D3 ATLAS：4.2M；D4：40 campaigns、15.2M 事件。
- 30% 日志抑制时四库平均 F1 86.1%；D4 P/R/F1/PHR 为 91.3/82.7/86.8/6.4。
- ReAct 在 D4 为 46.2/78.4/58.1/61.5，显示无验证 LLM 幻觉显著。
- 70% 擦除时 F1 约 40.8--41.4，precision 83.7--85.3，但预算耗尽率可达 95.7%。
- 单次调查约 38,200 tokens、4.7 次 LLM 调用、0.19 美元、42.8 秒。

## 7. 关键知识点

- 语义假设和物理证据必须分层；LLM 不应生成不可验证的标识符。
- 正交源的价值是能在一个通道受损时形成独立验证，而不只是增加字段数量。
- 安全停止/弃权是证据不足调查的必要输出。

## 8. 优点

- 威胁模型、反取证、验证器和证据等级定义清楚。
- 同时评价路径恢复、幻觉和预算耗尽。
- 适合直接转化为本课题的可信推理约束。

## 9. 局限

- 至少一个可信正交源幸存是强前提；完全观测崩溃无法处理。
- D1--D3 反取证为后处理，D4 为自建数据；VMI 是否暴露给系统的描述有歧义。
- 网络模态停留在 NetFlow，缺少 PCAP 原始包锚点。
- 没有攻击意图、目标候选、不确定性校准或组织归因。

## 10. 对我选题的启发

- 事件图必须区分 observed/derived/inferred 三类边。
- LLM 只生成语义候选；跨源对齐由稳定标识、时间容差和冲突规则验证。
- 输出链、意图、行为体候选时都需要预算耗尽与弃权机制。

## 11. 可转化的研究问题

1. 能否把 PCAP frame/flow 与 HFish/system log 作为两种正交验证源？
2. 如何把阶段链的不确定性进一步传播到意图候选而不越过证据？
3. 当双源冲突或缺失时，哪些链边应降级为 investigative lead？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| PROVSEEK | 都强调外部验证；PROVSEEK 强制 claim 绑定 node/edge ID |
| ANANKE | 都以知识增强扩展 provenance 图；ANANKE 更依赖 LLM 裁决 |
| FuseChain | 后者学习多源事件图异常和阶段，不使用 LLM |

## 13. 论文写作可引用句式

- 在反取证环境中，语言模型应负责提出受约束的语义假设，而物理身份和事件发生性必须由独立遥测验证。

## 14. 我的批注与疑问

- 不能把文中的 actor alias 误写为 threat actor attribution。
- 本课题若只做“图 + LLM 补链”，会被该文直接压住；差异必须落实到双源 PCAP、意图候选与可校准证据路径。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：4/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是
