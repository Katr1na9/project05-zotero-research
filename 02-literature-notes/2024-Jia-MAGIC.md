# MAGIC: Detecting Advanced Persistent Threats via Masked Graph Representation Learning

## 1. 基本信息

- 英文题名：MAGIC: Detecting Advanced Persistent Threats via Masked Graph Representation Learning
- 中文译名：MAGIC：基于掩码图表示学习的高级持续性威胁检测
- 作者：Zian Jia; Yun Xiong; Yuhong Nan; Yao Zhang; Jinjing Zhao; Mi Wen
- 年份：2024
- Venue：33rd USENIX Security Symposium, USENIX Security 2024
- 页码：5197-5214
- 官方页面：https://www.usenix.org/conference/usenixsecurity24/presentation/jia-zian
- 官方 PDF：https://www.usenix.org/system/files/usenixsecurity24-jia-zian.pdf
- arXiv：https://arxiv.org/abs/2310.09831
- 官方代码：https://github.com/FDUDSDE/MAGIC
- Zotero key：`SV57VQLV`；PDF attachment key：`WMMURBGH`
- 阅读日期：2026-07-13
- 阅读状态：全文精读 + 附录复核 + 官方 `main` 分支关键代码审计
- 论文类型：APT detection / provenance graph / self-supervised graph anomaly detection
- 对 Project05 的定位：日志侧上游证据生成器，不是归因器、调查规划器或 Agent

### 证据锚点

下文页码均指官方 PDF 页码，而不是论文印刷页码。

| 内容 | PDF 位置 |
|---|---|
| 摘要、问题与贡献 | pp. 2-3 |
| 威胁模型与两种检测粒度 | p. 4 |
| 系统总览 | p. 5, Fig. 2 |
| 图构建与降噪 | p. 6, Fig. 3 |
| 掩码图编码器与解码器 | pp. 7-8, Fig. 4 |
| KNN 异常检测与适应机制 | pp. 8-9 |
| 数据集、划分与主结果 | pp. 9-12, Tables 1-5 |
| 时间和内存开销 | pp. 12-13, Table 6 |
| 消融、阈值与论文自述局限 | pp. 13-14, Figs. 7-9 |
| 对抗、复杂度、案例与标注附录 | pp. 17-19, Appendices A-G |

## 2. 一句话结论

MAGIC 用掩码图自编码器学习良性 provenance graph 中的节点行为表示，再用 KNN 距离检测异常批次或异常实体；它在公开基准上展示了很强的异常排序能力和较低的图表示开销，但官方实现存在测试表示暴露、标签辅助训练清洗、测试标签选阈值及论文与代码参数不一致等复现级风险，因此论文中的 AUC 可作为受控基准下的排序证据，Precision、Recall、FPR 和 F1 不应直接当作无标签真实部署性能。

## 3. 它究竟做什么，不做什么

| 问题 | MAGIC 的回答 |
|---|---|
| 输入是什么？ | 来自同一审计源的系统审计日志，转换为进程、文件、网络对象及其交互组成的 provenance graph。 |
| 学什么？ | 只建模良性图中的节点类型、边类型和局部多跳结构。 |
| 输出什么？ | 批级异常分数，或实体级异常分数及可疑进程、文件、连接。 |
| 是否识别 APT actor？ | 否。没有攻击组织标签、actor ranking 或归因置信度。 |
| 是否恢复完整攻击链？ | 否。作者只称可疑实体可供后续 investigation/story recovery 使用。 |
| 是否映射 ATT&CK？ | 否。没有 TTP、tactic、intent 或 CTI 语义对齐。 |
| 是否主动补证？ | 否。没有 action space、证据成本、预算、STOP 或下一步取证选择。 |
| 是否是 Agent？ | 否。它是固定的图表征与异常检测流水线。 |
| LLM 发挥什么作用？ | 没有使用 LLM。 |

特别注意：MAGIC 所谓 `multi-granularity` 是“批级检测”和“实体级检测”两档，不是 Project05 的 G0-G3 结论粒度门控，也不是 actor、campaign、family 等归因粒度。

