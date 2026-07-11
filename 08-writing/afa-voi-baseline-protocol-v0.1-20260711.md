# AFA-VOI 同接口领域适配基线参数锁定协议 v0.1

日期：2026-07-11
状态：读取结果前冻结

## 1. 目的与边界

本实验回答：通用 Active Feature Acquisition（AFA）的 value-of-information 与非贪心 objective-cost trade-off 思路，在不读取隐藏恢复集合时，能否直接适配 Project05 的公开动作空间并超过透明部署策略 M2？

本实验不是 NOCTA、WinRegRL 或其他论文官方代码的逐行复现。原因是这些方法分别依赖纵向预测器、专家转移模型或特定 Windows 取证状态，不能在不改变任务的情况下直接运行于 C07-C10。本文实现两个明确标记为 **domain adaptation baseline** 的策略：

1. `afa_voi_myopic`：标准一步期望信息价值减成本；
2. `afa_voi_rollout_h3`：NOCT 类非贪心 objective-cost trade-off 的有限公开 rollout 适配，最大规划深度固定为 3。

二者用于检验“Project05 是否只是简单 AFA”，不得写成对原论文算法的完全复现或优越性比较。

## 2. 公开终端效用

规划器只使用当前公开匹配节点、CTI 图、动作 `intended_cti_node_ids`、通道和成本。对公开代理节点集 \(M\)，定义：

\[
U(M)=g(M)+0.5\,\mathrm{NodeCov}(M)+0.5\,\mathrm{EdgeCov}(M),
\]

其中 \(g(M)\in\{0,1,2,3\}\) 是按当前 G0-G3 结构规则计算的公开代理粒度等级。计划 \(\pi\) 的净价值为：

\[
J(\pi\mid s)=\mathbb{E}[U(M_\pi)]-U(M_0)
-\frac{\sum_{a\in\pi}c(a)}{B_{\mathrm{total}}}.
\]

通道成功按 `channel_reliability` 建模；同一计划中同通道动作共享一个通道状态，以匹配当前模拟器的通道级可用性。失败动作不增加代理节点，但仍支付成本。

## 3. 信息边界

严禁读取：

- `recoverable_claim_ids`；
- 当前隐藏 claims；
- realized channel state；
- Oracle 路径或未来真实恢复结果；
- M2、M3a 或 XGBoost 分数。

必须通过测试证明：仅修改隐藏恢复字段不改变动作选择，且选择过程不修改输入状态或动作。

## 4. 冻结比较

- 独立案例：C07-C10，共 4 个；
- 重复条件：每策略 180 个，不能写成独立攻击数；
- 比较：M2、AFA-VOI Myopic、AFA-VOI Rollout-H3、Oracle；
- 指标：success、成功成本、Oracle regret、zero-yield、premature STOP、ceiling violation、逐条件 paired cost；
- 不在 C07-C10 结果后调整效用系数、成本归一化、深度或 tie-break。

## 5. 解释规则

- AFA 适配若胜出，只能说明通用 VOI 目标在当前代理状态上有效，不能声称真实归因准确率提升；
- 若与 M2 持平或更差，支持“领域结构和信息边界使简单 AFA 适配不足”，但不能声称 AFA 整体无效；
- 非贪心 rollout 若未优于 myopic，不启动新的 RL 工程。
