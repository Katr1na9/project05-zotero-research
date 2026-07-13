# Project05 论文主图/表契约 v0.3

日期：2026-07-13

后端：Python / matplotlib（独占）

输出目录：`figures/main-v0.4/`

## Figure 1：调查控制框架与信息边界

- 核心结论：部分对齐是可更新调查状态，不是流水线终点。
- 面板：闭环流程；规划器公开区与执行器/Oracle 隐藏区。
- 红线：LLM 不得画成在线主模型；隐藏恢复集合不得连入规划器；STOP 不得暗示必然最优。

## Figure 2：参数锁定攻击轨迹留出与非短视边界

- a：C07-C09 的 Oracle 相对紧预算 success；M2 高于 M3a。
- b：C07-C10 序贯 success 与成功条件均成本；M2/XGBoost/Depth-2 达标，M2 成本最低。
- c：192 个独立受控环境的 one-step、M2、Depth-2 与 DP success；Gate A 通过、Gate B 不通过。
- 统计边界：135/180/540 个条件是重复测量；独立轨迹案例数分别为 3/4/4，不绘制伪置信区间，也不表述为自然发生的独立 APT。

## Figure 3：AFA 对照与代理敏感性

- a：Oracle、M2、AFA-VOI Myopic、Rollout-H3 的 C07-C10 成功条件均成本；四者 success 均为 1.0。
- b：16 个 M2 单权重 ±25% 变体的首动作一致率与成本变化；13 个完全同序、3 个轻微改变且成本增加。
- c：C01-C06 多 claim 开发案例 OR/AND success；明确标注真实 C07-C10 的 OR/AND 不可识别。
- 红线：不得把领域适配标成 NOCTA/WinRegRL 官方复现；不得把开发 OR/AND 差异外推为真实攻击结果。

## Table C11：第三封装与 AND/OR 敏感性

- C11 作为独立 G2 外部效度压力，不加入 Figure 2/3 的 C07-C10 聚合均值。
- 主表报告 AND 下 Oracle、Coverage、M1、M3a、M2、Random 的 success、成功条件成本、regret、premature STOP 和 ceiling violation。
- 正文报告 M2 AND cost `3.6667`、OR cost `1.0222`；不把差异解释为算法改善。
- 明确 45 条是一个 APT29 emulation 链的重复条件；多 claim 来自同一主机归档的不同 Windows provider。
- XGBoost、AFA-VOI 与 Depth-2 未在 C11 v0.1 上运行，不出现在该表。

## 视觉与复现规范

- 双栏宽 183 mm；白底；正文不小于 7 pt；颜色之外同时使用线型、标记或文字。
- M2 深蓝、XGBoost 青色、AFA 绿色系、M3a 暗红、Oracle 深灰；不使用彩虹色。
- 输出 SVG、PNG、PDF 与 600 dpi TIFF；图中文字可编辑。
- 生成入口：`09-experiments/scripts/make_paper_main_figures.py`。
- 源数据：紧预算 CSV、XGBoost 汇总、非短视 Gate/轨迹接入 JSON、AFA 汇总、敏感性汇总。
- 自动测试验证输入维度、关键数值和输出文件；人工 QA 验证无遮挡、标签含义与统计单位。
