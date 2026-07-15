# 方法学松散参量治理与支撑度加固方案 v0.1

- 日期：2026-07-14
- 对象：`paper-main-draft-v0.8-human-annotation-round1-20260713.md` 及其冻结实验
- 起因：复核发现 `cost` 是一个"人为设定即可大幅改变结论、却缺权威依据"的参量；本文把同类参量统一治理
- 姊妹文件：`cost-assignment-standard-v0.1-20260714.md`（cost 专项）、`paper-support-strengthening-audit-v0.1-20260714.md`（文献映射）
- 依据：本仓 76 篇 `02-literature-notes/` 的系统复核

> ⚠️ 两条硬边界：
> 1. **不改任何已冻结产物**（v0.2 盲标包、C07-C12 主结果的字节/哈希）。所有"调参"以**新臂 / 新版本**落地。
> 2. **引用待核**：带具体数字的文献来自笔记摘要，正式入稿前须回原文核对；带 🔴 的与本项目专利或"官方复现"边界冲突，需先对齐。

---

## 0. 为什么要专门治理这类参量

这类参量有两个共同病征，也是本文对每一项的打分维度：

- **意外性（结果杠杆）**：人手改一下，主结论（success / cost 排序 / 是否达标）就明显移动。意外性越高，越是"隐形的结论开关"。
- **宽松度（依据缺失）**：取值靠直觉，无书面出处、无测量、无敏感性。宽松度越高，越经不起审稿人一句"为什么是这个数"。

**核心命题（与 cost 文档一致）**：权威性不来自"把某组数字调得更漂亮"，而来自三件事同时做到——① 溯源（每个数字可追到可观测事实或既有标准）；② 可通约（成本/收益同量纲）；③ 稳健（结论在一段可辩护区间内不变）。因此下面每一项的"改进"都不是"重调一次"，而是**给出有据的默认值/范围 + 稳健性报告 + 冻结边界**。

---

## 1. 问题总览

| 编号 | 参量 | 意外性 | 宽松度 | 当前依据 | 可即时采纳？ |
|---|---|---|---|---|---|
| **C** | 取证动作 cost | 高 | 高 | 无（已成文治理） | 是（新臂） |
| **W1** | 粒度阈值 G0-G3（0.75/0.60/0.45/0.15、≥2 阶段） | 高 | 高 | 仅"结构代理" | 部分（阈值网格可即时） |
| **W7** | OR/AND 覆盖语义 | **极高**（C11：3.67↔1.02） | 高 | 仅描述性 | 是（重定为 corroboration 强度扫描） |
| **W2** | M2 奖励权重（2/1.5/1.5/1.5/1/-1.5/-1/-0.75） | 中 | 高 | ±25% 单权重扰动 | 是（VoI 重述 + α 扫描） |
| **W6** | 动作 `expected_effects` 与通道可靠性先验 | 高 | **极高**（完全未被质疑） | 无 | 部分（可测的即时、其余标专家先验） |
| **W3** | 双人盲标 codebook | 高 | 中 | 预注册门槛（已失败） | 是（round 2 设计，不动 v0.2） |
| **W4** | 评估终点 | 高 | 高 | 内部 success | 是（附加终点，不改现有表） |
| **W5** | AFA 端点契约 | 低 | 中 | 领域适配声明 | 是（叙事+契约） |
| **W9** | 信息边界新颖性叙事 | 低 | 中 | 三条接口性质 | 是（叙事加固） |

---

## 2. 逐项详述（现象 / 意外性 / 宽松度 / 文献依据 / 解决 + 调参 / 边界）

### C · 取证动作 cost（已单独成文，此处纳入统一框架）

见 `cost-assignment-standard-v0.1-20260714.md`。要点：拆为 5 分量 **E 努力 / V 易失性 / D 数据量 / A 访问合规 / R 侵入风险**（各 0-3，锚点定义见该文），合成后缩放回既有 `{1..4}` 带。依据 **RFC 3227 易失性次序** 与 **NIST SP 800-86 采集三因素（volatility + effort + value）**，通约依据 **Howard 1966 价值-信息理论**，稳健性用 **三臂（Uniform / Rubric / Measured）+ 敏感性 + Pareto**。

> **具体调参（新臂，不动冻结）**：以 C11 为例，`extend_log_window·scranton_powershell` 现值 2；按 rubric ≈ E1+V2+D2+A1+R0=6，缩放 s=2 → 3。此类重排只在新臂 `cost_arm=rubric` 下产生，主结果仍用现值。**目的不是改数字，而是让每个数字可溯源。**

---

