# C11 OTRF APT29 Day 1 AND Multi-Claim Result

Date: 2026-07-12
Case: `C11-otrf-apt29-day1-scranton-nashua`
Primary semantics: `AND`
Target/support ceiling: `G2_tactic_intent`

## Result scope

C11 is a parameter-locked third-data-family case compiled from the OTRF APT29 Day 1 emulation. It is not a real-world unknown-actor attribution benchmark. The independent unit is one emulated attack chain; the 45 mask/intensity/seed conditions per planner are repeated measurements.

The frozen `3aka3.doc` anchor matched no event. N01 remains unsupported, so C11 is correctly downgraded from the preregistered G3 ceiling to a compiled G2 target. Four remaining nodes each require two claims from distinct Windows provider families.

## Main results

| Planner | Runs | Success | Mean cost | Regret vs Oracle | Premature STOP |
|---|---:|---:|---:|---:|---:|
| Oracle | 45 | 1.0000 | 3.0000 | 0.0000 | 0.0000 |
| M1 / coverage / CMI | 45 each | 1.0000 | 3.2444 | 0.2444 | 0.0000 |
| M3a | 45 | 1.0000 | 3.5556 | 0.5556 | 0.0000 |
| M2 | 45 | 1.0000 | 3.6667 | 0.6667 | 0.0000 |
| Random | 45 | 0.6000 | 3.4444 on success | 0.6889 | 0.4000 |

All planners have zero ceiling violations. M2 is not the lowest-cost non-Oracle method on C11; this result must not be combined with the C07-C10 G3 mean as if targets and source types were identical.

## OR sensitivity

The same claims, actions, masks, seeds, target and ceiling were rerun with only `node_coverage_semantics` changed from `AND` to `OR`. M2 success remains 1.0000, but mean cost falls from 3.6667 to 1.0222, a difference of -2.6445. Oracle also falls from 3.0000 to 1.0222.

This is sensitivity evidence that OR semantics treats a single claim as sufficient too early in this case. AND remains the preregistered main analysis; OR does not replace it.

## Files

- `*_mvp_results.csv`: 630 rows, 14 planners x 45 repeated conditions.
- `*_mvp_summary.json`: planner-level summary.
- `*_mvp_traces.json`: local-only generated traces, ignored by Git.
- OR sensitivity: `../c11_or_sensitivity_v0.1/`.

## Boundaries

- C11 closes an engineering data-family/multi-claim gap, not human granularity validity.
- APT29 is an emulation label, not an actor prediction endpoint.
- Host and Zeek packages do not overlap in time; Zeek contributes no event-level claim.
- C11 is one case and cannot support broad statistical generalization.
