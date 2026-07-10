# M3b-3 动作可靠性反馈实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 为 M3b 序贯取证策略加入基于 yield/zero-yield 反馈的 Beta 可靠性后验，并在 DARPA E3 的正常与诱饵动作条件下完成配对评估。

**架构：** 新逻辑全部位于 `09-experiments/scripts/run_m3b.py`。每轮选择前，策略只使用 `state.action_feedback` 与公开动作字段重建后验；评分为 `P(补关键缺口) × 可靠性均值 - 成本惩罚`。既有 `run_mvp.py` 继续执行动作和生成反馈，因此不改动其隐藏证据边界。

**技术栈：** Python 3 标准库、现有 dependency-free simulator、`unittest`、JSON/CSV。

## 全局约束

- 训练仅使用 `09-experiments/examples/C01-C03`，测试仅使用 `09-experiments/real_cases/C04-C06`。
- Oracle 之外的策略在选择前不得读取 `recoverable_claim_ids` 或 `hidden_claim_ids`。
- 分组键固定为 `action_type + sorted(expected_evidence_types)`；空列表使用 `unknown`。
- 先验固定为 `Beta(1,1)`；`recovered_count > 0` 增加 alpha，零产出增加 beta。
- 汇总必须保留 case-condition 配对关系，并分别报告独立案例数与重复条件数。

---

### Task 1：实现可靠性后验和公开动作选择器

**文件：**

- 修改：`09-experiments/scripts/run_m3b.py`
- 修改：`09-experiments/tests/test_run_m3b_policy.py`

**接口：**

- `reliability_group(action: dict[str, Any]) -> str`
- `reliability_posteriors(actions: list[dict[str, Any]], action_feedback: list[dict[str, Any]]) -> dict[str, dict[str, float]]`
- `reliability_action_score(config, state, action, actions, model, cost_penalty) -> tuple[float, float, float]`
- `select_reliability_model_action(config, state, actions, model, cost_penalty) -> dict[str, Any] | None`

- [ ] **Step 1：写失败测试，固定 Beta 更新和组隔离。**

```python
def test_reliability_posteriors_update_only_observed_group(self):
    feedback = [
        {"action_id": "critical-expensive", "recovered_count": 0},
        {"action_id": "other-cheap", "recovered_count": 1},
    ]
    posterior = run_m3b.reliability_posteriors(self.actions, feedback)

    self.assertEqual("query_host_subgraph|unknown", run_m3b.reliability_group(self.actions[0]))
    self.assertEqual(1.0, posterior["query_host_subgraph|unknown"]["alpha"])
    self.assertEqual(2.0, posterior["query_host_subgraph|unknown"]["beta"])
    self.assertAlmostEqual(1 / 3, posterior["query_host_subgraph|unknown"]["mean"])
    self.assertAlmostEqual(2 / 3, posterior["recover_network_summary|unknown"]["mean"])
```

- [ ] **Step 2：运行测试，确认函数尚未定义。**

```powershell
python -m unittest 09-experiments.tests.test_run_m3b_policy.M3bPolicyTests.test_reliability_posteriors_update_only_observed_group
```

预期：失败信息包含 `reliability_posteriors`。

- [ ] **Step 3：实现最小后验与选择器。**

```python
def reliability_group(action: dict[str, Any]) -> str:
    evidence_types = sorted(action.get("expected_evidence_types", []) or ["unknown"])
    return f"{action.get('action_type', 'unknown')}|{','.join(evidence_types)}"


def reliability_posteriors(actions, action_feedback):
    by_id = run_mvp.action_by_id(actions)
    posterior = {}
    for feedback in action_feedback:
        action = by_id.get(str(feedback["action_id"]))
        if action is None:
            continue
        stats = posterior.setdefault(reliability_group(action), {"alpha": 1.0, "beta": 1.0})
        stats["alpha" if int(feedback.get("recovered_count", 0)) > 0 else "beta"] += 1.0
    for stats in posterior.values():
        stats["mean"] = stats["alpha"] / (stats["alpha"] + stats["beta"])
    return posterior


def reliability_action_score(config, state, action, actions, model, cost_penalty):
    probability = predict_probability(model, feature_row(config, state, action))
    stats = reliability_posteriors(actions, state.get("action_feedback", []))
    reliability = stats.get(reliability_group(action), {"mean": 0.5})["mean"]
    return probability * reliability - cost_penalty * float(action["cost"]), probability, reliability
```