### W1 · 粒度阈值 G0-G3 —— cost 的结构孪生

**现象**：§3.2 用 节点覆盖≥0.75→G3、≥0.45 且 ≥2 阶段→G2、≥0.15→G1 判级，决定全部 success/ceiling。

**意外性 高**：C07-C10 的 G3 实际由"关键节点全覆盖"主导（§6.7），但换库/换语义时阈值会显性影响达标；阈值是隐形达标开关。

**宽松度 高**：0.75/0.60 无任何出处，论文自称"结构代理"。

**文献依据**：
- `2025-Prasad-Survey`：归因五级阶梯（基础设施→恶意软件族→campaign→APT 组织→国家）——**分层本身**有据。
- `2025-Horst`：relative vs absolute attribution；TTP 可分性极低（silhouette≈-0.087）→ 高粒度需更强证据。
- `2026-Saha-Kitten-or-Panda`：仅 ~34% 组有组特异技术 → G3/actor 常不可达，天然降级有据。
- `2026-Weinberg-ARCANE`：证据累积后置信 0.15-0.20 plateau → 有上限、需截断。

**解决 + 调参**：
1. **叙事**：把 G-ladder 明确写成"Prasad 阶梯 / relative-vs-absolute 在受控实验中的离散实例化"；权威落在"分层"而非具体切点。
2. **调参（可即时，不动冻结主结果）**：把现有 3 档（Lenient/Default/Conservative）**扩成阈值网格**并出敏感性表——节点覆盖 ∈ {0.60,0.65,0.70,0.75,0.80}、边覆盖 ∈ {0.50,0.55,0.60,0.65}、阶段数 ∈ {2,3}，报告 success/ceiling 是否在网格内稳定。这是把"任意切点"变成"稳健区间"的正解。
3. **不做**：不发明"更权威的精确阈值"（文献给不出），避免用一个新任意值换旧任意值。

**边界**：网格敏感性是**新增分析**，不改 Default 主结果。

---

### W7 · OR/AND 覆盖语义 —— 意外性最高的开关

**现象**：C11 中仅把 `node_coverage_semantics` 从 AND 改 OR，M2 成本 3.6667→1.0222，Oracle 3.0→1.0222。

**意外性 极高**：一个二值开关 3.6 倍改成本，且改的是达标门槛本身。

**宽松度 高**：默认 AND 目前只有 §6.8 的描述性说明，无原则依据。

**文献依据**：
- `2023-Teuwen-Opinion-Pools`：**对数意见池（几何平均）"强调被所有模块共同支持的 actor"**——AND 的数学表达；Pairing Aggregator 在 40% false-flag 下 F1 0.813 vs 单体 0.614 → **要求多源一致对抗误导更稳健**。
- `2026-Duan-MLDSJ`：Dempster-Shafer 多源合取；"未知拒绝更强、已知细粒度更弱"的取舍。
- `2026-Ghanem-WinRegRL`：状态含 corroboration level，强 corroboration 给最高奖励。
- 反面（OR 不安全）：`Saha`(34%)、`Horst`(silhouette-0.087)、`2026-Balassone`（AI 仿真体收敛到相同 TTP）。
- 🔴 `2021-US20210281585A1`：多源相关 + unique-technique 阈值 → 置信（专利先例，双刃）。

**解决 + 调参（推荐即时采纳）**：
1. **把二值 OR/AND 升级为"corroboration 强度 k-of-n"可调参量**：节点被覆盖 ⟺ 其 required claims 中 ≥ k 条独立来源可见。OR = k=1（乐观下界），AND = k=n（保守主分析）。
2. **报告 k=1..n 的成本曲线**，把"语义敏感性"正式化为**corroboration 强度扫描**，并**将 AND(k=n) 立为主分析**，依据 Teuwen 对数意见池 + false-flag 稳健性。
3. 用 Saha/Horst 论证：单源(k=1)在非特异/对抗证据下不可靠，故保守 AND 不是任性而是正确默认。

**边界**：k-of-n 是对现有 OR/AND 的**推广**；C11 现有 AND 主结果与 OR 敏感性都是该曲线的端点，不需重定义已冻结结果，新增中间 k 值为新分析。

---

### W2 · M2 奖励权重 —— 与 cost 同类

**现象**：`2Δg+1.5Δu+1.5Δr+1.5d_stage+d_evidence−1.5o−r_zero−0.75ρ_c`。

**意外性 中**：已有 ±25% 单权重扰动显示 C07-C10 局部稳定（首动作一致率降到 0.8778、成本 +0.0222），但跨库排序会变。

