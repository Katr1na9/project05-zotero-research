# 取证动作成本（acquisition cost）赋值标准 v0.1

- 日期：2026-07-14
- 适用对象：Project05 主动取证动作规划中 `acquisition_actions.json` 的 `cost` 字段
- 状态：方法学草案（供论文/专利"成本建模"小节与审稿答辩使用）
- 关联代码：`run_mvp.py`（cost/benefit 比、预算门控、精确最小成本 oracle、`cost_regret_vs_oracle`）、`plot_budget_efficiency.py`

---

## 0. 问题陈述（为什么现状不可辩护）

现状：9 个真实案例的动作成本全部是人工直觉给的小整数 `cost ∈ {1,2,3,4}`，
无任何书面依据。而 `cost` 是**决定全部主结论的枢纽参量**：

- M2 与各 baseline 的"成本-收益"比较（`run_mvp.py` 的 planner 打分、`cost_regret_vs_oracle`）；
- 预算约束下的可达性（budget gating）；
- 预算效率 Pareto 曲线（`plot_budget_efficiency.py`）。

只要有人手动改 `cost`，主结论就会大幅移动。因此"权威性"不能靠**把某一组成本调得更漂亮**来获得。
文献里也**没有任何工作能给你"唯一正确的成本向量"**——成本永远是一个建模选择。

**本标准的核心命题：**成本的可辩护性来自三件事同时做到，而不是某一组数字本身。

1. **溯源性（provenance）**：把成本分解为**可观测、可测量**的运营分量，每个数字都能追溯到证据学/运营事实，而非直觉。
2. **可通约性（commensurability）**：成本与收益必须在**同一决策论量纲**下比较（价值-信息理论）。
3. **稳健性（robustness）**：既然任何具体成本向量都是建模选择，真正的辩护是证明**结论在一段可辩护的成本区间内不变**（敏感性分析 + Pareto 前沿）。只在某一手挑成本向量下成立的结论，不算结论。

---

## 1. 文献支撑（权威佐证）

### 1.1 "acquisition cost" 是被公认的成本类别（不是我们发明的）

| 文献 | 关键论点 | 对本项目的作用 |
|---|---|---|
| **Turney, P.D. (2000). "Types of cost in inductive concept learning." ICML Workshop on Cost-Sensitive Learning.** | 归纳学习成本的权威分类；明确区分 **feature/test acquisition cost**（测量、时间、金钱）与 misclassification cost。 | 我们的 `cost` 属于其中的 *cost of tests / attribute acquisition*，有名有据。|
| **Melville, Saar-Tsechansky, Provost, Mooney (2004). "Active Feature-Value Acquisition for Classifier Induction." ICDM.** / **Saar-Tsechansky, Melville, Provost (2009). "Active Feature-Value Acquisition." *Management Science* 55(4):664–684.** | AFA 的标准框架：在**给定采集预算**下，按信息价值增量增量式采集；成本作为外生给定量。含 **Sensitivity Analyses** 一节（见 §4）。| 直接对应"下一步取哪条证据"；给出"成本外生 + 预算 + 信息价值"的标准骨架。|
| **Ji, S. & Carin, L. (2007). "Cost-sensitive feature acquisition and classification." *Pattern Recognition* 40(5):1474–1485.** | 用 **POMDP** 把顺序测量成本与误分类成本统一，低成本测量先做、必要时再上高成本测量。 | 对应我们 POMDP-ish 贪心/非贪心 planner；"先便宜后昂贵"的采集次序有理论依据。|
| **Elkan, C. (2001). "The Foundations of Cost-Sensitive Learning." IJCAI.** | 成本敏感决策的规范基础：最优决策依赖成本与概率的**乘积**，成本尺度可辩护性至关重要。 | 论证"成本尺度必须显式、可核验"。|
| **Dinh et al. (2025/2026). "NOCTA: Non-Greedy Objective Cost-Tradeoff Acquisition." arXiv:2507.12412.** | 纵向数据下非贪心 AFA，统一评估预测收益与 acquisition cost；含 adaptive stopping。成本是外生、固定、可加的相对权重：Synthetic 为 1/1，ADNI 的 PET/MRI 为 1/0.5，OAI 为 0.3/0.5/0.8/1.0。 | 支撑“给定成本后做计划级权衡”，但其成本仍由作者按模态和 effort 手工指定，未用真实运营量、专家一致性或成本敏感性验证；不能作为本项目直觉整数的充分辩护。|

### 1.2 成本与收益的通约：价值-信息理论

- **Howard, R.A. (1966). "Information Value Theory." *IEEE Trans. Systems Science and Cybernetics* 2(1):22–26.**
  信息的价值必须同时考虑**概率结构**与**经济后果（效用）**，据此可给"消除/减少某项不确定性"赋一个**与成本同量纲**的货币/效用值（EVPI/EVSI 的思想源头）。
  → 结论：`cost` 必须与"归因粒度收益 / 不确定性下降"折算到同一效用轴上，否则 cost/benefit 比无意义。这为 `run_mvp.py` 中"收益项 − λ·cost"式打分提供规范依据，并要求 λ（成本换算系数）显式化、可做敏感性分析。

