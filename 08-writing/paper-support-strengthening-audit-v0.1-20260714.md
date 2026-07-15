# 论文支撑度增强审计 v0.1（以 cost 为模板的可加固点）

- 日期：2026-07-14
- 对象：`paper-main-draft-v0.8-human-annotation-round1-20260713.md`
- 方法：以 `cost-assignment-standard-v0.1-20260714.md` 的思路为模板——找"人为设定、影响巨大、缺权威依据"的参量，用 `02-literature-notes/` 的文献给出grounding/对照/威胁
- 依据：本仓 76 篇文献笔记的三路系统复核（评估/不确定性、AFA/RL/规划、归因/融合/合成数据）

> ⚠️ 引用核验：以下文献的具体数字与题名来自笔记摘要，正式写入论文前须回原文核对（尤其 `Prasad-Survey`、`von Kleist`、各专利号）。带 🔴 的是**红线**：既是可用支撑，又与本项目专利或"官方复现"边界冲突，需谨慎。

---

## 0. 结论先行

`cost` 不是孤例。它属于一类"**松散赋值、结果杠杆极大**"的参量。论文里同型的还有至少 5 个，其中 3 个是与 `cost` 完全同构的"任意旋钮"（W1 粒度阈值、W7 OR/AND 覆盖语义、W2/W6 权重与 expected_effects），另外 2 个是严谨性审计已列的 Major 缺口，但**现在能用文献部分补上**（W3 人工一致性失败、W4 缺真实终点）。

优先级（按"审稿人最先开火 × 修复性价比"）：

| 级别 | 加固点 | 类型 | 一句话 |
|---|---|---|---|
| **P0** | W1 粒度阈值 G0-G3 | 任意旋钮（cost 孪生） | 0.75/0.60/≥2 阶段无出处，却决定全部 success |
| **P0** | W7 OR/AND 覆盖语义 | 任意旋钮（cost 孪生） | C11 成本 3.67 vs 1.02 只因 AND↔OR，必须给corroboration依据 |
| **P0** | W3 人工一致性失败 | Major 缺口，可补 | κ=-0.1455 需"领域固有难"叙事 + codebook 重设 |
| **P1** | W4 缺真实终点 | Major 缺口，可补 | 无 actor 正确率/分析师效用，可先上 over-attribution/abstention 终点 |
| **P1** | W2 M2 权重 | 任意旋钮 | 需重构为 VoI 线性化 + α 扫描 |
| **P1** | W6 expected_effects/通道先验 | 任意旋钮（cost 孪生） | 同 cost 一样是拍脑袋数字，用同一 rubric 处理 |
| **P2** | W5 AFA 端点契约 | 诚实性 | von Kleist missing-aware 评测直接背书我们的 masking |
| **P2** | W9 信息边界新颖性 | 叙事加固 | 用评测泄漏/去标识文献强化 |

---

## P0-1 · W1：粒度阶梯 G0-G3 与数值阈值（cost 的结构孪生）

**问题**：论文 §3.2 的阈值——节点覆盖 ≥0.75 进 G3、≥0.45 且 ≥2 阶段进 G2、≥0.15 进 G1——是纯人为设定，却直接决定所有 success/ceiling 结果。论文自己也只称其为"结构代理"。这与 `cost` 是同一种病。

**审稿人怎么打**：为什么是 0.75 不是 0.7？换阈值结论是否翻转？（正是你对 cost 的质疑）