## 4. 研究问题与威胁模型

### 4.1 论文要解决的问题

作者认为当时的 provenance-based APT detection 有三类主要不足：

1. 监督方法依赖攻击样本、攻击规则或先验攻击知识，难以覆盖未知攻击。
2. 浅层统计异常方法不能充分编码节点之间的复杂上下文，误报较多。
3. 深度序列或图模型在大规模审计日志上的训练、推理和内存开销过高。

MAGIC 的目标不是回答“谁实施了攻击”，而是回答：

> 在不使用攻击样本训练表示模型的条件下，能否从大规模 provenance graph 中高效找到偏离良性行为分布的批次和实体？

### 4.2 威胁模型

- 攻击者来自系统外部，并以系统中的高价值信息为目标。
- 攻击过程可以复杂，但会在审计日志中留下可观测痕迹。
- 硬件、操作系统和审计软件被视为可信计算基。
- 正文明确把 poisoning 和 evasion 排除在威胁模型之外。
- 训练期需要覆盖“截至当前的全部良性系统行为”；若良性覆盖不足，作者承认会产生较多误报。
- 批级和实体级任务均假定日志来自一致的数据源，没有验证跨企业、跨主机族或跨审计框架的零样本迁移。

附录 A 虽然又做了简单图扰动实验，但该实验使用无模型反馈、无内部参数访问的弱攻击者，不能改写正文威胁模型的边界。

## 5. 方法框架

### 5.1 总流程

```text
Raw audit logs
  -> parse entities and interactions
  -> provenance graph construction and edge reduction
  -> masked graph autoencoder
       -> masked feature reconstruction
       -> sampled structure reconstruction
  -> benign node or whole-graph embeddings
  -> KNN distance model over benign embeddings
  -> anomaly score
       -> batch-level APT alarm
       -> entity-level suspicious entity list
  -> optional analyst-confirmed feedback adaptation
```

### 5.2 Provenance graph 构建

- 节点代表进程、文件、socket/netflow 等系统实体。
- 有向边代表 execute、read、write、connect 等交互。
- 复杂属性先通过哈希或类型映射转换为离散标签，再映射为初始特征。
- 同一节点对之间、同一类型的重复边只保留一条。
- 若同一节点对仍有多种边类型，则把这些边的初始嵌入平均成一条边。
- 论文称该处理在 E3 Trace 上平均减少 `79.60%` 的边。

这个压缩非常适合降低 GNN 开销，却会删除 Project05 调查控制需要的细节：

- 事件发生次数；
- 精确时间和先后顺序；
- 重复交互的频率；
- 原始 UUID 和字段来源；
- 压缩边到原始事件的回指。

因此，MAGIC 官方预处理图可用于复现其检测器，不能直接作为 Project05 的真实证据回放数据。

### 5.3 掩码图表示学习

训练时随机掩码约 `50%` 的节点初始特征，边特征不掩码。编码器使用多层 GAT，把源节点及边类型的信息传播到目标节点。目标是让模型从邻域上下文恢复被遮住的节点类型，并保留足以描述图结构的信息。

训练损失由两部分组成：

```text
L = L_feature_reconstruction + L_structure_reconstruction
```

- `L_feature_reconstruction`：被掩码节点的原始特征与重建特征之间的 scaled cosine error，论文设缩放指数 `gamma = 3`。
- `L_structure_reconstruction`：现有边作为正样本、无边节点对作为负样本，用两层 MLP 和二元交叉熵预测节点对是否相连。
- 整图表示由节点表示池化得到，用于批级任务；节点表示直接用于实体级任务。

### 5.4 KNN 异常检测

表示模型只学习良性行为。检测阶段把良性嵌入存入近邻索引，对目标嵌入计算其 K 个最近良性邻居的平均欧氏距离：

```text
raw_distance(x) = mean distance from x to its K nearest benign embeddings
score(x) = raw_distance(x) / mean benign-neighbor distance
```

若 `score(x) >= theta`，就把目标批次或实体判为异常。

