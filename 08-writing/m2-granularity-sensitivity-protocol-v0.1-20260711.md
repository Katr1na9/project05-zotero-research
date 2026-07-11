# M2 权重与粒度代理敏感性协议 v0.1

日期：2026-07-11
状态：读取敏感性结果前冻结

## 1. 目的

本分析检验两类内部设计选择是否决定主要结论：

1. M2 的八个公开评分权重；
2. G0-G3 的节点/边阈值和节点 required claims 的 OR/AND 覆盖语义。

敏感性分析是稳健性审计，不用于结果后重新选择“最好”的 M2 参数。

## 2. M2 权重

冻结基准权重为：granularity 2.00、uncertainty 1.50、risk 1.50、stage gap 1.50、evidence gap 1.00、overlap 1.50、no-yield 1.00、cost 0.75。对每个权重单独乘以 0.75 和 1.25，其余权重保持不变，共 16 个 one-at-a-time 变体，加原始 M2。

评估范围为 C07-C10。报告 success、成功成本、zero-yield、premature STOP、ceiling violation，以及相对原始 M2 的逐状态首动作一致率和逐条件成本差。重复条件不是独立攻击样本。

## 3. 粒度阈值

| 版本 | G3 node | G3 edge | G2 node | G2 stages | G1 node |
|---|---:|---:|---:|---:|---:|
| Lenient | 0.65 | 0.50 | 0.35 | 2 | 0.10 |
| Default | 0.75 | 0.60 | 0.45 | 2 | 0.15 |
| Conservative | 0.85 | 0.70 | 0.55 | 2 | 0.25 |

每个版本分别运行 M2 与相同语义下的 Oracle，不能用默认 Oracle 给变体打分。

## 4. OR/AND 覆盖

- OR：节点任一 required claim 可见即覆盖；
- AND：节点全部 required claims 可见才覆盖。

C07-C10 的每个 CTI 节点只有一条 required claim，因此 OR 与 AND 在这些案例上按定义完全等价。该事实必须在结果中报告为“不可识别”，不能写成 OR/AND 鲁棒性证据。

为观察语义差异，另在存在多 claim 节点的 C01-C06 上运行开发性压力分析。该部分不属于 holdout，也不能用于选择 C07-C10 的阈值或权重。

## 5. 解释规则

- 若小幅权重扰动保持主要结论，仅支持局部稳健性，不支持最优权重；
- 若阈值改变 success，说明 success 依赖内部代理，应进一步弱化“归因能力”措辞；
- OR/AND 开发压力若差异较大，说明未来真实案例必须编译多源 corroboration 节点并完成人工校准。
