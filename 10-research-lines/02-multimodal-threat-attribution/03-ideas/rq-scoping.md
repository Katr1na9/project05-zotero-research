# P05-L2 RQ Scoping

状态：2026-07-15 二次检索和综合已完成；3 个候选 RQ 已形成，等待用户人工选择，RQ 仍未冻结。

## 第一轮：Clarification

1. 用户已有任务积累：流量侧从 PCAP 和上游检测结果形成威胁观察，查询知识图谱，定位行为/攻击模式并给出溯源、阶段和意图候选。
2. 日志侧积累：已为 HFish 数据定义事件标准化、行为图节点/边和阶段/战术候选路线，但当前仓库未实现抽取与建图脚本。
3. 当前实现缺口：`ThreatObservation` 尚未成为所有样本统一的一等实体；恶意样本仍主要存为 `threat + attack_stage`。
4. 当前建图缺口：现有代码能导出背景知识子图和构造展示图，但尚未从流量与日志联合构造持久化事件级证据图。
5. 当前语义缺口：`CanPrecede` 和关键词命中只能提供候选先验，不能证明该攻击链在当前事件中真实发生。
6. 当前可信缺口：上游 attack label/technique 可能同时进入输入和评价，存在泄漏与自证风险。
7. 多模态边界：流量与日志是优先双源；packet bytes、header/session、flow、model output、graph evidence 是流量侧内部视图；五种协议模式先作为环境变量。
8. 工程边界：CENI controller、网元和代理部署不作为论文贡献。

## 第二轮：检索后的回答

1. PCAP agents、traffic-language、network-enhanced provenance、CTI graph matching 和 LLM/agent investigation 均已被直接工作覆盖。
2. 宽泛统一事件图只是工程贡献；可检验问题必须落到 packet-log candidate relation、calibration、conflict state 和 downstream graph/chain gain。
3. ATT&CK tactic、event intent、goal intent 和 actor motive 必须分开；高层 intent 只能作为有独立标注协议的次要终点。
4. 最清晰 ground truth 是 record-level relation 与 chain edge，而非 actor/goal intent；ProvICS/AIT v2 可支持 pilot annotation。
5. 通过 traffic-only/log-only/equal-budget/deterministic-join/oracle-link ablation、missing/conflict corruption 和 risk-coverage 证明增益。
6. Candidate B 是最稳健硕士核心；Candidate A 保留 LLM+tracing 叙事，Candidate C 是高风险扩展。

## 后续层

- Layer 2：假设探查，检查“多模态一定更好”等隐含假设；
- Layer 3：证据与可行性，确认数据、标签、baseline 和资源；
- Layer 4：替代观点，比较多模态与更强单模态/检索方法；
- Layer 5：意义与风险，明确论文价值、误用风险和失败后仍有价值的结论。

## G1 候选出口

候选题、权重可行性矩阵、方法/实验蓝图和 kill criteria 已写入 [candidate-thesis-topics-and-feasibility-v0.1-20260715.md](candidate-thesis-topics-and-feasibility-v0.1-20260715.md)。用户选择后再冻结单一 Primary RQ、Sub-RQ、FINER、in/out scope 和最终检索关键词。