这部分没有学习“攻击类别”，而是把“远离良性表示空间”解释为“潜在 APT”。所以它能发现未知行为，也天然会把新的良性软件、罕见管理操作和环境变化当作异常。

### 5.5 两阶段部署

作者建议先做计算较便宜的批级筛查，只对阳性批次运行实体级检测：

```text
all log batches
  -> batch-level detector
  -> suspicious batches only
  -> entity-level detector
  -> suspicious processes/files/connections
```

该设计的本质是告警过滤，不是序贯调查规划。两阶段顺序固定，没有根据当前证据缺口、行动成本或预期信息增益动态选择下一步。

### 5.6 模型适应

- 分析师确认的反馈可用于重新训练图表示模块，因为该模块本身不读取攻击标签。
- KNN 检测器只能加入被确认的良性样本。
- 当记忆容量超过限制时，系统删除最早的良性嵌入。

这不是自主闭环：系统仍需要分析师先判断 FP/TN。论文没有评估标签延迟、分析师成本、错误反馈、攻击者诱导反馈、灾难性遗忘或自动触发重训练的条件。

## 6. 数据集与实验设计

### 6.1 数据集

| 任务 | 数据集 | 主要规模 | 攻击性质 |
|---|---|---:|---|
| 批级 | StreamSpot | 600 批；500 良性、100 attack | SystemTap 控制环境模拟 |
| 批级 | Unicorn Wget | 150 批；125 良性、25 attack | CamFlow 供应链攻击模拟 |
| 实体级 | DARPA TC E3 Trace | 15.40 GB；3,220,594 个良性节点；68,082 个攻击相关节点 | 红蓝对抗环境 |
| 实体级 | DARPA TC E3 THEIA | 17.91 GB；1,598,647 个良性节点；25,319 个攻击相关节点 | 红蓝对抗环境 |
| 实体级 | DARPA TC E3 CADETS | 18.38 GB；1,614,189 个良性节点；12,846 个攻击相关节点 | 红蓝对抗环境 |

论文合计处理约 `131 GB` 审计日志。E3 三个子集包含约 `6.54M` 个实体和 `68.13M` 次交互。

### 6.2 论文声称的划分

- StreamSpot：从 500 个良性批次中随机取 400 个训练，余下 100 个良性批次与 100 个攻击批次测试。
- Wget：100 个良性批次训练，25 个良性批次与 25 个攻击批次测试。
- DARPA E3：按事件发生顺序，前 80% 训练、后 20% 测试；表示训练只使用良性样本。
- 论文报告 100 个全局随机种子的平均结果。

这些是论文正文的表述。官方代码的实际处理与此并不完全一致，见第 9 节。

### 6.3 标注

- 主实验沿用 THREATRACE 的实体标签。
- 附录 G 还描述了替代标注流程：从 ground-truth 报告中提取关键攻击实体名称，匹配日志中的实体，再沿邻域扩展攻击相关节点。
- 这里的正类更接近 `attack-relevant entity`，不等于“每个实体自身执行了恶意动作”。
- 邻域扩展会把被读取文件、动态库或上下游依赖纳入正类，标签粒度与真实 SOC 的“需要生成一个独立告警”并不相同。

## 7. 论文报告的结果

### 7.1 主结果

| 数据集 | Precision | Recall | FPR | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| StreamSpot | 99.41% | 100.00% | 0.59% | 99.71% | 99.95% |
| Unicorn Wget | 98.02% | 96.00% | 2.00% | 96.98% | 96.32% |
| E3 Trace | 99.17% | 99.98% | 0.09% | 99.57% | 99.99% |
| E3 THEIA | 98.23% | 99.99% | 0.14% | 99.11% | 99.87% |
| E3 CADETS | 94.40% | 99.77% | 0.22% | 97.01% | 99.77% |

E3 测试集共 `1,386,046` 个实体，其中 `106,246` 个被标为攻击相关。这个正类比例远高于自然运营环境中的真实告警基率，因此不能只凭实体级 FPR 推导生产告警负担。

### 7.2 失败类型

作者明确观察到：

