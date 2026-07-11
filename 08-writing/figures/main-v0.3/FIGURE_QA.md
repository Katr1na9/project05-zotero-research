# Figure QA

日期：2026-07-11
后端：Python / matplotlib；未使用 R 或其他绘图后端

## Figure 1

- 文件：`fig1_method_and_information_boundary.{svg,pdf,png,tiff}`
- 最终设计尺寸：7.2 × 4.25 in，双栏宽。
- PNG：1734 × 1041 px。
- SVG 可编辑文本节点：25。
- 视觉检查：五段闭环无框体重叠；反馈箭头与主流程区分；公开/隐藏字段由虚线边界隔离；LLM 未被画入在线主循环。
- 数据/统计：方法示意图，不含定量统计。

## Figure 2

- 文件：`fig2_holdout_and_nonmyopic_results.{svg,pdf,png,tiff}`
- 最终设计尺寸：7.2 × 4.65 in，双栏宽。
- PNG：1845 × 1311 px。
- SVG 可编辑文本节点：63。
- Panel a 源数据：`table-budget-efficiency-c07-c09.csv`。
- Panel b 源数据：`xgboost_policy_results.csv`，由脚本按 planner 汇总 success、成功条件 cost 与 zero-yield。
- Panel c 源数据：`nonmyopic_gate_summary.json`。
- 统计完整性：未绘制把重复 mask/seed 当独立样本的误差条；各面板直接标注独立案例/环境数量。
- 视觉检查：M2、M3a、XGBoost、Oracle 在不同面板保持一致语义色；颜色之外同时使用线型、标记和文字标签；无彩虹色图；无图例遮挡；Gate A/B 结论可在最终尺寸读取。

## Export contract

- SVG：主编辑格式，`svg.fonttype=none`。
- PDF：`pdf.fonttype=42`，文字保持 TrueType。
- PNG：300 dpi 预览。
- TIFF：600 dpi 投稿备选。
- 背景：白色；字体：Arial/Helvetica/DejaVu Sans fallback。

最终投稿前仍需按目标期刊图宽、最大高度和 TIFF 压缩要求复核。