**文献支撑（来自笔记）**：
- 🟢 **grounding 阶梯本身（而非具体数字）**：`2025-Prasad-Cyber-Threat-Attribution-Survey` 的五级归因阶梯（基础设施→恶意软件族→campaign→APT 组织→国家/动机），说明"归因天然是多级、不同层级需要不同证据与置信表达"——直接为 G1/G2/G3 的**分层设计**背书。
- 🟢 `2025-Horst-High-Stakes-Low-Certainty`：**relative vs absolute attribution** 的二分，且实测 TTP 可分性极低（同 RTA 重叠 0.37、跨 RTA 0.21、silhouette≈-0.087）——支撑"高粒度需要更强证据，低粒度更可复现"的门槛逻辑。
- 🟢 `2026-Saha-Kitten-or-Panda`：仅约 34% ATT&CK 组有组特异技术，融合后仍约 64% 组无任何组特异行为——**量化说明为何 G3/actor 级往往不可达**，天然降级有据。
- 🟢 `2026-Weinberg-ARCANE`：贝叶斯累积证据后置信仍在 **0.15-0.20 plateau**——支撑"有上限、需截断"。
- 🔴 `2021-US20210281585A1`（专利）：high/moderate/low 置信 + information gap + 补充狩猎建议——**与我们 G-ladder + STOP/降级几乎同构**，是最强 grounding，但它是**专利先例**，同时对我们自己的专利是碰撞项，双刃。

**建议动作**：
1. 把 G0-G3 明确写成"**既有归因层级框架（Prasad 阶梯 / relative-vs-absolute Horst）在受控实验中的离散实例化**"，把权威性落在"分层"而非"0.75"上。
2. 具体数值坦承为约定，用**已有的三档阈值敏感性**（Lenient/Default/Conservative）证明结论不被具体切点驱动——这正是 cost 的三臂稳健思路，你已有一半。
3. 引 Saha/Weinberg 把"G3→G2 自然降级"从"数据缺陷"重述为"**领域固有的可分性上限**"。

---

## P0-2 · W7：OR/AND 覆盖语义（cost 的另一结构孪生）

**问题**：C11 中 M2 成本 3.6667（AND）vs 1.0222（OR），Oracle 同样 3.0→1.02。一个二值开关就把成本改了 3.6 倍，却只在 §6.8 描述、无原则性依据。这是比 cost 更尖锐的"松散大杠杆"。

**审稿人怎么打**：AND 是不是为了让数字好看而选的？corroboration 门槛的合法性何在？

**文献支撑（来自笔记）**：
- 🟢 `2023-Teuwen-Opinion-Pools`：**对数意见池（几何平均）"强调被所有模块共同支持的 actor"**——这正是 AND 的数学表达；且 Pairing Aggregator 在 40% false-flag 注入下 F1 0.813 vs 单体 0.614，**证明"要求多源一致"对抗误导证据更稳健**。这是 AND 默认的最强 grounding。
- 🟢 `2026-Duan-MLDSJ`：Dempster-Shafer 组合多源；作者自承"未知拒绝更强，但已知细粒度更弱"——支撑"多源合取提升稳健、牺牲覆盖"的取舍。
- 🟢 `2026-Ghanem-WinRegRL`：状态含 **corroboration level**，强 corroboration 给 +100 奖励——取证 RL 里 corroboration 是一等公民。
- 🔴 `2021-US20210281585A1`：**tool correlation + TTP correlation + unique-techniques 阈值**共同决定置信——多源合取先例（专利，双刃同上）。
- 🟢 反面支撑（为何 OR 不安全）：`Saha`（34% 组特异）、`Horst`（silhouette -0.087）、`2026-Balassone-Synthetic-APTs`（AI 仿真体在无预设情况下**收敛**到相同 TTP）——**单源/OR 覆盖会被非特异或收敛证据误导**。

**建议动作**：
1. 把 AND 定为**主分析**并给出原则依据一句："节点覆盖要求**独立多源 corroboration**（对数意见池 / DS 融合语义），OR 仅作乐观敏感性下界"。
2. 用 Teuwen 的 false-flag 稳健性 + Saha/Horst 的低可分性，论证 OR 在对抗/非特异证据下**不可靠**，从而 AND 不是任意选择而是保守正确选择。
3. 保留 OR/AND 双报（已有），措辞上从"语义敏感性"升级为"corroboration 强度的可识别消融"。

---

## P0-3 · W3：双人盲标首轮未过门槛（最硬的 Major，但可叙事化）