- 主动发起行为的恶意进程和网络连接更容易被检出。
- 恶意文件、动态库等被动实体更容易成为 FN，因为它们的交互行为与普通文件相似。
- 作者认为这些被动实体可在后续 attack story recovery 中由已检出的进程带出，但论文没有真正评估这一步，也没有报告攻击链恢复完整率。

### 7.3 与其他方法比较

论文比较了 StreamSpot、UNICORN、Prov-Gem、THREATRACE、DeepLog、Log2vec 和 ShadeWatcher。MAGIC 在列出的多数数据集上取得最高或接近最高的 Precision/F1/AUC，并声称比 ShadeWatcher 在 E3 Trace 上快约 51 倍。

该比较不是完全同协议：

- 各方法使用的监督信息不同；
- 部分数值来自原论文而不是统一复现；
- train ratio、标签、阈值和预处理不完全一致；
- 规则/查询驱动的 POIROT、HOLMES、MORSE 被排除，因为任务设置不同。

因此可以支持“MAGIC 在其协议下是一种有竞争力的异常检测器”，不能支持“它普遍优于所有 APT 检测与调查方法”。

### 7.4 误报适应

E3 Trace 的 FPR：

| 设置 | FPR |
|---|---:|
| 80% train，无适应 | 0.089% |
| 20% train，无适应 | 0.426% |
| 20% train + 后续 20% FP | 0.272% |
| 20% train + 后续 20% FP/TN | 0.220% |
| 20% train + 后续 40% FP/TN | 0.173% |

结果说明已确认的良性反馈有用，但没有和分析师标注成本一起报告，也没有检验反馈错误或攻击污染。

### 7.5 性能开销

E3 Trace：

| 阶段 | GPU 时间 | CPU-only 时间 | 峰值内存 |
|---|---:|---:|---:|
| 图构建 | N/A | 642 s | 2,610 MB |
| 表示训练 | 151 s | 685 s | 1,564 MB |
| 检测器训练 | 78 s | 78 s | 1,320 MB |
| 表示推理 | 5 s | 10 s | 2,108 MB |
| KNN 检测 | 825 s | 825 s | 1,667 MB |

真正的瓶颈是 KNN，而不是 GAT。作者自己承认，检查 684,111 个目标耗时约 13.8 分钟，占推理时间的 99%。论文把 KD-tree 单次查询写成近似 `O(log N)`，但在 64/256 维空间中 KD-tree 会受维度灾难影响，实际扩展性不能仅由该渐近式保证。

## 8. 论文层面的优点

1. 任务定位清楚：只用良性行为建模，避免把未知攻击检测伪装成已知类别分类。
2. 方法组合合理：掩码特征重建降低训练成本，采样结构重建保留部分拓扑监督。
3. 同时提供批级和实体级输出，比只给整图告警的 UNICORN 更接近调查入口。
4. 公开代码、预处理数据和模型检查点，至少允许检查主要实现逻辑。
5. 不回避被动文件实体的漏检、训练数据覆盖要求和 KNN 瓶颈。
6. 把图表示开销与检测器开销拆开报告，工程分析比只报 F1 更完整。

## 9. 官方代码审计：需要降级解读的关键问题

本节审计对象是 2026-07-13 访问到的官方仓库 `main` 分支。以下是复现风险判断，不等同于已经完成独立重跑后的学术不端指控；正式引用这些差异前应固定 commit 并复现实验。

### 9.1 高风险：批级表示模型看过测试良性图

官方 `utils/loaddata.py` 的 `load_batch_level_dataset()` 把所有标签为良性的批次放入 `train_index`。`train.py` 用这个完整集合训练图表示模型。随后 `model/eval.py` 才随机挑出 400/100 个良性嵌入训练 KNN，并把剩余良性批次作为测试。

结果是：

- KNN 检测器没有直接使用测试标签训练；
- 但上游图编码器已经自监督看过全部良性测试图；
- 这是 transductive test exposure，不是正文描述的端到端严格留出。

它会让测试良性分布更容易被编码，从而可能降低 FP。