### 1.3 成本的**大小与次序**从何而来：数字取证权威规范（本项目的关键锚）

这是把"直觉整数"变成"有据数字"的核心。数字取证界对"先取什么证据、代价几何"有成文规范：

| 规范 | 权威论点 | 映射到 `cost` 的分量 |
|---|---|---|
| **RFC 3227 (Brezinski & Killalea, 2002). "Guidelines for Evidence Collection and Archiving."**（IETF BCP） | **Order of Volatility（易失性次序）**：从最易失到最不易失依次采集（寄存器/缓存 → 路由表/ARP/进程表/内存 → 临时文件系统 → 磁盘 → 远程日志 → 物理配置/拓扑 → 归档介质）。 | **易失性/时效性分量 V**：越易失、保留窗口越短 ⇒ 采集时机代价越高（错过不可逆，对应 NOCTA 的 longitudinal 约束）。|
| **NIST SP 800-86 (Kent, Chevalier, Grance, Dang, 2006). "Guide to Integrating Forensic Techniques into Incident Response."** | 采集优先级取决于三因素：**Volatility**、**Amount of Effort Required**、以及数据的**预期价值/相关性**。其中 *Effort* 明确包含：分析师与相关人员（含法务）时间、设备与外部服务费用；并举例"从路由器取数据 vs 从远程 ISP 取数据"所需 effort 差异极大。 | **努力分量 E**（人时/工具/法务/外部服务）、**访问/边界分量 A**（跨主机、跨组织、需授权/取证令）。|

> 权威结论（可直接进论文）：成本不应是单一直觉标量，而应是**易失性(V) + 采集努力(E) + 访问/合规开销(A)** 等**可观测运营分量**的函数——这正是 NIST SP 800-86 采集计划三因素的操作化。

---

## 2. 成本赋值标准（可操作的分解式）

把每个动作 a 的成本分解为 5 个**带锚点定义**的分量，各自 0–3 分（0=可忽略，3=极高）：

| 代号 | 分量 | 锚点（0 / 1 / 2 / 3） | 权威来源 |
|---|---|---|---|
| **E** | 采集/分析努力 | 0=一次现成查询；1=常规日志查询；2=多步/跨源关联或需专用工具；3=需人工逆向/取样分析 | NIST 800-86 "Amount of Effort" |
| **V** | 易失性 / 时效压力 | 0=归档介质/长期留存；1=磁盘/长窗口日志；2=短保留窗口日志；3=内存/进程/近实时易失态 | RFC 3227 Order of Volatility；NOCTA longitudinal |
| **D** | 数据规模 / 扫描量 | 0=单条记录；1=单主机小窗口；2=单主机大窗口/多进程；3=跨主机大规模扫描 | 可从数据集**实测**（事件数/字节数）|
| **A** | 访问 / 合规 / 边界 | 0=本地已授权；1=同域跨主机；2=需提权/新授权；3=跨组织/法务/外部服务 | NIST 800-86（法务、外部专家、路由器 vs ISP 例）|
| **R** | 侵入性 / 取证风险 | 0=只读旁路；1=轻微；2=可能扰动在线系统；3=有改动证据/中断业务风险 | RFC 3227（"remove external avenues for change"）|

**合成公式（默认等权，权重需在 §3 预注册）：**

```
raw(a) = w_E·E + w_V·V + w_D·D + w_A·A + w_R·R          （默认 w_* = 1）
cost(a) = clip(round(raw(a) / s), 1, C_max)              （s 使量纲落回既有 {1..4} 带）
```

- 保留既有 `{1..4}` 整数带以**向后兼容**已冻结实验；`s` 为量纲缩放常数，记录在 case 元数据里。
- 允许 `cost` 为连续值（代码已 `float(action["cost"])`），故"实测版"（§3 Arm C）可直接用测量量，不必取整。

> 关键纪律：**本标准的交付物是"如何得到成本"的程序，而不是又一组手调数字。** 谁都不许为了让某个 planner 好看而回头改分量分。

---

## 3. 校准与验证协议（让它在答辩中站得住）