`select_reliability_model_action` 必须使用 `run_mvp.available_actions`，并以 `(utility, probability, reliability, -cost, action_id)` 作为稳定排序键。

- [ ] **Step 4：运行局部与全量测试。**

```powershell
python -m unittest 09-experiments.tests.test_run_m3b_policy
python -m unittest discover 09-experiments\tests
```

预期：两条命令均为 `OK`。

- [ ] **Step 5：提交后验基础层。**

```powershell
git add 09-experiments/scripts/run_m3b.py 09-experiments/tests/test_run_m3b_policy.py
git commit -m "experiment: add m3b reliability posterior"
```

### Task 2：实现自适应 episode 回放和 trace 审计

**文件：**

- 修改：`09-experiments/scripts/run_m3b.py`
- 修改：`09-experiments/tests/test_run_m3b_policy.py`

**接口：**

- `run_reliability_model_episode(config, claims, actions, mask_strategy, mask_intensity, seed, model, cost_penalty) -> tuple[dict[str, Any], list[dict[str, Any]]]`

- [ ] **Step 1：写失败测试，验证反馈后的后验和 trace。**

```python
def test_reliability_episode_records_posterior_only_after_feedback(self):
    actions = run_m3b.inject_matched_decoys(self.config, self.actions)
    result, trace = run_m3b.run_reliability_model_episode(
        self.config, self.claims, actions, "discriminative", 0.5, 11, self.model, 0.1
    )

    self.assertEqual("project05_m3b_reliability_policy", result["planner"])
    self.assertEqual(0.5, trace[1]["reliability_mean_before"])
    self.assertLess(trace[1]["reliability_mean_after"], 0.5)
    self.assertIn("reliability_adjusted_utility", trace[1])
```

再写一条边界测试：交换两个候选动作的 `recoverable_claim_ids` 后，`select_reliability_model_action` 在无历史反馈时的首选动作保持不变。

- [ ] **Step 2：运行失败测试。**

```powershell
python -m unittest 09-experiments.tests.test_run_m3b_policy.M3bPolicyTests.test_reliability_episode_records_posterior_only_after_feedback
```

预期：失败信息包含 `run_reliability_model_episode`。

- [ ] **Step 3：复用既有 simulator 实现策略。**

```python
result, trace = run_mvp.run_episode(
    config, claims, actions, mask_strategy, mask_intensity, seed,
    "project05_m3b_reliability_policy",
    action_selector=lambda episode_config, state, episode_actions:
        select_reliability_model_action(
            episode_config, state, episode_actions, model, cost_penalty
        ),
)
```

回放结束后遍历 `zip(trace, trace[1:])`。每个 `action_taken` event 用前一 state 的 `action_feedback` 重建 action group 的后验，再用该 event 的 `recovered_claim_ids` 构造新增反馈，记录：`reliability_group`、`reliability_mean_before`、`reliability_mean_after`、`predicted_gap_probability`、`reliability_adjusted_utility`。这一步只用于审计，不能影响已完成的选择。

- [ ] **Step 4：验证并提交。**

```powershell
python -m unittest 09-experiments.tests.test_run_m3b_policy
python -m unittest discover 09-experiments\tests
python -m py_compile 09-experiments\scripts\run_m3b.py
git add 09-experiments/scripts/run_m3b.py 09-experiments/tests/test_run_m3b_policy.py
git commit -m "experiment: add adaptive m3b reliability policy"
```

预期：测试通过，Python 编译退出码为 0。

### Task 3：配对评估、重复诱饵压力测试与研究记录

**文件：**

- 修改：`09-experiments/scripts/run_m3b.py`
- 修改：`09-experiments/tests/test_run_m3b_policy.py`
- 创建：`09-experiments/results/m3b_reliability_toy_train_real_test/`
- 创建：`04-progress/m3b-reliability-feedback-experiment-20260710.md`