### 9.2 高风险：实体训练集通过 ground truth 清除攻击实体

官方 `utils/trace_parser.py` 在生成训练图时读取恶意实体 ID 集合，并跳过与已知恶意实体相连的大部分事件。也就是说，“只用良性训练”并非完全来自一个天然干净的历史窗口，而是借助 ground truth 对训练数据做了 oracle cleaning。

这削弱了“无需攻击知识”的部署主张：真实部署时，系统通常不知道训练窗口内哪些实体属于尚未发现的 APT。

### 9.3 高风险：Trace 的测试构造不是简单的后 20%

当前 parser 中，Trace 的测试文件列表包含前四个训练文件和最后一个文件。评估脚本随后：

- 从前几个重叠文件中只保留恶意实体作为测试正类；
- 丢弃这些重叠文件中的良性实体；
- 对最后一个文件保留全部实体。

这不是正文所述的普通 `earliest 80% train / last 20% test`。正负类来自不同的时间选择规则，且部分正类来自与训练文件重叠的时期。

### 9.4 高风险：测试标签直接参与阈值选择

官方 `model/eval.py`：

- 批级任务在 `y_test` 上计算 precision-recall curve，并选择测试集 F1 最大的阈值。
- 实体级任务也在 `y_test` 上计算 PR curve，再按预设目标 recall 找阈值；目标值与论文表中的高召回结果高度对应。

因此：

- AUC 本身不依赖单一阈值，仍可反映当前测试构造下的排序能力。
- Precision、Recall、FPR、F1 是 test-label-tuned operating point，不能当作标签不可见时的部署表现。
- 正确协议应只用训练/验证期良性数据按目标 FPR 校准阈值，再冻结到测试集。

### 9.5 中高风险：论文与代码的模型/参数不一致

| 项目 | 论文描述 | 官方代码 |
|---|---|---|
| GAT 层数 | 实现部分称统一 3 层 | 批级 4 层，实体级 3 层 |
| KNN 的 K | `k = 10` | StreamSpot 8，Wget 2，Trace/THEIA 10，CADETS 200 |
| 检测嵌入 | 初始表示与各 GAT 层输出拼接 | `embed()` 返回最后一层 GAT 输出 |
| 结构重建样本 | 非掩码节点上的现有边与负边 | 代码从全图随机采至多 10,000 条正边和负边，未按论文表述排除掩码节点 |
| 100 seeds | 论文称报告全局随机种子平均 | 发布的批级脚本重复 KNN 划分；表示模型固定，实体级函数返回 0 标准差 |

这些差异未必全部改变结论，但会阻碍逐项复现，也说明不能只根据正文公式重实现后期待得到同一数值。

### 9.6 中风险：测试集参与特征空间定义

实体级 loader 同时扫描 train 和 test 图来确定 one-hot 特征维度；parser 也可在处理测试图时扩充类型字典。这是轻度 transductive vocabulary exposure。对类型数量很少的数据可能影响有限，但“跨源泛化”主张因此更弱。

### 9.7 数据可复用边界

官方 `graphs.zip` 中是序列化后的图对象，而 parser 最终只保留整数节点及 node/edge type。原始 UUID、事件时间、重复边、参数字段和边到原始 CDM 记录的映射未随图保存。

结论：

- 可用于快速复现 MAGIC 的图异常检测。
- 不可用于 Project05 的 evidence item、channel、cost、recoverability、时间窗或真实原始记录回指。
- Project05 应继续使用自己保存的 DARPA TC 原始日志和确定性 adapter，不应把 MAGIC 预处理包替换为主数据。

## 10. 证据质量分级

