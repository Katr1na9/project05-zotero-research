# P05-L2 Compound Learning Log

记录只对多模态研究线成立、但未来可能复用的方法经验。

## 2026-07-12：从任务失败而不是模型名称定义多模态价值

- 起点：当前只有“加入多模态”的宽 idea。
- 冻结原则：先定位单模态的具体不可观察性或证据缺口，再决定额外模态；没有独立信息增益时，不进入方法设计。
- 复用方式：后续每个候选模态都要回答“它提供了什么其他模态没有的信息，以及如何被单独消融验证”。

## 2026-07-12：协议模式必须拆成声明、配置与数据面观测

- 起点：Project03 为保证工程链稳定，优先按文件名前缀写入 modality；SCION 样本在 wire 上仍表现为 IPv4/UDP。
- 沉淀：实验中的“模态”至少包含 configured、intended 和 observed 三层，任何一层都不能自动成为另外两层的真值。
- 复用方式：后续多源安全研究均应保存 claim source、observation source、冲突状态和可支持结论，而不是只保留融合后的标签。

## 2026-07-15：从“系统组合”转向“关系任务”定义创新

- 起点：traffic + logs + graph + LLM 看似新，但每个系统模块都有直接近邻。
- 沉淀：把创新单位降到可标注、可校准、可消融的 packet-log observation relation，才可区分于确定性 join、图内补边和概念性框架。
- 复用方式：以后遇到“X + Y + LLM”选题，先写输入-表示-关系-输出矩阵，再寻找最小可证伪关系任务。

## 2026-07-15：confidence 不等于 calibration

- 起点：MPCA、APMP、概率证据图和许多 LLM 系统都输出分数或概率。
- 沉淀：只有在独立 calibration set 上报告 Brier/ECE/reliability/risk-coverage，才能称为校准；Softmax、专家权重和路径分数都不自动成立。
- 复用方式：所有可信安全论文同时检查 discrimination、calibration、selective risk 和 independent unit split。

## 2026-07-15：证据层与假设层必须分开

- 起点：缺失边补全、ATT&CK 映射和 LLM 叙事容易直接写回图。
- 沉淀：observed/candidate/verified/rejected/conflict/knowledge-hypothesis 是不同状态；模型生成内容不得覆盖原始证据。
- 复用方式：每条语义 claim 保存 graph IDs 与 raw record pointers，无法回放时拒答或降级。
