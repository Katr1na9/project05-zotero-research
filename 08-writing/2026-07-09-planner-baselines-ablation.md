# Planner Baselines and Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Oracle leakage from ordinary planners and add honest Oracle, CMI proxy, and M1 ablation experiments.

**Architecture:** Keep hidden evidence inside the environment transition. Ordinary planners score only current state and public action metadata; Oracle receives explicit privileged access. Planner variants share one M1 component scorer so each ablation removes exactly one term.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, CSV.

## Global Constraints

- Only `oracle_optimal` may inspect `hidden_ids` while scoring actions.
- `cmi_proxy` must never be described as true conditional mutual information.
- Preserve the three-case factorial experiment and case-level independence.
- Do not introduce real attack data in this implementation batch.

---

### Task 1: Enforce Planner Information Boundary

**Files:**
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

- [ ] Write a failing test where public state/action metadata are unchanged but hidden evidence differs; assert `coverage_greedy` and `project05_m1` choose the same action.
- [ ] Run `python -m unittest discover -s 09-experiments/tests -v` and confirm the test fails.
- [ ] Replace hidden-outcome scoring in ordinary planners with `expected_effects` scoring.
- [ ] Run the test suite and confirm it passes.

### Task 2: Add Oracle and CMI Proxy

**Files:**
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

- [ ] Write failing tests proving `oracle_optimal` reacts to changed hidden outcomes and `cmi_proxy` ranks by expected uncertainty reduction per cost.
- [ ] Confirm RED with the full unit-test command.
- [ ] Implement both planners and add them to `PLANNERS`.
- [ ] Confirm GREEN with the full unit-test command.

### Task 3: Add M1 Ablations and Oracle-relative Metrics

**Files:**
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

- [ ] Write failing tests for the five ablation names and for `cost_regret_vs_oracle`.
- [ ] Confirm RED.
- [ ] Implement a shared M1 component scorer and variant masks.
- [ ] Add post-run Oracle cost/action metrics grouped by case, mask, intensity, and seed.
- [ ] Confirm GREEN.

### Task 4: Re-run Matrix and Document Corrected Results

**Files:**
- Modify: `09-experiments/results/all_cases_results.csv`
- Modify: `09-experiments/results/all_cases_summary.json`
- Modify: `09-experiments/README.md`
- Modify: `04-progress/research-progress.md`

- [ ] Run the complete three-case matrix.
- [ ] Validate all JSON records and result counts.
- [ ] Record corrected results and explicitly retire the leakage-affected snapshot.
- [ ] Run `python -m py_compile`, the full test suite, and `git diff --check`.