**问题**：Claim weighted κ=-0.1455、Intent Jaccard=0.3673/F1=0.4878，均未过预注册门槛；粒度文件 A/B 哈希相同待确认。这是 rigor review 的 Major 1。

**文献支撑（来自笔记）**：
- 🟢 **对照锚点（说明这是难任务而非做砸了）**：`2025-Horst` 主题分析 Krippendorff α=0.872（**但那是"证据是否充分"这类较易任务，2 coder**）；`2026-Cheng-CTIConnect` κ=0.85（GPT-4 vs 专家，QA 校验）；`2025-Mitra-LocalIntel` Fleiss κ=0.6477（3 SME，"substantial"）。→ 用它们说明 CTI 任务**能**达到高一致的，是"证据充分性/QA"类；而我们失败的是**"公开意图/claim 支持"这类本质模糊的判断**。
- 🟢 **固有难度证据**：`2025-Guru`（GPT-4 vs MITRE TTP Jaccard 0.39±0.12、漏 41%）、`2025-Mezzi`（APT 标签 precision/recall 低至 0.02）、`2026-Meng`（LLM-CTI 失败源于表面元数据虚假关联、冲突源、新威胁泛化）、`Saha`（标签本质多义：2,260 多标签样本）——**共同证明 claim/intent 判断在人和模型上都不可靠是领域结构性的**。
- 🟢 **正面 codebook 实践（供 round 2 借鉴）**：`2024-Saha-ADAPT-it` 在 Malpedia/MITRE 标签冲突时用**双研究者裁决**流程——正是我们第三人裁决的先例。

**建议动作**：
1. 讨论区把首轮失败从"我们的 codebook 差"重述为"**该判断的固有难度**"（引 Guru/Mezzi/Meng/Saha），同时**不淡化**——保持诚实叙事。
2. codebook round 2 具体改进（文献驱动）：
   - Claim 任务加**负例**（当前 source_pointer 全是 "yes"，无法检验错误指针识别——这是 κ 崩塌的直接技术原因）；
   - Intent 任务把"单一直接目标 vs 宽意图集合"的歧义写成**显式判定规则**（当前 25/27 分歧都出在这）；
   - 报告时并列 Horst/CTIConnect/LocalIntel 的 κ 作为"CTI 任务可达一致度谱系"。
3. 粒度哈希异常：在确认独立性前不写"perfect agreement"（rigor 红线 9，已守住）。

---

## P1-1 · W4：缺真实终点（Major 6，可先上"选择性/弃权"终点）

**问题**：无 actor 正确率、无分析师效用；内部 success ≠ 归因准确率。这是重要性主张的天花板。

**文献支撑（可直接采纳的终点/指标）**：
- 🟢 `2026-Barnes-OpenSec`：**EGAR（evidence-gated action rate）、Correct Abstention Rate、Over-Attribution Rate、TTFC、blast radius**——几乎为我们量身定制的"证据受限下的正确弃权/过度归因"指标族。
- 🟢 `2026-Williams-High-Precision-APT-Malware-Attribution`：**selective accuracy（~95%）+ coverage + OOS rejection（~94%）**——开集+弃权范式，可套到"证据不足时降级/拒答"。
- 🟢 `2025-Xiao-TAA-EPLMR`：**over-attribution rate** + **Dataset-Full / Incomplete / Noise** 三分——可直接借来做"不完整证据仍强行给 actor 标签"的可证伪终点。
- 🟢 `2024-Alam-CTIBench`（CTI-TAA）：50 去标识报告，**correct/related/incorrect** via Malpedia 别名 + MITRE related-group 图——低成本 actor 级代理终点。
- 🟢 `2025-ExCyTIn-Bench`：investigation-graph 锚定的多跳 QA（7,542 题）+ 记录 query 步数/成本——最接近我们的"调查控制 + 成本"终点。
- 🟢 `2022-Xu-DEPCOMM`：**attack-step coverage / evidence precision-recall / 人工检查工作量**——分析师效用型终点，不需要 actor GT。