**宽松度 高**：系数无理论出处，自称"工程设定"。

**文献依据**：
- `2025-Aronsson-AFA-Survey`：AFA 标准打分 **Δ₁ = I(y;x_a|x_S) − α·c_a**（信息增益 − α·成本）。
- `2025-NOCTA`：**α 逐数据集扫描**成本-性能曲线。
- `2025-Horst`：从业者对证据**非对称加权**（勒索信/C2 > TTP）是常态。

**解决 + 调参（可即时）**：
1. 把 M2 重述为"**VoI − α·cost 目标的可解释领域线性化**"：Δg/Δu/Δr 对应信息增益类项，ρ_c 对应 α·cost 项，各项系数是该线性化的领域权重。
2. 归一化各项到可比尺度后**暴露单一 α**（成本换算系数），做 α 扫描（对齐 NOCTA），并保留已有 16 个单权重扰动。
3. 引 Horst 说明"不同证据项不同权重"有领域依据。

**边界**：叙事重述 + α 扫描为新增；不改 Default M2 主结果。

---

### W6 · 动作 expected_effects 与通道先验 —— 宽松度最高、目前完全未被质疑

**现象**：`acquisition_actions.json` 每个动作的 `expected_granularity_gain / expected_uncertainty_reduction / expected_over_attribution_risk_reduction / expected_coverage_delta`，以及通道可靠性先验，全是人为数字；M2、AFA-VOI、Depth-2 都消费它们。

**意外性 高**：这些先验直接进 M2/AFA 打分与 Depth-2 期望效用，改它们等于改策略排序。

**宽松度 极高**：与 cost 一模一样是拍脑袋，但审计里此前从未被点名——**审稿人会用你对 cost 的逻辑原样反打。**

**文献依据**：
- `2026-Ghanem-WinRegRL`：转移 **P_expert** 由 GCFE/GCFA 专家图设定、观测分 **absent/weak/partial/strong/conflicting**、奖励 -10…+100，且"学习转移=future work"——**专家先验 + 明示为未来工作**的合法先例。
- `2025-NOCTA`：训练期用完整未来轨迹的 **plug-in 效用**；成本外生。
- `2025-Aronsson`：默认**确定性 reveal** + 分组采集（一动作揭示一束特征）。

**解决 + 调参（部分即时）**：
1. **能测就测**：`expected_granularity_gain`、`expected_coverage_delta` 可由每个动作在冻结案例里的**实际**粒度增益 / 覆盖 delta 反算替换（把直觉换成测量）。
2. **不可测的**（uncertainty/over-attribution reduction）显式声明为**专家先验**，引 WinRegRL 的 absent/weak/partial/strong/conflicting 分级作为标度，并做 ±25% 敏感性（与 M2 权重同法）。
3. 观测/reveal 语义引 Aronsson 的确定性 reveal + 分组采集，明确"通道→claim bundle"符合 AFA 标准形式。

**边界**：measured 版为新臂；专家先验敏感性为新增分析；不改冻结动作定义。

---

### W3 · 双人盲标 codebook —— 最硬 Major，可叙事化 + round 2 重设

**现象**：Claim weighted κ=-0.1455、Intent Jaccard=0.3673/F1=0.4878 未过门槛；粒度 A/B 哈希相同待确认。

**意外性 高**、**宽松度 中**（有预注册门槛，但 codebook 设计有技术缺陷）。

**文献依据**：
- 对照锚点（说明是难任务）：`Horst` α=0.872、`CTIConnect` κ=0.85、`LocalIntel` Fleiss κ=0.6477——都属较易的"证据充分性/QA"类。
- 固有难度：`Guru`（GPT-4 vs MITRE TTP Jaccard 0.39、漏 41%）、`Mezzi`（APT 标签 P/R 低至 0.02）、`Meng`（表面元数据虚假关联等失败族）、`Saha`（标签本质多义）。
- 正面 codebook 实践：`2024-Saha-ADAPT-it` 标签冲突时**双研究者裁决**（= 我们第三人裁决先例）。

**解决 + 调参（round 2，绝不动 v0.2）**：
1. **技术病根修复**：Claim 的 `source_pointer` 首轮全是 "yes"，无负例 → κ 必崩；round 2 **注入错误指针负例**，使"错误指针识别"可检验。
2. Intent 的 25/27 分歧集中在"单一直接目标 vs 宽意图集合"→ 写**显式判定规则**（如"只标动作直接指向的节点，不标下游可能受益节点"）。
3. **叙事**：讨论区把失败重述为"该判断的领域固有难度"（引 Guru/Mezzi/Meng/Saha），并列 Horst/CTIConnect/LocalIntel 作"CTI 任务可达一致度谱系"，同时**不淡化**首轮负结果（保持诚实，守 rigor 红线 8/9）。

