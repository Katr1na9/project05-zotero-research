# Project05 贡献边界与结果简报 v0.1

日期：2026-07-10  
状态：M4 压力测试后冻结版；**技术主线 = M3a**  
对应 RQ：[topic-rq-brief-v2.1-g1-final-20260706.md](../03-ideas/topic-rq-brief-v2.1-g1-final-20260706.md)

## 1. 一句话定位

Project05 不做新的 CTI–provenance 对齐器，也不做可学习效用模型升级；当前可辩护技术主线是：

> 把对齐结果建模为可更新的证据缺口状态，用公开的 **action→CTI-gap 兼容性（M3a）** 在成本约束下规划取证，并在通道不可靠 / 目标不可达时显式 **STOP/降级**。

## 2. 冻结的方法定义（主线）

### 2.1 状态

- CTI 行为图节点/边覆盖、关键缺口、可支撑归因粒度（G0–G3+）。
- 输入来自对齐器输出；本仓库用 OR 节点覆盖语义的模拟器实例化。

### 2.2 动作与信息边界

- 动作公开字段：`intended_cti_node_ids`、`cost`、`acquisition_channel`、手写 `expected_*`（M3a **不依赖**后者）。
- 隐藏字段：`recoverable_claim_ids` 仅用于环境实现与 Oracle；规划器不可读。
- **P0-#1**：通道可靠性把门控“声明目标 ≠ 实际恢复”；`network_telemetry` 先验 0.5，可靠回退在其他通道。

### 2.3 规划器：`project05_m3a_gap_compat`

打分只用公开状态与公开意图：

```text
score ∝ critical_gap_hits + gap_hits + precision + recall − λ·cost
STOP 的 break-even utility = 0
```

不读隐藏恢复结果、不读 Oracle 路径。

### 2.4 停止语义

- 显式 `STOP`：零成本结束，接受当前粒度。
- `correct_degrade_stop` / `justified_degrade_stop`：目标不可达时与 Oracle 一致的认输。
- `premature_stop`：Oracle 仍可达时过早停止。

### 2.5 明确降级为对照（非主线）

| 组件 | 角色 |
|---|---|
| M1 / M2 | 负基线（静态 expected gain / 粗粒度反馈） |
| logistic M3b（静态/自适应） | **冻结对照**：学到通道先验，但相对 M3a 无稳定独立成功率优势 |
| coverage / CMI proxy / random | 弱基线 |
| Oracle | 成本下界与可行性上界 |

**不再推进**：在 logistic 上加层、同质 decoy 加压、GNN/RL 取证规划（除非换问题设定）。

## 3. 结果总表（可引用数字）

数字来自 2026-07-10 通道可靠性门控后的重跑产物。

### 3.1 常规矩阵（通道门控后）

| 设定 | Planner | success | mean cost† | mean zero-yield |
|---|---|---:|---:|---:|
| Toy C01–C03 | Oracle | 0.9778 | 2.49 | 0.01 |
| Toy C01–C03 | **M3a** | **0.9556** | **2.67** | 0.20 |
| Toy C01–C03 | M2 | 0.8000 | 3.73 | 0.62 |
| Real C04–C06 | Oracle | 1.0000 | 1.79 | 0.00 |
| Real C04–C06 | **M3a** | **0.9778** | **1.77** | 0.07 |
| Real C04–C06 | M2 | 0.8000 | 1.77 | 0.24 |

† `mean_cost_to_target`（仅达标 episode）。产物：`09-experiments/results/m3a_{toy,real}_cases/`。

### 3.2 M4 压力（真实案例，toy 训练 / real 测试协议下的对照表）

| 压力 | 干预 | Oracle | M3a | 静态/自适应 M3b | 要点 |
|---|---|---:|---:|---:|---|
| 通道离线 | 仅离线 seed | 1.00 | 0.94 | 0.96 / 0.96 | 可靠回退仍在；M3b 略省成本，非质变 |
| 真正应停 | 离线 + 剥回退 | 0.81 / stop=1.0 | **对齐 Oracle** | **对齐 Oracle** | 会停；M3b 无额外停止优势 |
| 部分可达选路 | 离线 + 预算=`C*`，保留回退 | 1.00 | **0.00** | 0.10 / 0.10 | 会停 ≠ 会选路；M3b 近负 |
| 同质 twin decoy | 公开不可区分零收益 | — | — | 自适应失效 | 负对照：反馈帮不上忙 |

