# DARPA E3 Motif Experiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile the extracted R01/R02 DARPA E3 traces into behavior-motif evidence claims and run the first M1/CMI/Oracle comparison on real attack data.

**Architecture:** A deterministic compiler loads the bounded node set, streams the bounded event set once, evaluates case-specific motif rules, and emits auditable `evidence_claims.json`. Real case configs and acquisition actions reuse the existing simulator, with an explicit support ceiling preventing R02 from being promoted above its naturally supportable G2 level.

**Tech Stack:** Python 3 standard library, JSON/JSONL, `unittest`, existing Project05 simulator.

## Global Constraints

- Raw Event/Node files remain under Git-ignored `extracted/`.
- Every generated motif claim records match count, first/last timestamp, and representative Event UUIDs.
- Ground truth may define motif rules only in the offline case-construction layer.
- Ordinary planners may not inspect hidden claim outcomes.
- R01 target and ceiling are `G3_campaign`; R02 target and ceiling are `G2_tactic_intent`.
- R01/R02 are development cases and cannot support a generalization claim.

---

### Task 1: Deterministic Motif Compiler

**Files:**
- Create: `09-experiments/scripts/compile_real_motifs.py`
- Create: `09-experiments/tests/test_compile_real_motifs.py`

**Interfaces:**
- Consumes: `events.jsonl`, `nodes.jsonl`, and a motif specification containing `motif_id`, `match`, and `claim`.
- Produces: `compile_motifs(events_path: Path, nodes_path: Path, spec: dict) -> tuple[list[dict], dict]`.

- [ ] **Step 1: Write a failing end-to-end fixture test**

Create a tiny node/event fixture with process, file, and NetFlow nodes. Assert that a rule combining `process`, `event_type`, and `remote_ip` emits one claim with the correct representative Event UUID and match count.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python -m unittest 09-experiments/tests/test_compile_real_motifs.py -v
```

Expected: failure because `compile_real_motifs.py` does not exist.

- [ ] **Step 3: Implement normalized event context**

Implement `build_node_lookup(nodes_path: Path) -> dict[str, dict]` and `event_context(event: dict, nodes: dict[str, dict]) -> dict`. The context must expose `event_type`, `process`, `path`, `remote_ip`, `subject_uuid`, and `predicate_uuid`. Use `raw.properties.map.exec`, `raw.properties.map.image_path`, `predicateObjectPath`, and referenced node attributes without using ground-truth fields.

- [ ] **Step 4: Implement rule matching and claim audit fields**

Implement exact-match and case-insensitive substring/list operators for normalized context fields. Emit only motifs with at least one real match. Add `source_pointer.record_id`, `notes`, and tags containing `real_cdm`, `hideable`, stage, and CTI node.

- [ ] **Step 5: Verify GREEN and commit**

Run the focused and full test suites, then commit:

```powershell
git add 09-experiments/scripts/compile_real_motifs.py 09-experiments/tests/test_compile_real_motifs.py
git commit -m "experiment: add real cdm motif compiler"
```

### Task 2: Support Ceiling and Correct-stop Metrics

**Files:**
- Modify: `09-experiments/scripts/run_mvp.py`
- Modify: `09-experiments/tests/test_run_mvp.py`

**Interfaces:**
- Consumes: optional `support_ceiling` in `case_config.json`.
- Produces: ceiling-clamped `supportable_granularity` and result fields `support_ceiling`, `correct_stop`, and `ceiling_violation`.

- [ ] **Step 1: Write failing ceiling tests**

Add a config whose evidence coverage normally supports G3 but whose `support_ceiling` is G2. Assert:

```python
self.assertEqual(
    "G2_tactic_intent",
    run_mvp.supportable_granularity(config, visible_ids),
)
```

Add an episode assertion that final G2 is a correct stop and is not a ceiling violation.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python -m unittest 09-experiments/tests/test_run_mvp.py -v
```

Expected: the ceiling test reports G3 before implementation.

- [ ] **Step 3: Implement the clamp**

Compute the structural granularity as before, then return:

```python
ceiling = config.get("support_ceiling", structural_granularity)
return min(
    (structural_granularity, ceiling),
    key=lambda level: granularity_index(config, level),
)
```

Add result metrics based only on final granularity and public config.

- [ ] **Step 4: Verify GREEN and commit**

Run the full suite and commit:

```powershell
git add 09-experiments/scripts/run_mvp.py 09-experiments/tests/test_run_mvp.py
git commit -m "experiment: enforce attribution support ceiling"
```

### Task 3: Build R01/R02 Real Cases

**Files:**
- Create: `09-experiments/real_cases/C04-darpa-e3-fivedirections/motif_spec.json`
- Create: `09-experiments/real_cases/C04-darpa-e3-fivedirections/case_config.json`
- Create: `09-experiments/real_cases/C04-darpa-e3-fivedirections/acquisition_actions.json`
- Generate: `09-experiments/real_cases/C04-darpa-e3-fivedirections/evidence_claims.json`
- Create: `09-experiments/real_cases/C05-darpa-e3-cadets/motif_spec.json`
- Create: `09-experiments/real_cases/C05-darpa-e3-cadets/case_config.json`
- Create: `09-experiments/real_cases/C05-darpa-e3-cadets/acquisition_actions.json`
- Generate: `09-experiments/real_cases/C05-darpa-e3-cadets/evidence_claims.json`
- Create: `09-experiments/tests/test_real_cases.py`

**Interfaces:**
- C04 maps to source case R01 and uses G3 target/ceiling.
- C05 maps to source case R02 and uses G2 target/ceiling.

- [ ] **Step 1: Discover and record motif signatures**

Use one-pass searches over the ignored Event/Node subsets to confirm process names, paths, IPs, event types, and representative UUIDs. Do not infer an observed motif solely from the ground-truth report.

- [ ] **Step 2: Write failing cross-reference tests**

Assert every required claim exists, every action recovers only hideable claims, C04 has G3 target/ceiling, C05 has G2 target/ceiling, and every generated claim contains `real_cdm`.

- [ ] **Step 3: Define motif specs**

Use exactly 8 behavior motifs per case. C04 must cover execution, C2, discovery, collection, and exfiltration. C05 must cover initial execution, payload activity, C2, and discovery/injection attempt; the G2 support ceiling represents the absent complete collection/exfiltration chain without inventing a positive or negative CDM event.

- [ ] **Step 4: Compile claims and define actions**

Run:

```powershell
python 09-experiments/scripts/compile_real_motifs.py --spec <spec> --events <events> --nodes <nodes> --output <evidence_claims>
```

Actions must group claims by actual query surface: host subgraph, network summary, time-window extension, and local TTP probe.

- [ ] **Step 5: Verify and commit**

Run all tests and commit the two complete real case directories.

### Task 4: Run and Report the Real-data Matrix

**Files:**
- Create: `09-experiments/results/real_e3_results.csv`
- Create: `09-experiments/results/real_e3_summary.json`
- Modify: `09-experiments/README.md`
- Modify: `04-progress/research-progress.md`

**Interfaces:**
- Consumes: C04/C05 real case directories through `run_mvp.run_cases`.
- Produces: planner results stratified by case, mask strategy, and mask intensity.

- [ ] **Step 1: Run the complete real-case matrix**

Use the existing 20%, 40%, and 60% mask intensities, three mask strategies, fixed seeds, all planners, and M1 ablations.

- [ ] **Step 2: Validate results**

Assert no negative Oracle cost regret, C04 full-evidence reaches G3, C05 full-evidence stops at G2, and no run exceeds its support ceiling.

- [ ] **Step 3: Summarize without pseudoreplication**

Report per-case and per-condition metrics. Label seeds as repeated runs, not independent attack samples.

- [ ] **Step 4: Verify and commit**

Run:

```powershell
python -m unittest discover -s 09-experiments/tests -v
python -m py_compile 09-experiments/scripts/*.py
git diff --check
```

Commit the result tables, summaries, and documentation.
