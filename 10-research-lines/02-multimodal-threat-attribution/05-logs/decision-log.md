# P05-L2 Decision Log

## 2026-07-12：建立独立多模态论文线

- 决策：将多模态方向注册为 P05-L2，与 P05-L1 的调查控制论文线隔离。
- 原因：两条线可以共享精读和安全知识，但 RQ、贡献、数据、实验与论文主张必须独立。
- 当前命名：`multimodal-threat-attribution`，仅为工作区名。
- ARS 路由：`deep-research / socratic`。
- 当前禁止：检索结论、候选题目、方法框架、实验结果和论文草稿。
- 下一决策点：用户确认 RQ Summary 后决定是否通过 G1。

## 2026-07-12：以 Project03 五模态作为 P05-L2 的实验起点

- 决策：P05-L2 优先围绕 IPv4、IPv6、MPLS、GeoNetworking、SCION 的异构路径观测展开，不再以泛化“文本+图像”作为默认起点。
- 交接原则：复用控制、重放、逐跳观测和候选解释接口；不继承 attack-stage 映射、置信度或意图 Top-1 作为论文真值。
- 关键区分：configured modality、intended modality、observed wire modality 必须分字段管理。
- SCION 边界：真实数据面封装未验证前，不进入 wire-level 五模态平均结果。
- 下一决策点：完成 I1/I3/I2 最新撞题检索后，由用户选择主问题，再做 FINER/G1。

## 2026-07-12：不保留原始 I1/I2/I3 作为论文主贡献

- I1：通用路径验证、一致性检测和 network provenance 已被直接覆盖。
- I2：protocol-agnostic IDS 与网络流量跨模态融合已经拥挤。
- I3：不确定/校准的攻击阶段推断已有直接工作。
- 决策：仅暂存 W1，研究协议 transformation 如何改变攻击行为证据及可支持的 stage/TTP/intent 结论。
- 状态：`amber`；P0 全文精读前不进入 G1，不产生题目或方法框架。

## 2026-07-13：五种协议降为环境条件，流量/日志成为双源主线

- 决策：IPv4/IPv6/MPLS/Geo/SCION 不再称为五个模态。
- 理由：它们主要描述协议/转发环境；真正具有独立证据来源的是 PCAP/traffic 与 host/system/application logs。
- 复用：Project03 的 ThreatObservation、图查询和定位思想。
- 排除：CENI 部署妥协、controller/网元适配和文件名模态标签。

## 2026-07-15：选择 R2 作为最强残余，不把 Agent 作为主创新

- 决策：最强候选核心为 calibrated multi-candidate traffic-log observation relation。
- 理由：二次检索已发现 broad dual-source graph、概率证据图、补边、CTI-provenance 匹配、missing-hop 和 agent investigation 的直接先例。
- LLM 定位：下游 evidence-constrained chain/ATT&CK/intent consumer；Agent 只作附录或扩展。
- 推荐架构：Candidate A 叙事 + Candidate B 必做核心 + Candidate C 可选。
- 状态：待用户批准；不是已冻结选题。
