# 外部 AFA 基线源码审计与任务映射协议 v0.1

日期：2026-07-13

状态：源码与接口 Gate 已完成；尚未产生可称为“官方同任务复现”的数值结果。

## 1. 目的

本协议回应 Reviewer 对“正式外部 AFA 基线”的要求。目标不是把任意公开 AFA 代码接到 Project05 后重新命名，而是先回答：

1. 公开实现解决的决策对象是否与 Project05 相同；
2. STOP、非均匀成本和非短视规划等能力能否保留；
3. 哪些转换会改变任务定义或引入 Project05 自己的收益模型；
4. 在什么条件下才允许写“外部同任务基线”。

## 2. 冻结来源

| 方法 | 冻结来源 | 代码状态 | Project05 角色 |
|---|---|---|---|
| AFABench | [KDD 2026 论文](https://doi.org/10.1145/3770855.3817493)；[官方仓库](https://github.com/Linusaronsson/AFA-Benchmark) `8ebf5e9f0287a7dac09218e1c3c9684b546faddb` | 官方 benchmark；本地 commit 校验通过 | 外部 AFA 框架参照 |
| WinRegRL | [Scientific Reports 2026 论文](https://doi.org/10.1038/s41598-026-57787-6)；[官方仓库](https://github.com/mcghanem2026/WinRegRL) `d3db7643b39eb9e3af666d5ed0c257250f27adef` | 官方 MATLAB 参考实现；ZIP 哈希校验通过 | 最接近运营调查规划的邻居 |
| AACO | [ICML 2024 论文](https://proceedings.mlr.press/v235/valancius24a.html)；[作者仓库](https://github.com/lupalab/aaco) `3b2316661651699d11e904e9c5911c175e8b2fdc` | 作者实现；仓库顶层未声明 LICENSE | 非贪心 acquisition 方法参照 |
| NOCTA | [arXiv 论文](https://arxiv.org/abs/2507.12412) | 截至本次审计未验证到公开代码；ICLR 2026 投稿已撤回 | 仅作纵向非贪心相关工作 |

锁文件：`../09-experiments/external_baselines/external_baseline_lock_v0.1.json`。

源码审计结果：3 个可得官方/作者仓库全部命中冻结 commit；WinRegRL 压缩包 SHA-256 为 `5B701C83C8740FEEE3FBE133A6224BEF9AB1CA0B808728C9E2B2AB09D815BC98`。本机无 MATLAB/Octave，因此未声称 WinRegRL 数值复现。

## 3. 任务不等价性

### AFABench / AACO

公开 AFA 主任务以“选择并揭示预先存在的特征，随后预测静态标签/作出静态决策”为中心。Project05 的动作会执行具有通道、失败和零收益反馈的证据采集，并更新 claim、图覆盖、可达性和结论粒度。主要不等价点如下：

- 静态 feature reveal 不等于随机证据 bundle 执行；
- 固定 feature 数量或 hard budget 不等于显式成本与 STOP；
- 静态监督标签不等于受支持上限约束的调查结论；
- fully observed training instance 会暴露 Project05 刻意隔离的恢复集合。

AFABench 代码层支持 STOP 和非均匀 `selection_costs`，因此可作框架参照；这不足以消除任务端点差异。

### WinRegRL

WinRegRL 具有有限 MDP、值迭代、局部表格 Q 更新和调查动作本体，语义上最接近 Project05。但其状态、动作和转移专用于 Windows Registry/Timeline；转移概率由专家指定，也没有 evidence-claim、粒度上限或 `intended != recoverable` 信息边界。

官方仓库的 `reproduce_results.m` 明确使用合成生成器复现结构/趋势，并包含论文参考数值；因此不得把脚本运行写成论文原始数据的精确复现。

## 4. 动作族映射

| Project05 动作类型 | WinRegRL 最近动作族 | 边界 |
|---|---|---|
| `extend_log_window` | `ingest` | 都扩展数据入口，但 Project05 还包含时间窗与零收益反馈 |
| `query_host_subgraph` | `correlate` | 都围绕实体关系扩展；状态表示不等价 |
| `recover_network_summary` | `parse_device` | 都解析设备/网络证据；WinRegRL 不是网络取证 benchmark |
| `ttp_local_probe` | `correlate` | 仅为最邻近动作族，不等于同一效用函数 |
| `human_review` | `validate` | 都执行验证；Project05 的粒度截断仍是独有状态变量 |

C07-C12 当前 5 种实际动作类型已 5/5 映射，无未映射类型。该结果只证明动作词汇可对齐，不证明算法可直接比较。

## 5. 冻结判定

```text
direct_same_task_claim_allowed = false
external_framework = AFABench
operational_nearest_neighbor = WinRegRL
```

当前已有 AFA-Myopic / Rollout-H3 结果继续称为“同接口领域适配”，不得改称 AFABench、AACO、NOCTA 或 WinRegRL 官方复现。

## 6. 公平比较的两个允许路径

1. **跨任务复现**：严格运行官方代码及其原任务，单独报告环境、commit、原始指标和复现偏差。该结果只证明代码可复现，不进入 Project05 成本 Pareto。
2. **显式端点适配**：事先冻结静态预测端点、动作到 feature 的转换和训练可见性；保留公开实现的 acquisition 逻辑，并把任务转换损失单独报告。结果必须标为“external-method adapter”，不能称同任务原生实现。

若无法定义不泄漏恢复集合的静态端点，则应诚实保留“外部基线不可直接比较”的结论，而不是制造一个数值基线。

## 7. 下一 Gate

在投入官方框架运行前，必须先完成一个最小 endpoint contract：

- 预测目标是什么；
- 训练时可见哪些 claim/action 字段；
- STOP 与非均匀成本如何保留；
- feature reveal 如何转换为通道执行且不读取实际恢复集合；
- 跨任务结果是否与主结果分表。

未通过该 Gate，不启动重型依赖安装，也不把外部代码结果写进论文主表。