细节：`04-progress/m4-*.md`。

### 3.3 诊断性（不可当独立泛化）

- C06 挑战子集曾显示 M3a 修复 M2 的节点级错选（27/27 vs 5/27，P0-#1 前快照）。
- **C06 / R03 已用于 M2 诊断 → 不得写成最终 holdout 或跨数据集泛化。**

## 4. 可以主张 / 不可以主张

### 4.1 可以主张

1. **问题设定**：对齐之后的证据状态 + 成本约束主动取证 + 粒度门控停止，区别于“再做一个对齐器/分类器”。
2. **表示假设**：节点级 action–gap 兼容性优于 stage/type 粗覆盖与静态 expected gain（M3a ≫ M2/M1）。
3. **信息边界纠错**：声明目标与实现恢复必须解耦（通道可靠性）；否则 `intended_cti_node_ids` 会泄题。
4. **停止机制**：真不可达时强规划器可与 Oracle 对齐 `justified_degrade`；弱规划器过早停。
5. **负结果也是贡献**：logistic 条件效用与反馈自适应，在当前设定下**不能**稳定超越 M3a 选路。

### 4.2 不可以主张

1. 跨数据集泛化（尚无未参与设计的 E5/OpTC 真留出）。
2. “首次 MDP/RL 主动取证”（撞 WinRegRL 等红线）。
3. “可学习效用 / GCEU-Net 已验证”（M3b 已冻结为近负对照）。
4. C06 为独立 holdout。
5. LLM 在线效用预测或自由归因（LLM 仅限语义编译/解释，未进主循环）。
6. 部分可达紧预算下 M3a 已会可靠选路（当前失败；属已知边界）。

## 5. 专利 / 论文叙事骨架（对齐 M3a）

可写权利要求/章节主轴：

```text
对齐感知证据缺口图
  → 公开动作意图（intended CTI nodes）与通道先验
  → 成本约束下的 gap-compat 序贯选择
  → 达标停止 / 不可达降级停止
  → 再对齐更新状态
```

避开：宽泛“LLM 多轮拉数据调查”、单独“CTI–provenance 对齐算法”、宽泛“MDP/RL 取证”。

## 6. 主线下一步（按优先级）

1. **真留出 C07**：DARPA TC **E5**（优先 THEIA/ClearScope，异于 E3 CADETS/FiveDirections）或 **OpTC** 红队日；协议见 `08-writing/c07-true-holdout-protocol-v0.1-20260710.md`。冻结 M3a 公式后再编译案例。
2. **专利 v0.3**：按第 5 节骨架重写，替换 v0.2 的旧粒度门控表述。
3. **可选增强（仍属 M3a 主线，非 M3b）**：为 `intended_cti_node_ids` 增加可审计的 LLM/规则映射协议（离线标注，不进效用模型）；扩充噪声/误导动作空间后再测 M3a 鲁棒性。
4. **明确不做**：logistic/GNN/RL 升级；再堆同构 decoy/离线压力。

## 7. 关键产物索引

| 类型 | 路径 |
|---|---|
| M3a 实现 | `09-experiments/scripts/run_mvp.py`（`m3a_gap_compat_score`） |
| 通道/STOP/Oracle | 同上；M4 CLI 在 `run_m3b.py`（仅评估入口） |
| P0-#1 | `04-progress/p0-1-break-feature-leak-channel-reliability-20260710.md` |
| M3a 实验 | `04-progress/m3a-action-gap-compatibility-experiment-20260710.md` |
| M4 套件 | `04-progress/m4-*.md` |
| 本简报 | `08-writing/contribution-boundary-and-results-brief-v0.1.md` |
| C07 协议 | `08-writing/c07-true-holdout-protocol-v0.1-20260710.md` |