| 论文主张 | 证据强度 | 判断 |
|---|---|---|
| 掩码图表示可在这些基准上区分良性与攻击相关实体 | 中 | 多数据集 AUC 很高，但受标签构造与划分协议影响。 |
| 不使用攻击信息即可完成训练和部署 | 低 | 正文如此表述，官方实体 parser 实际使用恶意 ID 清洗训练图。 |
| 报告的低 FPR 可直接迁移到真实 SOC | 低 | 测试标签选阈值、正类基率异常高，且无自然运营部署。 |
| 图表示模块比重型图方法更高效 | 中高 | 给出分阶段时间/内存，且表示训练确实较快；跨论文比较仍非统一硬件协议。 |
| 模型适应能应对真实 concept drift | 低到中 | 有受控反馈实验，无错误反馈、长期漂移或生产部署。 |
| 对对抗操纵具有鲁棒性 | 低 | 附录仅做弱威胁模型下的合成扰动。 |
| 方法具有跨源 universality | 低 | 在多个公开源上分别训练和调阈值，不是跨源迁移。 |

## 11. 主要局限

### 11.1 构造效度

- “异常实体”不是“APT actor”，也不是完整攻击链。
- DARPA 实体标签是攻击相关性标签，不能直接等价于逐实体恶意性。
- 批级 StreamSpot 中不同用户场景天然分离，容易把场景分类能力误读成 APT 检测能力。
- 用节点/边类型即可达到近乎完美 AUC，可能部分反映数据生成和标注规律，而非真实未知 APT 的普遍结构特征。

### 11.2 内部效度

- 测试表示暴露、oracle cleaning、标签选阈值和特殊 Trace 测试构造会抬高部署指标。
- 没有严格的 host-level 或 engagement-level 独立留出。
- 100 seeds 并非发布脚本中的完整端到端重训。

### 11.3 外部效度

- 没有真实企业自然运营数据。
- 没有跨组织、跨审计源或跨 OS 迁移实验。
- 没有在线流式端到端延迟、长期告警率或分析师研究。
- 作者声称 Trace 上实体检测约 40 个 FP/天、两阶段约 24 个 FP/天，但这仍是 DARPA 受控数据上的换算。

### 11.4 安全性

- 主威胁模型排除日志篡改、poisoning 和 evasion。
- 反馈适应可能把攻击行为逐步吸收到“良性”记忆中，论文未做长期污染测试。
- FIFO 删除最早嵌入可能忘掉低频但合法的周期行为。

### 11.5 可解释性

MAGIC 的“可解释输出”主要是可疑实体 ID 和异常分数，不是因果解释：

- 不说明哪些原始事件支持判断；
- 不输出最小证据路径；
- 不给出反事实或缺失证据；
- 不说明当前证据最多支持到什么结论粒度；
- 不生成可核查的自然语言调查叙事。

## 12. 与相关 provenance 方法的位置关系

| 方法 | 主要粒度 | 主要输出 | 与 MAGIC 的关系 |
|---|---|---|---|
| UNICORN | 系统/批级 | graph sketch anomaly | MAGIC 增加实体级节点表示，并换用 masked GAE + KNN。 |
| THREATRACE | 实体级 | 异常节点与追踪 | 与 MAGIC 最接近；MAGIC强调无监督表示与效率。 |
| PROGRAPHER | snapshot + indicator | 异常快照与关键节点 | PROGRAPHER 建模时间序列；MAGIC 基本丢弃时间顺序。 |
| KAIROS | 边/攻击图 | 异常边与 attack summary graph | KAIROS 更接近攻击故事重建；MAGIC 更像候选实体筛选。 |
| DEPCOMM | POI 驱动调查 | 压缩 dependency graph / InfoPath | DEPCOMM 从已知 POI 向外调查；MAGIC 负责发现潜在 POI。 |
| CLIProv | 日志到情报语义 | TTP 和 attack scenario | CLIProv 做语义对齐；MAGIC 只做结构异常。 |

## 13. 对 Project05 论文主线的意义

### 13.1 可放在技术路线哪里

MAGIC 最适合成为一个可替换的上游观察器：

```text
raw provenance events
  -> MAGIC-like detector
  -> anomaly score + suspicious entity candidates
  -> Project05 evidence compiler
  -> evidence-gap state
  -> cost-aware acquisition / STOP
  -> granularity-controlled investigation conclusion
```

它提供候选，不提供事实真值。Project05 必须保留：

