# AFA-VOI 同接口领域适配基线结果 v0.1

日期：2026-07-11
协议：`afa-voi-baseline-protocol-v0.1-20260711.md`
状态：冻结参数后的首次结果

## 1. 比较对象

本实验将通用 Active Feature Acquisition 的一步 expected value-of-information 与非贪心 objective-cost trade-off 思路适配到 Project05 的公开动作接口 [@aronsson_survey_2025; @noauthor_nocta_2025]。`afa_voi_myopic` 评价单步公开终端效用增量减成本；`afa_voi_rollout_h3` 在同一目标下搜索最多三步计划。二者不读取隐藏恢复集合，也不使用 M2 分数。

这是领域适配基线，不是 NOCTA 或 WinRegRL 官方实现的直接复现。C07-C10 每策略 180 个重复条件，四个策略共 720 个 episode；独立攻击案例数为 4。

## 2. 聚合结果

| Planner | Success | Mean cost | Regret | Zero-yield | Oracle top-1 hit |
|---|---:|---:|---:|---:|---:|
| Oracle | 1.0000 | 3.9333 | 0.0000 | 0.0000 | 0.9389 |
| **M2** | **1.0000** | **4.5333** | **0.6000** | **0.2667** | 0.5167 |
| AFA-VOI Myopic | 1.0000 | 4.9722 | 1.0389 | 0.3000 | 0.3333 |
| AFA-VOI Rollout-H3 | 1.0000 | 4.9722 | 1.0389 | 0.3000 | 0.3333 |

两种 AFA 适配均保持目标达成率，但平均成功成本比 M2 高 0.4389。逐条件比较中，两者相对 M2 均为 24 次成本胜、91 次平、65 次负，没有 success 修复或退化。Myopic 与 Rollout-H3 的 success、成本和 regret 完全相同；两者只在少量同成本动作顺序上有差异，导致 overlap waste 分别为 0.5744 和 0.5757。

## 3. 分案例成本

| 案例 | M2 | AFA Myopic | AFA Rollout-H3 |
|---|---:|---:|---:|
| C07 | 4.3111 | 4.6444 | 4.6444 |
| C08 | 4.5111 | 4.8444 | 4.8444 |
| C09 | 4.7556 | 5.0889 | 5.0889 |
| C10 | 4.5556 | 5.3111 | 5.3111 |

四个案例方向一致：通用公开节点覆盖 VOI 没有降低 M2 成本，C10 差距最大。

## 4. 解释

结果关闭了“缺少通用 AFA 对照”的实验空白，但不支持“AFA 无效”。当前适配把动作收益近似为公开意图节点带来的粒度、节点和边覆盖；由于 `intended_cti_node_ids` 被刻意与真实恢复集合隔离，该代理会高估过宽意图并产生更多动作重叠。M2 额外利用阶段/证据类型缺口、历史零收益和重叠惩罚，因此在当前四个案例中成本更低。

非贪心 rollout 未超过 myopic，说明当前公开 schema 没有提供足够的可验证动作依赖，使三步组合搜索产生新收益。该结果与 Depth-2 Public 负结果一致：继续增加规划深度不是当前优先项；若未来重开，应先加入独立验证的前置条件或转移模型。

## 5. 可复现产物

- 实现：`09-experiments/scripts/run_afa_voi_baselines.py`
- 测试：`09-experiments/tests/test_afa_voi_baselines.py`
- 结果：`09-experiments/results/afa_voi_c07_c10_v0.1/`
