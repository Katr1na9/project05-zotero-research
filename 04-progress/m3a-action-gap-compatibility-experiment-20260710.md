# M3a Action-Gap Compatibility 实验记录

日期：2026-07-10  
状态：已完成第一轮实现与 C01-C06 对比实验

## 1. 本轮目标

M2 在 C06 held-out 诊断中失败的核心原因不是反馈权重不够，而是 action 与当前证据缺口之间缺少节点级对应关系。M2 只能看到 `expected_stages`、`expected_evidence_types` 和手写收益，因此当 `C06-AA-001` 与 `C06-AA-002` 都属于 execution stage 时，它会被更高的 `expected_granularity_gain` 误导。

M3a 的目标不是最终模型，而是验证一个表示假设：

> 如果给每个取证 action 增加公开的 `intended_cti_node_ids`，即该 action 语义上希望解决哪些 CTI 缺口节点，那么仅用 action-gap compatibility 是否就能显著修复 M2 的失败模式？

## 2. 本轮改动

### 2.1 Schema

在 `09-experiments/data_schema/acquisition_action.schema.json` 中新增：

```json
"intended_cti_node_ids": []
```

该字段表示公开的 action-to-gap intent，只能来自取证请求语义与 CTI schema，不能从隐藏的 `recoverable_claim_ids` 自动复制。

### 2.2 数据

已为以下 case 的全部 acquisition actions 补充 `intended_cti_node_ids`：

- C01 Linux toy case
- C02 FreeBSD toy case
- C03 Windows toy case
- C04 DARPA E3 FiveDirections real case
- C05 DARPA E3 CADETS real case
- C06 DARPA E3 CADETS April 12 diagnostic case

### 2.3 Planner

新增 planner：

```text
project05_m3a_gap_compat
```

打分信号只使用：

- 当前 state 的 `unmatched_cti_node_ids`
- action 的公开 `intended_cti_node_ids`
- CTI 节点的 `critical` 标记
- action cost

它不读取：

- hidden claim ids
- `recoverable_claim_ids` 的真实恢复交集
- oracle path

## 3. 边界测试

新增测试约束：

1. M3a 在修改 `recoverable_claim_ids` 后选择不变，证明不依赖隐藏恢复结果。
2. M3a 会优先选择命中未匹配关键 CTI 节点的 action，即便另一个 action 有更高手写 expected gain。
3. C01-C06 的所有 action 必须显式声明 `intended_cti_node_ids`。
4. 所有 `intended_cti_node_ids` 必须能在对应 case 的 `cti_nodes` 中找到。

全量测试结果：

```text
Ran 39 tests in 0.442s
OK
```

## 4. 实验结果

### 4.1 Toy cases: C01-C03

结果文件：

- `09-experiments/results/m3a_toy_cases/all_cases_results.csv`
- `09-experiments/results/m3a_toy_cases/all_cases_summary.json`

| Planner | Success | Mean cost to target | Oracle top-1 hit | Zero-yield | Overlap waste |
|---|---:|---:|---:|---:|---:|
| project05_m1 | 0.9333 | 3.5714 | 0.2000 | 0.1556 | 0.0801 |
| project05_m2 | 0.9037 | 3.3115 | 0.2074 | 0.1333 | 0.0772 |
| project05_m3a_gap_compat | 1.0000 | 2.3926 | 0.5111 | 0.0000 | 0.0056 |
| coverage_greedy | 0.9630 | 4.3077 | 0.3111 | 0.3481 | 0.2031 |
| cmi_proxy | 0.7704 | 4.0000 | 0.3185 | 0.7926 | 0.4429 |
| oracle_optimal | 1.0000 | 2.3778 | 0.8519 | 0.0000 | 0.0086 |

### 4.2 Real cases: C04-C06

结果文件：

- `09-experiments/results/m3a_real_cases/all_cases_results.csv`
- `09-experiments/results/m3a_real_cases/all_cases_summary.json`