- 异常分数来源；
- 候选实体到原始事件的回指；
- 该信号属于哪个 evidence channel；
- 不确定性与可能误报；
- 后续动作能验证或反驳什么 claim。

### 13.2 它没有撞掉当前主贡献

MAGIC 不研究：

- `intended evidence != recoverable evidence`；
- 部分可观测证据缺口状态；
- 有成本的下一步证据获取；
- 何时 STOP；
- G0-G3 结论粒度截断；
- 调查计划不能读取动作执行后的真实恢复集合。

所以它与当前“信息边界约束下的证据缺口驱动调查控制”主线直接撞题风险低。真正的风险是写作时把自己的贡献退回成“用图神经网络检测 APT”，那会直接进入 MAGIC、THREATRACE、PROGRAPHER、KAIROS 已高度拥挤的区域。

### 13.3 能否作为实验输入或 baseline

可以，但有三种不同强度：

1. **低成本使用**：把已有 anomaly score 作为一种证据源，测试 Project05 是否会错误地把高异常分数当作归因真值。
2. **中成本使用**：实现一个严格留出、固定阈值的简化 MAGIC，作为上游候选排序器。
3. **高成本复现**：在原始 E3 上完整复现官方 pipeline，并修复划分和阈值协议。当前论文主线不需要立即承担这项工程。

对现阶段最合理的是第 1 种；若投稿 reviewer 要求上游 detector sensitivity，再做第 2 种。

## 14. 对 Agent 支线的意义

MAGIC 自身不是 Agent，但可作为 Agent 的一个工具：

```text
detect_batch(log_window)
rank_suspicious_entities(graph)
score_entity(entity_id)
```

Agent 支线不能把“Agent 调用 MAGIC 再总结”当创新。更有空间的方向是：

> 面向图异常检测盲点的证据审计 Agent：把 detector 输出视为可错观察，主动选择原始事件、进程祖先、网络上下文、文件信誉和 CTI 证据进行验证，在预算约束下确认、反驳或保持弃权。

这个方向的真正变量是验证策略、信息边界、证据引用和停止条件，不是再训练一个 masked GNN。它和当前主线有方法复用关系，是否独立成 Agent 支线需继续与 SherAgent、ExCyTIn-Bench、IRCopilot 等工作做撞题矩阵。

## 15. 对多模态支线的意义

- MAGIC 只有 provenance graph 一种模态。
- 它不处理 CTI 文本、截图、二进制、网络包或自然语言报告。
- 将 MAGIC 图嵌入与 CTI 文本直接对齐的朴素方案会撞 CLIProv、APT-CGLP 等图文对齐工作。
- 更合理的多模态问题不是“融合后分类更准”，而是比较不同模态对特定 evidence gap 的可恢复性、成本和相互矛盾，并让系统决定是否需要再采一种模态。

## 16. 若要复现，必须采用的修正版协议

1. 按时间、主机或 engagement 冻结 train/validation/test，编码器不得看到测试图。
2. 训练窗口中若含攻击，不得用测试 ground truth 静默删除；应报告污染鲁棒性，或使用明确独立的干净训练期。
3. node/edge vocabulary 只由训练集建立，测试未见类型使用 `UNK`。
4. 阈值只由训练/验证良性数据按目标 FPR 校准，测试标签只用于最终一次评估。
5. 固定并公开 K、层数、嵌入维度、采样规模和随机种子。
6. 端到端重复训练，而不是只重复 KNN 划分。
7. 同时报告 AUC-ROC、AUPRC、固定 FPR 下 recall、alerts/day、case-level detection 和 attack-chain coverage。
8. 保留 UUID、timestamp、edge multiplicity 和 raw-event backlinks，防止高分检测器无法进入后续调查。
9. 单列 passive entity 召回，不能用“后续可能恢复”替代实验。
10. 对 concept drift 报告分析师反馈量、错误反馈敏感性和长期污染风险。

## 17. 撞题风险矩阵

