# P05-L2 RQ Scoping

状态：第一轮范围澄清已由用户与 Project03 证据部分完成；等待候选撞题检索后收敛。

## 第一轮：Clarification

1. 具体失败场景：controller 配置、数据集声明和数据面真实封装可能不一致，单点/单字段无法可靠追溯行为经过的异构路径。
2. 现实可获得模态：IPv4、IPv6、MPLS、GeoNetworking、SCION；但 SCION 当前只有 intended label，wire evidence 待补。
3. 用户已有任务积累：行为追溯与攻击意图候选感知，不把心理动机或完整攻击链当作已知真值。
4. 当前方法失败：filename-first modality、attack-type-first stage、未校准 intent Top-1、逐跳证据未进入统一表示。
5. 实验边界：优先复用 Project03/CENI 可控重放与多点抓包，不把工程演示记录直接当 benchmark。

## 第二轮：待检索后回答

1. I1“模态声明一致性 + 逐跳行为追溯”是否已有同功能方法？
2. I3“模态/上下文条件化的 stage-intent 校准”中，协议模态是否提供可证明的独立信息？
3. I2“跨协议行为不变表示”与 protocol-agnostic IDS/domain generalization 的差异能否成立？
4. 哪个问题可获得不依赖规则自证的 ground truth？
5. 选择一个主输出后，其余模块如何降为输入、评价或扩展，而不是堆成大框架？

## 后续层

- Layer 2：假设探查，检查“多模态一定更好”等隐含假设；
- Layer 3：证据与可行性，确认数据、标签、baseline 和资源；
- Layer 4：替代观点，比较多模态与更强单模态/检索方法；
- Layer 5：意义与风险，明确论文价值、误用风险和失败后仍有价值的结论。

## G1 输出占位

用户确认后再生成：

- 单一 Primary RQ；
- 2-3 个 Sub-RQ；
- FINER 评分；
- in-scope / out-of-scope；
- methodology type；
- theoretical framework；
- 5-10 个检索关键词。
