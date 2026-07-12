# C11 OR Semantics Sensitivity

This directory is a one-field sensitivity run over the frozen C11 case:

```json
{"node_coverage_semantics": "OR"}
```

Claims, actions, target, support ceiling, masks, seeds, budgets and planner code are unchanged. The source C11 config is AND and remains the primary analysis.

| Planner | AND cost | OR cost | OR - AND | Success in both |
|---|---:|---:|---:|---:|
| Oracle | 3.0000 | 1.0222 | -1.9778 | 1.0000 |
| M1 / coverage / CMI | 3.2444 | 1.0222 | -2.2222 | 1.0000 |
| M3a | 3.5556 | 1.0222 | -2.5334 | 1.0000 |
| M2 | 3.6667 | 1.0222 | -2.6445 | 1.0000 |

Interpretation: OR materially reduces the evidence required to mark nodes covered. It is an optimistic sensitivity condition, not a replacement for the preregistered AND result.
