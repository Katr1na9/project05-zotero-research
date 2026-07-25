# Multi-case Experiment Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalize the C01 simulator so it can run multiple cases across mask intensities and produce auditable, stratified results.

**Architecture:** Keep the simulator dependency-free and preserve the existing case JSON interface. Separate experiment-matrix expansion, case execution, and result aggregation into testable functions; expose both one-case and all-case CLI modes.

**Tech Stack:** Python 3 standard library, `unittest`, JSON, CSV.

## Global Constraints

- Preserve the current C01 behavior when only its configured mask intensity is used.
- Treat a case as the independent experimental unit; seeds and masks are repeated measurements.
- Keep large raw datasets and source reports outside Git.
- Do not add LLM, Agent, RL, or model-training code in this phase.

---

### Task 1: Experiment Matrix and Mask Intensity Override

**Files:**
- Create: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

**Interfaces:**
- Produces: `experiment_conditions(config) -> list[tuple[str, float, int]]`
- Produces: `build_hidden_claims(config, claims, strategy, seed, mask_intensity=None) -> set[str]`
- Produces: result rows containing `mask_intensity`.

- [ ] **Step 1: Write failing tests**

Add tests asserting that three strategies, three intensities, and two seeds generate 18 conditions; an explicit intensity overrides case configuration; and run IDs differ by intensity.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: FAIL because `experiment_conditions` and the override parameter do not exist.

- [ ] **Step 3: Implement matrix expansion**

Read `mask_intensities` when present, otherwise fall back to `[mask_intensity]`. Pass the selected intensity through masking, state construction, run IDs, traces, and result rows.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: all Task 1 tests pass.

### Task 2: Multi-case Batch Runner

**Files:**
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

**Interfaces:**
- Produces: `discover_case_dirs(examples_dir) -> list[Path]`
- Produces: `run_cases(case_dirs, output_dir, write_traces=True) -> list[dict]`
- CLI accepts mutually exclusive `--case-dir` and `--examples-dir`.

- [ ] **Step 1: Write failing tests**

Add temporary C01/C02 directories and assert discovery ignores incomplete folders, sorts case IDs, and rejects duplicate case IDs.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: FAIL because multi-case discovery and execution do not exist.

- [ ] **Step 3: Implement batch execution**

Load each complete case directory, validate unique case IDs, execute every experimental condition and planner, then write:

```text
all_cases_results.csv
all_cases_summary.json
all_cases_traces.json
```

Keep the existing one-case CLI path for compatibility.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: all Task 1-2 tests pass.

### Task 3: Stratified Statistical Summary

**Files:**
- Modify: `09-experiments/tests/test_run_mvp.py`
- Modify: `09-experiments/scripts/run_mvp.py`

**Interfaces:**
- Produces: `summarize_stratified(rows) -> dict`
- Summary levels: overall planner, case/planner, mask strategy/intensity/planner.

- [ ] **Step 1: Write failing tests**

Use four synthetic rows to assert success rate, successful-run cost, and the number of independent cases are computed without treating seeds as extra cases.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: FAIL because stratified summary does not exist.

- [ ] **Step 3: Implement aggregation**

Generate overall and stratified tables while explicitly reporting `independent_case_count` and `repeated_run_count`.

- [ ] **Step 4: Verify GREEN**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: all tests pass.

### Task 4: C02/C03 and Documentation

**Files:**
- Create: `09-experiments/examples/C02/case_config.json`
- Create: `09-experiments/examples/C02/evidence_claims.json`
- Create: `09-experiments/examples/C02/acquisition_actions.json`
- Create: `09-experiments/examples/C03/case_config.json`
- Create: `09-experiments/examples/C03/evidence_claims.json`
- Create: `09-experiments/examples/C03/acquisition_actions.json`
- Modify: `09-experiments/README.md`
- Modify: `04-progress/research-progress.md`

**Interfaces:**
- Consumes: the unchanged three-file case interface.
- Produces: FreeBSD and Windows toy scenarios with distinct evidence types and actions.

- [ ] **Step 1: Add schema and semantic validation tests**

Assert each case has unique claim/action IDs, every CTI node requirement references a claim, and every action recovery target references a hideable claim.

- [ ] **Step 2: Verify RED**

Run: `python -m unittest discover -s 09-experiments/tests -v`

Expected: FAIL because C02/C03 do not exist.

- [ ] **Step 3: Construct C02/C03**

C02 models a FreeBSD provenance chain with process, file, network, and a noisy noncritical claim. C03 models a Windows chain with process, registry, PowerShell, file, network, and command-line evidence.

- [ ] **Step 4: Run the full matrix**

Run:

```powershell
python .\09-experiments\scripts\run_mvp.py --examples-dir .\09-experiments\examples
```

Expected: all three cases execute and the aggregate outputs contain every case, planner, mask strategy, and configured intensity.

- [ ] **Step 5: Verify and document**

Run:

```powershell
python -m unittest discover -s 09-experiments/tests -v
python -m py_compile 09-experiments/scripts/run_mvp.py
git diff --check
```

Record the exact case count, run count, and key aggregate results in the experiment README and progress log.