**边界**：所有改动进 codebook round 2 与新一轮包；v0.2 冻结包与首轮 IAA 原样保留。

---

### W4 · 评估终点 —— 拿不到 actor GT 也能先上"证据受限终点"

**现象**：无 actor 正确率/分析师效用；内部 success ≠ 归因准确率（Major 6）。

**意外性 高**（决定重要性主张）、**宽松度 高**。

**文献依据（可直接采纳的指标）**：
- `2026-Barnes-OpenSec`：**EGAR / Correct Abstention Rate / Over-Attribution Rate / TTFC / blast radius**。
- `2026-Williams`：**selective accuracy(~95%) + coverage + OOS rejection(~94%)**。
- `2025-Xiao-TAA-EPLMR`：**over-attribution rate** + **Full/Incomplete/Noise** 三分。
- `2024-CTIBench`(CTI-TAA)：correct/related/incorrect via Malpedia 别名 + MITRE related-group 图。
- `2025-ExCyTIn-Bench`、`2022-DEPCOMM`（attack-step coverage / 人工检查工作量）。

**解决 + 调参（附加，不改现有表）**：新增一组**证据受限终点**——过度归因率（TAA-EPLMR）+ 正确弃权率/EGAR（OpenSec）+ selective accuracy/coverage（Williams）。把"我们不做 actor 分类"从缺陷升级为**被文献认可的 selective-prediction 立场**。中期再引 CTIBench/ExCyTIn/SAGA 做外部终点。

**边界**：这些是**附加指标**，可在现有 45/180 条件上直接计算，不改 success/cost 主表。

---

### W5 · AFA 端点契约 & W9 · 信息边界新颖性 —— 叙事加固（低意外性）

- **W5**：`2025-Aronsson` 引的 **von Kleist missing-aware evaluation（区分原生缺失 vs 实验性 masked）** 直接**背书我们的 masking 方法学与公开/隐藏边界**——建议显式引用；domain-transfer 合法性引 `DDQN-malware`、`NOCTA`。正式外部数值仍需先冻结 endpoint adapter（Major 4，维持现状）。
- **W9**：用 `CTIBench` 去标识防泄漏、`APT-CGLP` 仅良性日志预训练避泄漏、`MAGIC`"检测器不决定不完整证据支持何种粒度"、`OpenSec` 对抗性证据校准，把我们的"运行时 allowlist / 节点级泄漏审计"接入**评测污染/答案泄漏**这一被认可的问题谱系。

---

## 3. 统一治理协议（把 cost 三臂升级为通用规程）

对上述**每一个**参量，采用同一套可辩护流程：

1. **预注册**：先冻结取值规则/锚点/权重，且在看主结果之前完成赋值；写入案例元数据。
2. **溯源**：每个数字标注来源类型——`measured`（数据实测）/ `standard`（如 RFC3227/NIST/Prasad/Teuwen）/ `expert-prior`（显式声明，引 WinRegRL）。
3. **可通约**：成本/收益折算到同一效用轴（Howard VoI）。
4. **稳健三臂 + 敏感性**：
   - cost：Uniform / Rubric / Measured；
   - 粒度阈值：阈值网格；
   - 覆盖语义：k-of-n 扫描；
   - M2/expected_effects：α 扫描 + ±25% 权重扰动。
   结论必须在各臂/扫描内方向一致才可写。
5. **Pareto**：以"粒度/成功率 vs 累计成本"报告前沿（对接 `plot_budget_efficiency.py`），而非单点。
6. **一致性**：主观赋值（cost 分量、粒度标签、intent）双人标注 + ICC/Kappa（复用现成盲标流水线）。
7. **冻结边界**：一切重赋值以新臂/新版本落地；已冻结 v0.2/主结果字节不变。

---

## 4. 具体调参与改进建议汇总（"度"的显式声明）

