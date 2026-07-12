# Project03-Derived Idea Pool v0.1

日期：2026-07-12  
状态：候选池；未做 2026-07-12 撞题检索；不得写成论文贡献。

## 评价规则

每个 idea 必须回答五件事：研究对象是什么、额外模态提供什么独立信息、如何证伪、现有资产能复用多少、最可能失败在哪里。

## I1：模态声明一致性感知的行为追溯

**问题。** 当前系统把 controller 配置、文件名声明和 wire observation 合并成一个 modality。SCION 样本已经证明三者可能不一致。能否显式建模这些声明及其逐跳证据，以定位封装漂移、运行态漂移或观测缺失？

**输入。** 同一 replay 的 controller state、文件名/数据 manifest、host1/s1 ingress/s1 egress/s3 capture、API observation。

**输出。** 逐跳 modality provenance graph、冲突类型、可支持的行为追溯结论和置信/拒答状态。

**可证伪假设。** 与单一 filename-first modality 相比，显式区分 configured/intended/observed modality 能提高错配检测与故障跳点定位，并减少错误的协议级归因陈述。

**最低 baseline。** 文件名前缀规则、末端单点嗅探、controller state-only、简单多数投票。

**主要风险。** 容易退化成网络运维故障诊断；必须证明它改善安全行为追溯或攻击意图证据边界，而非只识别协议。

**优先级。** A，优先进入撞题检索。它直接来自真实失败案例，且最能体现 Project03 的独特实验资产。

## I2：跨协议不变的攻击行为表示与模态特异证据分解

**问题。** 同一攻击行为在 IPv4/IPv6/MPLS/Geo/SCION 路径上，哪些行为特征应保持不变，哪些特征属于封装/路径特异信息？

**输入。** 严格配对的同源攻击 replay，五模态逐跳 capture 与统一行为标签。

**输出。** `behavior-invariant` 与 `modality-specific` 两类表示，以及攻击行为/阶段候选。

**可证伪假设。** 解耦表示在 leave-one-modality-out、缺失模态和封装变化条件下，比直接拼接或单模态模型更稳定。

**最低 baseline。** 原始特征分类、late fusion、domain-adversarial/domain-generalization、协议归一化后的单模型。

**主要风险。** 跨域/协议无关 IDS 已有大量工作；若最终任务只是攻击分类，会偏离“行为追溯与意图感知”。SCION 当前也没有可信 wire 真值。

**优先级。** B，先解决数据配对与撞题问题，再判断是否保留。

## I3：模态与上下文条件化的阶段/意图候选校准

**问题。** 当前 stage 由 attack-type 先验、文本词和少量窗口特征启发式打分；modality 主要只进入检索关键词。能否输出证据可追溯、可校准、允许拒答的阶段与意图候选分布？

**输入。** 行为统计、逐跳模态证据、Technique/ATT&CK 语义、前后事件上下文；可选 HFish 行为证据。

**输出。** stage/TTP/intent candidate distribution、证据引用、校准置信度、abstention。

**可证伪假设。** 在模态缺失、冲突和 OOD 攻击下，证据条件化候选分布比静态映射和未校准 Top-1 具有更低 ECE/Brier 和更高 risk-coverage 性能。

**最低 baseline。** `ATTACK_STAGE_MAP`、Project03 当前 heuristic、仅行为特征模型、仅知识检索、简单融合。

**主要风险。** 模态本身可能与意图语义无关；若消融显示独立贡献为零，应将“模态”降为 observation reliability，而不是强行用于语义预测。

**优先级。** A-，与 I1 互补；可成为 I1 的下游任务，但暂不合并成大而全框架。

## I4：五模态流量与 HFish 行为图的交叉证据验证

**问题。** 流量侧给出攻击/阶段候选，HFish 给出扫描、访问、登录等真实交互行为。两条观测链能否互相验证，而不是把同一标签重复两次？

**输入。** 五模态流量 observation 与按 source/target/time 对齐的 HFish session graph。

**输出。** 跨源 evidence graph、被支持/冲突的阶段与意图候选。

**可证伪假设。** 仅在实体和时间对齐可靠时，HFish 证据能改善候选排序、证据覆盖或拒答质量；错配时系统应降级而非获得虚假增益。

**最低 baseline。** 流量-only、HFish-only、无校验拼接、规则级时间/IP join。

**主要风险。** 现有 HFish 数据主要是扫描，模态配对稀疏；这是一条辅助证据线，不是五类网络模态中的第六类。

**优先级。** B-，作为扩展或数据增强备选。

## I5：基于多点观测的最小充分取证选择

**问题。** 当五模态路径中的部分 hop capture 缺失或冲突时，应优先补采哪个点，才能以最低成本消除行为追溯或意图候选歧义？

**输入。** I1 的证据缺口状态与可用抓包动作。

**输出。** 下一观测点/模态采集建议、STOP 和当前可支持结论。

**可证伪假设。** 相比固定全路径抓包或固定顺序采集，缺口驱动的观测选择能在同等结论风险下降低采集成本。

**主要风险。** 与 P05-L1 的“调查控制”贡献高度邻近，可能造成研究线重复。

**优先级。** C，暂不作为 P05-L2 主问题；只有明确限定为网络路径观测选择且通过跨线去重后再考虑。

## 当前优先顺序

1. I1：最强本地问题证据，先做功能级撞题检索。
2. I3：最贴近用户负责的攻击意图候选感知，但必须验证模态的独立贡献。
3. I2：可形成算法线，前提是拿到严格配对的五模态数据。
4. I4：作为跨源证据扩展。
5. I5：与 P05-L1 重叠，暂时冻结。

## 暂定问题母体，不是 RQ

> 面向 IPv4、IPv6、MPLS、GeoNetworking 与 SCION 异构路径，研究如何显式区分配置、声明和数据面观测的模态证据，并利用逐跳一致性与冲突来约束攻击行为追溯和意图候选感知。

下一步必须先完成 I1/I3/I2 的截至 2026-07-12 文献与专利碰撞检索，再由用户决定收敛方向。

## 2026-07-12 撞题更新

详见 [preliminary collision scan](../02-literature-notes/collision-scan-project03-ideas-20260712.md)。

- I1 宽版本：淘汰。路径验证、控制-数据平面一致性、通用 network security provenance 已有直接工作和专利。
- I2：降为数据与鲁棒性子问题。protocol-agnostic IDS 和网络流量多模态融合已拥挤。
- I3：降为下游评价问题。不确定 stage inference、校准和 provenance-temporal fusion 已有 2025-2026 直接工作。
- I4：保留为远期辅助证据，当前数据不足。
- I5：继续冻结，避免与 P05-L1 重复。

当前仅保留 `amber` 问题母体 W1：协议封装/转换造成的行为证据保真、丢失和冲突，如何约束可支持的 stage/TTP/intent 候选。W1 不是论文题目，必须先完成 P0 精读。
