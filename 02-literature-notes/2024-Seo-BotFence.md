# BotFence: A Framework for Network-Enriched Botnet Detection and Response With SmartNICs

## 1. 基本信息

- 中文译名：BotFence：基于 SmartNIC 的网络增强型僵尸网络检测与响应框架
- 作者：Hyunmin Seo; Seungwon Shin; Seungsoo Lee
- 年份：2024
- Venue：IEEE Access, 12, 114878-114893
- DOI：https://doi.org/10.1109/ACCESS.2024.3446535
- 开放全文：https://cclab.info/papers/2024_seo_botfence.pdf
- 阅读日期：2026-07-14
- 阅读优先级：必读（双线建图直接红线）
- 所属主题：Host Events + Network Packets / Provenance Graph / TTP / SmartNIC / Botnet

## 2. 一句话总结

BotFence 用 eBPF 采集主机事件并按预定义规则映射为 ATT&CK TTP，通过 PID/PPID 形成 TTP provenance，再用 SmartNIC DPI 检查明文或卸载解密后的 L7 包，以 5-tuple 把网络节点挂接到对应 TTP，形成 Network-enhanced Threat Provenance Graph（NTPG）并实时阻断僵尸网络扩散；它直接占据“主机事件 + 网络包 + TTP 图”的宽泛创新，但没有双线独立 observation schema、候选跨源边校准、冲突/缺失传播、LLM 或图/链级准确性评价。

## 3. 研究问题

- 仅依赖主机 provenance 为何难以利用 C2、恶意载荷和代码下载等网络包证据？
- 如何在不显著降低吞吐的情况下，把 L7 payload inspection 与主机事件分析联合起来？
- 如何将低层系统调用聚合为 TTP，并把网络包信息连接到 TTP provenance graph？
- 如何依据图严重度与恶意包结果实时生成 `inspect`/`block` 网络策略？

## 4. 核心贡献

1. 提出在 NVIDIA BlueField-2 SmartNIC 上协同执行主机事件分析、DPI、NTPG 构建和策略下发的实时系统。
2. 以 eBPF kernel probe 收集进程、文件和网络系统调用，标准化为带 PID、类别、操作和参数的 feed。
3. 按 MITRE ATT&CK 预定义规则将一个或多个 feed 映射成 TTP，并按 PID/PPID 与时间顺序形成 provenance。
4. 以 host feed 与 DPI 结果的 5-tuple 相等为条件，把网络 packet inspection 节点挂到 TTP，形成 NTPG。
5. 用 CAPEC 严重度分数和恶意 payload 命中驱动 `inspect`/`block` 决策，并通过 SmartNIC 数据面执行。

## 5. 方法框架

### 输入

- 主机侧：eBPF 拦截的进程创建、文件访问和网络系统调用及 PID/PPID。
- 网络侧：SmartNIC DPI 对进入/离开主机的 L7 payload 检查结果与 5-tuple。
- 先验：人工配置的 TTP generation rules、ATT&CK、CAPEC 严重度与检测阈值。

### 输出

- 以 TTP 为主节点、网络信息为增强节点的 NTPG。
- 僵尸网络感染与扩散阶段的可视化攻击过程。
- 针对进程网络活动的 `inspect` 或 `block` 策略。

### 关键模块

| 模块 | 作用 | 可借鉴点 |
|---|---|---|
| Host Agent/Event Handler | eBPF 采集并把事件标准化为 feed | 可作为日志/主机侧 observation 生成基线 |
| TTP Correlation | 用预定义规则把 feed 聚合为 ATT&CK TTP | 适合规则 baseline，不适合作为未知攻击语义真值 |
| NTPG Builder | PID/PPID 排序 TTP，以 5-tuple 接入 DPI 节点 | 是双源图最直接的确定性基线 |
| Decision/Policy Enforcer | CAPEC 累积分数和 payload 命中驱动阻断 | 属部署与响应，不是本支线计划复用的论文核心 |

### 方法流程

```text
eBPF 主机事件 -> feed -> 预定义规则 -> TTP 节点 -> PID/PPID provenance
SmartNIC packet -> DPI 恶意 payload 结果 -> 5-tuple 等值匹配 ----┘
                                      -> NTPG -> CAPEC score -> inspect/block
```

## 6. 数据集与实验

- 系统实现在 NVIDIA BlueField-2 SmartNIC；ARM 核运行事件收集、NTPG、决策和策略模块，硬件 DPI/packet pipeline 负责包处理。
- 安全评价为作者自建的五阶段僵尸网络感染/扩散模拟：C2 握手、系统信息收集、信息外传、定制 rootkit 下载、远程服务横向扩散。
- NTPG 案例展示 T1573、T1071.001、T1082、T1041、T1014、T1210 等节点及相关网络信息，并成功阻断到第二台主机的 RDP 会话。
- 安全评价没有公开 benchmark、重复场景数、事件/边真值、Precision/Recall/F1 或消融；“提高检测准确性”主要由案例说明支撑。
- 性能测试使用两台 Xeon/64 GB 主机、40G 链路，服务端装 BlueField-2，以 Nginx、wrk/wrk2 和 Snort inline 作对比。
- 论文称超过 99%（摘要写 99.9%）的决策与规则生成操作在 1 ms 内完成；L7 throughput 接近 baseline，Snort throughput 低于其 25%，延迟仅小幅高于 baseline。

## 7. 关键知识点

