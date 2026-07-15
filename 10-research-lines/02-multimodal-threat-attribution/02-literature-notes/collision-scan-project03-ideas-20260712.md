# Project03-Derived Ideas: Preliminary Collision Scan

> Superseded for active scoping on 2026-07-13. This file preserves the earlier path/protocol-transformation scan, but W1 is no longer the active main line after the user clarified the Project03 contribution boundary. Use `search-protocol-pcap-llm-kg-20260713.md` and the 2026-07-13 reusable-core audit for current work.

检索日期：2026-07-12
检索范围：截至 2026-07-12 可发现的论文、预印本、RFC 与专利。
状态：功能级初筛完成；不是系统综述，不等于 G2 通过。

## 1. 检索目标

对 Project03 派生的三条优先候选做撞题判断：

- I1：模态声明一致性感知的行为追溯；
- I3：模态与上下文条件化的阶段/意图候选校准；
- I2：跨协议不变的攻击行为表示。

判断标准是功能是否已被覆盖，不以题名是否出现 `IPv4/IPv6/MPLS/Geo/SCION` 为准。

## 2. 检索过程

使用路线：

1. `agent-reach doctor` 核验 Exa 与网页读取能力；
2. Exa 初始检索一次后触发免费 MCP `429`，不继续重复请求；
3. `nature-academic-search` OpenAlex fallback：一条请求遇到 SSL failure，一条因终端 GBK 输出失败，修正 UTF-8 后可运行，但该主题排序噪声较大；
4. 使用 arXiv、USENIX、IEEE/ACM/Elsevier/MDPI、IETF 与 Google Patents 页面做关键词扩展和原始来源核验。

核心查询族：

```text
packet provenance / path verification / proof of transit
P4 / INT / control-data plane consistency / configuration drift
protocol-agnostic intrusion detection / cross-protocol / domain generalization
attack stage inference / intrusion intention / uncertainty / calibration
network security provenance / forensic coverage / evidence transformation
configured intended observed network behavior / modality conflict
```

## 3. 高风险近邻矩阵

