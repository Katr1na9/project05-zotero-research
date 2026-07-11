# Project05 论文主图契约 v0.1

日期：2026-07-11
后端：Python / matplotlib（独占）

## Figure 1：方法与信息边界

- 核心结论：部分 CTI-本地证据对齐不是流水线终点，而是成本约束主动取证闭环的可更新状态。
- 图形类型：schematic-led composite。
- 证据链：
  - a：输入、证据缺口状态、规划、通道执行、状态更新和 STOP/降级闭环。
  - b：规划器可见的公开动作意图/成本/历史反馈，与仅执行器和 Oracle 可见的实际恢复集合相隔离。
- 审稿风险：不能把 LLM 画成在线主模型；不能把隐藏恢复集合画成规划器输入；不能暗示 STOP 必然最优。
- 输出：双栏宽 183 mm；SVG、PDF、PNG、600 dpi TIFF；文本可编辑。

## Figure 2：真实留出与非短视 Gate

- 核心结论：M2 是当前最稳健的真实留出部署锚点；学习器尚未降低其成本；非短视需求成立但 DQN 必要性不成立。
- 图形类型：quantitative grid，a 为主面板。
- 证据链：
  - a：C07-C09 在 Oracle 相对紧预算下的 success 曲线，显示 M2 持续高于 M3a。
  - b：C07-C10 的序贯 success 与成功条件均成本，纳入冻结 Depth-2 Public；显示 M2/XGBoost/Depth-2 均达标，但 M2 成本更低且 Depth-2 未获真实成本收益。
  - c：192 个受控环境中的 one-step、M2、Depth-2 与 DP success，显示多步规划必要性。
- 统计边界：
  - a 的 135 条条件来自 3 个独立攻击案例的重复遮蔽条件，不作为 135 个独立样本。
  - b 的 180 个 episode 来自 4 个独立案例，不绘制虚假置信区间。
  - c 的独立环境数为 192，每环境 10 个 seed；图中报告平均 success，不把 seed 扩张为独立环境。
- 审稿风险：不得用视觉编码暗示 XGBoost 优于 M2；不得把 DP 标为部署模型；不得把 Gate B 写成通过。
- 源数据：
  - `08-writing/table-budget-efficiency-c07-c09.csv`
  - `09-experiments/results/xgboost_c01_c06_train_c07_c10_test/xgboost_policy_results.csv`
  - `09-experiments/results/nonmyopic_dqn_gate_v0.1/nonmyopic_gate_summary.json`
  - `09-experiments/results/nonmyopic_real_v0.1/nonmyopic_policy_summary.json`
- 输出：双栏宽 183 mm；SVG、PDF、PNG、600 dpi TIFF；文本可编辑。

## 视觉规范

- 白色背景，Arial/Helvetica/DejaVu Sans；正文 7 pt，面板字母 9 pt。
- M2 使用深蓝；XGBoost 使用青色；M3a 使用暗红；Oracle 使用深灰；其余基线使用低饱和中性色。
- 不使用彩虹色图；颜色不是唯一编码，线型、标记和文字标签共同区分。
- 不报告没有独立统计单位支持的误差条或显著性检验。