| Planner | Success | Mean cost to target | Oracle top-1 hit | Zero-yield | Overlap waste |
|---|---:|---:|---:|---:|---:|
| project05_m1 | 0.8296 | 1.8571 | 0.2963 | 0.1852 | 0.2176 |
| project05_m2 | 0.8370 | 1.7876 | 0.2000 | 0.1556 | 0.1856 |
| project05_m3a_gap_compat | 1.0000 | 1.6519 | 0.5111 | 0.0000 | 0.0494 |
| coverage_greedy | 0.9037 | 2.1803 | 0.2963 | 0.2963 | 0.1932 |
| cmi_proxy | 0.8370 | 1.4425 | 0.3185 | 0.3778 | 0.2514 |
| oracle_optimal | 1.0000 | 1.6519 | 0.5333 | 0.0000 | 0.0444 |

### 4.3 C06 challenge subset

统计范围：C06 中 initial granularity 未达到 target granularity 的 27 个挑战条件。

| Planner | Challenge success | Oracle top-1 hit | First action distribution |
|---|---:|---:|---|
| project05_m1 | 5/27 | 0/27 | `C06-AA-007`: 27 |
| project05_m2 | 5/27 | 1/27 | `C06-AA-007`: 6, `C06-AA-002`: 21 |
| project05_m3a_gap_compat | 27/27 | 24/27 | `C06-AA-001`: 22, `C06-AA-005`: 4, `C06-AA-004`: 1 |
| coverage_greedy | 14/27 | 0/27 | `C06-AA-007`: 27 |
| cmi_proxy | 5/27 | 2/27 | `C06-AA-005`: 27 |
| oracle_optimal | 27/27 | 27/27 | `C06-AA-001`: 22, `C06-AA-002`: 3, `C06-AA-005`: 2 |

M3a 修复的典型失败条件：

- 当缺失 `N01_initial_access` 时，M2 经常先选 `C06-AA-002` 或 `C06-AA-007`。
- M3a 会优先选中面向 `N01_initial_access` 的 `C06-AA-001`。
- 在 stage/discriminative 高遮蔽条件下，M3a 的路径经常与 oracle 一致为 `C06-AA-001|C06-AA-002`。

## 5. 当前结论

M3a 强烈支持以下判断：

> Project05 的主线不应只是“多源证据融合 + LLM 解释”，而应收束为“面向归因目标的证据缺口图建模与条件取证收益估计”。

更具体地说，当前实验证明：

1. 节点级 action-gap compatibility 比 stage/type coverage 更能解释 M2 的失败。
2. 只做静态 expected gain 排序容易选中高收益但不解决当前关键缺口的 action。
3. 当前最有价值的创新点是把“缺什么证据”推进为“哪个取证动作最可能解决哪个关键缺口节点，并使归因粒度达标”。

## 6. 必须保留的谨慎边界

M3a 目前还不能直接作为最终论文贡献，因为：

1. `intended_cti_node_ids` 是人工补充的公开语义字段，需要后续说明由 LLM/规则如何从自然语言取证请求映射得到。
2. C06 已经用于 M2 失败诊断，因此不能再作为 M3 的真正独立 holdout。
3. M3a 是启发式 baseline，不是可学习模型。它验证表示空间重要，但还没有证明 conditional utility model 的泛化能力。
4. 现有 C01-C06 的 action 空间较干净，后续要加入噪声 action、冗余 action、误导 action 和不可用 action。

## 7. 下一步

### M3b: 可校准条件收益模型

将 M3a 的公开 action-gap 表示升级为可学习模型：

```text
Input: evidence-gap state + action features + action-gap compatibility
Output:
  P(action resolves node v | state)
  P(recovered_count > 0 | state, action)
  P(next granularity >= target | state, action)
```

首选模型不是大模型，也不是 RL，而是：

- logistic regression
- random forest / XGBoost
- small MLP

评估指标：

- node-resolution AUROC / AUPRC
- Brier score / ECE
- oracle top-1 hit
- NDCG
- budget success rate
- zero-yield action count
- regret vs oracle

### 新 holdout

下一轮必须接入真正未参与设计的攻击 trace：

- DARPA TC E5
- 或 OPTC
- 或其他 campaign-level provenance trace

只有在新 holdout 上仍然成立，M3 才能从“诊断性改进”变成“论文级证据”。