1. **预注册（pre-registration）**：先冻结上表锚点与权重 `w_*`、缩放 `s`，**且在看任何 planner 结果之前**完成全部动作打分。写入 case 元数据与本文件的附录。这一步直接封杀"成本被反向调参"的质疑。
2. **双人独立标注 + 一致性**：每个动作的 5 个分量由两名标注者独立打分，报告 **ICC / 加权 Kappa**。本仓库已有成熟的盲标 + 一致性设施（`build_annotation_packets.py`、`analyze_annotation_agreement.py`），成本分量标注可直接复用同一流水线。
3. **能测就不猜**：把 D（数据规模）、V（保留窗口天数）、A（跨主机数）尽量替换为从 DARPA E3/E5、OpTC、OTRF、WitFoo **实测**的量（事件数、字节数、host 跳数、日志窗口跨度）。把直觉降级为测量，是提升权威性的最有效一步。
4. **三臂成本稳健性设计（面向审稿的核心防御）**——同一结论必须在三种成本口径下同时成立：
   - **Arm A · Uniform**：所有 `cost=1`（去掉一切成本设计；已有 `m1_no_cost` planner 可作近似对照——它直接屏蔽 cost 字段）。
   - **Arm B · Graded rubric**：本 §2 预注册评分（当前 `{1..4}` 的"有据版"）。
   - **Arm C · Measured**：由 §3.3 实测量导出的连续成本。
   
   若 M2 相对 baseline 的**排序**在 A/B/C 下一致，则"成本设计驱动了结论"的质疑不成立。
5. **敏感性分析**：对 Arm B 的成本向量做扰动——整体缩放（×0.5 / ×2）、加噪、分量权重网格、交换相邻次序——报告 planner 排序与 `cost_regret_vs_oracle` 的稳定性。Provost/Melville 的 AFA 论文正是用专门的 *Sensitivity Analyses* 一节这样做的。
6. **报告 Pareto 前沿而非单一预算点**：以"归因粒度/成功率 vs. 累计成本"作 Pareto 曲线（对接现有 `plot_budget_efficiency.py`、`cost_to_target`、`cost_regret_vs_oracle`），呈现整条效率前沿。这与成本敏感特征选择的 **cost-Pareto / ROC-Convex-Hull-with-Cost（ROCCHC）** 报告范式一致，避免"只在某个预算下赢"。

---

## 4. 论文可用句式（英文）

- "Acquisition cost is treated as an exogenous, decomposable quantity in the standard active-feature-acquisition sense (Turney, 2000; Saar-Tsechansky et al., 2009), rather than a hand-tuned scalar."
- "Costs are grounded in the two operational factors that digital-forensics practice uses to prioritize evidence collection—**order of volatility** (RFC 3227) and **amount of effort required** (NIST SP 800-86)—operationalized as an anchored, pre-registered rubric with reported inter-rater reliability."
- "Because any fixed cost vector is a modeling choice, we do not claim a single 'correct' cost. Instead we report planner rankings under uniform, rubric-based, and dataset-measured cost regimes, together with a sensitivity analysis and a cost–granularity Pareto frontier; our conclusions hold across all three regimes."

---

## 5. 落地检查清单

- [ ] 在 case 元数据中为每个动作补 5 分量原始打分 + 权重/缩放常数（预注册）。
- [ ] 双人标注成本分量，跑 ICC/Kappa，写入结果。
- [ ] 用真实数据实测 D/V/A，产出 Arm C 成本表。
- [ ] 在 `run_mvp.py` 增加成本口径开关（uniform / rubric / measured），或以外部成本表注入，避免改动已冻结产物。
- [ ] 出敏感性分析表 + cost–granularity Pareto 图。
- [ ] 若涉及重跑已冻结实验，另立版本（不覆盖 v0.2 冻结基线）。

---

## 参考文献

1. Turney, P. D. (2000). *Types of cost in inductive concept learning.* Proc. Workshop on Cost-Sensitive Learning, ICML 2000, 15–21.
2. Melville, P., Saar-Tsechansky, M., Provost, F., & Mooney, R. (2004). *Active Feature-Value Acquisition for Classifier Induction.* ICDM 2004. doi:10.1109/ICDM.2004.10075.
3. Saar-Tsechansky, M., Melville, P., & Provost, F. (2009). *Active Feature-Value Acquisition.* Management Science 55(4), 664–684. doi:10.1287/mnsc.1080.0952.
4. Ji, S., & Carin, L. (2007). *Cost-sensitive feature acquisition and classification.* Pattern Recognition 40(5), 1474–1485. doi:10.1016/j.patcog.2006.11.008.
5. Elkan, C. (2001). *The Foundations of Cost-Sensitive Learning.* IJCAI 2001, 973–978.
6. Howard, R. A. (1966). *Information Value Theory.* IEEE Trans. Systems Science and Cybernetics 2(1), 22–26. doi:10.1109/TSSC.1966.300074.
7. Brezinski, D., & Killalea, T. (2002). *Guidelines for Evidence Collection and Archiving.* RFC 3227 / BCP 55, IETF.
8. Kent, K., Chevalier, S., Grance, T., & Dang, H. (2006). *Guide to Integrating Forensic Techniques into Incident Response.* NIST SP 800-86.
9. Dinh, D., Chen, B., Qu, Y., Niethammer, M., & Oliva, J. (2025). *NOCTA: Non-Greedy Objective Cost-Tradeoff Acquisition for Longitudinal Data.* arXiv:2507.12412.