- `Network-enhanced Threat Provenance Graph` 已是明确命名并实现过的组合，不能作为新题名或宽泛贡献。
- 主机线先被规则压缩为 TTP，网络线则只保留 DPI 命中的 payload 信息；两线并非对等、独立的原始事件子图。
- 跨源边是单一确定性 5-tuple 等值匹配，没有时间漂移、NAT、共享地址、重传、多连接、多进程复用或不确定候选。
- 论文图中的“causal”主要来自 PID/PPID、事件顺序和预定义 TTP 规则，不是学习/校准后的因果结论。
- 只存被判定为真实攻击的 NTPG，有利于压缩，却会丢失负证据、被拒绝候选和后续审计所需上下文。

### 术语翻译

| 英文 | 建议译法 | 备注 |
|---|---|---|
| Network-enhanced Threat Provenance Graph | 网络增强威胁溯源图 | 本文缩写 NTPG；不可再作为我们的新概念 |
| Feed | 标准化主机事件记录 | 带 PID、类别、操作和参数 |
| TTP generation rule | TTP 生成规则 | 人工预定义的系统调用/参数模式 |
| Packet inspection result | 数据包检查结果 | DPI 命中的 payload 特征与 5-tuple |

## 8. 优点

- 真正同时采集主机系统调用和网络 packet payload，而不是在两个数据集上分别测试。
- 清楚给出 TTP 生成、PID/PPID lineage 和 5-tuple 接边算法，可作为强确定性 baseline。
- 将图分析结果落实到实时策略执行，并系统测量延迟、吞吐与规则规模影响。
- SmartNIC 隔离与 TLS offload 使系统能在特定部署条件下检查加密前/解密后 payload。

## 9. 局限

- 任务仅聚焦自动化 botnet 感染和扩散，不覆盖一般 APT、并发 campaign、行为体归因和高层意图。
- TTP、CAPEC 分数、DPI signature 和阈值依赖人工规则，对新攻击、未知载荷和加密不可见流量泛化有限。
- 5-tuple 等值接边没有候选、多义性、置信度、校准、冲突或拒绝状态。
- 没有不可变 packet frame/log record ID、hash、parser version 和 claim-to-raw replay 评价。
- 只保留已认定攻击的 NTPG，无法完整审计误报、漏报及被丢弃证据。
- 安全有效性只用一个作者控制的模拟场景展示，未报告图边、链、阶段或检测的统计指标。
- 没有 traffic-only、host-only、简单融合和 NTPG 消融，无法量化两条线的独立与联合贡献。
- SmartNIC、解密 offload 与可编程数据面的部署假设较重，不适合作为本论文可推广核心。

## 10. 对我选题的启发

- 不能再用“构建网络增强 provenance graph”概括创新；BotFence 已完成并部署。
- 图构建贡献必须落在 BotFence 没解决的对象：原始 traffic/log observation 保持、跨源多候选关系、关系后验校准、显式冲突/拒绝、链级不确定性传播。
- Project03 的 `ThreatObservation` 应与日志侧 observation 对等存在；二者先各自成图，再由可学习且可验证的 relation layer 连接，避免网络节点仅作为 TTP 附件。
- BotFence 的 PID/PPID + 5-tuple 可作为 deterministic-join baseline；对比必须加入 NAT、时钟漂移、共享 IP、缺失源和多候选条件。
- 图谱构建是否成立应由 edge-F1/calibration、source preservation 和下游 chain/intent 增益证明，而不是只展示一张攻击图。

## 11. 可转化的研究问题

1. 多候选、可校准的 packet-log relation model 相比 PID/5-tuple 等值匹配，在复杂网络条件下能否显著降低错误关联？
2. 流量子图和日志子图各自能恢复哪些攻击步骤，联合图在何种缺失/冲突条件下仍应合并或拒绝？
3. 保留原始双源锚点、负证据和冲突边，能否提高 LLM 链/意图结论的可回放率、忠实度和风险覆盖性能？

## 12. 和其他论文的关系

| 相关论文 | 关系 |
|---|---|
| He et al. 2016 Evidence Graph | 更早做包+程序日志证据图；BotFence 更现代、实时并明确接入 TTP 与 payload |
| APTGuard | 都采集 packet/PCAP 与主机日志；APTGuard 固定窗口融合并用 LLM，BotFence 显式建 NTPG 但无 LLM |
| MuSAR | 都恢复多阶段链；MuSAR 联合网络告警/应用日志，BotFence 用主机事件与 packet DPI |
| UTLParser | 后者解决异构日志解析/融合；BotFence 可作为 traffic-host deterministic join 基线 |
| Project03 支线 | 最强双线建图红线，迫使贡献收紧到 source-preserving、calibrated relation 与 evidence-grounded LLM |

## 13. 论文写作可引用句式

- 已有系统能够将 eBPF 主机事件映射为 ATT&CK TTP，并通过 PID/PPID 和 5-tuple 将 SmartNIC 数据包检查结果接入网络增强威胁溯源图；然而，这类确定性、规则驱动的融合尚未处理跨源关系多义性、概率校准、证据冲突及图构建质量的独立评价。

## 14. 我的批注与疑问

- 论文交替使用 `Provenance` 与 `Providence`，引用时统一采用正式概念 `Provenance`。
- 摘要写“99.9% host events in 1 ms”，正文性能段写“超过 99% operations”；应按更保守的正文口径引用。
- 论文称网络包与 host event “inherently linked”，实质是同一网络 feed 和 DPI 结果的 5-tuple 相等；在 NAT/容器/代理环境中不天然成立。
- NTPG 先把日志压到 TTP 层，可能造成错误 TTP 一旦写入就污染后续图；我们的 schema 应保留 observation、relation、semantic hypothesis 三层。

## 15. 结论评级

- 相关性评分：5/5
- 方法可借鉴性：5/5
- 实验可复现性：3/5
- 作为硕士论文基础价值：5/5
- 是否进入核心文献：是（双线图构建最直接系统先例）