**建议动作**：**即使拿不到 actor GT，也先加一个"证据受限终点"**——推荐组合：over-attribution rate（TAA-EPLMR）+ correct abstention/EGAR（OpenSec）+ selective accuracy/coverage（Williams）。这把"我们不做 actor 分类"从**缺陷**变成**被文献认可的 selective-prediction 立场**。中期再引 CTIBench/ExCyTIn/SAGA 做外部终点。

---

## P1-2 · W2：M2 奖励权重（cost 同类）

**问题**：`2Δg+1.5Δu+1.5Δr+1.5d_stage+d_evidence-1.5o-r_zero-0.75ρ_c` 是工程设定。已有 ±25% 单权重扰动，但缺理论出处。

**文献支撑**：
- 🟢 `2025-Aronsson-AFA-Survey`：AFA 标准打分 **Δ₁=I(y;x_a|x_S)−α·c_a**（信息增益 − α·成本）——把 M2 重述为该 **VoI−成本** 目标的**可解释线性化**。
- 🟢 `2025-NOCTA`：**α 逐数据集扫描**出成本-性能曲线——为"权重不是唯一真值、要扫描"提供先例（与你的 cost 三臂一致）。
- 🟢 `2025-Horst`：从业者对证据**非对称加权**（勒索信/泄露站/C2 > TTP）——支撑"不同项不同权重"是领域常态而非任性。

**建议动作**：把 M2 定位为"VoI−成本目标的领域线性化"，各项对应 Δ粒度/Δ不确定性/Δ风险的公开代理；系数做 α/权重扫描（已有），叙事上引 Aronsson+NOCTA。

---

## P1-3 · W6：expected_effects 与通道先验（cost 的直接孪生，最易被忽略）

**问题**：`acquisition_actions.json` 里每个动作的 `expected_granularity_gain / expected_uncertainty_reduction / expected_over_attribution_risk_reduction / expected_coverage_delta` 以及通道可靠性先验，**全部是人为数字**，和 cost 一模一样，但目前完全没被质疑到。M2/AFA-VOI/Depth-2 都吃这些数字。

**文献支撑**：
- 🟢 `2026-Ghanem-WinRegRL`：转移 **P_expert** 由 GCFE/GCFA 专家图设定、奖励表 -10…+100、观测分 **absent/weak/partial/strong/conflicting**，且"学习转移=future work"——**专家设定先验 + 明确其为未来工作**正是我们的合法先例。
- 🟢 `2025-NOCTA`：训练期用完整未来轨迹的 **plug-in 效用**、成本外生——先验来自可核验来源而非直觉。
- 🟢 `2025-Aronsson`：默认**确定性 reveal** 转移 + 分组采集（一个动作揭示一束特征）——与我们"通道→claim bundle"一致。

**建议动作**：把 §2（cost 标准）的 rubric/measured/perturbation 三臂**推广到 expected_effects**：要么用数据实测（如实际粒度增益、实际覆盖 delta），要么显式声明为专家先验（引 WinRegRL）并做敏感性。**否则审稿人用你自己对 cost 的逻辑反打 expected_effects。**

---

## P2 · W5 / W9：诚实性与新颖性叙事加固

- **W5（AFA 端点契约）**：🟢 `2025-Aronsson` 引的 **von Kleist missing-aware evaluation（native missing vs 实验性 masked 的区分）** 直接**背书我们的 masking 方法学与公开/隐藏边界**——这是意外强的一击，建议显式引用。domain-transfer 合法性引 `2026-DDQN-malware`、`NOCTA`。
- **W9（信息边界/节点级泄漏新颖性）**：🟢 `2024-Alam-CTIBench` 去标识防答案泄漏、`2025-Qiu-APT-CGLP` 仅用良性日志预训练避免泄漏、`2024-Jia-MAGIC` 明确"检测器不决定不完整证据支持何种结论粒度"、`2026-Barnes-OpenSec` 对抗性证据校准——共同把我们的"运行时公开视图 allowlist / 节点级泄漏审计"放进**评测污染/答案泄漏**这一更被认可的问题谱系。