| 参量 | 现值 | 文献锚定的建议 | 采纳方式 | 依据 |
|---|---|---|---|---|
| cost | {1..4} 直觉 | 5 分量 rubric + measured 版 | **新臂**，主结果不变 | RFC3227 / NIST800-86 / Howard |
| 粒度阈值 | 0.75/0.60/0.45/0.15 | 保留 Default，**加阈值网格敏感性** | **新增分析** | Prasad / Horst / Saha / Weinberg |
| 覆盖语义 | 二值 OR/AND | 推广为 **k-of-n**，AND=k=n 主分析 | **新增扫描**，端点=现结果 | Teuwen 对数意见池 / Duan DS |
| M2 权重 | 8 个手调系数 | 重述为 **VoI−α·cost**，暴露 α 并扫描 | **新增分析**，Default 不变 | Aronsson / NOCTA / Horst |
| expected_effects | 全直觉 | 可测项**实测替换**，其余标专家先验+敏感性 | **新臂**（measured）+ 新增敏感性 | WinRegRL / NOCTA / Aronsson |
| codebook | 首轮失败 | Claim 加负例、Intent 显式规则 | **round 2 新包**，v0.2 不动 | Guru/Mezzi/Meng/Saha/ADAPT-it |
| 评估终点 | 仅 success | 加 over-attribution/abstention/selective-acc | **附加指标** | OpenSec / Williams / TAA-EPLMR |

> **我把"度"定在这里**：所有建议都**不覆盖任何冻结科研记录**——要么是新臂、要么是新增敏感性/指标、要么进 round 2 新包。真正"改一个数就重跑主结果"的动作（如把 Default 阈值改成别的定值、把主 cost 表换成 rubric 值）**一律不做**，只作为"如需另立版本时的方向"。这样既补足了权威性，又不动研究诚信底线。

---

## 5. 落地清单（建议排期）

- [ ] **P0-W7**：实现 k-of-n 覆盖开关，出 C11 的 k=1..n 成本曲线；AND 立为主分析。
- [ ] **P0-W1**：扩阈值网格，出 C07-C12 稳健性表；§3.2 接 Prasad 阶梯。
- [ ] **P0-W3**：起草 codebook round 2（Claim 负例 + Intent 判定规则），讨论区加"固有难度 + 一致度谱系"。
- [ ] **P1-W6**：实测替换可测 expected_effects，其余标专家先验并做 ±25% 敏感性。
- [ ] **P1-W2**：M2 重述为 VoI−α·cost，加 α 扫描。
- [ ] **P1-W4**：新增证据受限终点三件套。
- [ ] **P2-W5/W9**：显式引 von Kleist + CTIBench/APT-CGLP/MAGIC 加固边界叙事。
- [ ] 全部引用回原文核验；🔴 专利项先与 `patent-claim-collision-matrix` 对齐。

---

## 6. 参考文献（合并 cost 与审计；数字待核）

**成本与决策论**
1. Turney (2000) Types of cost in inductive concept learning. ICML CSL Workshop.
2. Melville et al. (2004) Active Feature-Value Acquisition. ICDM.
3. Saar-Tsechansky, Melville, Provost (2009) Active Feature-Value Acquisition. Management Science 55(4).
4. Ji & Carin (2007) Cost-sensitive feature acquisition and classification. Pattern Recognition 40(5).
5. Elkan (2001) The Foundations of Cost-Sensitive Learning. IJCAI.
6. Howard (1966) Information Value Theory. IEEE TSSC 2(1).
7. Brezinski & Killalea (2002) RFC 3227 / BCP 55.
8. Kent, Chevalier, Grance, Dang (2006) NIST SP 800-86.
9. Aronsson et al. (2025) AFA Survey（含 schütz AFABench、von Kleist missing-aware evaluation）.
10. Dinh et al. (2025) NOCTA. arXiv:2507.12412.
11. Ghanem et al. (2026) WinRegRL.

**归因层级 / 不确定性 / corroboration**
12. Prasad (2025) Cyber Threat Attribution Survey.
13. Horst (2025) High Stakes, Low Certainty.
14. Saha (2026) Kitten or Panda（组特异性）.
15. Weinberg (2026) ARCANE Bayesian Attribution.
16. Teuwen (2023) Modular Threat Attribution / Opinion Pools.
17. Duan (2026) MLDSJ 多级 DS 融合.
18. 🔴 US20210281585A1 Confidence-Level Cyber Campaign Attribution（专利）.

**评估终点 / 可靠性 / 泄漏**
19. Barnes (2026) OpenSec.
20. Williams (2026) High-Precision APT Malware Attribution.
21. Xiao (2025) TAA-EPLMR.
22. Alam (2024) CTIBench.
23. Wu (2025) ExCyTIn-Bench.
24. Mezzi (2025) LLMs Unreliable for CTI.
25. Guru (2025) Technique Identification & Actor Attribution.
26. Meng (2026) Uncovering Vulnerabilities in LLM-Assisted CTI.
27. Qiu (2025) APT-CGLP.
28. Jia (2024) MAGIC.
29. Saha (2024) ADAPT-it.
30. Xu (2022) DEPCOMM.