| Project05 候选表述 | 风险 | 原因 |
|---|---:|---|
| 基于 masked graph learning 的 APT detection | 5/5 | MAGIC 已直接覆盖。 |
| 自监督 provenance entity anomaly detection | 5/5 | MAGIC 与 THREATRACE 等已覆盖。 |
| 批级到实体级两阶段检测 | 5/5 | MAGIC 的明确部署方案。 |
| 图异常结果的 LLM 文本总结 | 4/5 | 技术贡献弱，且 SHIELD/CLIProv 等已有解释或语义层。 |
| 图异常候选作为调查 Agent 工具 | 2/5 | 工具层被覆盖，Agent 决策层仍有空间。 |
| 不完整证据下的成本敏感补证与 STOP | 1/5 | MAGIC 没有动作、成本、缺口状态或停止决策。 |
| 多模态证据可恢复性和冲突驱动采集 | 2/5 | MAGIC 不做多模态，需另查相邻工作。 |

## 18. 可直接用于写作的边界句

英文：

> Provenance-based detectors such as MAGIC can rank anomalous batches and system entities from audit graphs, but they neither determine whether the available evidence is sufficient for an investigation claim nor decide which evidence should be acquired next under a cost and information boundary.

> MAGIC's multi-granularity detection distinguishes batch-level from entity-level alarms; it should not be conflated with conclusion-granularity control, which limits what an investigator may claim from incomplete evidence.

中文：

> MAGIC 等 provenance 检测器能够从审计图中筛选异常批次和异常实体，但并不判断现有证据是否足以支持某一级调查结论，也不在成本与信息边界约束下决定下一步应获取何种证据。

## 19. 我的批注与最终判断

- 这是一篇需要认真引用的 USENIX Security 论文，但引用位置应是“上游 provenance anomaly detector”，不是“APT 归因方法”。
- 方法思想成立：掩码图表示加近邻异常检测确实是高效、合理的未知行为筛选方案。
- 论文数值不能照单全收。官方代码暴露的划分、标签清洗和阈值选择问题足以让我们对 FPR/F1 做明显降级解读。
- 最值得 Project05 吸收的不是 GAT，而是“异常候选仍需后续调查”这一接口位置。
- 最值得 Project05 避免的是把压缩后的节点异常分数当成可审计证据；没有原始事件回指，就无法支持证据充分性、补证动作和归因粒度门控。
- 当前不建议为了论文主线立即完整复现 MAGIC。先把它写入 Related Work 和上游接口边界；只有在 reviewer 要求上游 detector sensitivity 时，再按第 16 节的严格协议实现简化版。

## 20. 结论评级

- 与 Project05 当前论文主线的相关性：4/5，属于重要上游工作
- 对主线的直接撞题风险：1/5
- 对“图异常检测”类备选方案的撞题风险：5/5
- 方法可借鉴性：3/5
- 官方数据对当前真实证据实验的可复用性：1/5
- 论文表面可复现性：4/5
- 经代码审计后的严格可复现性：2/5
- 是否进入核心文献：是，但归入 `provenance detection / upstream evidence generator`

## 21. 来源与代码核验入口

- [USENIX 官方论文页面](https://www.usenix.org/conference/usenixsecurity24/presentation/jia-zian)
- [USENIX 官方开放 PDF](https://www.usenix.org/system/files/usenixsecurity24-jia-zian.pdf)
- [官方代码仓库](https://github.com/FDUDSDE/MAGIC)
- [批级与实体级主训练入口](https://github.com/FDUDSDE/MAGIC/blob/main/train.py)
- [批级与实体级主评估入口](https://github.com/FDUDSDE/MAGIC/blob/main/eval.py)
- [数据加载与批级划分](https://github.com/FDUDSDE/MAGIC/blob/main/utils/loaddata.py)
- [DARPA E3 parser 与标签清洗](https://github.com/FDUDSDE/MAGIC/blob/main/utils/trace_parser.py)
- [掩码图自编码器实现](https://github.com/FDUDSDE/MAGIC/blob/main/model/autoencoder.py)
- [KNN、阈值与测试指标实现](https://github.com/FDUDSDE/MAGIC/blob/main/model/eval.py)