**接口：**

- `evaluate_reliability_policy_case_dirs(cases, model, cost_penalty, baseline_planners, conditions=None) -> tuple[list[dict[str, Any]], dict[str, Any]]`
- `run_reliability_policy_experiment(train_root, test_root, output_dir, label_column, cost_penalty, baseline_planners) -> dict[str, Any]`
- `run_reliability_decoy_stress_experiment(train_root, test_root, output_dir, label_column, cost_penalty, baseline_planners, copies_per_action=2) -> dict[str, Any]`

- [ ] **Step 1：写失败测试，固定结果集与重复诱饵输出。**

```python
def test_reliability_stress_writes_adaptive_and_static_results(self):
    report = run_m3b.run_reliability_decoy_stress_experiment(
        root / "examples", root / "real_cases", output_dir,
        "label_resolves_critical_gap_node", 0.1,
        ["coverage_greedy", "project05_m2", "project05_m3a_gap_compat", "oracle_optimal"],
        copies_per_action=2,
    )
    self.assertIn("project05_m3b_reliability_policy", report["summary"])
    self.assertIn("project05_m3b_policy", report["summary"])
    self.assertTrue((output_dir / "m3b_reliability_decoy_stress_results.csv").is_file())
```

- [ ] **Step 2：运行失败测试。**

```powershell
python -m unittest 09-experiments.tests.test_run_m3b_policy.M3bPolicyTests.test_reliability_stress_writes_adaptive_and_static_results
```

预期：失败信息包含 `run_reliability_decoy_stress_experiment`。

- [ ] **Step 3：实现配对评估和重复诱饵构造。**

为 `inject_matched_decoys` 增加 `copies_per_action: int = 1`。值为 1 时保留既有 `zz_decoy_<action_id>` 命名；值大于 1 时按 `zz_decoy_01_<action_id>`、`zz_decoy_02_<action_id>` 命名，且每个副本的 `recoverable_claim_ids=[]`。

每个 condition 必须写入自适应 M3b、静态 M3b 与所有规则基线；随后统一调用 `run_mvp.add_oracle_relative_metrics(rows)`。正常评估写入 `m3b_reliability_policy_results.csv`、`m3b_reliability_policy_summary.json`；压力测试写入 `m3b_reliability_decoy_stress_results.csv`、`m3b_reliability_decoy_stress_summary.json`。两个摘要均写明 case 数、成本惩罚、诱饵副本数、原始与扩增动作数、模型参数和按 planner 汇总指标。

- [ ] **Step 4：运行可复现实验。**

```powershell
python 09-experiments\scripts\run_m3b.py `
  --train-dir 09-experiments\examples `
  --test-dir 09-experiments\real_cases `
  --output-dir 09-experiments\results\m3b_reliability_toy_train_real_test `
  --label-column label_resolves_critical_gap_node `
  --evaluate-reliability-policy --reliability-decoy-stress --cost-penalty 0.1
```

记录正常与重复诱饵条件下的成功率、达标成本、预算使用、零产出动作数、相对 Oracle 成本遗憾。若结果未改善，研究记录必须如实报告，并检查 trace 是否在首次失败后降低相应组的可靠性。

- [ ] **Step 5：完成验证、记录与推送。**

```powershell
python -m unittest discover 09-experiments\tests
python -m py_compile 09-experiments\scripts\run_mvp.py 09-experiments\scripts\run_m3b.py
python -m json.tool 09-experiments\results\m3b_reliability_toy_train_real_test\m3b_reliability_policy_summary.json > $null
python -m json.tool 09-experiments\results\m3b_reliability_toy_train_real_test\m3b_reliability_decoy_stress_summary.json > $null
git diff --check
git add 09-experiments/scripts/run_m3b.py 09-experiments/tests/test_run_m3b_policy.py 09-experiments/results/m3b_reliability_toy_train_real_test 04-progress/m3b-reliability-feedback-experiment-20260710.md
git commit -m "experiment: evaluate m3b reliability feedback"
git push origin main
```

预期：测试全部通过，两个 JSON 文件可解析，Git 差异无空白错误。