---

## 竞品区分（避免"你只是 X 加规划"）

来自笔记的最近竞品分两条道，需一句话切割：
- **归因分类器道**（会被要求对比）：`TAA-EPLMR`(Micro-F1 0.861)、`APT-MMF`(0.8321)、`AURA`、`Cai-APT-ATT`、`Au-HKG`、`Duan-MLDSJ`、`King-TRAIL`——它们在**不完整证据下直接输出 actor**。
- **调查控制道**（最像我们）：`ExCyTIn-Bench`（优化 QA 正确率）、`NOCTA`（临床、确定性 reveal、无失败动作）、🔴`Varonis US12530469`（告警 TP/FP 三分，非粒度门）、`WinRegRL`（artefact 恢复效率，非归因终点）。

**切割句（可直接用）**：最近的**分类器**在不完整证据下强行输出 actor；最近的**调查器**优化 QA 正确率或告警三分——没有一个做"**对齐感知的粒度门控 + AND corroboration 下面向可支撑归因层级的成本感知取证**"。

---

## 落地清单（按 P0→P2）

- [ ] W1：重写 §3.2，把 G-ladder 归因到 Prasad 阶梯 / relative-vs-absolute；G3→G2 降级引 Saha/Weinberg。
- [ ] W7：把 AND 立为主分析并引 Teuwen 对数意见池 + false-flag 稳健性；OR 降为乐观下界。
- [ ] W3：讨论区加"领域固有难度"叙事（Guru/Mezzi/Meng/Saha）+ 一致度谱系（Horst/CTIConnect/LocalIntel）；round 2 codebook 加 Claim 负例、Intent 显式判定规则。
- [ ] W4：新增证据受限终点（over-attribution + correct abstention/EGAR + selective accuracy）。
- [ ] W2/W6：把 cost 三臂标准推广到 M2 权重与 expected_effects；引 Aronsson/NOCTA/WinRegRL。
- [ ] W5/W9：显式引 von Kleist missing-aware + CTIBench/APT-CGLP/MAGIC 加固边界叙事。
- [ ] 相关工作补"竞品两条道 + 切割句"。
- [ ] 全部引用回原文核验；专利类（US20210281585A1 等）先与专利碰撞矩阵对齐再入稿。

---

## 参考（笔记内文件，供定位；数字待核）

评估/不确定性：`2025-Prasad-Cyber-Threat-Attribution-Survey`、`2025-Horst-High-Stakes-Low-Certainty`、`2026-Saha-Kitten-or-Panda`、`2026-Weinberg-ARCANE`、`2023-Teuwen-Opinion-Pools`、`2024-Alam-CTIBench`、`2026-Barnes-OpenSec`、`2026-Williams-High-Precision`、`2025-Mezzi-LLMs-Unreliable-CTI`、`2025-Guru-Technique-Identification`、`2026-Meng-Vulnerabilities-LLM-CTI`、`2026-Cheng-CTIConnect`、`2025-Mitra-LocalIntel`、`2024-Saha-ADAPT-it`、`2025-ExCyTIn-Bench`。
AFA/RL/规划：`2025-Aronsson-AFA-Survey`、`2025-NOCTA`、`2026-Ghanem-WinRegRL`、`2026-Adaptive-Malware-DDQN`、`2025-Basnet-APT-DRL`、`2025-Qiu-APT-CGLP`、`2024-Jia-MAGIC`。
归因/融合/合成：`2026-Duan-MLDSJ`、`2024-Xiao-APT-MMF`、`2025-Xiao-TAA-EPLMR`、`2024-Huang-SAGA`、`2026-Balassone-Synthetic-APTs`。
专利红线：`2021-US20210281585A1`、`2025-US12368730B2`、`2026-Varonis-US12530469`。
