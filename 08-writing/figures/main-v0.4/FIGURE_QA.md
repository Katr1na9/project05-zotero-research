# Figure QA：论文主图 v0.4

日期：2026-07-11

生成脚本：`09-experiments/scripts/make_paper_main_figures.py`

## 自动检查

- `test_paper_main_figures.py`：M2、XGBoost、M3a、Depth-2、AFA 和敏感性关键数值通过。
- `test_paper_v04_consistency.py`：主图/结果 JSON 与论文 v0.4 的关键数字及引文键一致。
- 生成格式：PNG、SVG、PDF、600 dpi TIFF 均存在；仓库仅跟踪允许的轻量格式。

## 人工视觉检查

| 图 | 检查结果 | 备注 |
|---|---|---|
| Figure 1 | PASS | 初次发现 Evidence-gap state 文本与流程箭头相碰；改为四行标签后重生成，无遮挡；隐藏区未连入规划器 |
| Figure 2 | PASS | 三面板标题、图例、数值标签和坐标轴无重叠；重复条件与独立案例数写在图内；Gate A/B 方向正确 |
| Figure 3 | PASS | AFA 成本、16 个权重变体分组和 OR/AND 开发压力清楚；明确写出 holdout OR=AND |

## 统计与语义红线

- 未绘制把 repeated masks/seeds 当独立样本的误差条或显著性标记。
- Figure 3 的 AFA 标签使用 adapter 缩写，不标成 NOCTA/WinRegRL 官方复现。
- Figure 3c 明确为 C01-C06 development only，不外推到真实 C07-C10。
- Figure 1 未把 LLM 画进在线规划回路，也未暗示 STOP 始终最优。

结论：v0.4 三张主图通过当前投稿母本的视觉、数字与语义 QA。