| 工作 | 年份 | 已覆盖功能 | 对候选的影响 | 判定 |
|---|---:|---|---|---|
| [EPIC](https://www.usenix.org/conference/usenixsecurity20/presentation/legner) | 2020 | SCION/path-aware Internet 中的路径授权、路径验证与源认证 | 不能把“验证实际路径是否遵循预期路径”作为 I1 新意 | 强碰撞 |
| [ID-INT: Secure Inter-Domain In-Band Telemetry](https://dl.ifip.org/db/conf/cnsm/cnsm2024/1571050975.pdf) | 2024 | SCION 上带认证的跨域 INT、路径 tracing 与 telemetry | 不能把“SCION + secure INT/逐跳遥测”作为新意 | 强碰撞 |
| [RFC 9315: Intent-Based Networking](https://datatracker.ietf.org/doc/rfc9315/) | 2022 | 比较 intended behavior 与 observed behavior，检测 intent drift | configured/intended/observed 的概念区分不是首次提出 | 概念碰撞 |
| [P4Prime](https://doi.org/10.1016/j.comnet.2026.112446) | 2026 | P4 数据面实时一致性/环路检测与故障交换机定位 | 不能把控制-数据平面不一致检测或 first-fault localization 作为主贡献 | 强碰撞 |
| [SecTracer](https://doi.org/10.1016/j.cose.2025.104760) | 2026 | 数据包、拓扑、策略、配置和转发表的网络级 provenance；攻击历史重建和 RCA | 通用 network-level security provenance 与 attack history reconstruction 已被覆盖 | 极强碰撞 |
| [Auditing Inferential Blind Spots](https://doi.org/10.3390/network6010009) | 2026 | 审计 packet/flow/aggregate 证据变换后哪些 ATT&CK 假设仍可支持 | “证据表示决定可支持威胁结论”的主张已有直接近邻 | 极强碰撞 |
| [US10999250B1](https://patents.google.com/patent/US10999250) / [US10237068B2](https://patents.google.com/patent/US10237068B2/en) | 2021/2019 | packet path signatures、path provenance、proof of transit | 路径 provenance 与 in-band proof 的专利空间拥挤 | 专利红线 |
| [Protocol-Agnostic and Packet-Based IDS](https://ieeexplore.ieee.org/document/10942348/) | 2025 | protocol-agnostic packet detection | I2 不能只做跨协议攻击分类 | 强碰撞 |
| [tFusion](https://doi.org/10.1145/3719027.3765143) | 2025 | packet/flow/host 多粒度跨模态恶意流量检测 | “网络流量多模态融合提升检测”已高度拥挤 | 强碰撞 |
| [XMF-GNN](https://www.sciencedirect.com/science/article/pii/S0925231225019575) | 2025/2026 | packet-flow 跨模态异构图融合 | I2 的普通融合/解耦叙事风险高 | 强碰撞 |
| [Uncertainty-Aware Attack Stage Classification](https://arxiv.org/abs/2508.00368) | 2025 | EDL、Dirichlet stage distribution、OOD uncertainty | I3 不能宣称首次不确定攻击阶段推断 | 极强碰撞 |
| [XAPT](https://doi.org/10.1109/ACCESS.2025.3636501) | 2025 | 校准异常分数、Bayesian stage inference、SHAP | I3 不能以“校准 + 可解释 stage”作为主创新 | 极强碰撞 |
| [StageFinder](https://arxiv.org/abs/2603.07560) | 2026 | host/network provenance 融合、时序图学习、ATT&CK stage probability | I3 不能以 provenance + temporal stage estimation 为新意 | 极强碰撞 |
| [M-IDAS preprint](https://openreview.net/pdf?id=rTdbRWWdR5) | 2024 preprint | 多源网络/系统数据中的 modality entanglement/conflict | 一般性的“多模态冲突感知 IDS”也已有直接尝试 | 高风险近邻 |

## 4. 候选裁决

### I1 宽版本：淘汰

以下内容均不能作为论文主贡献：

- path verification；
- proof of transit；
- control-data plane consistency；
- 通用 network security provenance；
- 根据网络配置/转发表重建攻击历史；
- intended vs observed behavior 的概念区分。

### I2：降为数据/鲁棒性子问题

跨协议不变表示如果最终只服务 attack classification，会落入 protocol-agnostic IDS、domain generalization 或 packet-flow multimodal fusion 的拥挤区域。除非出现明确的 behavior-tracing 终点和五模态配对 benchmark，否则不作为主线。

### I3：降为下游评价问题

不确定 stage inference、校准和 provenance-temporal fusion 已有 2025-2026 直接工作。P05-L2 可复用 calibration/abstention 作为评价要求，但不能把它们单独包装成创新。

## 5. 暂存白空间 W1

以下是撞题后仍可继续核验的问题，不是已经成立的新颖性结论：

> 在 IPv4、IPv6、MPLS、GeoNetworking 与 SCION 的协议封装/转换路径中，逐跳观测会保留、改变或丢失哪些攻击行为证据？当 configured、intended 与 observed wire evidence 冲突时，系统如何给出协议转换感知的证据 lineage，并限制其能够支持的 stage/TTP/intent 候选，而不把路径可达、协议标签或攻击类别先验误当作行为证据？

W1 与近邻的暂定差异：

| 近邻 | 它解决什么 | W1 必须额外证明什么 |
|---|---|---|
| EPIC/ID-INT/P4Prime | 路径/遥测是否可信、运行态是否一致 | 协议转换后安全行为证据的语义保真、丢失和结论边界 |
| SecTracer | 通用网络级 provenance 与 RCA | 五协议逐跳 transformation semantics；label/wire conflict 对行为结论的影响 |
| Forensic Coverage | packet 到 flow/aggregate 的抽象损失 | 不同协议封装与解析路径造成的 evidence transformation，而非仅粒度聚合 |
| EDL/XAPT/StageFinder | stage 概率、校准、时序 provenance | 上游 observation supportability 如何约束候选；stage 模型只作下游验证 |
| protocol-agnostic IDS/tFusion | 检测准确率和跨环境泛化 | 不以攻击分类准确率为主要终点，而评价 lineage、supportability 与拒答 |

## 6. W1 的通过条件

W1 进入 G1 前必须同时满足：

1. 找不到已经直接研究“五协议 transformation evidence -> ATT&CK/TTP supportability”的同功能工作；
2. 能为至少三种真实 wire modality 建立严格配对 replay，SCION 未验证时不能计入；
3. 定义可人工核验的 evidence preservation/loss ground truth；
4. 主要指标不是 IDS accuracy，而是 evidence preservation、lineage correctness、supportability 和 selective risk；
5. 证明它不同于 P05-L1 的主动调查控制，也不同于 SecTracer 的通用 provenance/RCA；
6. LLM 若加入，只能作为受证据约束的语义映射或解释组件，不能成为新颖性本身。

## 7. 当前结论

- 没有任何原始候选可直接通过 G1。
- I1/I2/I3 的宽版本均已撞题或高度拥挤。
- W1 是当前唯一值得继续验证的问题母体，但仍是 `amber`，不是选题。
- 下一步应先精读 SecTracer、Forensic Coverage、ID-INT、P4Prime、EDL/XAPT/StageFinder，再决定是否保留 W1。
