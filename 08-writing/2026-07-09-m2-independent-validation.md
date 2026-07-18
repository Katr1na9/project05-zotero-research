# M2 Independent Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen dynamic marginal-utility planner M2 and evaluate it on the held-out CADETS 2018-04-12 case C06.

**Architecture:** M2 scores actions only from public expected metadata, current coverage gaps, public action signatures, remaining budget, and post-action recovered-count feedback. C06 is extracted and compiled only after the M2 formula is implemented and tested, then used once as an internal held-out evaluation.

**Tech Stack:** Python 3 standard library, JSON/JSONL, CSV, `unittest`, existing DARPA CDM extractor and motif compiler.

## Global Constraints

- M2 must not inspect `hidden_ids`, `recoverable_claim_ids`, `oracle_effects`, or ground truth.
- The scoring coefficients in the approved design are frozen before C06 is run.
- C04/C05 remain development cases; C06 is the held-out validation case.
- Raw archives and extracted Event/Node files remain Git-ignored.
- C06 is an internal same-dataset-family holdout, not cross-dataset generalization evidence.

---

### Task 1: Public Action Metadata and Feedback

**Files:**
- Modify: `09-experiments/data_schema/acquisition_action.schema.json`
- Modify: `09-experiments/data_schema/alignment_state.schema.json`
- Modify: `09-experiments/scripts/run_mvp.py`
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/real_cases/C04-darpa-e3-fivedirections/acquisition_actions.json`
- Modify: `09-experiments/real_cases/C05-darpa-e3-cadets/acquisition_actions.json`

**Interfaces:**
- Action metadata adds `expected_stages: list[str]`.
- State adds `action_feedback: list[dict]`, each containing `action_id`, `action_type`, and `recovered_count`.
- `build_state(config, claims, actions, run_id, step_index, mask_strategy, mask_intensity, seed, visible_ids, hidden_ids, recovered_ids, actions_taken, budget_used, action_feedback=None) -> dict`.

- [ ] Write a failing test asserting that executed action `C01-AA-001` appears in the next state as `{"action_id": "C01-AA-001", "action_type": "extend_log_window", "recovered_count": 0}`.
- [ ] Run `python -m unittest 09-experiments/tests/test_run_mvp.py -v` and confirm RED.
- [ ] Add schema fields and thread the feedback list through `run_episode` and `build_state`.
- [ ] Add `expected_stages` to all C04/C05 actions based on their existing query semantics.
- [ ] Run the full test suite and commit with `experiment: add public action feedback`.

### Task 2: Frozen M2 Scoring

**Files:**
- Modify: `09-experiments/scripts/run_mvp.py`
- Modify: `09-experiments/tests/test_run_mvp.py`

**Interfaces:**
- Produces `action_signature(action: dict) -> set[str]`.
- Produces `m2_action_score(action: dict, state: dict, actions: list[dict]) -> float`.
- Registers planner name `project05_m2`.

- [ ] Write failing tests proving M2 selection is unchanged when `hidden_ids` changes and when only `recoverable_claim_ids` changes.
- [ ] Write failing tests proving zero-yield feedback lowers a same-type candidate score and signature overlap lowers an otherwise equal candidate score.
- [ ] Verify RED with the focused test suite.
- [ ] Implement the approved frozen formula exactly:

```text
2.00*granularity_gain + 1.50*uncertainty_reduction
+ 1.50*risk_reduction + 1.50*stage_gap + 1.00*evidence_gap
- 1.50*overlap - 1.00*no_yield_risk - 0.75*cost_ratio
```

- [ ] Use tie-breakers `lower cost`, `more expected stages`, then lexicographically smaller `action_id`.
- [ ] Run all tests and commit with `experiment: add frozen m2 planner`.

### Task 3: Extract the Held-out C06 Trace

**Files:**
- Modify: `09-experiments/real_data/darpa_tc_e3/manifest.json`
- Create: `09-experiments/real_data/darpa_tc_e3/ground_truth/R03.json`
- Create: `09-experiments/real_data/darpa_tc_e3/derived/R03_extraction_summary.json`
- Modify: `09-experiments/tests/test_real_manifest.py`
- Runtime ignored: `09-experiments/real_data/darpa_tc_e3/raw/ta1-cadets-e3-official-2.json.tar.gz`
- Runtime ignored: `09-experiments/real_data/darpa_tc_e3/extracted/R03/`

**Interfaces:**
- Source case R03 maps to CADETS 2018-04-12 and later becomes experimental case C06.
- UTC extraction window is `2018-04-12T17:30:00Z` through `2018-04-12T19:00:00Z`.

- [ ] Add a failing manifest test for R03 source/case cross-references and the exact UTC window.
- [ ] Extract the official-2 JSON archive from the already downloaded CADETS ZIP without modifying the ZIP.
- [ ] Run `extract_cdm_window.py` for R03 and validate zero invalid lines plus complete or explicitly quantified node resolution.
- [ ] Record source/output SHA-256 and observable checks in the compact derived summary.
- [ ] Run manifest and full tests, then commit with `experiment: extract held-out cadets trace`.

### Task 4: Compile C06 Without Changing M2

**Files:**
- Create: `09-experiments/real_cases/C06-darpa-e3-cadets-0412/motif_spec.json`
- Create: `09-experiments/real_cases/C06-darpa-e3-cadets-0412/case_config.json`
- Create: `09-experiments/real_cases/C06-darpa-e3-cadets-0412/acquisition_actions.json`
- Generate: `09-experiments/real_cases/C06-darpa-e3-cadets-0412/evidence_claims.json`
- Generate: `09-experiments/real_cases/C06-darpa-e3-cadets-0412/motif_report.json`
- Modify: `09-experiments/tests/test_real_cases.py`

**Interfaces:**
- C06 target and support ceiling are both `G3_campaign`.
- Motifs cover Nginx exploitation, payload delivery/execution, privilege activity, Drakon/Micro C2, and port scanning.

- [ ] Discover actual C06 process/path/IP/event combinations from the extracted CDM subset.
- [ ] Add a failing integrity test requiring exactly 10 observed real-CDM motifs, G3 target/ceiling, and action `expected_stages`.
- [ ] Define motif and action files without changing M2 code or coefficients.
- [ ] Compile claims and require 10/10 motif observations.
- [ ] Run all tests and commit with `experiment: add held-out cadets motif case`.

### Task 5: Held-out Evaluation and Transparent Report

**Files:**
- Create: `09-experiments/results/c06_holdout_results.csv`
- Create: `09-experiments/results/c06_holdout_summary.json`
- Create: `09-experiments/results/c06_holdout_analysis.json`
- Modify: `09-experiments/README.md`
- Modify: `04-progress/research-progress.md`

**Interfaces:**
- Runs all registered planners on C06 but reports the primary comparison among M2, frozen M1, CMI proxy, coverage greedy, and Oracle.

- [ ] Run the complete C06 matrix with 3 mask strategies, 3 intensities, 5 seeds, and all planners.
- [ ] Assert full-evidence reaches G3, no run exceeds the ceiling, and Oracle regret is never negative.
- [ ] Report success rate, success cost, Oracle regret, zero-yield action count, overlapping-action waste, and Oracle top-1 hit.
- [ ] Preserve the result whether M2 wins, ties, or loses; do not modify M2 after observing C06.
- [ ] Run full tests, Python compilation, JSON parsing, result gates, and `git diff --check`.
- [ ] Commit with `experiment: report c06 holdout evaluation` and push `main`.
