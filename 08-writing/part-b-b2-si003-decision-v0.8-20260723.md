# PB-SI-003 exact-finite decision closeout plan

Status: **LOCAL REVIEW — DECISION ONLY**

```text
PB-SI-003: CLOSED — APPROVED FOR EXACT FINITE TABLES
World pairs: all legal worlds partitioned by q; complete support × alternative
Pair form: unordered / lexicographically canonical / frozen pre-outcome
Threshold: per-action exact rational delta_a, inclusive >=
Aggregation: MINIMUM_TV_WORST_CASE
sampling_authority=false
Estimated-model acceptance: UNRESOLVED_PB_B2_SI_003
CERTIFIED_STOP: UNCHANGED
```

## Exact allowlist

1. `schemas/part-b-b2-world-pair-delta-decision.schema.json`
2. `configs/part-b-b2-world-pair-delta-decision-v0.8.yaml`
3. `contracts/part-b-b2-world-pair-delta-decision-v0.8.md`
4. `contracts/part-b-b2-boundary-v0.8.md`
5. `contracts/part-b-b2-stochastic-observation-v0.8.md`
6. `src/scope/part-b-b0-spec-issues.md`
7. `src/scope/part-b-b2-spec-issues.md`
8. `tests/unit/test_part_b_b2_si003_world_pair_delta.py`
9. `08-writing/part-b-b2-si003-decision-v0.8-20260723.md`
10. `08-writing/KERNEL-V0.8-AUTHORITY-STATUS-20260722.md`

No B2 YAML/hash is modified. No sampler, stochastic executor, connector,
dataset, Claim IR, Part A behavior, Planner/M3*, LLM or experiment path is in
the allowlist.

## RED / GREEN

RED was recorded when the new test failed because the decision Schema did not
exist. GREEN requires the new decision tests, existing B2 tests, the complete
repository suite, `compileall`, `git diff --check`, canonical hash replay and
an exact ten-file diff audit.

Passing those checks closes the stated semantics only. It does not approve a
production executable catalog and does not turn `sampling_authority=false`
into sampler authority. `UNRESOLVED_PB_B2_SI_003` and the simulation gate
remain independently open. No change is made to `CERTIFIED_STOP`.

## Local verification record

```text
Decision tests: 9/9 PASS
B2 + decision targeted tests: 24/24 PASS
Full repository tests: 180/180 PASS
python -m compileall -q src tests: PASS
git diff --check: PASS
Exact allowlist: 10/10 files
Staged files: NONE
Commit / push / PR: NOT PERFORMED
```

Decision artifact identity:

```text
sha256:1a9668ef8c968c968e14587778d261b023dff60a0234e4e67251051ec07e5919
```

The frozen B2 catalog, TV-policy and manifest hashes replay unchanged.
