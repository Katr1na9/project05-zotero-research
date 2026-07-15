# Devil's Advocate Report - Checkpoint 2

Review target: literature synthesis, residual-gap claim and three candidate thesis topics.
Verdict: **PASS WITH MAJOR CONDITIONS**

## Critical Issues

No critical issue blocks presenting the candidates to the user. Implementation remains blocked until the user selects a topic and pilot relation annotation passes.

## Major Issues

### 1. Residual-gap evidence is absence-based

- Type: evidence/novelty.
- Problem: no located direct equivalent does not prove no equivalent exists, especially across inaccessible IEEE/ACM papers, patents and industrial systems.
- Impact: “first” claims would be indefensible.
- Required fix: use scoped wording (“we formulate/evaluate...”) and repeat the exact-title/functional search before submission. Never claim universal absence.

### 2. Relation truth may be circular

- Type: methodology.
- Problem: if packet-log positive labels are created with the same time/five-tuple/PID rule used as a baseline, a learned model can only reproduce the annotation rule.
- Impact: the central R2 contribution becomes invalid.
- Required fix: define relation semantics independently, double-annotate ambiguous pairs, include hard negatives and use raw scenario ground truth.

### 3. Calibration requires enough independent units

- Type: statistics.
- Problem: millions of record pairs are not millions of independent samples; campaign/host/time correlation can make ECE and confidence intervals look artificially strong.
- Impact: overstated reliability and leakage.
- Required fix: split by campaign, bootstrap at campaign/scenario level and report per-campaign calibration, not only pooled pair metrics.

### 4. “Intent” is under-defined

- Type: construct validity.
- Problem: ATT&CK tactic, attack objective, actor motive and malicious event intent are currently adjacent but distinct constructs.
- Impact: Candidate C can become subjective relabeling.
- Required fix: freeze a small ontology, provide annotator instructions, measure agreement and drop high-level intent if agreement is inadequate.

### 5. Dual-source gain may only reflect extra information

- Type: alternative explanation.
- Problem: a joint graph may beat single-source baselines simply because it receives more observations, not because the proposed relation model is better.
- Impact: causal claim about relation calibration would be unsupported.
- Required fix: compare equal candidate evidence budgets, deterministic joins, uncalibrated learned links and oracle links; plot downstream performance against controlled link corruption.

### 6. Project03 protocol diversity may overload the thesis

- Type: scope.
- Problem: IPv4/IPv6/MPLS/Geo/SCION could become five separate engineering tracks.
- Impact: core R2 experiment may never stabilize.
- Required fix: treat them as environment strata. Implement only strata present in the chosen data; do not promise five complete pipelines.

## Minor Issues

- Raw PCAP may contain sensitive payloads; use public datasets and document minimization/redaction.
- Timestamp synchronization and parser-version drift must be recorded in the Material Passport.
- Patent redlines need final CNIPA/legal verification if commercialization or patent filing is considered.
- LLM model/version/prompt changes can confound results; freeze prompts and retain structured outputs.

## Strongest Counter-Argument

“The proposed method is an elaborate learned join between records that could be matched adequately with time, five-tuples and PIDs; any downstream gain comes from additional telemetry, while calibration and LLM explanations add presentation rather than new security capability.”

The experiment must answer this directly with deterministic-join baselines, oracle links, controlled edge corruption, source-budget controls and campaign-level uncertainty.

## What's Missing Before Implementation

- pilot dataset manifest and confirmed license;
- relation ontology and double-annotation agreement;
- power/sample justification at campaign level;
- final user-selected RQ;
- precise compute and annotation budget.

## Stress Test Results

| Test | Result |
|---|---|
| Remove APTGuard/BotFence, does the broad collision still hold? | yes; historical evidence-graph and multi-log works remain |
| Remove APMP/MPCA, does R2 still look distinct? | yes, but confidence wording becomes less constrained |
| Flip the RQ: deterministic joins are sufficient | credible and must be a serious null hypothesis |
| Apply outside ICS | not yet proven; AIT v2 external test is required |
| Remove the LLM | thesis core still holds under Candidate B |
| “So what?” | justified only if calibrated links improve chain fidelity, selective risk or analyst verification |

## Checkpoint Decision

PASS to user review of candidates. Do not proceed to dataset acquisition or implementation until the user chooses the topic and accepts the scope hierarchy.
